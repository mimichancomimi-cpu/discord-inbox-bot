# 自動ツールまとめ（目次）

このノートは「どれが手動で、どれが自動か」をすぐ判断するための目次です。  
詳細コマンドは各リンク先に集約しています。

---

## 自動で取得してくれるもの（常時ON）

### 1) Discordメモ受信箱（個人メモ）

- 状態: 自動起動設定済み（`launchd`）
- 役割: Discordメモチャンネル投稿を `brain/タスク管理/Discord自動受信箱.md` に追記
- 実装: `brain/scripts/discord_inbox_bot/bot.py`
- 設定: `brain/scripts/discord_inbox_bot/.env`
- 補足: 停止中の投稿は次回起動時にキャッチアップ

### 2) つきのわハウス Discordログ取得

- 状態: 自動起動設定済み（`launchd`）
- 役割: サーバー内ログを差分保存
- 出力先:
  - `brain/つきのわハウス/Discordログ/channels/`
  - `brain/つきのわハウス/Discordログ/threads/`
- 実装: `brain/scripts/discord_obsidian_archiver/archiver.py`
- 設定: `brain/scripts/discord_obsidian_archiver/.env`
- 補足: 取得間隔は `.env` の `DISCORD_ARCHIVE_INTERVAL_SEC`

---

## 手動で実行すべきもの（必要時だけ）

### 1) Googleカレンダー予定追加

- 役割: 指定日時の予定をGoogleカレンダーに登録
- 実装: `brain/scripts/add_calendar_event.py`
- 詳細: [[カレンダー予定追加_AI用]]

### 2) Discordログの手動ワンショット同期

- 役割: 自動起動とは別に、今すぐ1回だけ同期したいときに実行
- コマンド:

```bash
cd "/Users/sasaki/Library/Mobile Documents/iCloud~md~obsidian/Documents/brain/scripts/discord_obsidian_archiver"
source .venv/bin/activate
python3 archiver.py --once
```

- 状態リセットして全履歴を取り直す場合:

```bash
rm -f state.json
python3 archiver.py --once
```

---

## 困ったときの確認先

- カレンダー: [[カレンダー予定追加_AI用]]
- Discordログ手動ノート: [[Discordログ_手動で取得]]
