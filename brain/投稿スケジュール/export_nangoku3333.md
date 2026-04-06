# @nangoku3333 の投稿を全て記録する

対象: https://www.threads.com/@nangoku3333?hl=ja

## 手順

**このアカウント（@nangoku3333）の投稿を取得するには、そのアカウントで発行した Threads API のアクセストークンが必要です。**

1. @nangoku3333 でログインした状態で、Meta for Developers からアクセストークンを取得する。
2. ターミナルで以下を実行する（トークンは環境変数か `-t` で渡す）。

```bash
cd "brain/投稿スケジュール"

# 方法A: URLをそのまま指定（ユーザー名を自動解決）
export THREADS_ACCESS_TOKEN="ここに@nangoku3333用のアクセストークンを貼る"
python threads_export_to_csv.py "https://www.threads.com/@nangoku3333?hl=ja" -o nangoku3333_全投稿.csv

# 方法B: ユーザー名だけ指定
python threads_export_to_csv.py nangoku3333 -o nangoku3333_全投稿.csv
```

3. 完了すると `nangoku3333_全投稿.csv` に全投稿＋ツリーが記録されます。

※他アカウントのトークンでは @nangoku3333 の投稿は取得できません。必ず @nangoku3333 用のトークンで実行してください。
