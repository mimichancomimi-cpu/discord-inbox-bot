# 投稿作成・スプレッドシート自動記入システム

ボールト内のフォルダの並び・役割は [[フォルダ案内]] を参照してください。

アカウント設計ファイルを読み込んで投稿を作成し、自動でGoogleスプレッドシートに記入するシステムです。

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. Google Sheets APIの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Sheets APIとGoogle Drive APIを有効化
3. サービスアカウントを作成し、JSONキーをダウンロード
4. ダウンロードしたJSONファイルのパスを`config.json`に設定

### 3. スプレッドシートの準備

既にThreadsと連携しているスプレッドシート（[こちら](https://docs.google.com/spreadsheets/d/1uj5a4GVcxMTzW8aoCIQL8Oj9Y8qvY3Wsn3bYGfEPymw/edit?usp=sharing)）がデフォルトで使用されます。

1. サービスアカウントのメールアドレスにスプレッドシートの編集権限を付与
2. 利用可能なシートを確認:
   ```bash
   python scripts/post_creator.py "dummy.md" --credentials credentials.json --list-sheets
   ```

**注意:** 既存のスプレッドシートとシートのみを使用します。新規作成は行いません。

### 4. 設定ファイルの作成

`config.example.json`をコピーして`config.json`を作成し、必要な情報を入力してください。

```json
{
  "spreadsheet_id": "1uj5a4GVcxMTzW8aoCIQL8Oj9Y8qvY3Wsn3bYGfEPymw",
  "worksheet_name": "自動投稿",
  "credentials_path": "credentials.jsonへのパス",
  "openai_api_key": "あなたのOpenAI APIキー（オプション）",
  "account_mappings": {
    "ぽんこつ母ちゃん": {
      "spreadsheet_id": "1uj5a4GVcxMTzW8aoCIQL8Oj9Y8qvY3Wsn3bYGfEPymw",
      "worksheet_name": "自動投稿"
    },
    "おつかれママ": {
      "spreadsheet_id": "16Z0Qyi0pZGjb9JM_VcBvX_-7wiCSJJUaleOr9a4kuTk",
      "worksheet_name": "自動投稿"
    },
    "100日後に離婚するおでんママ": {
      "spreadsheet_id": "1Eya_xEUUvufypuQktJXxre4FONmRB-ar2y58Kk9fHMo",
      "worksheet_name": "自動投稿"
    },
    "おでんママ": {
      "spreadsheet_id": "1Eya_xEUUvufypuQktJXxre4FONmRB-ar2y58Kk9fHMo",
      "worksheet_name": "自動投稿"
    },
    "はなママ": {
      "spreadsheet_id": "173WQXSf2K1ktGdR0CQ3uq5dQLCR6HVaVEtyXQNw5txk",
      "worksheet_name": "自動投稿"
    },
    "みゃこ🐱": {
      "spreadsheet_id": "1Z__kqC-2BYYNsSeRRFAIyf60jEv6ioZNe9WjlJoZhgE",
      "worksheet_name": "自動投稿"
    },
    "すいせいちゃん": {
      "spreadsheet_id": "1Hlu575ZaxNvDi-2l6g3fEhNBHoAyOPvq6eKPwAyeyFk",
      "worksheet_name": "自動投稿"
    },
    "ねこリーマン": {
      "spreadsheet_id": "1dDFy-oXQUg3pYmeQKDOE1wvt_aJoxd4b4kzhRjr2gSU",
      "worksheet_name": "自動投稿"
    },
    "最強らぶちゃん❤️‍🔥": {
      "spreadsheet_id": "1w6W1Ad580LJQT6BCTnFHXSNihkBC2IcvZC-x8pvQ8Ho",
      "worksheet_name": "自動投稿"
    },
    "無敵メンタルめるちゃん": {
      "spreadsheet_id": "1SkfhJFM0YlknNMcC7v81AF2zfy9iNSU238NI1JHlE-0",
      "worksheet_name": "自動投稿"
    },
    "ゆるスピのアオ子": {
      "spreadsheet_id": "1TnWD-b8FUquhuKPeeiYdWtlvE6HoToJcKZqBuzr2psw",
      "worksheet_name": "自動投稿"
    },
    "天音🪽元恋愛依存が語る幸せの恋愛術": {
      "spreadsheet_id": "1AOFaeIeC2N0B8VRF0OCiQlYef7sx2-aZ9VU_Rwjtbf4",
      "worksheet_name": "自動投稿"
    },
    "天音": {
      "spreadsheet_id": "1AOFaeIeC2N0B8VRF0OCiQlYef7sx2-aZ9VU_Rwjtbf4",
      "worksheet_name": "自動投稿"
    },
    "りぼんちゃん🎀": {
      "spreadsheet_id": "1kUL_Gz0Fb36ftLr2GDA8BlFLoi2Y6SN9RsG2O98rrHw",
      "worksheet_name": "自動投稿"
    },
    "りぼんちゃん": {
      "spreadsheet_id": "1kUL_Gz0Fb36ftLr2GDA8BlFLoi2Y6SN9RsG2O98rrHw",
      "worksheet_name": "自動投稿"
    }
  }
}
```

**注意:** 
- `spreadsheet_id`を省略すると、既存のThreads予約投稿ツールが自動的に使用されます
- `account_mappings`で各アカウントごとに異なるスプレッドシートやシートを指定できます（50アカウント対応）

## 使い方

### 単一アカウントの処理

#### 設定ファイルを使用する方法（推奨）

1. `config.json`を作成して設定を記入
2. 以下のコマンドで実行：

```bash
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md"
```

#### コマンドライン引数を使用する方法

```bash
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" \
  --spreadsheet-id YOUR_SPREADSHEET_ID \
  --credentials path/to/credentials.json
```

### 複数アカウントの一括処理（50アカウント対応）

フォルダ内の全アカウント設計ファイルを一括処理できます。

```bash
# フォルダ内の全ファイルを処理
python scripts/post_creator.py --batch "５０アカウント運用" \
  --credentials credentials.json

# 特定のパターンのファイルのみ処理
python scripts/post_creator.py --batch "５０アカウント運用" \
  --credentials credentials.json \
  --pattern "*.md"
```

**バッチ処理の特徴:**
- フォルダ内の全アカウント設計ファイルを自動検出
- 各アカウントごとに適切なスプレッドシート/シートに自動記入
- `account_mappings`設定で各アカウントのスプレッドシート/シートを個別指定可能
- 進捗表示とエラーハンドリング付き
- 成功/失敗のサマリーを表示

### オプション

- `--batch`: バッチ処理モード（指定したディレクトリ内の全ファイルを処理）
- `--config`: 設定ファイルのパス（デフォルト: config.json）
- `--spreadsheet-id`: Google SheetsのスプレッドシートID（デフォルト: 既存のThreads予約投稿ツール）
- `--credentials`: Google認証情報のJSONファイルパス
- `--worksheet`: ワークシート名を指定（デフォルト: "自動投稿"）
  - 利用可能: "自動投稿", "無限投稿", "曜日投稿", "ランダム投稿", "予約枠投稿"
- `--openai-key`: OpenAI APIキーを指定（AI生成を使用する場合）
- `--theme`: 投稿のテーマを指定（全アカウントに適用）
- `--scheduled-time`: 投稿予定日時（YYYY-MM-DD HH:MM:SS形式、全アカウントに適用）
- `--image-path`: 画像ファイルのパス（オプション）
- `--pattern`: バッチ処理時のファイルパターン（デフォルト: *.md）
- `--list-sheets`: 利用可能なシートの一覧を表示

### 例

```bash
# 設定ファイルを使用（最も簡単）
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md"

# テーマを指定して投稿を作成
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" \
  --theme "スマホひとつでポイ活"

# 別のシートに記入（例: 無限投稿）
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" \
  --worksheet "無限投稿"

# 投稿予定日時を指定
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" \
  --scheduled-time "2025-01-20 15:00:00"

# バッチ処理（50アカウント対応）
python scripts/post_creator.py --batch "５０アカウント運用" \
  --credentials credentials.json

# バッチ処理（テーマを指定して全アカウントに適用）
python scripts/post_creator.py --batch "５０アカウント運用" \
  --credentials credentials.json \
  --theme "スマホひとつでポイ活"

# 利用可能なシートを確認
python scripts/post_creator.py "dummy.md" \
  --credentials credentials.json \
  --list-sheets

# 別の設定ファイルを使用
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" \
  --config my_config.json

# コマンドライン引数で全て指定
python scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" \
  --spreadsheet-id abc123 \
  --credentials credentials.json \
  --worksheet "自動投稿" \
  --openai-key sk-xxxxx \
  --theme "スマホひとつでポイ活" \
  --scheduled-time "2025-01-20 15:00:00"
```

## アカウント設計ファイルの形式

アカウント設計ファイルは以下の形式で記述してください：

```markdown
**名前:** アカウント名
**ジャンル:** ジャンル名
**キーワード:** キーワード1 / キーワード2 / キーワード3
**自己紹介文:** 自己紹介文

### Threadsアカウント設計案

#### 1. コンテンツの柱（投稿ジャンル）
1. **柱1のタイトル**
2. **柱2のタイトル**
3. **柱3のタイトル**

#### 2. 投稿テンプレート
テンプレート内容...
```

## スプレッドシートの形式

既存のThreads予約投稿ツールのスプレッドシートを使用する場合、各シートの既存の構造に合わせてデータが記入されます。

スクリプトは自動的にシートのヘッダー行を読み取り、以下のような列名にマッピングします：

- **投稿内容**: "投稿", "内容", "テキスト" などの列
- **日時**: "日時", "時刻", "time", "date" などの列
- **アカウント名**: "アカウント" などの列
- **ジャンル**: "ジャンル", "genre" などの列
- **テーマ**: "テーマ", "theme" などの列
- **キーワード**: "キーワード", "keyword" などの列
- **画像**: "画像", "動画", "image", "video" などの列

シートの構造が異なる場合でも、投稿内容は適切な列に記入されます。

## 注意事項

- OpenAI APIキーはオプションです。指定しない場合は、テンプレートベースで投稿が生成されます
- 既存のスプレッドシートとシートのみを使用します。新規作成は行いません
- 指定したシートが存在しない場合はエラーになります。`--list-sheets`で利用可能なシートを確認してください
- サービスアカウントにスプレッドシートの編集権限を付与することを忘れないでください
- **50アカウント対応**: `account_mappings`で各アカウントごとに異なるスプレッドシートやシートを指定できます
- バッチ処理時は、各アカウントの名前を`account_mappings`のキーと一致させるか、部分一致でマッピングされます
