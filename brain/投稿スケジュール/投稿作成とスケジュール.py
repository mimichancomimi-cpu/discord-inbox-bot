#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アカウント設計ファイルから投稿を生成してスプレッドシートに転記する統合スクリプト
Cursor上で実行可能
"""

import os
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# 親ディレクトリのパスを取得
SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent

# モジュールのインポート
sys.path.insert(0, str(SCRIPT_DIR))
from 投稿スケジュール import schedule_posts_to_spreadsheet

# プロンプト生成モジュールから関数をインポート
import importlib.util
prompt_module_file = SCRIPT_DIR / "プロンプト生成.py"
spec = importlib.util.spec_from_file_location("プロンプト生成", prompt_module_file)
prompt_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompt_module)

# 投稿品質チェックモジュールをインポート
quality_check_file = SCRIPT_DIR / "投稿品質チェック.py"
spec_qc = importlib.util.spec_from_file_location("投稿品質チェック", quality_check_file)
quality_check_module = importlib.util.module_from_spec(spec_qc)
spec_qc.loader.exec_module(quality_check_module)

# 重複チェックモジュールをインポート
duplicate_check_file = SCRIPT_DIR / "重複チェック.py"
spec_dup = importlib.util.spec_from_file_location("重複チェック", duplicate_check_file)
duplicate_check_module = importlib.util.module_from_spec(spec_dup)
spec_dup.loader.exec_module(duplicate_check_module)

def generate_post_with_ai(prompt: str, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> Optional[str]:
    """
    AIを使って投稿を生成
    
    Args:
        prompt: プロンプト
        api_key: OpenAI APIキー（Noneの場合はCursorのAIを使用する形式でプロンプトを返す）
        model: 使用するモデル
    
    Returns:
        生成された投稿、またはNone（APIキーがない場合）
    """
    if not api_key:
        print("\n" + "="*60)
        print("OpenAI APIキーが設定されていません")
        print("="*60)
        print("\n以下のプロンプトをCursorのAIチャットに貼り付けて投稿を生成してください：\n")
        print("-"*60)
        print(prompt)
        print("-"*60)
        print("\n生成された投稿をコピーして、このスクリプトを再実行してください。")
        print("または、--posts オプションで投稿内容を直接指定してください。\n")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("AIで投稿を生成しています...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "あなたはThreads投稿の専門家です。指定されたアカウント設計に基づいて、魅力的な投稿を作成してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        post = response.choices[0].message.content.strip()
        
        # 分析や説明部分を削除（投稿内容のみを抽出）
        lines = post.split('\n')
        cleaned_lines = []
        skip = False
        
        for line in lines:
            # 分析や説明のマーカーを検出
            if any(marker in line for marker in ['分析', '説明', 'この投稿', '上記の投稿', '##', '**分析', '**説明']):
                skip = True
                continue
            
            # マークダウンの見出しや装飾をスキップ
            if line.strip().startswith('#') or line.strip().startswith('**') and '**' in line:
                continue
            
            if not skip and line.strip():
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        if not result:
            # クリーンアップがうまくいかなかった場合は元のテキストを使用
            result = post
        
        print("✓ 投稿を生成しました")
        return result
        
    except ImportError:
        print("エラー: openaiライブラリがインストールされていません")
        print("インストール: pip install openai")
        return None
    except Exception as e:
        print(f"エラー: 投稿生成に失敗しました: {e}")
        return None

def list_accounts():
    """利用可能なアカウント一覧を表示"""
    accounts_dir = PARENT_DIR / "５０アカウント運用"
    
    if not accounts_dir.exists():
        print(f"エラー: アカウントディレクトリが見つかりません: {accounts_dir}")
        return
    
    account_files = sorted(accounts_dir.glob("*.md"))
    
    print("\n利用可能なアカウント:")
    print("="*60)
    
    for i, file in enumerate(account_files, 1):
        # アカウント名を抽出
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'\*\*アカウント名:\*\*\s*(.+)', content)
                account_name = match.group(1).strip() if match else file.stem
        except:
            account_name = file.stem
        
        print(f"{i:2d}. {account_name}")
        print(f"    ファイル: {file.name}")
    
    print("="*60)

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='アカウント設計ファイルから投稿を生成してスプレッドシートに転記',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # アカウント一覧を表示
  python3 投稿作成とスケジュール.py --list
  
  # 投稿を生成してスプレッドシートに転記（AI使用）
  python3 投稿作成とスケジュール.py "５０アカウント運用/12.天音🪽元恋愛依存が語る幸せの恋愛術.md" --count 5
  
  # 投稿を直接指定してスプレッドシートに転記
  python3 投稿作成とスケジュール.py "５０アカウント運用/12.天音🪽元恋愛依存が語る幸せの恋愛術.md" --posts "投稿1" "投稿2"
  
  # テーマを指定
  python3 投稿作成とスケジュール.py "５０アカウント運用/1.ぽんこつ母ちゃん.md" --theme "ポイ活のコツ" --count 3
        """
    )
    
    parser.add_argument('account_file', nargs='?', help='アカウント設計ファイルのパス（親ディレクトリからの相対パス）')
    parser.add_argument('--list', action='store_true', help='利用可能なアカウント一覧を表示')
    parser.add_argument('--count', type=int, default=1, help='生成する投稿数（デフォルト: 1）')
    parser.add_argument('--theme', help='投稿のテーマ（オプション）')
    parser.add_argument('--post-type', choices=['短文', '中文', '長文'], help='投稿タイプ（オプション）')
    parser.add_argument('--emoji', choices=['使用する', '最小限', '使用しない'], default='最小限', help='絵文字の使用方針')
    parser.add_argument('--posts', nargs='+', help='投稿内容を直接指定（AI生成をスキップ）')
    parser.add_argument('--api-key', help='OpenAI APIキー（config.jsonからも読み込み可能）')
    parser.add_argument('--model', default='gpt-4o-mini', help='使用するAIモデル（デフォルト: gpt-4o-mini）')
    parser.add_argument('--morning-hour', type=int, default=9, help='朝の投稿時間（時、デフォルト: 9）')
    parser.add_argument('--morning-minute', type=int, default=0, help='朝の投稿時間（分、デフォルト: 0）')
    parser.add_argument('--evening-hour', type=int, default=21, help='夜の投稿時間（時、デフォルト: 21）')
    parser.add_argument('--evening-minute', type=int, default=0, help='夜の投稿時間（分、デフォルト: 0）')
    parser.add_argument('--start-date', help='開始日（YYYY-MM-DD形式、デフォルト: 今日）')
    parser.add_argument('--posts-per-day', type=int, choices=[1, 2], default=2, help='1日の投稿数（1または2、デフォルト: 2）')
    parser.add_argument('--no-schedule', action='store_true', help='スプレッドシートへの転記をスキップ（投稿生成のみ）')
    parser.add_argument('--prompt-only', action='store_true', help='プロンプトのみを表示（投稿生成は行わない）')
    parser.add_argument('--check-quality', action='store_true', default=True, help='生成された投稿の品質をチェック（デフォルト: 有効）')
    parser.add_argument('--no-check-quality', action='store_false', dest='check_quality', help='品質チェックをスキップ')
    parser.add_argument('--candidates', type=int, default=1, help='1投稿あたりの候補数（デフォルト: 1、複数候補から最適なものを選択）')
    parser.add_argument('--check-duplicate', action='store_true', default=True, help='過去投稿との重複をチェック（デフォルト: 有効）')
    parser.add_argument('--no-check-duplicate', action='store_false', dest='check_duplicate', help='重複チェックをスキップ')
    
    args = parser.parse_args()
    
    # アカウント一覧を表示
    if args.list:
        list_accounts()
        return
    
    # アカウントファイルが指定されていない場合
    if not args.account_file:
        parser.print_help()
        print("\nエラー: アカウントファイルを指定してください")
        print("\n利用可能なアカウント一覧を表示: --list")
        return
    
    # ファイルパスを解決
    if not os.path.isabs(args.account_file):
        account_file = PARENT_DIR / args.account_file
    else:
        account_file = Path(args.account_file)
    
    if not account_file.exists():
        print(f"エラー: ファイルが見つかりません: {account_file}")
        print("\n利用可能なアカウント一覧を表示: --list")
        return
    
    # 設定ファイルを読み込む
    config_file = PARENT_DIR / "config.json"
    config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # APIキーを取得
    api_key = args.api_key or config.get('openai_api_key', '')
    
    print(f"\n{'='*60}")
    print(f"アカウント設計ファイル: {account_file.name}")
    print(f"{'='*60}\n")
    
    # アカウント情報を抽出
    print("アカウント情報を読み込んでいます...")
    account_info = prompt_module.extract_account_info(account_file)
    print(f"✓ アカウント名: {account_info['account_name']}")
    
    # プロンプトを生成
    print("\nプロンプトを生成しています...")
    prompt = prompt_module.generate_prompt(
        account_info,
        theme=args.theme,
        post_type=args.post_type,
        emoji_policy=args.emoji
    )
    
    # プロンプトのみ表示
    if args.prompt_only:
        print("\n" + "="*60)
        print("生成されたプロンプト:")
        print("="*60 + "\n")
        print(prompt)
        return
    
    # 投稿を生成または取得
    posts = []
    
    if args.posts:
        # 投稿が直接指定されている場合
        posts = args.posts
        print(f"\n✓ {len(posts)}個の投稿を取得しました")
    else:
        # AIで投稿を生成
        print(f"\n{args.count}個の投稿を生成します...")
        if args.candidates > 1:
            print(f"  各投稿について{args.candidates}個の候補を生成し、最適なものを選択します")
        
        for i in range(args.count):
            print(f"\n[{i+1}/{args.count}] 投稿を生成中...")
            
            # 複数候補を生成
            candidates = []
            for j in range(args.candidates):
                if args.candidates > 1:
                    print(f"  候補 {j+1}/{args.candidates} を生成中...")
                candidate = generate_post_with_ai(prompt, api_key, args.model)
                
                if candidate:
                    # 品質チェック
                    quality_score = 0
                    check_results = None
                    if args.check_quality:
                        check_results = quality_check_module.check_post_quality(candidate, account_info)
                        quality_score = check_results['score'] / check_results['max_score'] * 100 if check_results['max_score'] > 0 else 0
                    
                    candidates.append({
                        'text': candidate,
                        'score': quality_score,
                        'check_results': check_results
                    })
                    
                    if args.candidates > 1:
                        print(f"    品質スコア: {quality_score:.1f}%")
            
            if not candidates:
                # APIキーがない場合は、プロンプトを表示して終了
                if not api_key:
                    print("\n投稿を生成するには、以下のいずれかの方法を使用してください：")
                    print("1. OpenAI APIキーを設定（--api-key または config.json）")
                    print("2. CursorのAIチャットに上記のプロンプトを貼り付けて投稿を生成")
                    print("3. --posts オプションで投稿内容を直接指定")
                    return
                continue
            
            # 最適な候補を選択（品質スコアが最も高いもの）
            if args.candidates > 1:
                best_candidate = max(candidates, key=lambda x: x['score'])
                print(f"  → 最適な候補を選択（品質スコア: {best_candidate['score']:.1f}%）")
                post = best_candidate['text']
                check_results = best_candidate['check_results']
            else:
                post = candidates[0]['text']
                check_results = candidates[0]['check_results']
            
            # 品質チェック結果を表示
            if args.check_quality and check_results:
                quality_score = check_results['score'] / check_results['max_score'] * 100 if check_results['max_score'] > 0 else 0
                
                if quality_score < 60:
                    print(f"  ⚠ 警告: 品質スコアが低いです ({quality_score:.1f}%)")
                    if check_results['warnings']:
                        print("  主な問題点:")
                        for warning in check_results['warnings'][:3]:
                            print(f"    - {warning['name']}: {warning['message']}")
                elif quality_score < 80:
                    print(f"  ⚠ 注意: 品質スコア {quality_score:.1f}%（改善の余地あり）")
                else:
                    print(f"  ✓ 品質スコア: {quality_score:.1f}%")
            
            # 重複チェック
            if args.check_duplicate:
                print("  重複をチェック中...")
                duplicate_result = duplicate_check_module.check_duplicate_for_account(post, account_file)
                if duplicate_result.get('is_duplicate'):
                    print(f"  ⚠ 警告: 過去の投稿と類似しています（類似度: {duplicate_result.get('similarity_score', 0)*100:.1f}%）")
                    if duplicate_result.get('similar_posts'):
                        print("  類似している投稿:")
                        for similar in duplicate_result['similar_posts'][:2]:
                            print(f"    - 類似度 {similar['similarity']*100:.1f}%: {similar['post'][:80]}...")
                else:
                    print("  ✓ 重複は検出されませんでした")
            
            posts.append(post)
            print(f"生成された投稿:")
            print("-" * 40)
            print(post[:200] + "..." if len(post) > 200 else post)
            print("-" * 40)
        
        if not posts:
            print("\nエラー: 投稿が生成されませんでした")
            return
    
    # スプレッドシートへの転記をスキップ
    if args.no_schedule:
        print(f"\n✓ {len(posts)}個の投稿を生成しました（スプレッドシートへの転記はスキップ）")
        print("\n生成された投稿:")
        print("="*60)
        for i, post in enumerate(posts, 1):
            print(f"\n[{i}/{len(posts)}]")
            print("-" * 40)
            print(post)
            print("-" * 40)
        return
    
    # スプレッドシートに転記
    print(f"\n{'='*60}")
    print("スプレッドシートに転記します...")
    print(f"{'='*60}\n")
    
    # 開始日をパース
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        except:
            print(f"警告: 開始日の形式が正しくありません: {args.start_date}")
    
    # スプレッドシートに転記
    success = schedule_posts_to_spreadsheet(
        account_file_path=str(account_file.relative_to(PARENT_DIR)),
        posts=posts,
        morning_hour=args.morning_hour,
        morning_minute=args.morning_minute,
        evening_hour=args.evening_hour,
        evening_minute=args.evening_minute,
        start_date=start_date,
        posts_per_day=args.posts_per_day
    )
    
    if success:
        print(f"\n✓ 完了しました！{len(posts)}個の投稿をスプレッドシートに転記しました。")
    else:
        print(f"\n✗ 一部の投稿の転記に失敗しました。")

if __name__ == '__main__':
    main()
