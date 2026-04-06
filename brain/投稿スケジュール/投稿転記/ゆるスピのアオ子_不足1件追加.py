#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ゆるスピのアオ子スプシに不足していた10本目を1件追加（2/12 6:00）"""

import json
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

root_dir = Path(__file__).resolve().parent.parent.parent
config_file = root_dir / "config.json"
credentials_file = root_dir / "credentials.json"

with open(config_file, "r", encoding="utf-8") as f:
    config = json.load(f)
mapping = config["account_mappings"].get("ゆるスピのアオ子")
spreadsheet_id = mapping["spreadsheet_id"]
worksheet_name = mapping.get("worksheet_name", "自動投稿")

creds = Credentials.from_service_account_file(
    str(credentials_file),
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
client = gspread.authorize(creds)
sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

# 10本目（スピリチュアルに興味ある人フォローして…）を25行目に追加。2/12 6:00で1件だけ延長。
post_10 = "スピリチュアルに興味ある人、フォローしてくれたら嬉しいな💎ゆる〜く引き寄せとかメンタルデトックスとか、頑張らないやり方だけ発信してるから。一緒に人生イージーモードにしよ✌️"
row_data = ["", post_10, "2026/02/12", 6, 0]
sheet.append_row(row_data)
print("不足分の10本目を1件追加しました（2/12 6:00）。")
