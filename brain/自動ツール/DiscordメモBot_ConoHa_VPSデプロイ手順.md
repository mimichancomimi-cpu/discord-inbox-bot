# Discord メモ Bot（ConoHa VPS）— よく使うコマンド集

**前提:** Vault は GitHub から clone し、例として **`/opt/vault`** に置く。パスが違うときは読み替える。

---

## VPS に入る（Mac のターミナル）

```bash
ssh root@133.88.122.254
```

初回は `yes` → パスワード（入力しても表示されないのが普通）。

**抜ける:** `exit` または `Ctrl+D`

---

## いまよく使う場所

| 用途 | パス例 |
|------|--------|
| Bot 本体・`.env` | `/opt/vault/brain/scripts/discord_inbox_bot/` |
| リポジトリのルート | `/opt/vault/` |

```bash
cd /opt/vault/brain/scripts/discord_inbox_bot
```

---

## git pull（GitHub の最新を取り込む）

**リモート（GitHub）の `main` を、いまのフォルダのリポジトリに取り込む**コマンド。

### VPS（例: `/opt/vault`）

```bash
cd /opt/vault
git pull origin main
```

- ブランチ名が違うときは `git branch` で確認（`master` なら `git pull origin master`）。
- **ローカルに未コミットの変更があると失敗**することがある → 下の「GitHub と揃えて Bot を再起動」の `fetch` + `reset --hard` か、`git stash` を検討。

### Mac（Obsidian の Vault）

ターミナルでリポジトリのルートへ移動してから:

```bash
cd "/Users/sasaki/Library/Mobile Documents/iCloud~md~obsidian/Documents"
git pull origin main
```

Vault を別の場所に置いているなら、`cd` をそのパスに変える。

### 事前に確認したいとき

```bash
git status
git remote -v
```

問題なければ `git pull origin main` でよい。

---

## GitHub と揃えて Bot を再起動（作業ツリーが汚れて `git pull` できないとき）

未コミットの追記を捨てて **リモートの `main` に合わせる**（GitHub が正のとき）。

```bash
cd /opt/vault
git fetch origin
git reset --hard origin/main
sudo systemctl restart discord-inbox-bot
```

または（リポジトリにスクリプトがある場合）:

```bash
sudo bash /opt/vault/brain/scripts/discord_inbox_bot/vps_pull_restart.sh
```

---

## systemd（Bot の起動・状態・ログ）

```bash
sudo systemctl status discord-inbox-bot
sudo systemctl restart discord-inbox-bot
sudo journalctl -u discord-inbox-bot -n 50 --no-pager
sudo journalctl -u discord-inbox-bot -f
```

**設定ファイルの場所を確認:**

```bash
systemctl cat discord-inbox-bot
```

---

## 手動で Bot を一度動かす（デバッグ用）

```bash
cd /opt/vault/brain/scripts/discord_inbox_bot
source .venv/bin/activate
set -a && source .env && set +a
python bot.py
```

止める: `Ctrl+C`

---

## venv の作り直し（`python` が動かないとき）

```bash
cd /opt/vault/brain/scripts/discord_inbox_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

---

## Mac で同じ Bot を止める（二重起動防止）

VPS で動かすなら Mac 側は止める。

```bash
launchctl bootout gui/$(id -u)/com.sasaki.discord-inbox-bot 2>/dev/null
```

---

## 初回セットアップの流れ（超短縮）

1. ConoHa で Ubuntu VPS を作り、**IP** と **root パスワード**をメモ。
2. `ssh root@IP` で入る。
3. `apt update && apt install -y git python3 python3-venv python3-pip` など（初回のみ）。
4. `git clone` で `/opt/vault` などに置く。
5. `discord_inbox_bot` で `python3 -m venv .venv` → `pip install -r requirements.txt`。
6. Mac から **`.env`**（必要なら **`credentials.json`** / **`team_channels.json`**）を同じフォルダに置く。
7. **`/etc/systemd/system/discord-inbox-bot.service`** を作成し、`WorkingDirectory` / `ExecStart` を実パスに合わせる。
8. `systemctl daemon-reload && systemctl enable --now discord-inbox-bot`

---

## つまずき早見

| 症状 | 見るところ |
|------|------------|
| `ssh` できない | IP・パスワード・ファイアウォール |
| `git pull` できない | `git status` → 未コミットがあれば `stash` か `reset --hard` |
| Discord 反応なし | `.env`、Mac 側 Bot がまだ動いていないか、`journalctl` |
| Obsidian と中身が違う | Mac で `git pull`（Bot は GitHub 経由ならリモートが正） |

---

## 補足

- **カレンダー自動追加**は `brain/credentials.json`・`calendar_config.json` と `ENABLE_CALENDAR_AUTO_ADD` などが揃っている必要あり（詳細は `brain/自動ツール/カレンダー予定追加_AI用.md`）。
- Mac の Vault と **自動では同期しない**。Git / GitHub 連携で揃える。
