# 複数サイト対応 在庫監視ツール v2

複数のECサイト（エディオン、ビックカメラ等）の商品を一括監視し、在庫復活時にDiscordで通知するツール。

## 🎯 監視対象

`config.yaml` で設定：

| サイト | 商品 |
|--------|------|
| エディオン | ポケモン30周年 ピカチュウ1/1 |
| ビックカメラ | iPhone 17（全5色） |

## 🚀 使い方

### テストモード（通知なし）

```bash
# 全商品をチェック
python monitor.py --test

# 特定URLのみチェック
python monitor.py --test --url "https://..."

# 通知テスト
python monitor.py --test-notify
```

### 本番実行

```bash
export DISCORD_WEBHOOK_URL="your_webhook_url"
python monitor.py
```

## 📝 商品の追加・削除

`config.yaml` を編集：

```yaml
products:
  - name: "商品名"
    url: "https://..."
    site: "edion"  # または "biccamera"
    enabled: true   # false で監視停止
```

## ⚙️ 対応サイト

| サイトID | サイト名 |
|----------|----------|
| `edion` | エディオン |
| `biccamera` | ビックカメラ |

新サイト追加は `sites/` に新しいハンドラーを作成。

## 🔧 GitHub Actionsで自動実行

1. リポジトリにpush
2. Settings → Secrets → `DISCORD_WEBHOOK_URL` を設定
3. 5分ごとに自動チェック開始

**ローカル実行時の準備:**
```bash
pip install -r requirements.txt
playwright install chromium firefox
```

## 📁 ファイル構成

```
edion_stock_monitor/
├── monitor.py          # メインスクリプト
├── config.yaml         # 監視対象設定
├── requirements.txt    # 依存パッケージ
├── sites/              # サイト別ハンドラー
│   ├── __init__.py
│   ├── base.py         # 基底クラス
│   ├── edion.py        # エディオン
│   └── biccamera.py    # ビックカメラ
└── .github/workflows/
    └── stock_monitor.yml
```
