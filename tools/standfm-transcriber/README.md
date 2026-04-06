# stand.fm 文字起こし Chrome拡張機能

stand.fm のエピソードページでワンクリックで音声を文字起こしする Chrome 拡張機能です。  
ローカルの MLX Whisper (Apple Silicon 最適化) で処理するため、外部 API 不要・無料で使えます。

## 構成

```
standfm-transcriber/
├── extension/          ← Chrome拡張機能
│   ├── manifest.json
│   ├── popup.html
│   └── popup.js
├── server.py           ← ローカル文字起こしサーバー
├── requirements.txt
├── start_server.command ← ダブルクリックでサーバー起動
└── README.md
```

## セットアップ

### 1. サーバーの準備

`start_server.command` をダブルクリック、または：

```bash
cd tools/standfm-transcriber
pip3 install -r requirements.txt
python3 server.py
```

初回起動時に Whisper モデル (約 1.5GB) を自動ダウンロードします。

### 2. Chrome拡張機能のインストール

1. Chrome で `chrome://extensions/` を開く
2. 右上の **デベロッパーモード** を ON にする
3. **パッケージ化されていない拡張機能を読み込む** をクリック
4. `tools/standfm-transcriber/extension` フォルダを選択

## 使い方

1. **サーバーを起動** (`start_server.command` をダブルクリック)
2. Chrome で stand.fm のエピソードページを開く
3. ツールバーの拡張機能アイコンをクリック
4. **「文字起こしを開始」** ボタンを押す
5. 完了後、テキストをコピーまたは Obsidian に直接保存

## 所要時間の目安

| 音声の長さ | 文字起こし時間 (M1/M2 Mac) |
| ---------- | -------------------------- |
| 5分        | 約30秒                     |
| 15分       | 約1〜2分                   |
| 30分       | 約3〜4分                   |

## 設定

### Obsidian Vault のパス変更

デフォルトでは `~/Library/Mobile Documents/iCloud~md~obsidian/Documents` を使用します。  
変更する場合は環境変数で指定してください：

```bash
OBSIDIAN_VAULT=/path/to/your/vault python3 server.py
```
