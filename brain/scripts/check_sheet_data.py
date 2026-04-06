#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""スプレッドシートの最新データを確認するスクリプト"""

import gspread
from google.oauth2.service_account import Credentials

credentials_path = "credentials.json"
spreadsheet_id = "1TnWD-b8FUquhuKPeeiYdWtlvE6HoToJcKZqBuzr2psw"
worksheet_name = "自動投稿"

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(spreadsheet_id)
worksheet = spreadsheet.worksheet(worksheet_name)

print(f"シート名: {worksheet_name}")
print(f"総行数: {worksheet.row_count}")
print(f"総列数: {worksheet.col_count}")

# 最後の20行を確認
print("\n" + "="*60)
print("最後の20行を確認:")
print("="*60)

for i in range(max(1, worksheet.row_count - 19), worksheet.row_count + 1):
    row = worksheet.row_values(i)
    # 空でない行のみ表示
    if any(cell for cell in row):
        print(f"\n行 {i}:")
        for j, cell in enumerate(row[:10]):  # 最初の10列のみ表示
            if cell:
                print(f"  列 {j+1} ({chr(65+j)}): {cell[:150]}")  # 最初の150文字のみ表示

# データが入っている行を探す（行5から行100まで）
print("\n" + "="*60)
print("データが入っている行を検索（行5から行100まで）:")
print("="*60)

all_values = worksheet.get_all_values()
found_data = False
for i in range(4, min(100, len(all_values))):  # 行5（インデックス4）から100行まで
    row = all_values[i]
    if any(cell.strip() for cell in row if cell):
        found_data = True
        print(f"\n行 {i+1}:")
        for j, cell in enumerate(row[:10]):
            if cell and cell.strip():
                print(f"  列 {j+1} ({chr(65+j)}): {cell[:150]}")

if not found_data:
    print("行5から行100までにデータが見つかりませんでした。")
    print("\n行10001以降のデータを確認します:")
    for i in range(10000, min(10010, len(all_values))):
        row = all_values[i]
        if any(cell.strip() for cell in row if cell):
            print(f"\n行 {i+1}:")
            for j, cell in enumerate(row[:10]):
                if cell and cell.strip():
                    print(f"  列 {j+1} ({chr(65+j)}): {cell[:150]}")
