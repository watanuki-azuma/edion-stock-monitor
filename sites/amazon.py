"""
Amazon.co.jp用サイトハンドラー
"""

from playwright.async_api import Page
from .base import BaseSiteHandler, ProductInfo


class AmazonHandler(BaseSiteHandler):
    """Amazon.co.jp専用のハンドラー"""

    SITE_ID = "amazon"
    SITE_NAME = "Amazon"

    AVAILABLE_KEYWORDS = ["カートに入れる", "通常注文", "在庫あり"]
    SOLDOUT_KEYWORDS = ["在庫切れ", "現在在庫切れ", "販売を終了しました", "在庫なし"]

    async def fetch_product_info(self, page: Page, url: str) -> ProductInfo | None:
        """Amazon商品ページから情報を取得"""
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if not response or response.status != 200:
                print(f"[ERROR] {self.SITE_NAME}: HTTPステータス {response.status if response else 'None'}")
                return None

            await page.wait_for_timeout(3000)
            page_text = await page.inner_text("body")

            if "To discuss automated access" in page_text or "Access Denied" in page_text:
                print(f"[ERROR] {self.SITE_NAME}: アクセス拒否")
                return None

            try:
                name = await page.inner_text("#productTitle")
                name = name.strip()
            except Exception:
                name = "商品名取得失敗"

            try:
                price_elem = page.locator(
                    "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen, "
                    "#corePriceDisplay_mobile_feature_div .a-price .a-offscreen, "
                    ".a-price .a-offscreen"
                ).first
                price = await price_elem.inner_text()
                price = price.strip()
            except Exception:
                price = "価格取得失敗"

            cart_button_enabled = False
            try:
                cart_button = page.locator("#add-to-cart-button").first
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
