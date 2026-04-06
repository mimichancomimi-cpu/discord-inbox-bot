# Google カレンダーに予定を追加するとき（AI・自分用メモ）

自動ツール全体の一覧は **`[[自動ツール_AI用まとめ]]`** を参照。

このファイルを **@自動ツール/カレンダー予定追加_AI用.md** でチャットに添えて依頼すると、カレンダー登録の意図が伝わりやすいです。

## 前提（ローカル）

- `brain/credentials.json` … サービスアカウント（既にある）
- `brain/calendar_config.json` … `calendar_id` を書いておくと `--calendar-id` 省略可（`calendar_config.example.json` をコピー）
- 実行は **`brain` フォルダがカレント** で:

```bash
python3 scripts/add_calendar_event.py \
  --summary "予定のタイトル" \
  --start "2026-04-03T22:30:00" \
  --end "2026-04-03T23:30:00" \
  --timezone "Asia/Tokyo"
```

`calendar_config.json` がない／別カレンダーに入れたいときだけ `--calendar-id "…@group.calendar.google.com"` を付ける。

## 依頼の言い方の例

- 「4/5 20:00〜21:00 で ○○ミーティング を入れて」
- 「来週月曜 15時から1時間、△△」
- 日付が曖昧なときは **西暦と曜日を確認**してから実行してよい、と書いておくと安全。

## 接続確認

```bash
python3 scripts/add_calendar_event.py --list-calendars
```
