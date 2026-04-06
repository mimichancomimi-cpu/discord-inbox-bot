# Threads 投稿をCSVに抽出するツール

`threads_export_to_csv.py` は、**Threads API** を使って、指定したユーザーIDの**投稿全体**と**ツリー投稿（リプライ）**を1つのCSVにまとめて出力するスクリプトです。**ユーザーIDを入力するだけで**実行できます。

## 重要な制限（Threads API 仕様）

- **取得できるのは「使用しているアクセストークンに紐づく認証ユーザー自身の投稿」のみです。**
- 他アカウントのユーザーIDを指定しても、APIではそのアカウントの投稿は取得できません（0件またはエラーになります）。
- **複数アカウント分を抽出したい場合**は、**各アカウントごとにそのアカウントのアクセストークンで実行**してください。

## 前提条件

- **Python 3.10+**（`list[str]` などの型表記を使っています）
- **requests**: `pip install requests`
- **Threads API のアクセストークン**（`threads_basic` 権限）
  - 取得できるのは**ログインしているユーザー自身の投稿のみ**です（他アカウントの全投稿取得はAPIでは不可）

## アクセストークンの取得

1. [Meta for Developers](https://developers.facebook.com/) でアプリを作成し、**Threads** をプロダクトに追加する。
2. [Get Access Tokens - Threads](https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions/) の手順に従い、認可URLで `threads_basic` をスコープに含めてユーザー認可を行う。
3. 発行された**短期トークン**を、[長期トークンに交換](https://developers.facebook.com/docs/threads/get-started/long-lived-tokens/)（60日有効）しておくと便利です。

※ 既に「Threads予約投稿ツール」などでトークンを取得している場合は、そのトークンを流用できます（スプレッドシートの「アクセストークン設定」などに保存されている値）。

## 使い方

**ユーザーID（または `me`）を指定するだけで**、そのアカウントの全投稿＋ツリーをCSVに出力します。

### 基本（認証ユーザー自身の投稿を抽出）

```bash
cd brain/投稿スケジュール
export THREADS_ACCESS_TOKEN="あなたのアクセストークン"
python threads_export_to_csv.py
# または明示的に
python threads_export_to_csv.py me
```

出力ファイル: `threads_me_export.csv`（`-o` で変更可能）

### 特定のユーザーIDを指定する（トークンに紐づくアカウントである必要あり）

```bash
python threads_export_to_csv.py 12345678901234567 -o そのアカウントの投稿.csv
```

※取得できるのは「そのトークンの認証ユーザー」の投稿のみです。別アカウントのIDを指定しても投稿は取得できません。

### トークンを引数で渡す

```bash
python threads_export_to_csv.py me -t "あなたのアクセストークン" -o threads_全投稿.csv
```

### ツリー（リプライ）を含めない（親投稿のみ）

```bash
python threads_export_to_csv.py me --no-trees -o posts_only.csv
```

### テストで最初の10件だけ取得

```bash
python threads_export_to_csv.py me --max-posts 10 -o test.csv
```

### 引数・オプション一覧

| 指定方法 | 説明 |
|----------|------|
| `USER_ID`（位置引数） | 抽出したいThreadsユーザーID。省略時は `me`（認証ユーザー自身）。 |
| `-o`, `--output` | 出力CSVのパス。未指定時は `threads_<USER_ID>_export.csv` |
| `-t`, `--token` | アクセストークン。未指定時は環境変数 `THREADS_ACCESS_TOKEN` |
| `--no-trees` | ツリーを取得せず親投稿のみ出力 |
| `--max-posts N` | 取得する投稿数の上限（テスト用） |

## 出力CSVの形式

| 列名 | 説明 |
|------|------|
| `post_id` | 投稿（メディア）ID |
| `parent_id` | 直上の親の投稿ID（親投稿の場合は空） |
| `root_post_id` | スレッドのルート（親投稿）ID |
| `depth` | 0=親投稿、1=リプライ（conversation はフラットなので 1 で統一） |
| `is_reply` | リプライなら 1、親なら 0 |
| `text` | 本文（改行はスペースに変換） |
| `timestamp` | 投稿日時（ISO 8601） |
| `username` | 投稿者のユーザー名 |
| `media_type` | TEXT_POST / IMAGE / VIDEO など |
| `permalink` | 投稿のURL |
| `media_url` | メディアのURL（画像・動画など） |

- 1行目はヘッダーです。
- 同じスレッドは `root_post_id` が同じなので、スプレッドシートやPandasでグループ化してツリー構造を復元できます。

## 注意

- APIのレート制限に合わせて、リクエスト間に少し待機時間を入れています。投稿数が多いと完了まで時間がかかります。
- **他アカウントの投稿は取得できません。** 複数アカウント分を取りたい場合は、各アカウントのアクセストークンを用意し、そのトークンで `python threads_export_to_csv.py me -o アカウント名.csv` のように実行してください。
