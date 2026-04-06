# Discord → GitHub（Obsidian用md追記）Bot

## 何ができるか

指定した **Discord テキストチャンネル** にあなたが投稿すると、**GitHub リポジトリ内の1ファイル**（既定: `brain/タスク管理/Discord自動受信箱.md`）の**末尾に1行追記**されます。成功するとメッセージに ✅ が付きます。

## 前提

- Vault（少なくとも追記先ファイル）を **プライベート GitHub リポジトリ** に置ける（または専用リポジトリを1つ作る）
- **Bot を常時起動できる場所**がある  
  - 例: 自宅のMacを寝る間も起動しっぱなしにして `python bot.py`  
  - 例: Railway / Fly.io / 自宅Raspberry Pi などに同じスクリプトを配置

**iCloud のみ**でGitを使っていない場合は、先に「VaultをGitHubにミラーする」か「受信箱だけ別リポジトリ」かを決めてください。手順は Vault 内の **`[[Discord自動化_GitHub連携_手順]]`** を参照。

## セットアップ（短縮）

1. Discord Developer Portal で Application → Bot を作成し **Token** をコピー。**MESSAGE CONTENT INTENT** をオン。
2. OAuth2 → URL Generator で `bot` スコープ、`Read Messages/View Channels`, `Send Messages`, `Add Reactions` などを選び、生成URLで自分のサーバーに招待。
3. GitHub で **Fine-grained token**（対象リポジトリへの Contents 読み書き）または classic **repo** を発行。
4. テキストチャンネルID: Discord 設定の開発者モードでチャンネルを右クリック → ID をコピー。
5. `.env.example` を `.env` にコピーし、値を埋める。
6. `pip install -r requirements.txt` → `python bot.py`

## チーム複数チャンネル（人別タスク・朝サマリー）

`brain/scripts/discord_inbox_bot/team_channels.example.json` を `team_channels.json` にコピーし、**Discord のテキストチャンネルID**（開発者モードでコピー）と **`label`（表示名）**、**`local_inbox` / `task_file`**（Vault 内の相対パス）を埋めます。  
このファイルがあると **`.env` の `DISCORD_CHANNEL_ID` は使われず**、列挙したチャンネルごとに受信箱・自動タスク一覧が分かれます。**朝の定時サマリー**は各ルートの `summary_channel_id` へ（省略時はそのメモチャンネルと同じ）投稿されます。  
`github_file` を省略または `null` にすると、そのチャンネルの **受信箱**は GitHub に送りません。  
**自動タスク一覧**を GitHub に同期するには **`github_task_file`**（リポジトリ内パス、例: `brain/タスク管理/自動タスク一覧_かおりん.md`）を指定します。タスク追加・完了のたびにそのファイルを API で更新します。

## Mac でログイン時・蓋を開いたあとも遡って同期する

- **前提**: Bot プロセスが動いている間、`last_message_id` より後の Discord メッセージを取りこぼさないよう、**起動直後（`on_ready`）**と **スリープ後に Gateway が RESUME したとき（`on_resumed`）**の両方でキャッチアップ（受信箱追記・カレンダー・タスク）を走らせます。続けて両方が呼ばれても **ロックで直列化**し、先の実行で空振りしても **後からもう一度履歴を取りに行く**ので取りこぼしにくくしています。
- **随時タスクサマリー**: メモチャンネルに **1行だけ** 次のいずれかを送ると、定時朝サマリーと同じ内容を **そのルートの `summary_channel_id`** へ投稿します（例: `タスクサマリー` / `タスク一覧` / `今のタスク` / `今のタスク一覧` / `朝サマリー` / `タスクまとめ` / 互換の `サマリーテスト`）。追加のキーワードは `.env` の `SUMMARY_NOW_KEYWORDS`（カンマ区切り）で指定可能。
- **常時起動の例**: `launchd/com.sasaki.discord-inbox-bot.plist.example` の `VAULT_PATH` をこの Vault のフルパスに置換し、`python3` を `which python3`（または venv の `python`）に合わせてから `~/Library/LaunchAgents/` にコピーし、`launchctl load ~/Library/LaunchAgents/com.sasaki.discord-inbox-bot.plist`。**KeepAlive** で落ちたら再起動します。
- **注意**: Mac を完全にシャットダウンしている間は動きません。プロセスが止まっている間に送ったメッセージは、**次に Bot が起動してから**遡って処理されます。

## 秘密情報

**`.env` とトークンを Git にコミットしないでください。** `.gitignore` に `.env` があることを確認してください。
