#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
すいせいちゃんの投稿をスプレッドシートに転記
"""

import re
from pathlib import Path
import sys

# 親ディレクトリのパスを取得
SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent.parent  # 投稿スケジュール/ディレクトリ
ROOT_DIR = PARENT_DIR.parent  # ルートディレクトリ

# モジュールのインポート
sys.path.insert(0, str(PARENT_DIR))
from 投稿スケジュール import schedule_posts_to_spreadsheet

# 投稿ファイルを読み込む
file_path = PARENT_DIR / '投稿例' / 'すいせいちゃん_投稿5個.md'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 投稿を抽出（## 投稿 X から次の --- まで）
posts = []
pattern = r'## 投稿 \d+.*?\n\n(.*?)(?=\n---|\n## 投稿|\Z)'
matches = re.findall(pattern, content, re.DOTALL)

for match in matches:
    post = match.strip()
    if post:
        posts.append(post)

print(f"✓ {len(posts)}個の投稿を抽出しました\n")

# スプレッドシートに転記
account_file = str(ROOT_DIR / "５０アカウント運用/7.すいせいちゃん.md")

schedule_posts_to_spreadsheet(
    account_file_path=account_file,
    posts=posts,
    morning_hour=9,
    morning_minute=0,
    evening_hour=21,
    evening_minute=0
)
