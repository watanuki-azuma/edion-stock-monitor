"""
ヨドバシカメラ用サイトハンドラー
"""

from playwright.async_api import Page
from .base import BaseSiteHandler, ProductInfo


class YodobashiHandler(BaseSiteHandler):
    """ヨドバシカメラ専用のハンドラー"""

    SITE_ID = "yodobashi"
    SITE_NAME = "ヨドバシカメラ"

    AVAILABLE_KEYWORDS = ["カートに入れる", "在庫あり", "在庫あり（在庫僅少）"]
    SOLDOUT_KEYWORDS = ["在庫なし", "販売終了", "予定数の販売を終了", "お取り寄せ"]

    async def fetch_product_info(self, page: Page, url: str) -> ProductInfo | None:
        """ヨドバシ商品ページから情報を取得"""
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if not response or response.status != 200:
                print(f"[ERROR] {self.SITE_NAME}: HTTPステータス {response.status if response else 'None'}")
                return None

            await page.wait_for_timeout(3000)
            page_text = await page.inner_text("body")

            if "Access Denied" in page_text or "アクセスが拒否" in page_text:
                print(f"[ERROR] {self.SITE_NAME}: アクセス拒否")
                return None

            try:
                name = await page.inner_text("h1")
                name = name.strip()
            except Exception:
                name = "商品名取得失敗"

            try:
                price_elem = page.locator(
                    ".priceYen, #js_scl_p, .productPrice .price"
                ).first
                price = await price_elem.inner_text()
                price = price.strip()
            except Exception:
                price = "価格取得失敗"

            cart_button_enabled = False
            try:
                cart_button = page.locator(
                    'button:has-text("カートに入れる"), a:has-text("カートに入れる")'
                ).first
                is_visible = await cart_button.is_visible()
                if is_visible:
                    is_disabled = await cart_button.get_attribute("disabled")
                    cart_button_enabled = is_disabled is None
            except Exception:
                pass

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
