# エディオン在庫監視ツール

エディオンの商品ページを定期的に監視し、在庫が復活したらDiscordに通知するツールです。

## 🎯 対象商品

- **商品名**: タカラトミー ポケモン30周年記念 おかえり!ピカチュウ1/1
- **URL**: https://www.edion.com/detail.html?p_cd=00084797278

## 🚀 セットアップ

### 1. Discord Webhookの作成

1. Discordサーバーで通知を受け取りたいチャンネルを開く
2. チャンネル設定（⚙️）→「連携サービス」→「ウェブフック」
3. 「新しいウェブフック」をクリック
4. 名前を設定（例：「在庫通知」）
5. 「ウェブフックURLをコピー」をクリック

### 2. GitHubリポジトリの設定

1. このフォルダを新しいGitHubリポジトリにpush
2. リポジトリの Settings → Secrets and variables → Actions
3. 「New repository secret」をクリック
4. Name: `DISCORD_WEBHOOK_URL`
5. Secret: コピーしたWebhook URL
6. 「Add secret」をクリック

### 3. GitHub Actionsの有効化

- リポジトリにpush後、自動的にActionsが有効になります
- パブリックリポジトリであれば無料で利用可能
- 5分ごとに自動実行されます

## 💻 ローカルでの実行

```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# ドライラン（通知なしで動作確認）
python monitor.py --dry-run

# Discord通知テスト
export DISCORD_WEBHOOK_URL="your_webhook_url_here"
python monitor.py --test-notify

# 本番実行
python monitor.py
```

## 📝 コマンドラインオプション

| オプション | 説明 |
|-----------|------|
| `--url URL` | 監視する商品URLを指定（デフォルト: ピカチュウ商品） |
| `--dry-run` | 通知を送信せずに結果を確認 |
| `--test-notify` | テスト通知を送信 |

## ⚠️ 注意事項

- GitHub Actionsの定期実行は最短5分間隔です
- パブリックリポジトリでないと無料枠を超える可能性があります
- エディオンのサイト構造が変更された場合、スクリプトの修正が必要になる可能性があります
