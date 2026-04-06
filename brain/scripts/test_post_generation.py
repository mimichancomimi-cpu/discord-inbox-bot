#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投稿生成ロジックのテストスクリプト
投稿生成部分だけを確認できます
"""

import json
import os
from generate_posts import AccountDesign, load_all_account_designs, generate_posts_with_ai, generate_sample_posts


def test_single_account(account_name: str = None):
    """単一アカウントの投稿生成をテスト"""
    # 設定を読み込む
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"エラー: {config_path} が見つかりません")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # アカウント設計を読み込む
    accounts_dir = "５０アカウント運用"
    accounts = load_all_account_designs(accounts_dir)
    
    if not accounts:
        print("エラー: アカウント設計ファイルが見つかりません")
        return
    
    # 指定されたアカウントを探す、または最初のアカウントを使用
    if account_name:
        account = next((a for a in accounts if account_name in a.account_name), None)
        if not account:
            print(f"エラー: {account_name} が見つかりません")
            print(f"利用可能なアカウント: {', '.join([a.account_name for a in accounts])}")
            return
    else:
        account = accounts[0]
    
    print("=" * 60)
    print(f"投稿生成テスト: {account.account_name}")
    print("=" * 60)
    
    # アカウント設計の情報を表示
    print(f"\n📋 アカウント情報:")
    print(f"  ジャンル: {account.genre}")
    print(f"  キーワード: {', '.join(account.keywords[:5])}")
    print(f"  コンテンツの柱: {len(account.content_pillars)}個")
    print(f"  テンプレート: {len(account.templates)}個")
    
    # OpenAI APIキーを取得
    api_key = config.get('openai_api_key', '')
    
    if not api_key:
        print(f"\n⚠ OpenAI APIキーが設定されていません。")
        print(f"   サンプル投稿を生成します。\n")
        use_ai = False
    else:
        print(f"\n✓ OpenAI APIキーが設定されています。")
        print(f"   AI投稿を生成します。\n")
        use_ai = True
    
    # 投稿を生成
    print("📝 投稿生成中...\n")
    posts = generate_posts_with_ai(account, num_posts=5, api_key=api_key if use_ai else "")
    
    # 結果を表示
    print("=" * 60)
    print(f"生成された投稿 ({len(posts)}件)")
    print("=" * 60)
    
    for i, post in enumerate(posts, 1):
        print(f"\n【投稿 {i}】")
        print("-" * 60)
        print(post)
        print("-" * 60)
        print(f"文字数: {len(post)}文字")
    
    # サマリー
    print("\n" + "=" * 60)
    print("サマリー")
    print("=" * 60)
    print(f"生成された投稿数: {len(posts)}件")
    avg_length = sum(len(p) for p in posts) / len(posts) if posts else 0
    print(f"平均文字数: {avg_length:.1f}文字")
    print(f"最短: {min(len(p) for p in posts) if posts else 0}文字")
    print(f"最長: {max(len(p) for p in posts) if posts else 0}文字")


def test_all_accounts_design_loading():
    """すべてのアカウント設計の読み込みをテスト"""
    accounts_dir = "５０アカウント運用"
    accounts = load_all_account_designs(accounts_dir)
    
    print("=" * 60)
    print("アカウント設計読み込みテスト")
    print("=" * 60)
    print(f"\n読み込まれたアカウント数: {len(accounts)}個\n")
    
    for account in accounts:
        print(f"✓ {account.account_name}")
        print(f"  ジャンル: {account.genre}")
        print(f"  コンテンツの柱: {len(account.content_pillars)}個")
        print(f"  テンプレート: {len(account.templates)}個")
        print(f"  キーワード数: {len(account.keywords)}個")
        if account.templates:
            print(f"  テンプレート例: {account.templates[0]['theme']}")
        print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test-loading':
            # アカウント設計の読み込みテスト
            test_all_accounts_design_loading()
        elif sys.argv[1] == '--account':
            # 指定されたアカウントでテスト
            account_name = sys.argv[2] if len(sys.argv) > 2 else None
            test_single_account(account_name)
        else:
            print("使用方法:")
            print("  python test_post_generation.py                    # 最初のアカウントでテスト")
            print("  python test_post_generation.py --account はなママ  # 指定アカウントでテスト")
            print("  python test_post_generation.py --test-loading     # アカウント設計読み込みテスト")
    else:
        # デフォルト: 最初のアカウントでテスト
        test_single_account()
