# Discord メモ Bot を ConoHa VPS に載せる（初心者向け）

## まずイメージだけ掴む

- **今まで**: Bot は **あなたの Mac の中** で動いている。Mac を寝かせると動かない／不安定になりやすい。
- **これから**: **インターネット上の「レンタル PC」（VPS）** を借りて、そこで Bot を 24 時間動かす。
- **ConoHa がしてくれること**: レンタル PC（Linux）を用意して、そこに **ログインできる権限**を渡すところまで。
- **あなたがやること**: その PC の中に、**今 Mac にある Bot のプログラムと設定**をコピーして、「電源を切っても自動で起動する」ように登録する。

```
[Discord] ←→ [インターネット] ←→ [ConoHa の VPS 上で Bot が動く]
                                      ↑
                               Mac の Obsidian と揃えるには
                               Git などでファイルを同期する運用がおすすめ
```

---

## 用語の超短い説明

| 言葉 | 意味 |
|------|------|
| **VPS** | 遠くのデータセンターにある「小さなパソコン」を1台借りるサービス。 |
| **SSH** | そのパソコンに、**文字だけで遠隔操作**する方法（ターミナルから）。 |
| **Ubuntu** | よく使われる Linux の種類。OS はこれを選ぶと手順が多い。 |
| **`.env`** | パスワードやトークンを書くファイル。Bot が読む。 |
| **仮想環境（venv）** | その PC 専用の Python 部屋。他と干渉しないようにする。 |
| **systemd** | Linux が「このプログラムを常時起動してね」と覚えておく仕組み。 |

---

## 事前に決めること（2つだけ）

1. **Mac で動いている同じ Bot は、VPS に移したら止める**  
   同じトークンで **2台同時に動かすと Discord がおかしくなる**ので、どちらか一方だけにする。

2. **Vault の中身を VPS にどう持っていくか**  
   いちばんわかりやすいのは **GitHub にプライベートで保存**して、VPS から `git clone` すること。  
   Git を使わない場合は、**「コピーしてくる」**方法を別途考える（上級者向け）。

---

## ステップ1：ConoHa で VPS を作る

1. ConoHa のコントロールパネルにログインする。
2. **VPS を新規作成**する。
3. **OS** は **Ubuntu 22.04 / 24.04 LTS** のどちらかを選ぶ（おすすめ）。
4. **パスワード**（または SSH 鍵）を設定する。  
   **メモしてなくなさない場所に保存**する。
5. **パブリック IP アドレス**（数字の並び）が表示されたら **メモ**する。  
   例: `123.45.67.89`

---

## ステップ2：Mac のターミナルから VPS に入る（SSH）

Mac で **ターミナル** を開き、次を入力（`123.45.67.89` は自分の IP に変える）。

```bash
ssh root@123.45.67.89
```

- 初めてつなぐときは「続行しますか？」と出たら `yes` と打って Enter。
- パスワードを聞かれたら、ConoHa で設定した **root のパスワード**を入力（打っても画面に出ないのが普通）。

これで **ConoHa のレンタル PC の中**に入れた状態になる。

---

## ステップ3：VPS の中身を少し整える

VPS にログインしたまま、次を **順番に** コピペして Enter（全部終わるまで待つ）。

```bash
apt update && apt upgrade -y
apt install -y git python3 python3-venv python3-pip
timedatectl set-timezone Asia/Tokyo
```

意味だけ一言ずつ：

- **apt …** ソフトを入れる・更新する。
- **git** … GitHub から取ってくるときに使う。
- **python3 …** Bot は Python で動く。
- **タイムゾーン** … 朝サマリーの時刻を日本時間に合わせる。

---

## ステップ4：Vault（brain）を VPS に置く

### ここがいちばん大事なルール

Bot のプログラムは **`brain` フォルダの中の決まった場所**に置く前提で作られている。

例（Mac と同じ形にする）:

```text
（どこかのフォルダ）/brain/
  scripts/discord_inbox_bot/bot.py   ← ここに Bot 本体
  scripts/add_calendar_event.py
  タスク管理/…
  credentials.json（カレンダー使うなら）
```

### GitHub で管理している場合（おすすめ）

```bash
mkdir -p /opt && cd /opt
git clone （あなたのプライベートリポジトリのURL） vault
cd vault/brain/scripts/discord_inbox_bot
```

※ リポジトリのトップに `brain` フォルダが来るように clone する。  
　フォルダの作り方が違う場合は、**Mac の `brain` と同じ並び**になるように調整する。

### 秘密のファイルだけ注意

- **`.env`**（トークンなど）  
  → Git に入れていないなら、**あとで Mac からコピー**して VPS に新規作成する。
- **`credentials.json`**（Google カレンダー）  
  → これも **Git に入れない**ことが多い。Mac からコピーする。

---

## ステップ5：Python の部屋を作って、必要な部品を入れる

`discord_inbox_bot` フォルダにいる状態で：

```bash
cd /opt/vault/brain/scripts/discord_inbox_bot
```

（※ `/opt/vault/` の部分は、実際に clone した場所に合わせて変える）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

- **venv** … この Bot 専用の Python 環境。
- **requirements.txt** … Bot に必要なライブラリ一覧。

---

## ステップ6：`.env` を置く

1. Mac の `brain/scripts/discord_inbox_bot/.env` を開く。
2. 中身を **同じように** VPS 上の同じフォルダに **`.env` という名前で新規作成**して貼り付ける。  
   （nano エディタの使い方: `nano .env` で開き、貼り付けて `Ctrl+O` で保存、`Ctrl+X` で終了）

**チーム用の `team_channels.json`** を使っているなら、そのファイルも **同じフォルダに置く**。

---

## ステップ7：動くか一度だけ手で試す

```bash
cd /opt/vault/brain/scripts/discord_inbox_bot
source .venv/bin/activate
set -a && source .env && set +a
python bot.py
```

- エラーがずっと出ずに止まるようなら、**Discord でメッセージを送って反応するか**確認。
- 止めるときは **`Ctrl + C`**。

---

## ステップ8：電源を切っても自動で起動するようにする（systemd）

**1）** 設定ファイルを作る（パスは自分の環境に合わせる）:

```bash
nano /etc/systemd/system/discord-inbox-bot.service
```

**2）** 次の内容を貼る（**`/opt/vault/` は clone した場所に合わせて変える**）:

```ini
[Unit]
Description=Discord inbox bot for Obsidian
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vault/brain/scripts/discord_inbox_bot
EnvironmentFile=/opt/vault/brain/scripts/discord_inbox_bot/.env
ExecStart=/opt/vault/brain/scripts/discord_inbox_bot/.venv/bin/python /opt/vault/brain/scripts/discord_inbox_bot/bot.py
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
```

**3）** 保存してから、次を実行:

```bash
systemctl daemon-reload
systemctl enable discord-inbox-bot
systemctl start discord-inbox-bot
systemctl status discord-inbox-bot
```

- **active (running)** と出れば成功に近い。

ログを見る:

```bash
journalctl -u discord-inbox-bot -f
```

止めるときは `Ctrl+C`。

---

## ステップ9：Mac の Bot を止める（二重起動防止）

Mac のターミナルで:

```bash
launchctl bootout gui/$(id -u)/com.sasaki.discord-inbox-bot
```

（同じ Bot を Mac でも VPS でも動かさないため）

---

## 初心者がつまずきやすいポイント

| 症状 | よくある原因 |
|------|----------------|
| `ssh` でつながらない | IP を間違えた、パスワードを間違えた、ファイアウォール |
| `python bot.py` でエラー | `.env` がない、パスが違う、`venv` を有効にしてない |
| Discord 反応なし | トークン違い、Bot がサーバーに招待されていない、Mac 側もまだ動いている |
| Obsidian のファイルが更新されない | **VPS 上のファイル**が変わっている。Mac と揃えるには **Git で pull** などが必要 |

---

## 運用の注意（やさしく）

- **VPS に載せたあとは**、メモの `.md` は **VPS の中**に書き込まれる。  
  Mac の Obsidian と **自動では同じになりません**。
- **同じ内容にしたい**ときは、次のどちらかが現実的です。
  - **Git**: VPS に push できるようにする、Mac は pull する。
  - **GitHub 連携**: Bot が GitHub に追記する設定を活かし、Mac は `git pull` で取り込む。

---

## 元の詳細版（コマンド一覧）

細かいコマンドや注意は、上の流れで足りなければ **「詳細版」**として同じフォルダの内容を参照するか、Cursor に「VPS のパスが `/opt/vault` なので systemd を書き換えて」と頼むとよいです。

---

## チェックリスト

- [ ] ConoHa で VPS を作る（Ubuntu・IP をメモ）
- [ ] Mac から `ssh` で入れる
- [ ] `brain` が正しいフォルダ構成で VPS にある
- [ ] `venv` と `pip install -r requirements.txt` が終わった
- [ ] `.env`（と必要なら `credentials.json` / `team_channels.json`）がある
- [ ] `python bot.py` で一度成功した
- [ ] `systemd` で起動した
- [ ] Mac の Bot を止めた
