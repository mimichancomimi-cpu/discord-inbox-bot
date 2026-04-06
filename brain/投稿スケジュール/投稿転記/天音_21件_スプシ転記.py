#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天音の投稿21個（バズ用）をスプレッドシートに転記。1日3回（9:00, 14:00, 21:00）。
"""

import re
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent  # 投稿スケジュール
root_dir = parent_dir.parent               # brain
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from 投稿スケジュール.投稿スケジュール import schedule_posts_to_spreadsheet

# 投稿ファイルから本文のみ抽出（番号. を除く）
posts_file = root_dir / "投稿スケジュール/投稿例/天音_投稿21個_バズ用.md"
with open(posts_file, "r", encoding="utf-8") as f:
    content = f.read()

posts = []
for line in content.split("\n"):
    line = line.strip()
    if not line or line.startswith("#") or line == "---" or "Threads用" in line:
        continue
    m = re.match(r"^\d+\.\s+(.+)$", line)
    if m:
        posts.append(m.group(1).strip())

if len(posts) != 21:
    print(f"警告: 投稿数が21ではありません（{len(posts)}件）。続行します。")

account_file = str(root_dir / "５０アカウント運用/12.天音🪽元恋愛依存が語る幸せの恋愛術.md")

schedule_posts_to_spreadsheet(
    account_file_path=account_file,
    posts=posts,
    morning_hour=6,
    morning_minute=0,
    noon_hour=12,
    noon_minute=0,
    evening_hour=19,
    evening_minute=0,
    start_date=None,
    posts_per_day=3,
)
