# Discordメモ自動化_運用マニュアル

この1枚だけ見れば、日々の運用とトラブル対応ができます。

---

## 1. ふだんの使い方

### メモを残す

- Discordのメモチャンネルに普通に投稿する
- `brain/タスク管理/Discord自動受信箱.md` に自動追記される
- リアクション:
  - `✅` ローカル+GitHub追記成功
  - `📝` ローカル追記のみ成功
  - `⚠️` 追記失敗

### 予定を入れる

- 形式（どれでも可）:
  - `予定 4/1 12:00 病院`
  - `予定 明日 10:00 歯医者`
  - `予定 金曜 14:00 MTG`
- 成功時は `🗓️` が付く（Googleカレンダー追加成功）

### 朝サマリー

- 毎朝、`今日やる / 待ち / 今週` を自動投稿（中身は `brain/タスク管理/自動タスク一覧.md` を優先）
- 朝の時刻にMacが閉じていても、次回起動時に未送信なら投稿される
- いつでもサマリー: メモチャンネルに1行だけ `タスクサマリー` / `タスク一覧` / `今のタスク` / `タスクまとめ` など（`サマリーテスト` も可）と送ると、朝と同じサマリーがサマリー用チャンネルに送られる

### 自動タスク（タグ）

- 正本: `brain/タスク管理/自動タスク一覧.md`
- メモ1行がタスクとして追記され、先頭にタグが付く（手動で `【m】` など先頭指定も可）
  - **【つ】** つきのわハウス系
  - **【m】** mimiちゃん系（キーワードに合わないときも多くはここ）
  - **【ノ】** ノゾミ
  - **【た】** たかだ
  - **【シ】** シナちゃん
  - **【プ】** プライベート
- リアクション: `📌` タスク追加、`☑️` 完了（「〇〇は終わりました」など）

---

## 2. 設定ファイル

- Bot設定: `brain/scripts/discord_inbox_bot/.env`
- ひな形: `brain/scripts/discord_inbox_bot/.env.example`
- メイン実装: `brain/scripts/discord_inbox_bot/bot.py`

---

## 3. 止まったときの最短確認

### まず状態確認

```bash
launchctl print gui/$(id -u)/com.sasaki.discord-inbox-bot
```

- `state = running` なら起動中

### 再起動

```bash
launchctl kickstart -k gui/$(id -u)/com.sasaki.discord-inbox-bot
```

### ログ確認

- エラーログ: `/Users/sasaki/Library/Logs/discord-inbox-bot.error.log`
- 標準ログ: `/Users/sasaki/Library/Logs/discord-inbox-bot.log`

---

## 4. よくあるエラー

### `401 Unauthorized`

- `DISCORD_BOT_TOKEN` が無効
- Developer Portalで Bot Token を再発行して `.env` を更新

### `403 / error code: 1010`

- チャンネル送信権限不足 or チャンネル設定不一致
- Botのチャンネル権限（View/Send/Read History）を確認
- 必要なら `SUMMARY_CHANNEL_ID` を別チャンネルに分ける

### `🗓️` が付かない

- カレンダー連携失敗
- `brain/credentials.json` と `brain/calendar_config.json` を確認

---

## 5. 最低運用ルール

- 1日1回はMacを開く
- 夜に3分だけ `Discord自動受信箱.md` を見て振り分ける
- トークンは定期的に再発行（Discord/GitHub）

