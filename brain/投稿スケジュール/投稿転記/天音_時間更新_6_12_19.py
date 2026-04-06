#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天音スプシの既存21件の投稿時間を 朝6時・昼12時・夜19時 に更新する"""

import json
import sys
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

root_dir = Path(__file__).resolve().parent.parent.parent
config_file = root_dir / "config.json"
credentials_file = root_dir / "credentials.json"

with open(config_file, "r", encoding="utf-8") as f:
    config = json.load(f)
mapping = config["account_mappings"].get("天音") or config["account_mappings"].get("天音🪽元恋愛依存が語る幸せの恋愛術")
spreadsheet_id = mapping["spreadsheet_id"]
worksheet_name = mapping.get("worksheet_name", "自動投稿")

creds = Credentials.from_service_account_file(str(credentials_file), scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
])
client = gspread.authorize(creds)
sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

# 列 D=予約投稿時間(時), E=予約投稿時間(分)。行5〜25が21件。1日3回: 朝6, 昼12, 夜19
slots = [(6, 0), (12, 0), (19, 0)]
rows_data = [[slots[i % 3][0], slots[i % 3][1]] for i in range(21)]
sheet.update(values=rows_data, range_name="D5:E25")
print("21件の投稿時間を 6:00 / 12:00 / 19:00 に更新しました。")
