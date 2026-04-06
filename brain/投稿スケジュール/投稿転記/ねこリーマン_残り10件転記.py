#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ねこリーマンの転記で失敗した残り10件（12本目〜21本目）をスプシに追記。"""

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

root_dir = Path(__file__).resolve().parent.parent.parent
config_file = root_dir / "config.json"
credentials_file = root_dir / "credentials.json"
posts_file = root_dir / "投稿スケジュール/投稿例/ねこリーマン_投稿21個_楽天アフィ主婦向け.md"

with open(posts_file, "r", encoding="utf-8") as f:
    content = f.read()
posts = []
for line in content.split("\n"):
    line = line.strip()
    if not line or line.startswith("#") or line == "---" or "過去投稿" in line or "新規作成" in line:
        continue
    m = re.match(r"^\d+\.\s+(.+)$", line)
    if m:
        posts.append(m.group(1).strip())

# 12本目〜21本目（0-based: 11〜20）
remaining_posts = posts[11:21]
# 日時: 2/8 19:00, 2/9 6,12,19, 2/10 6,12,19, 2/11 6,12,19
start_date = datetime(2026, 2, 8)
slots = [(19, 0), (6, 0), (12, 0), (19, 0), (6, 0), (12, 0), (19, 0), (6, 0), (12, 0), (19, 0)]
dates = [start_date] + [start_date + timedelta(days=1)] * 3 + [start_date + timedelta(days=2)] * 3 + [start_date + timedelta(days=3)] * 3

with open(config_file, "r", encoding="utf-8") as f:
    config = json.load(f)
mapping = config["account_mappings"].get("ねこリーマン")
spreadsheet_id = mapping["spreadsheet_id"]
worksheet_name = mapping.get("worksheet_name", "自動投稿")

creds = Credentials.from_service_account_file(
    str(credentials_file),
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
client = gspread.authorize(creds)
sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

# 最初の空行（ねこリーマンは15行目まで書けてるので16行目から）
all_vals = sheet.get_all_values()
header_row = 4  # 1-based で5行目がヘッダーの次
first_empty = 16  # 5+11=16行目が次の空き
for i, (post, dt, (h, m)) in enumerate(zip(remaining_posts, dates, slots)):
    row = first_empty + i
    row_data = ["", post, dt.strftime("%Y/%m/%d"), h, m]
    sheet.append_row(row_data)
    time.sleep(1.2)  # レート制限回避
    print(f"  {12+i}本目 行追加: {dt.strftime('%m/%d')} {h}:{m:02d}")

print("残り10件の転記を完了しました。")
