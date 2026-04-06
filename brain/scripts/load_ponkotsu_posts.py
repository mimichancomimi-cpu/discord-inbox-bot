#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ぽんこつ母ちゃんの過去投稿を読み込んでMarkdownファイルに記録するスクリプト
"""

import json
import os
from datetime import datetime
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials


def load_insights(credentials_path: str, spreadsheet_id: str, limit: int = 200) -> list:
    """投稿インサイトから過去の投稿情報を読み込む"""
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(
            credentials_path, scopes=scope
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        worksheet = spreadsheet.worksheet("投稿インサイト")
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return []
        
        # ヘッダー行を取得
        headers = all_values[0]
        
        # データ行を処理
        insights = []
        for row in all_values[1:limit+1]:
            if not row or not any(cell for cell in row):
                continue
            
            insight = {}
            # 列名のマッピングを先に作成
            header_map = {}
            for i, header in enumerate(headers):
                header_clean = header.strip() if header else ''
                header_map[header_clean] = i
            
            # 列名またはインデックスでマッピング
            # 投稿本文（列I、インデックス8）
            if '投稿本文' in header_map:
                col_idx = header_map['投稿本文']
                if col_idx < len(row) and row[col_idx]:
                    insight['post_content'] = row[col_idx].strip()
            elif len(row) > 8 and row[8]:
                insight['post_content'] = row[8].strip()
            
            # いいね数（列D、インデックス3）
            if 'いいね数' in header_map:
                col_idx = header_map['いいね数']
                if col_idx < len(row) and row[col_idx]:
                    try:
                        insight['likes'] = int(str(row[col_idx]).replace(',', ''))
                    except:
                        insight['likes'] = 0
            elif len(row) > 3 and row[3]:
                try:
                    insight['likes'] = int(str(row[3]).replace(',', ''))
                except:
                    insight['likes'] = 0
            
            # 再生数/表示数（列C、インデックス2）
            if '再生数/表示数' in header_map:
                col_idx = header_map['再生数/表示数']
                if col_idx < len(row) and row[col_idx]:
                    try:
                        insight['views'] = int(str(row[col_idx]).replace(',', ''))
                    except:
                        insight['views'] = 0
            elif len(row) > 2 and row[2]:
                try:
                    insight['views'] = int(str(row[2]).replace(',', ''))
                except:
                    insight['views'] = 0
            
            # 返信数（列E、インデックス4）
            if '返信数' in header_map:
                col_idx = header_map['返信数']
                if col_idx < len(row) and row[col_idx]:
                    try:
                        insight['replies'] = int(str(row[col_idx]).replace(',', ''))
                    except:
                        insight['replies'] = 0
            elif len(row) > 4 and row[4]:
                try:
                    insight['replies'] = int(str(row[col_idx]).replace(',', ''))
                except:
                    insight['replies'] = 0
            
            # ポストURL（列A、インデックス0）
            if 'ポストURL' in header_map:
                col_idx = header_map['ポストURL']
                if col_idx < len(row) and row[col_idx]:
                    insight['post_url'] = row[col_idx].strip()
            elif len(row) > 0 and row[0]:
                insight['post_url'] = row[0].strip()
            
            # インサイト取得日時（列J、インデックス9）
            if 'インサイト取得日時' in header_map:
                col_idx = header_map['インサイト取得日時']
                if col_idx < len(row) and row[col_idx]:
                    insight['insight_date'] = row[col_idx].strip()
            elif len(row) > 9 and row[9]:
                insight['insight_date'] = row[9].strip()
            
            # 投稿本文がある場合のみ追加
            if insight.get('post_content') and len(insight['post_content']) > 5:
                insights.append(insight)
        
        return insights
    except Exception as e:
        print(f"投稿インサイト読み込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return []


def save_to_markdown(insights: list, account_file: str):
    """過去投稿をアカウント設計ファイルに追記"""
    # 既存のファイルを読み込む（存在しない場合は空文字列）
    if os.path.exists(account_file):
        with open(account_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    else:
        existing_content = ""
    
    # 既に過去投稿セクションがある場合は削除
    if "## 過去投稿記録" in existing_content:
        # 過去投稿セクション以降を削除
        existing_content = existing_content.split("## 過去投稿記録")[0].rstrip()
    
    # パフォーマンス順にソート（いいね数 + 表示数/10）
    sorted_insights = sorted(
        insights,
        key=lambda x: (x.get('likes', 0) + x.get('views', 0) // 10),
        reverse=True
    )
    
    # 過去投稿セクションを作成
    posts_section = "\n\n---\n\n## 過去投稿記録\n\n"
    posts_section += f"最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
    posts_section += f"総投稿数: {len(insights)}件\n\n"
    
    # パフォーマンス統計
    total_likes = sum(i.get('likes', 0) for i in insights)
    total_views = sum(i.get('views', 0) for i in insights)
    total_replies = sum(i.get('replies', 0) for i in insights)
    
    posts_section += f"**パフォーマンス統計:**\n"
    posts_section += f"- 総いいね数: {total_likes:,}\n"
    posts_section += f"- 総表示数: {total_views:,}\n"
    posts_section += f"- 総返信数: {total_replies:,}\n\n"
    posts_section += "---\n\n"
    
    # 各投稿を記録
    for i, insight in enumerate(sorted_insights, 1):
        post_content = insight.get('post_content', '')
        likes = insight.get('likes', 0)
        views = insight.get('views', 0)
        replies = insight.get('replies', 0)
        post_url = insight.get('post_url', '')
        insight_date = insight.get('insight_date', '')
        
        posts_section += f"### 投稿 {i}\n\n"
        posts_section += f"**投稿本文:**\n\n"
        posts_section += f"{post_content}\n\n"
        posts_section += f"**パフォーマンス:**\n"
        posts_section += f"- いいね数: {likes:,}\n"
        posts_section += f"- 表示数: {views:,}\n"
        posts_section += f"- 返信数: {replies:,}\n"
        if post_url:
            posts_section += f"- URL: {post_url}\n"
        if insight_date:
            posts_section += f"- 取得日時: {insight_date}\n"
        posts_section += "\n---\n\n"
    
    # ファイルに書き込む
    with open(account_file, 'w', encoding='utf-8') as f:
        f.write(existing_content + posts_section)


def main():
    # 設定を読み込む
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"エラー: {config_path} が見つかりません")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # ぽんこつ母ちゃんのスプレッドシートIDを取得
    account_mappings = config.get('account_mappings', {})
    ponkotsu_mapping = account_mappings.get('ぽんこつ母ちゃん')
    
    if not ponkotsu_mapping:
        print("エラー: ぽんこつ母ちゃんのアカウントマッピングが見つかりません")
        return
    
    spreadsheet_id = ponkotsu_mapping.get('spreadsheet_id')
    credentials_path = config.get('credentials_path', 'credentials.json')
    
    if not spreadsheet_id:
        print("エラー: ぽんこつ母ちゃんのスプレッドシートIDが見つかりません")
        return
    
    if not os.path.exists(credentials_path):
        print(f"エラー: 認証情報ファイルが見つかりません: {credentials_path}")
        return
    
    print("=" * 60)
    print("ぽんこつ母ちゃんの過去投稿を読み込んでいます...")
    print("=" * 60)
    print(f"スプレッドシートID: {spreadsheet_id}")
    print(f"認証情報: {credentials_path}\n")
    
    # 過去投稿を読み込む
    insights = load_insights(credentials_path, spreadsheet_id, limit=200)
    
    if not insights:
        print("⚠ 過去の投稿が見つかりませんでした")
        return
    
    print(f"✓ {len(insights)}件の過去投稿を読み込みました\n")
    
    # アカウント設計ファイルに追記
    account_file = "５０アカウント運用/1.ぽんこつ母ちゃん.md"
    save_to_markdown(insights, account_file)
    
    print(f"✓ 過去投稿を記録しました: {account_file}")
    print(f"  総投稿数: {len(insights)}件")
    
    # パフォーマンス統計
    total_likes = sum(i.get('likes', 0) for i in insights)
    total_views = sum(i.get('views', 0) for i in insights)
    total_replies = sum(i.get('replies', 0) for i in insights)
    
    print(f"\nパフォーマンス統計:")
    print(f"  総いいね数: {total_likes:,}")
    print(f"  総表示数: {total_views:,}")
    print(f"  総返信数: {total_replies:,}")
    
    # トップ5投稿を表示
    sorted_insights = sorted(
        insights,
        key=lambda x: (x.get('likes', 0) + x.get('views', 0) // 10),
        reverse=True
    )
    
    print(f"\nトップ5投稿:")
    for i, insight in enumerate(sorted_insights[:5], 1):
        post_content = insight.get('post_content', '')[:50] + '...' if len(insight.get('post_content', '')) > 50 else insight.get('post_content', '')
        likes = insight.get('likes', 0)
        views = insight.get('views', 0)
        print(f"  {i}. いいね: {likes:,}, 表示: {views:,}")
        print(f"     {post_content}")


if __name__ == '__main__':
    main()
