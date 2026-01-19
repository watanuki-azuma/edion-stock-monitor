"""
複数サイト対応 在庫監視スクリプト v2

YAML設定ファイルから監視対象を読み込み、
各サイトに対応したハンドラーで在庫をチェック。
在庫復活時にDiscord Webhookで通知する。
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

import yaml
import requests
from playwright.async_api import async_playwright

from sites import get_handler, ProductInfo

# 設定ファイルのデフォルトパス
CONFIG_FILE = Path(__file__).parent / "config.yaml"


def load_config(config_path: Path) -> list[dict]:
    """設定ファイルを読み込む"""
    if not config_path.exists():
        print(f"[ERROR] 設定ファイルが見つかりません: {config_path}")
        return []
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    products = config.get("products", [])
    # enabledが True のものだけフィルタ
    return [p for p in products if p.get("enabled", True)]


def send_discord_notification(webhook_url: str, product_info: ProductInfo, site_name: str) -> bool:
    """Discord Webhookで通知を送信"""
    
    embed = {
        "title": f"🎉 {site_name}で在庫復活！",
        "description": f"**{product_info.name}**",
        "color": 0x00FF00,
        "fields": [
            {"name": "💰 価格", "value": product_info.price, "inline": True},
            {"name": "📦 状態", "value": product_info.status, "inline": True},
            {"name": "🔗 リンク", "value": f"[購入ページへ]({product_info.url})", "inline": False},
        ],
        "footer": {"text": f"検知時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
    }
    
    payload = {
        "content": "⚠️ **今すぐ購入してください！** ⚠️",
        "embeds": [embed],
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[SUCCESS] Discord通知を送信しました: {product_info.name}")
        return True
    except requests.RequestException as e:
        print(f"[ERROR] Discord通知の送信に失敗: {e}")
        return False


async def check_single_product(browser, product: dict, webhook_url: str, dry_run: bool) -> dict:
    """単一商品の在庫をチェック"""
    handler = get_handler(product["site"])
    if not handler:
        print(f"[WARNING] 未対応サイト: {product['site']}")
        return {"product": product, "status": "未対応サイト", "available": False}
    
    print(f"\n[CHECK] {product['name']} ({handler.SITE_NAME})")
    print(f"        URL: {product['url']}")
    
    # サイトに応じたブラウザ設定
    context_options = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "locale": "ja-JP",
        "viewport": {"width": 1920, "height": 1080},
        "extra_http_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ja,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
    }
    
    context = await browser.new_context(**context_options)
    page = await context.new_page()
    
    try:
        info = await handler.fetch_product_info(page, product["url"])
        
        if info:
            print(f"        商品名: {info.name}")
            print(f"        価格: {info.price}")
            print(f"        状態: {info.status}")
            print(f"        購入可能: {'はい ✅' if info.is_available else 'いいえ'}")
            
            if info.is_available:
                print(f"[ALERT] ★★★ 在庫復活！ ★★★")
                if not dry_run and webhook_url:
                    send_discord_notification(webhook_url, info, handler.SITE_NAME)
            
            return {"product": product, "status": info.status, "available": info.is_available}
        else:
            print(f"        [ERROR] 情報取得失敗")
            return {"product": product, "status": "取得失敗", "available": False}
            
    finally:
        await context.close()


async def main_async(args):
    """非同期メイン処理"""
    
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    
    if not webhook_url and not args.dry_run and not args.test:
        print("[ERROR] 環境変数 DISCORD_WEBHOOK_URL が設定されていません")
        sys.exit(1)
    
    print("=" * 60)
    print("在庫監視ツール v2")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # テスト通知モード
    if args.test_notify:
        test_info = ProductInfo(
            name="テスト商品",
            price="¥9,999",
            status="テスト通知",
            is_available=True,
            url="https://example.com",
        )
        send_discord_notification(webhook_url, test_info, "テストサイト")
        return
    
    # 設定ファイルを読み込み
    config_path = Path(args.config) if args.config else CONFIG_FILE
    products = load_config(config_path)
    
    if not products:
        print("[ERROR] 監視対象の商品がありません")
        sys.exit(1)
    
    print(f"\n監視対象: {len(products)}件")
    
    # 特定URLのみチェック
    if args.url:
        products = [p for p in products if p["url"] == args.url]
        if not products:
            # URLが設定にない場合、サイトを自動判定して追加
            site = "unknown"
            if "edion.com" in args.url:
                site = "edion"
            elif "biccamera.com" in args.url:
                site = "biccamera"
            products = [{"name": "手動指定", "url": args.url, "site": site}]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        results = []
        available_count = 0
        
        for product in products:
            result = await check_single_product(browser, product, webhook_url, args.dry_run or args.test)
            results.append(result)
            if result["available"]:
                available_count += 1
        
        await browser.close()
    
    # サマリー表示
    print("\n" + "=" * 60)
    print("サマリー")
    print("=" * 60)
    print(f"チェック完了: {len(results)}件")
    print(f"在庫あり: {available_count}件")
    
    if args.test:
        print("\n[INFO] テストモード: 通知は送信されませんでした")
    elif args.dry_run:
        print("\n[INFO] ドライラン: 通知は送信されませんでした")


def main():
    parser = argparse.ArgumentParser(description="複数サイト対応 在庫監視ツール")
    parser.add_argument("--config", help="設定ファイルのパス")
    parser.add_argument("--url", help="特定URLのみチェック")
    parser.add_argument("--dry-run", action="store_true", help="通知を送信せずに結果を表示")
    parser.add_argument("--test", action="store_true", help="テストモード（通知なし）")
    parser.add_argument("--test-notify", action="store_true", help="テスト通知を送信")
    args = parser.parse_args()
    
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
