"""
ビックカメラ用サイトハンドラー（Firefox版）

ビックカメラはChromiumでBot対策により弾かれるため、
Firefoxブラウザを使用する。
"""

from playwright.async_api import Page
from .base import BaseSiteHandler, ProductInfo


class BiccameraHandler(BaseSiteHandler):
    """ビックカメラ専用のハンドラー（Firefox使用）"""
    
    SITE_ID = "biccamera"
    SITE_NAME = "ビックカメラ"
    
    # Firefoxを使用するフラグ
    USE_FIREFOX = True
    
    AVAILABLE_KEYWORDS = ["カートに入れる", "予約する", "在庫あり"]
    SOLDOUT_KEYWORDS = ["売り切れ", "在庫なし", "販売終了", "販売休止中", "予定数の販売を終了"]
    
    async def fetch_product_info(self, page: Page, url: str) -> ProductInfo | None:
        """ビックカメラ商品ページから情報を取得"""
        try:
            # ページにアクセス
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            if not response or response.status != 200:
                print(f"[ERROR] {self.SITE_NAME}: HTTPステータス {response.status if response else 'None'}")
                return None
            
            # コンテンツ読み込み待機
            await page.wait_for_timeout(3000)
            
            # ページテキストを取得
            page_text = await page.inner_text("body")
            
            # アクセス拒否チェック
            if "Access Denied" in page_text or "アクセスが拒否" in page_text:
                print(f"[ERROR] {self.SITE_NAME}: アクセス拒否")
                return None
            
            # 商品名を取得
            try:
                name_elem = page.locator("h1").first
                name = await name_elem.inner_text()
                name = name.strip()[:100]
            except Exception:
                name = "商品名取得失敗"
            
            # 価格を取得
            try:
                price_elem = page.locator(".bcs_price .val, .price .val, .itemPrice, .price").first
                price = await price_elem.inner_text()
                price = price.strip()
            except Exception:
                price = "価格取得失敗"
            
            # カートボタンの状態を確認
            cart_button_enabled = False
            try:
                cart_button = page.locator('button:has-text("カートに入れる")').first
                is_visible = await cart_button.is_visible()
                if is_visible:
                    is_disabled = await cart_button.get_attribute("disabled")
                    btn_class = await cart_button.get_attribute("class") or ""
                    cart_button_enabled = is_disabled is None and "gray" not in btn_class.lower()
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
