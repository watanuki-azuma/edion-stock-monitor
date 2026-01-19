"""
エディオン用サイトハンドラー
"""

from playwright.async_api import Page
from .base import BaseSiteHandler, ProductInfo


class EdionHandler(BaseSiteHandler):
    """エディオン専用のハンドラー"""
    
    SITE_ID = "edion"
    SITE_NAME = "エディオン"
    
    AVAILABLE_KEYWORDS = ["カートに入れる", "予約する", "在庫あり", "予約受付中"]
    SOLDOUT_KEYWORDS = ["売り切れ", "在庫なし", "販売終了", "予約終了"]
    
    async def fetch_product_info(self, page: Page, url: str) -> ProductInfo | None:
        """エディオン商品ページから情報を取得"""
        try:
            # ページにアクセス
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # コンテンツ読み込み待機
            try:
                await page.wait_for_selector("h1", timeout=10000)
            except Exception:
                pass
            
            await page.wait_for_timeout(3000)
            
            # ページテキストを取得
            page_text = await page.inner_text("body")
            
            # 商品名を取得
            try:
                name = await page.inner_text("h1")
                name = name.strip()
            except Exception:
                name = "商品名取得失敗"
            
            # 価格を取得
            try:
                price_elem = page.locator(".price, .item-price, .selling-price").first
                price = await price_elem.inner_text()
                price = price.strip()
            except Exception:
                price = "価格取得失敗"
            
            # カートボタンの状態を確認
            cart_button_enabled = False
            try:
                cart_button = page.locator('button:has-text("カート"), button:has-text("予約")').first
                is_disabled = await cart_button.get_attribute("disabled")
                cart_button_enabled = is_disabled is None
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
            print(f"[ERROR] {self.SITE_NAME}: ページ取得に失敗 - {e}")
            return None
