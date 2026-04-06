#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""スプレッドシートの構造を確認するスクリプト"""

import gspread
from google.oauth2.service_account import Credentials

credentials_path = "credentials.json"
spreadsheet_id = "1uj5a4GVcxMTzW8aoCIQL8Oj9Y8qvY3Wsn3bYGfEPymw"
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
print("\n" + "="*60)
print("最初の20行を表示:")
print("="*60)

# 最後の5行を表示
print("\n" + "="*60)
print("最後の5行を表示:")
print("="*60)

for i in range(max(1, worksheet.row_count - 4), worksheet.row_count + 1):
    row = worksheet.row_values(i)
    print(f"\n行 {i}:")
    for j, cell in enumerate(row[:10]):  # 最初の10列のみ表示
        if cell:
            print(f"  列 {j+1}: {cell[:100]}")  # 最初の100文字のみ表示
