#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
りぼんちゃんの投稿21個をスプレッドシートに転記。1日3回（6:00, 12:00, 19:00）。
"""

import re
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
root_dir = parent_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from 投稿スケジュール.投稿スケジュール import schedule_posts_to_spreadsheet

posts_file = root_dir / "投稿スケジュール/投稿例/りぼんちゃん_投稿21個.md"
with open(posts_file, "r", encoding="utf-8") as f:
    content = f.read()

posts = []
for line in content.split("\n"):
    line = line.strip()
    if not line or line.startswith("#") or line == "---" or "ビジネス系" in line or "過去投稿" in line:
        continue
    m = re.match(r"^\d+\.\s+(.+)$", line)
    if m:
        posts.append(m.group(1).strip())

if len(posts) != 21:
    print(f"警告: 投稿数が21ではありません（{len(posts)}件）。続行します。")

account_file = str(root_dir / "５０アカウント運用/13.りぼんちゃん🎀.md")

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
