#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投稿インサイトの構造を確認するスクリプト"""

import gspread
from google.oauth2.service_account import Credentials

credentials_path = "credentials.json"
spreadsheet_id = "1TnWD-b8FUquhuKPeeiYdWtlvE6HoToJcKZqBuzr2psw"

scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(spreadsheet_id)

# すべてのシートを確認
print("利用可能なシート:")
for sheet in spreadsheet.worksheets():
    print(f"  - {sheet.title} (ID: {sheet.id})")

# 投稿インサイトシートを確認
try:
    worksheet = spreadsheet.worksheet("投稿インサイト")
    print(f"\n投稿インサイトシートの構造:")
    print(f"総行数: {worksheet.row_count}")
    print(f"総列数: {worksheet.col_count}")
    
    print("\n最初の10行を表示:")
    for i in range(1, min(11, worksheet.row_count + 1)):
        row = worksheet.row_values(i)
        print(f"\n行 {i}:")
        for j, cell in enumerate(row[:10]):  # 最初の10列のみ表示
            if cell:
                print(f"  列 {j+1}: {cell[:100]}")  # 最初の100文字のみ表示
except Exception as e:
    print(f"エラー: {e}")
