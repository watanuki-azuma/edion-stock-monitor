"""
サイトハンドラー基底クラス

各サイト固有のスクレイピングロジックを実装するための抽象基底クラス。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from playwright.async_api import Page


@dataclass
class ProductInfo:
    """商品情報を格納するデータクラス"""
    name: str
    price: str
    status: str
    is_available: bool
    url: str


class BaseSiteHandler(ABC):
    """サイトハンドラーの基底クラス"""
    
    # サイト識別子（サブクラスでオーバーライド）
    SITE_ID: str = "base"
    
    # サイト名（通知表示用）
    SITE_NAME: str = "Unknown"
    
    # 在庫ありと判定するキーワード
    AVAILABLE_KEYWORDS: list[str] = ["カートに入れる", "予約する", "在庫あり"]
    
    # 売り切れと判定するキーワード
    SOLDOUT_KEYWORDS: list[str] = ["売り切れ", "在庫なし", "販売終了"]
    
    @abstractmethod
    async def fetch_product_info(self, page: Page, url: str) -> ProductInfo | None:
        """
        商品ページから情報を取得する（サブクラスで実装）
        
        Args:
            page: Playwrightのページオブジェクト
            url: 商品URL
            
        Returns:
            ProductInfo or None: 商品情報、取得失敗時はNone
        """
        pass
    
    def check_availability(self, page_text: str, cart_button_enabled: bool = False) -> tuple[str, bool]:
        """
        ページテキストから在庫状態を判定
        
        Args:
            page_text: ページ全体のテキスト
            cart_button_enabled: カートボタンが有効かどうか
            
        Returns:
            tuple[str, bool]: (状態文字列, 購入可能フラグ)
        """
        status = "不明"
        is_available = False
        
        # 売り切れキーワードをチェック
        for keyword in self.SOLDOUT_KEYWORDS:
            if keyword in page_text:
                status = "売り切れ"
                break
        
        # 購入可能キーワードをチェック
        for keyword in self.AVAILABLE_KEYWORDS:
            if keyword in page_text:
                if cart_button_enabled:
                    is_available = True
                    status = "購入可能"
                elif status != "売り切れ":
                    status = keyword + "（ボタン無効）"
                break
        
        return status, is_available
