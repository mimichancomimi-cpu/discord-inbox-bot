# セットアップガイド

## 1. Google認証情報の取得

### ステップ1: Google Cloud Consoleでプロジェクトを作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）

### ステップ2: APIを有効化

1. 「APIとサービス」→「ライブラリ」に移動
2. 以下のAPIを有効化：
   - **Google Sheets API**
   - **Google Drive API**

### ステップ3: サービスアカウントを作成

1. 「APIとサービス」→「認証情報」に移動
2. 「認証情報を作成」→「サービスアカウント」を選択
3. サービスアカウント名を入力（例: `threads-poster`）
4. 「作成して続行」をクリック
5. ロールは「編集者」を選択（またはスキップ）
6. 「完了」をクリック

### ステップ4: JSONキーをダウンロード

1. 作成したサービスアカウントをクリック
2. 「キー」タブを選択
3. 「キーを追加」→「新しいキーを作成」を選択
4. キーのタイプで「JSON」を選択
5. 「作成」をクリック
6. JSONファイルがダウンロードされます（例: `project-name-xxxxx.json`）

### ステップ5: 認証情報ファイルを配置

1. ダウンロードしたJSONファイルを `credentials.json` にリネーム
2. `/Users/sasaki/Documents/Obsidian Vault/` に配置

## 2. スプレッドシートの権限設定

1. 各スプレッドシートを開く
2. 右上の「共有」ボタンをクリック
3. サービスアカウントのメールアドレス（`xxxxx@xxxxx.iam.gserviceaccount.com`）を追加
4. 権限を「編集者」に設定
5. 「送信」をクリック

**重要**: 各アカウントのスプレッドシートすべてに権限を付与してください。

## 3. 設定ファイルの作成

1. `config.example.json` をコピーして `config.json` を作成：

```bash
cp config.example.json config.json
```

2. `config.json` を編集して、`credentials_path` を設定：

```json
{
  "credentials_path": "/Users/sasaki/Documents/Obsidian Vault/credentials.json",
  ...
}
```

## 4. 動作確認

以下のコマンドで動作確認：

```bash
cd "/Users/sasaki/Documents/Obsidian Vault"
python3 scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" --credentials credentials.json
```

または、設定ファイルを使用する場合：

```bash
python3 scripts/post_creator.py "５０アカウント運用/1.ぽんこつ母ちゃん.md"
```

## トラブルシューティング

### 認証情報ファイルが見つからない

- `credentials.json` が正しい場所にあるか確認
- パスが正しいか確認（絶対パスを使用することを推奨）

### 権限エラー

- サービスアカウントにスプレッドシートの編集権限が付与されているか確認
- スプレッドシートIDが正しいか確認

### APIが有効になっていない

- Google Sheets APIとGoogle Drive APIが有効になっているか確認
