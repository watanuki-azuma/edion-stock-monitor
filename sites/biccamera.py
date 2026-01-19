"""
ビックカメラ用サイトハンドラー

ビックカメラはBot対策が厳しいため、リトライロジックと
より人間らしいブラウザ設定を使用。
"""

import asyncio
from playwright.async_api import Page, BrowserContext
from .base import BaseSiteHandler, ProductInfo


class BiccameraHandler(BaseSiteHandler):
    """ビックカメラ専用のハンドラー"""
    
    SITE_ID = "biccamera"
    SITE_NAME = "ビックカメラ"
    
    AVAILABLE_KEYWORDS = ["カートに入れる", "予約する", "在庫あり"]
    SOLDOUT_KEYWORDS = ["売り切れ", "在庫なし", "販売終了", "販売休止中", "予定数の販売を終了"]
    
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # 秒
    
    async def fetch_product_info(self, page: Page, url: str) -> ProductInfo | None:
        """ビックカメラ商品ページから情報を取得（リトライ付き）"""
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    print(f"        リトライ {attempt + 1}/{self.MAX_RETRIES}...")
                    await asyncio.sleep(self.RETRY_DELAY)
                
                # ランダムな遅延を入れてより人間らしく
                await page.wait_for_timeout(1000 + (attempt * 500))
                
                # ページにアクセス（HTTP/1.1を強制するためにオプション変更）
                response = await page.goto(url, wait_until="load", timeout=60000)
                
                if response and response.status >= 400:
                    print(f"        HTTP {response.status} エラー")
                    continue
                
                # コンテンツ読み込み待機
                try:
                    await page.wait_for_selector("body", timeout=10000)
                except Exception:
                    pass
                
                await page.wait_for_timeout(3000)
                
                # ページテキストを取得
                page_text = await page.inner_text("body")
                
                # アクセス拒否の検出
                if "Access Denied" in page_text or "アクセスが拒否" in page_text:
                    print(f"        アクセス拒否を検出")
                    continue
                
                # 商品名を取得
                try:
                    # ビックカメラの商品タイトル
                    name_elem = page.locator(".bcs_title, .itemDetailHeader h1, h1").first
                    name = await name_elem.inner_text()
                    name = name.strip()[:100]  # 長すぎる場合は切り詰め
                except Exception:
                    name = "商品名取得失敗"
                
                # 価格を取得
                try:
                    price_elem = page.locator(".bcs_price .val, .price .val, .itemPrice").first
                    price = await price_elem.inner_text()
                    price = price.strip()
                except Exception:
                    price = "価格取得失敗"
                
                # カートボタンの状態を確認
                cart_button_enabled = False
                try:
                    cart_button = page.locator('.bcs_cart_btn button, .addtocart, button:has-text("カートに入れる")').first
                    is_visible = await cart_button.is_visible()
                    if is_visible:
                        is_disabled = await cart_button.get_attribute("disabled")
                        btn_class = await cart_button.get_attribute("class") or ""
                        cart_button_enabled = is_disabled is None and "gray" not in btn_class
                except Exception:
                    pass
                
                # 在庫状態を判定
                status, is_available = self.check_availability(page_text, cart_button_enabled)
                
                return ProductInfo(
                    name=name,
                    price=price,
                    status=status,
                    is_available=is_available,
                    url=url,
                )
                
            except Exception as e:
                error_msg = str(e)
                if "ERR_HTTP2_PROTOCOL_ERROR" in error_msg:
                    print(f"        HTTP/2エラー - リトライします")
                else:
                    print(f"[ERROR] {self.SITE_NAME}: {e}")
                
                if attempt == self.MAX_RETRIES - 1:
                    return None
        
        return None
