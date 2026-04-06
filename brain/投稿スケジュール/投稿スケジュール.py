#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投稿をスプレッドシートに転記して日時設定まで行う汎用スクリプト
どのアカウントでも使用可能
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

# 親ディレクトリのパスを取得（このスクリプトが投稿スケジュールフォルダ内にある場合）
SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent

def schedule_posts_to_spreadsheet(account_file_path, posts, morning_hour=9, morning_minute=0,
                                 noon_hour=14, noon_minute=0,
                                 evening_hour=21, evening_minute=0, start_date=None, posts_per_day=2):
    """
    投稿をスプレッドシートに転記して日時設定まで行う
    
    Args:
        account_file_path: アカウント設計ファイルのパス（親ディレクトリからの相対パス）
        posts: 投稿内容のリスト
        morning_hour: 朝の投稿時間（時）
        morning_minute: 朝の投稿時間（分）
        noon_hour: 昼の投稿時間（時、posts_per_day=3のとき使用）
        noon_minute: 昼の投稿時間（分）
        evening_hour: 夜の投稿時間（時）
        evening_minute: 夜の投稿時間（分）
        start_date: 開始日（datetime.dateオブジェクト、Noneの場合は今日）
        posts_per_day: 1日の投稿数（1, 2, または 3、デフォルト: 2）
    """
    # 設定ファイルのパス（親ディレクトリを基準）
    config_file = PARENT_DIR / "config.json"
    credentials_file = PARENT_DIR / "credentials.json"
    
    if not config_file.exists():
        print(f"エラー: {config_file} が見つかりません")
        return False
    
    if not credentials_file.exists():
        print(f"エラー: {credentials_file} が見つかりません")
        return False
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # アカウントファイルのパスを解決（親ディレクトリを基準）
    if not os.path.isabs(account_file_path):
        account_file = PARENT_DIR / account_file_path
    else:
        account_file = Path(account_file_path)
    
    # アカウント名を取得（ファイル名から推測、またはアカウント設計ファイルから読み込む）
    account_name = None
    if account_file.exists():
        # アカウント設計ファイルからアカウント名を読み込む
        try:
            with open(account_file, 'r', encoding='utf-8') as f:
                content = f.read()
                import re
                # アカウント名を抽出
                name_match = re.search(r'\*\*アカウント名:\*\*\s*(.+)', content)
                if name_match:
                    account_name = name_match.group(1).strip()
        except:
            pass
    
    # ファイル名からも推測
    if not account_name:
        file_name = account_file.name
        # ファイル名から数字と拡張子を除く
        account_name = file_name.replace('.md', '').split('.', 1)[-1].strip()
    
    print(f"アカウント名: {account_name}")
    
    # スプレッドシートIDとシート名を取得
    account_mappings = config.get('account_mappings', {})
    spreadsheet_id = None
    worksheet_name = '自動投稿'
    
    # アカウント名で検索（完全一致、部分一致）
    for key, mapping in account_mappings.items():
        if account_name == key or account_name in key or key in account_name:
            spreadsheet_id = mapping.get('spreadsheet_id')
            worksheet_name = mapping.get('worksheet_name', '自動投稿')
            print(f"マッピングを発見: {key}")
            break
    
    if not spreadsheet_id:
        print(f"警告: アカウント '{account_name}' のスプレッドシートIDが見つかりません")
        print(f"利用可能なアカウント: {list(account_mappings.keys())}")
        return False
    
    print(f"スプレッドシートID: {spreadsheet_id}")
    print(f"シート名: {worksheet_name}")
    
    # Google Sheetsに接続
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(str(credentials_file), scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    print(f"スプレッドシート '{worksheet_name}' に接続しました")
    
    # シートの構造を確認（ヘッダー行を探す）
    all_values = worksheet.get_all_values()
    header_row_index = 0
    headers = []
    
    for i in range(min(10, len(all_values))):
        row = all_values[i]
        if 'ポスト文' in ' '.join([str(cell) for cell in row if cell]):
            headers = row
            header_row_index = i
            break
    
    if not headers:
        headers = all_values[0] if all_values else []
        header_row_index = 0
    
    print(f"ヘッダー行: 行 {header_row_index + 1}")
    
    # 列のインデックスを取得
    post_col_idx = None
    date_col_idx = None
    hour_col_idx = None
    minute_col_idx = None
    
    for i, header in enumerate(headers):
        header_str = str(header).strip().replace('\n', ' ')
        if 'ポスト文' in header_str:
            post_col_idx = i
        elif '予約投稿' in header_str and '日時' in header_str:
            date_col_idx = i
        elif '予約投稿' in header_str and '時間' in header_str and '時' in header_str and '分' not in header_str:
            hour_col_idx = i
        elif '予約投稿' in header_str and '時間' in header_str and '分' in header_str:
            minute_col_idx = i
    
    if post_col_idx is None:
        post_col_idx = 1
        print(f"警告: ポスト文の列が見つかりませんでした。列2を使用します。")
    
    print(f"\n列マッピング:")
    print(f"  ポスト文: 列 {post_col_idx + 1}")
    print(f"  予約投稿日時: 列 {date_col_idx + 1 if date_col_idx is not None else '見つかりません'}")
    print(f"  予約投稿時間(時): 列 {hour_col_idx + 1 if hour_col_idx is not None else '見つかりません'}")
    print(f"  予約投稿時間(分): 列 {minute_col_idx + 1 if minute_col_idx is not None else '見つかりません'}")
    
    if date_col_idx is None or hour_col_idx is None or minute_col_idx is None:
        print("警告: 日時関連の列が見つかりませんでしたが、続行します。")
    
    # 開始日を決定
    if start_date is None:
        start_date = datetime.now().date()
    
    # 投稿数を計算
    if posts_per_day == 1:
        days_needed = len(posts)
        print(f"\n投稿数: {len(posts)}個")
        print(f"予約期間: {days_needed}日間（1日1回）")
    elif posts_per_day == 3:
        days_needed = (len(posts) + 2) // 3  # 切り上げ
        print(f"\n投稿数: {len(posts)}個")
        print(f"予約期間: {days_needed}日間（1日3回: {morning_hour}:{morning_minute:02d}, {noon_hour}:{noon_minute:02d}, {evening_hour}:{evening_minute:02d}）")
    else:
        days_needed = (len(posts) + 1) // 2  # 切り上げ
        print(f"\n投稿数: {len(posts)}個")
        print(f"予約期間: {days_needed}日間（1日2回）")
    print(f"開始日: {start_date}")
    
    # 最初の空の行を見つける
    next_row_index = header_row_index + 1
    for i in range(next_row_index, min(next_row_index + 1000, len(all_values))):
        row = all_values[i]
        if len(row) <= post_col_idx or not row[post_col_idx] or not row[post_col_idx].strip():
            next_row_index = i
            break
    else:
        next_row_index = len(all_values)
    
    print(f"最初の空の行: {next_row_index + 1}")
    
    # 各投稿を予約
    post_index = 0
    success_count = 0
    
    for day in range(days_needed):
        current_date = start_date + timedelta(days=day)
        
        # 1日1回の場合は朝の投稿のみ、1日2回の場合は朝と夜の両方
        if posts_per_day == 1:
            # 1日1回の場合は朝の時間を使用
            if post_index < len(posts):
                print(f"\n[{post_index + 1}/{len(posts)}] 投稿を予約: {current_date} {morning_hour:02d}:{morning_minute:02d}")
                print(f"投稿内容: {posts[post_index][:50]}...")
                
                # 行データを作成
                max_col = max(len(headers), post_col_idx + 1, 
                             (date_col_idx or 0) + 1, (hour_col_idx or 0) + 1, (minute_col_idx or 0) + 1)
                row_data = [''] * max_col
                
                # ポスト文を設定
                row_data[post_col_idx] = posts[post_index]
                
                # 日時を設定
                date_str = current_date.strftime('%Y/%m/%d')
                if date_col_idx is not None:
                    row_data[date_col_idx] = date_str
                # 時間は数値型として設定（文字列にしない）
                if hour_col_idx is not None:
                    row_data[hour_col_idx] = morning_hour  # 数値型のまま
                if minute_col_idx is not None:
                    row_data[minute_col_idx] = morning_minute  # 数値型のまま
                
                # スプレッドシートに書き込む
                try:
                    worksheet.update(range_name=f'A{next_row_index + 1}', values=[row_data])
                    
                    # 時間と分を個別に数値型として設定（確実に数値として認識させる）
                    if hour_col_idx is not None:
                        worksheet.update_cell(next_row_index + 1, hour_col_idx + 1, morning_hour)
                    if minute_col_idx is not None:
                        worksheet.update_cell(next_row_index + 1, minute_col_idx + 1, morning_minute)
                    
                    print(f"✓ 投稿を予約しました（行 {next_row_index + 1}）")
                    next_row_index += 1
                    success_count += 1
                except Exception as e:
                    print(f"✗ 投稿の予約に失敗しました: {e}")
                
                post_index += 1
                import time
                time.sleep(0.5)  # API制限を避けるため
            continue
        
        # 朝の投稿
        if post_index < len(posts):
            print(f"\n[{post_index + 1}/{len(posts)}] 朝の投稿を予約: {current_date} {morning_hour:02d}:{morning_minute:02d}")
            print(f"投稿内容: {posts[post_index][:50]}...")
            
            # 行データを作成
            max_col = max(len(headers), post_col_idx + 1, 
                         (date_col_idx or 0) + 1, (hour_col_idx or 0) + 1, (minute_col_idx or 0) + 1)
            row_data = [''] * max_col
            
            # ポスト文を設定
            row_data[post_col_idx] = posts[post_index]
            
            # 日時を設定
            date_str = current_date.strftime('%Y/%m/%d')
            if date_col_idx is not None:
                row_data[date_col_idx] = date_str
            # 時間は数値型として設定（文字列にしない）
            if hour_col_idx is not None:
                row_data[hour_col_idx] = morning_hour  # 数値型のまま
            if minute_col_idx is not None:
                row_data[minute_col_idx] = morning_minute  # 数値型のまま
            
            # スプレッドシートに書き込む
            try:
                worksheet.update(range_name=f'A{next_row_index + 1}', values=[row_data])
                
                # 時間と分を個別に数値型として設定（確実に数値として認識させる）
                if hour_col_idx is not None:
                    worksheet.update_cell(next_row_index + 1, hour_col_idx + 1, morning_hour)
                if minute_col_idx is not None:
                    worksheet.update_cell(next_row_index + 1, minute_col_idx + 1, morning_minute)
                
                print(f"✓ 朝の投稿を予約しました（行 {next_row_index + 1}）")
                next_row_index += 1
                success_count += 1
            except Exception as e:
                print(f"✗ 朝の投稿の予約に失敗しました: {e}")
            
            post_index += 1
            import time
            time.sleep(0.5)  # API制限を避けるため
        
        # 昼の投稿（1日3回の場合のみ）
        if posts_per_day == 3 and post_index < len(posts):
            print(f"\n[{post_index + 1}/{len(posts)}] 昼の投稿を予約: {current_date} {noon_hour:02d}:{noon_minute:02d}")
            print(f"投稿内容: {posts[post_index][:50]}...")
            max_col = max(len(headers), post_col_idx + 1,
                         (date_col_idx or 0) + 1, (hour_col_idx or 0) + 1, (minute_col_idx or 0) + 1)
            row_data = [''] * max_col
            row_data[post_col_idx] = posts[post_index]
            date_str = current_date.strftime('%Y/%m/%d')
            if date_col_idx is not None:
                row_data[date_col_idx] = date_str
            if hour_col_idx is not None:
                row_data[hour_col_idx] = noon_hour
            if minute_col_idx is not None:
                row_data[minute_col_idx] = noon_minute
            try:
                worksheet.update(range_name=f'A{next_row_index + 1}', values=[row_data])
                if hour_col_idx is not None:
                    worksheet.update_cell(next_row_index + 1, hour_col_idx + 1, noon_hour)
                if minute_col_idx is not None:
                    worksheet.update_cell(next_row_index + 1, minute_col_idx + 1, noon_minute)
                print(f"✓ 昼の投稿を予約しました（行 {next_row_index + 1}）")
                next_row_index += 1
                success_count += 1
            except Exception as e:
                print(f"✗ 昼の投稿の予約に失敗しました: {e}")
            post_index += 1
            import time
            time.sleep(0.5)
        
        # 夜の投稿
        if post_index < len(posts):
            print(f"\n[{post_index + 1}/{len(posts)}] 夜の投稿を予約: {current_date} {evening_hour:02d}:{evening_minute:02d}")
            print(f"投稿内容: {posts[post_index][:50]}...")
            
            # 行データを作成
            max_col = max(len(headers), post_col_idx + 1, 
                         (date_col_idx or 0) + 1, (hour_col_idx or 0) + 1, (minute_col_idx or 0) + 1)
            row_data = [''] * max_col
            
            # ポスト文を設定
            row_data[post_col_idx] = posts[post_index]
            
            # 日時を設定
            date_str = current_date.strftime('%Y/%m/%d')
            if date_col_idx is not None:
                row_data[date_col_idx] = date_str
            # 時間は数値型として設定（文字列にしない）
            if hour_col_idx is not None:
                row_data[hour_col_idx] = evening_hour  # 数値型のまま
            if minute_col_idx is not None:
                row_data[minute_col_idx] = evening_minute  # 数値型のまま
            
            # スプレッドシートに書き込む
            try:
                worksheet.update(range_name=f'A{next_row_index + 1}', values=[row_data])
                
                # 時間と分を個別に数値型として設定（確実に数値として認識させる）
                if hour_col_idx is not None:
                    worksheet.update_cell(next_row_index + 1, hour_col_idx + 1, evening_hour)
                if minute_col_idx is not None:
                    worksheet.update_cell(next_row_index + 1, minute_col_idx + 1, evening_minute)
                
                print(f"✓ 夜の投稿を予約しました（行 {next_row_index + 1}）")
                next_row_index += 1
                success_count += 1
            except Exception as e:
                print(f"✗ 夜の投稿の予約に失敗しました: {e}")
            
            post_index += 1
            import time
            time.sleep(0.5)  # API制限を避けるため
    
    print(f"\n{'='*60}")
    print(f"完了しました！{success_count}/{len(posts)}個の投稿を予約しました。")
    print(f"{'='*60}")
    
    return success_count == len(posts)


def main():
    """コマンドラインから実行する場合のメイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='投稿をスプレッドシートに転記して日時設定まで行う')
    parser.add_argument('account_file', help='アカウント設計ファイルのパス（親ディレクトリからの相対パス）')
    parser.add_argument('--posts-file', help='投稿内容が書かれたファイル（1行1投稿、またはJSON形式）')
    parser.add_argument('--posts', nargs='+', help='投稿内容（複数指定可能）')
    parser.add_argument('--morning-hour', type=int, default=9, help='朝の投稿時間（時、デフォルト: 9）')
    parser.add_argument('--morning-minute', type=int, default=0, help='朝の投稿時間（分、デフォルト: 0）')
    parser.add_argument('--evening-hour', type=int, default=21, help='夜の投稿時間（時、デフォルト: 21）')
    parser.add_argument('--evening-minute', type=int, default=0, help='夜の投稿時間（分、デフォルト: 0）')
    parser.add_argument('--start-date', help='開始日（YYYY-MM-DD形式、デフォルト: 今日）')
    
    args = parser.parse_args()
    
    # 投稿内容を取得
    posts = []
    
    if args.posts_file:
        # ファイルから読み込む
        posts_file = Path(args.posts_file)
        if not posts_file.is_absolute():
            posts_file = PARENT_DIR / posts_file
        
        with open(posts_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # JSON形式かどうか判定
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    posts = data
                else:
                    posts = [data]
            except:
                # テキスト形式（1行1投稿、または区切り文字で分割）
                posts = [line.strip() for line in content.split('\n') if line.strip()]
    elif args.posts:
        posts = args.posts
    else:
        print("エラー: 投稿内容を指定してください（--posts-file または --posts）")
        return
    
    if not posts:
        print("エラー: 投稿内容が空です")
        return
    
    # 開始日をパース
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        except:
            print(f"警告: 開始日の形式が正しくありません: {args.start_date}")
    
    # 実行
    schedule_posts_to_spreadsheet(
        account_file_path=args.account_file,
        posts=posts,
        morning_hour=args.morning_hour,
        morning_minute=args.morning_minute,
        evening_hour=args.evening_hour,
        evening_minute=args.evening_minute,
        start_date=start_date
    )


if __name__ == '__main__':
    # コマンドラインから実行された場合
    if len(sys.argv) > 1:
        main()
    else:
        # スクリプトとしてインポートして使用する場合の例
        print("使用方法:")
        print("  python3 投稿スケジュール.py <アカウントファイル> --posts-file <投稿ファイル>")
        print("  または")
        print("  python3 投稿スケジュール.py <アカウントファイル> --posts '投稿1' '投稿2' ...")
