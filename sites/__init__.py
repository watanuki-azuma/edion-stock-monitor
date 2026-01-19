"""
サイトハンドラーパッケージ

サポートされているサイトのハンドラーを提供する。
"""

from .base import BaseSiteHandler, ProductInfo
from .edion import EdionHandler
from .biccamera import BiccameraHandler
from .yodobashi import YodobashiHandler
from .amazon import AmazonHandler


# サイトID → ハンドラークラスのマッピング
SITE_HANDLERS: dict[str, type[BaseSiteHandler]] = {
    "edion": EdionHandler,
    "biccamera": BiccameraHandler,
    "yodobashi": YodobashiHandler,
    "amazon": AmazonHandler,
}


def get_handler(site_id: str) -> BaseSiteHandler | None:
    """
    サイトIDに対応するハンドラーを取得
    
    Args:
        site_id: サイト識別子（"edion", "biccamera"など）
        
    Returns:
        BaseSiteHandler or None: ハンドラーインスタンス、未対応サイトはNone
    """
    handler_class = SITE_HANDLERS.get(site_id)
    if handler_class:
        return handler_class()
    return None


__all__ = [
    "BaseSiteHandler",
    "ProductInfo",
    "EdionHandler",
    "BiccameraHandler",
    "YodobashiHandler",
    "AmazonHandler",
    "SITE_HANDLERS",
    "get_handler",
]
