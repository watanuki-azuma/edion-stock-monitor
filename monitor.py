"""
エディオン在庫監視スクリプト（Playwright版）

Playwrightを使用して実際のブラウザで商品ページにアクセスし、
在庫状況をチェック。在庫が復活した場合、Discord Webhookで通知を送信する。
"""

import os
import sys
import argparse
import asyncio
import requests
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# デフォルト設定
DEFAULT_PRODUCT_URL = "https://www.edion.com/detail.html?p_cd=00084797278"

# 在庫ありと判定するキーワード
AVAILABLE_KEYWORDS = ["カートに入れる", "予約する", "在庫あり", "予約受付中"]
# 売り切れと判定するキーワード
SOLDOUT_KEYWORDS = ["売り切れ", "在庫なし", "販売終了", "予約終了"]


async def fetch_product_page(url: str) -> dict | None:
    """Playwrightで商品ページを取得"""
    try:
        async with async_playwright() as p:
            # ヘッドレスブラウザを起動
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="ja-JP",
            )
            page = await context.new_page()
            
            # ページにアクセス（domcontentloadedで待機、タイムアウト延長）
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # ページコンテンツの読み込みを待つ
            try:
                await page.wait_for_selector("h1", timeout=10000)
            except Exception:
                pass  # セレクタが見つからなくても続行
            
            # 少し待機してJSの実行を待つ
            await page.wait_for_timeout(3000)
            
            # ページのテキストを取得
            page_text = await page.inner_text("body")
            
            # 商品名を取得
            try:
                name = await page.inner_text("h1")
            except Exception:
                name = "商品名取得失敗"
            
            # 価格を取得
            try:
                price_elem = page.locator(".price, .item-price, .selling-price").first
                price = await price_elem.inner_text()
            except Exception:
                price = "価格取得失敗"
            
            # カートボタンの状態を確認
            cart_button_enabled = False
            try:
                # カートに入れるボタンを探す
                cart_button = page.locator('button:has-text("カート"), button:has-text("予約"), .add-to-cart').first
                is_disabled = await cart_button.get_attribute("disabled")
                cart_button_enabled = is_disabled is None
            except Exception:
                pass
            
            await browser.close()
            
            return {
                "page_text": page_text,
                "name": name.strip() if name else "不明",
                "price": price.strip() if price else "不明",
                "cart_button_enabled": cart_button_enabled,
            }
            
    except PlaywrightTimeout:
        print("[ERROR] ページ読み込みがタイムアウトしました")
        return None
    except Exception as e:
        print(f"[ERROR] ページ取得に失敗: {e}")
        return None


def analyze_stock_status(page_data: dict) -> dict:
    """在庫状態を解析"""
    page_text = page_data["page_text"]
    
    is_available = False
    status = "不明"
    
    # 売り切れキーワードをチェック
    for keyword in SOLDOUT_KEYWORDS:
        if keyword in page_text:
            status = "売り切れ"
            break
    
    # 購入可能キーワードをチェック
    for keyword in AVAILABLE_KEYWORDS:
        if keyword in page_text:
            # カートボタンが有効かどうかで最終判定
            if page_data["cart_button_enabled"]:
                is_available = True
                status = "購入可能"
            elif "売り切れ" not in status:
                status = keyword + "（ボタン無効）"
            break
    
    return {
        "name": page_data["name"],
        "price": page_data["price"],
        "status": status,
        "is_available": is_available,
    }


def send_discord_notification(webhook_url: str, product_info: dict, product_url: str) -> bool:
    """Discord Webhookで通知を送信"""
    
    embed = {
        "title": "🎉 在庫復活！購入可能です！",
        "description": f"**{product_info['name']}**",
        "color": 0x00FF00,  # 緑色
        "fields": [
            {"name": "💰 価格", "value": product_info["price"], "inline": True},
            {"name": "📦 状態", "value": product_info["status"], "inline": True},
        ],
        "url": product_url,
        "footer": {"text": f"検知時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
    }
    
    payload = {
        "content": "⚠️ **今すぐ購入してください！** ⚠️",
        "embeds": [embed],
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("[SUCCESS] Discord通知を送信しました")
        return True
    except requests.RequestException as e:
        print(f"[ERROR] Discord通知の送信に失敗: {e}")
        return False


async def main_async(args):
    """非同期メイン処理"""
    
    # Discord Webhook URLを環境変数から取得
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    
    if not webhook_url and not args.dry_run:
        print("[ERROR] 環境変数 DISCORD_WEBHOOK_URL が設定されていません")
        sys.exit(1)
    
    print(f"[INFO] 監視URL: {args.url}")
    print(f"[INFO] 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テスト通知モード
    if args.test_notify:
        test_info = {
            "name": "テスト商品",
            "price": "¥9,999",
            "status": "テスト通知",
            "is_available": True,
        }
        send_discord_notification(webhook_url, test_info, args.url)
        return
    
    # 商品ページを取得
    page_data = await fetch_product_page(args.url)
    if not page_data:
        sys.exit(1)
    
    # 在庫状態を解析
    product_info = analyze_stock_status(page_data)
    
    print(f"[INFO] 商品名: {product_info['name']}")
    print(f"[INFO] 価格: {product_info['price']}")
    print(f"[INFO] 状態: {product_info['status']}")
    print(f"[INFO] 購入可能: {'はい' if product_info['is_available'] else 'いいえ'}")
    
    # 在庫ありの場合、通知を送信
    if product_info["is_available"]:
        print("[ALERT] ★★★ 在庫が復活しました！ ★★★")
        if not args.dry_run:
            send_discord_notification(webhook_url, product_info, args.url)
    else:
        print("[INFO] 現在は売り切れです。次回チェックまで待機します。")


def main():
    parser = argparse.ArgumentParser(description="エディオン在庫監視ツール")
    parser.add_argument("--url", default=DEFAULT_PRODUCT_URL, help="監視する商品URL")
    parser.add_argument("--dry-run", action="store_true", help="通知を送信せずに結果を表示")
    parser.add_argument("--test-notify", action="store_true", help="テスト通知を送信")
    args = parser.parse_args()
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
