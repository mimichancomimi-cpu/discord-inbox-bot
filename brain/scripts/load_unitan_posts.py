#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re

# 設定ファイルを読み込む
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# スプレッドシートID
SPREADSHEET_ID = "1yaKspJ5gcIOgvywNR7VQZe4TxZxJc9x4UXMgC7xOjkc"
CREDENTIALS_PATH = config.get('credentials_path', 'credentials.json')
WORKSHEET_NAME = "投稿インサイト"

# 認証情報を読み込む
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
client = gspread.authorize(creds)

# スプレッドシートを開く
try:
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    print(f"スプレッドシート '{spreadsheet.title}' の '{WORKSHEET_NAME}' シートを開きました")
except Exception as e:
    print(f"エラー: スプレッドシートを開けませんでした: {e}")
    exit(1)

# データを読み込む
all_values = worksheet.get_all_values()

if not all_values:
    print("データが見つかりませんでした")
    exit(1)

# ヘッダー行を探す
header_row = None
for i, row in enumerate(all_values):
    if any('投稿本文' in cell or '投稿内容' in cell or '本文' in cell for cell in row):
        header_row = i
        break

if header_row is None:
    print("ヘッダー行が見つかりませんでした")
    exit(1)

# ヘッダーを取得
headers = all_values[header_row]

# 列のインデックスを探す（柔軟に対応）
def find_column_index(headers, possible_names):
    for name in possible_names:
        for i, header in enumerate(headers):
            if name in header:
                return i
    return None

post_text_col = find_column_index(headers, ['投稿本文', '投稿内容', '本文', 'テキスト', '投稿'])
likes_col = find_column_index(headers, ['いいね', 'Like', 'likes', 'Likes'])
views_col = find_column_index(headers, ['表示', 'View', 'views', 'Views', 'インプレッション', 'impression'])
replies_col = find_column_index(headers, ['返信', 'Reply', 'replies', 'Replies', 'コメント', 'Comment'])
url_col = find_column_index(headers, ['URL', 'url', 'リンク', 'Link'])
date_col = find_column_index(headers, ['日時', 'Date', 'date', '投稿日時', '取得日時'])

# 列が見つからない場合はインデックスで推測
if post_text_col is None:
    post_text_col = 0  # 最初の列を仮定
if likes_col is None:
    likes_col = 1
if views_col is None:
    views_col = 2
if replies_col is None:
    replies_col = 3
if url_col is None:
    url_col = 4
if date_col is None:
    date_col = 5

print(f"列マッピング: 投稿本文={post_text_col}, いいね={likes_col}, 表示={views_col}, 返信={replies_col}, URL={url_col}, 日時={date_col}")

# 投稿データを取得
posts = []
for i, row in enumerate(all_values[header_row + 1:], start=header_row + 2):
    if not row or not row[post_text_col]:
        continue
    
    post_text = row[post_text_col].strip()
    if not post_text:
        continue
    
    # 数値を取得（空の場合は0）
    try:
        likes = int(row[likes_col]) if likes_col < len(row) and row[likes_col] else 0
    except (ValueError, IndexError):
        likes = 0
    
    try:
        views = int(row[views_col]) if views_col < len(row) and row[views_col] else 0
    except (ValueError, IndexError):
        views = 0
    
    try:
        replies = int(row[replies_col]) if replies_col < len(row) and row[replies_col] else 0
    except (ValueError, IndexError):
        replies = 0
    
    url = row[url_col] if url_col < len(row) else ""
    date = row[date_col] if date_col < len(row) else ""
    
    posts.append({
        'text': post_text,
        'likes': likes,
        'views': views,
        'replies': replies,
        'url': url,
        'date': date
    })

# いいね数でソート（降順）
posts.sort(key=lambda x: x['likes'], reverse=True)

print(f"\n{len(posts)}件の投稿を取得しました")

# Markdownファイルに追加
markdown_file = "５０アカウント運用/2.うにたん.md"

# ファイルを読み込む
with open(markdown_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 過去投稿記録セクションを探す
if "## 過去投稿記録" in content:
    # 既存のセクションを置き換え
    pattern = r'## 過去投稿記録.*?(?=\n## |\Z)'
    
    # 新しいセクションを作成
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    new_section = f"## 過去投稿記録\n\n最終更新: {now}\n\n総投稿数: {len(posts)}件\n\n"
    
    # 統計を計算
    total_likes = sum(p['likes'] for p in posts)
    total_views = sum(p['views'] for p in posts)
    total_replies = sum(p['replies'] for p in posts)
    
    new_section += f"**パフォーマンス統計:**\n"
    new_section += f"- 総いいね数: {total_likes}\n"
    new_section += f"- 総表示数: {total_views}\n"
    new_section += f"- 総返信数: {total_replies}\n\n"
    new_section += "---\n\n"
    
    # 各投稿を追加
    for i, post in enumerate(posts, 1):
        new_section += f"### 投稿 {i}\n\n"
        new_section += f"**投稿本文:**\n\n{post['text']}\n\n"
        new_section += f"**パフォーマンス:**\n"
        new_section += f"- いいね数: {post['likes']}\n"
        new_section += f"- 表示数: {post['views']}\n"
        new_section += f"- 返信数: {post['replies']}\n"
        if post['url']:
            new_section += f"- URL: {post['url']}\n"
        if post['date']:
            new_section += f"- 取得日時: {post['date']}\n"
        new_section += "\n---\n\n"
    
    # 置き換え
    content = re.sub(pattern, new_section.rstrip(), content, flags=re.DOTALL)
else:
    # セクションが存在しない場合は最後に追加
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    new_section = f"\n\n## 過去投稿記録\n\n最終更新: {now}\n\n総投稿数: {len(posts)}件\n\n"
    
    # 統計を計算
    total_likes = sum(p['likes'] for p in posts)
    total_views = sum(p['views'] for p in posts)
    total_replies = sum(p['replies'] for p in posts)
    
    new_section += f"**パフォーマンス統計:**\n"
    new_section += f"- 総いいね数: {total_likes}\n"
    new_section += f"- 総表示数: {total_views}\n"
    new_section += f"- 総返信数: {total_replies}\n\n"
    new_section += "---\n\n"
    
    # 各投稿を追加
    for i, post in enumerate(posts, 1):
        new_section += f"### 投稿 {i}\n\n"
        new_section += f"**投稿本文:**\n\n{post['text']}\n\n"
        new_section += f"**パフォーマンス:**\n"
        new_section += f"- いいね数: {post['likes']}\n"
        new_section += f"- 表示数: {post['views']}\n"
        new_section += f"- 返信数: {post['replies']}\n"
        if post['url']:
            new_section += f"- URL: {post['url']}\n"
        if post['date']:
            new_section += f"- 取得日時: {post['date']}\n"
        new_section += "\n---\n\n"
    
    content += new_section

# ファイルに書き込む
with open(markdown_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n{markdown_file} に {len(posts)}件の投稿を追加しました")
