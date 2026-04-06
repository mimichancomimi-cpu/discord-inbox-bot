#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
過去投稿のパフォーマンスを分析して、成功パターンを抽出するスクリプト
"""

import os
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import json

def extract_performance_data(file_path: Path) -> List[Dict]:
    """
    アカウント設計ファイルから過去投稿のパフォーマンスデータを抽出
    
    Returns:
        投稿データのリスト（各投稿にパフォーマンス情報を含む）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    posts = []
    posts_section = re.search(r'## 過去投稿記録.*?(?=##|$)', content, re.DOTALL)
    
    if not posts_section:
        return posts
    
    # 投稿ごとに抽出
    post_blocks = re.findall(r'### 投稿 \d+.*?(?=### 投稿|$)', posts_section.group(0), re.DOTALL)
    
    for post_block in post_blocks:
        post_data = {}
        
        # 投稿本文を抽出
        post_match = re.search(r'\*\*投稿本文:\*\*\s*(.+?)(?=\*\*パフォーマンス|\*\*URL|$)', post_block, re.DOTALL)
        if post_match:
            post_data['text'] = post_match.group(1).strip()
        else:
            continue
        
        # パフォーマンス情報を抽出
        likes_match = re.search(r'いいね数:\s*(\d+)', post_block)
        replies_match = re.search(r'返信数:\s*(\d+)', post_block)
        views_match = re.search(r'表示数:\s*(\d+)', post_block)
        date_match = re.search(r'取得日時:\s*([^\n]+)', post_block)
        
        post_data['likes'] = int(likes_match.group(1)) if likes_match else 0
        post_data['replies'] = int(replies_match.group(1)) if replies_match else 0
        post_data['views'] = int(views_match.group(1)) if views_match else 0
        post_data['date'] = date_match.group(1).strip() if date_match else ''
        
        # エンゲージメント率を計算
        if post_data['views'] > 0:
            post_data['engagement_rate'] = (post_data['likes'] + post_data['replies'] * 2) / post_data['views']
        else:
            post_data['engagement_rate'] = 0
        
        # 投稿の特徴を分析
        post_data['length'] = len(post_data['text'])
        post_data['line_count'] = len([l for l in post_data['text'].split('\n') if l.strip()])
        post_data['has_question'] = '？' in post_data['text'] or '?' in post_data['text'] or 'ですか' in post_data['text']
        post_data['has_emoji'] = bool(re.search(r'[\U0001F300-\U0001F9FF]', post_data['text']))
        post_data['has_cta'] = any(word in post_data['text'] for word in ['フォロー', 'いいね', 'コメント', '教えて', '一緒に'])
        
        posts.append(post_data)
    
    return posts

def analyze_performance(posts: List[Dict]) -> Dict:
    """
    パフォーマンスデータを分析して成功パターンを抽出
    
    Returns:
        分析結果の辞書
    """
    if not posts:
        return {}
    
    # エンゲージメント率でソート
    sorted_posts = sorted(posts, key=lambda x: x['engagement_rate'], reverse=True)
    
    # 上位20%を成功投稿として定義
    top_count = max(1, len(sorted_posts) // 5)
    top_posts = sorted_posts[:top_count]
    bottom_posts = sorted_posts[-top_count:] if len(sorted_posts) > top_count * 2 else []
    
    analysis = {
        'total_posts': len(posts),
        'top_posts': top_posts,
        'bottom_posts': bottom_posts,
        'insights': {}
    }
    
    # 成功投稿の特徴を分析
    if top_posts:
        # 平均文字数
        avg_length_top = sum(p['length'] for p in top_posts) / len(top_posts)
        avg_length_bottom = sum(p['length'] for p in bottom_posts) / len(bottom_posts) if bottom_posts else 0
        
        # 問いかけの含有率
        question_rate_top = sum(1 for p in top_posts if p['has_question']) / len(top_posts)
        question_rate_bottom = sum(1 for p in bottom_posts if p['has_question']) / len(bottom_posts) if bottom_posts else 0
        
        # CTAの含有率
        cta_rate_top = sum(1 for p in top_posts if p['has_cta']) / len(top_posts)
        cta_rate_bottom = sum(1 for p in bottom_posts if p['has_cta']) / len(bottom_posts) if bottom_posts else 0
        
        # 絵文字の使用率
        emoji_rate_top = sum(1 for p in top_posts if p['has_emoji']) / len(top_posts)
        emoji_rate_bottom = sum(1 for p in bottom_posts if p['has_emoji']) / len(bottom_posts) if bottom_posts else 0
        
        analysis['insights'] = {
            'optimal_length': {
                'top_avg': avg_length_top,
                'bottom_avg': avg_length_bottom,
                'recommendation': f'成功投稿の平均文字数: {avg_length_top:.0f}文字（失敗投稿: {avg_length_bottom:.0f}文字）'
            },
            'question_usage': {
                'top_rate': question_rate_top,
                'bottom_rate': question_rate_bottom,
                'recommendation': f'成功投稿の問いかけ含有率: {question_rate_top*100:.1f}%（失敗投稿: {question_rate_bottom*100:.1f}%）'
            },
            'cta_usage': {
                'top_rate': cta_rate_top,
                'bottom_rate': cta_rate_bottom,
                'recommendation': f'成功投稿のCTA含有率: {cta_rate_top*100:.1f}%（失敗投稿: {cta_rate_bottom*100:.1f}%）'
            },
            'emoji_usage': {
                'top_rate': emoji_rate_top,
                'bottom_rate': emoji_rate_bottom,
                'recommendation': f'成功投稿の絵文字使用率: {emoji_rate_top*100:.1f}%（失敗投稿: {emoji_rate_bottom*100:.1f}%）'
            }
        }
    
    return analysis

def generate_insights_prompt(analysis: Dict, account_info: Dict) -> str:
    """
    分析結果からプロンプトに追加するインサイトを生成
    
    Returns:
        インサイト文字列
    """
    if not analysis or not analysis.get('insights'):
        return ""
    
    insights = analysis['insights']
    prompt = "\n## 過去投稿のパフォーマンス分析結果（重要）\n\n"
    prompt += "以下の分析結果は、実際の投稿パフォーマンスデータから抽出された成功パターンです。\n"
    prompt += "必ず参考にして投稿を作成してください。\n\n"
    
    # 最適な文字数
    if 'optimal_length' in insights:
        prompt += f"**最適な文字数:** {insights['optimal_length']['recommendation']}\n\n"
    
    # 問いかけの重要性
    if 'question_usage' in insights:
        if insights['question_usage']['top_rate'] > insights['question_usage']['bottom_rate']:
            prompt += f"**問いかけの重要性:** {insights['question_usage']['recommendation']}\n"
            prompt += "→ 問いかけを含めることでエンゲージメントが向上する傾向があります。\n\n"
    
    # CTAの重要性
    if 'cta_usage' in insights:
        if insights['cta_usage']['top_rate'] > insights['cta_usage']['bottom_rate']:
            prompt += f"**CTA（行動喚起）の重要性:** {insights['cta_usage']['recommendation']}\n"
            prompt += "→ CTAを含めることでエンゲージメントが向上する傾向があります。\n\n"
    
    # 絵文字の使用
    if 'emoji_usage' in insights:
        prompt += f"**絵文字の使用:** {insights['emoji_usage']['recommendation']}\n\n"
    
    # 成功投稿の例
    if analysis.get('top_posts'):
        prompt += "**成功投稿の特徴（参考）:**\n"
        for i, post in enumerate(analysis['top_posts'][:3], 1):
            prompt += f"{i}. エンゲージメント率: {post['engagement_rate']*100:.2f}%, "
            prompt += f"文字数: {post['length']}, "
            prompt += f"問いかけ: {'あり' if post['has_question'] else 'なし'}, "
            prompt += f"CTA: {'あり' if post['has_cta'] else 'なし'}\n"
            prompt += f"   投稿例: {post['text'][:100]}...\n\n"
    
    return prompt

def analyze_account(file_path: Path) -> Dict:
    """
    アカウントのパフォーマンスを分析
    
    Returns:
        分析結果
    """
    posts = extract_performance_data(file_path)
    if not posts:
        return {'posts': [], 'analysis': {}, 'has_data': False}
    
    analysis = analyze_performance(posts)
    return {
        'posts': posts,
        'analysis': analysis,
        'has_data': True,
        'total_posts': len(posts),
        'avg_engagement': sum(p['engagement_rate'] for p in posts) / len(posts) if posts else 0
    }

def format_analysis_report(analysis_result: Dict) -> str:
    """
    分析結果をフォーマットして表示
    
    Returns:
        フォーマットされたレポート文字列
    """
    if not analysis_result.get('has_data'):
        return "分析データがありません。過去投稿記録を確認してください。"
    
    output = []
    output.append("=" * 60)
    output.append("パフォーマンス分析レポート")
    output.append("=" * 60)
    output.append(f"\n総投稿数: {analysis_result['total_posts']}")
    output.append(f"平均エンゲージメント率: {analysis_result['avg_engagement']*100:.2f}%")
    
    analysis = analysis_result['analysis']
    if analysis.get('insights'):
        output.append("\n【成功パターンの分析】")
        insights = analysis['insights']
        
        for key, value in insights.items():
            if isinstance(value, dict) and 'recommendation' in value:
                output.append(f"\n{value['recommendation']}")
    
    if analysis.get('top_posts'):
        output.append("\n【成功投稿トップ3】")
        for i, post in enumerate(analysis['top_posts'][:3], 1):
            output.append(f"\n{i}. エンゲージメント率: {post['engagement_rate']*100:.2f}%")
            output.append(f"   いいね: {post['likes']}, 返信: {post['replies']}, 表示: {post['views']}")
            output.append(f"   文字数: {post['length']}")
            output.append(f"   投稿: {post['text'][:150]}...")
    
    output.append("\n" + "=" * 60)
    return "\n".join(output)

if __name__ == '__main__':
    import sys
    import argparse
    from pathlib import Path
    
    SCRIPT_DIR = Path(__file__).parent
    PARENT_DIR = SCRIPT_DIR.parent
    
    parser = argparse.ArgumentParser(description='過去投稿のパフォーマンスを分析')
    parser.add_argument('account_file', nargs='?', help='アカウント設計ファイルのパス（指定しない場合は全アカウントを分析）')
    parser.add_argument('--all', action='store_true', help='全アカウントを分析')
    
    args = parser.parse_args()
    
    if args.all:
        # 全アカウントを分析
        accounts_dir = PARENT_DIR / "５０アカウント運用"
        if accounts_dir.exists():
            account_files = sorted(accounts_dir.glob("*.md"))
            print(f"\n全{len(account_files)}アカウントのパフォーマンス分析を実行します...\n")
            for account_file in account_files:
                print(f"\n{'='*60}")
                print(f"アカウント: {account_file.name}")
                print(f"{'='*60}")
                result = analyze_account(account_file)
                print(format_analysis_report(result))
        else:
            print(f"エラー: アカウントディレクトリが見つかりません: {accounts_dir}")
    elif args.account_file:
        # 指定されたアカウントを分析
        if not os.path.isabs(args.account_file):
            account_file = PARENT_DIR / args.account_file
        else:
            account_file = Path(args.account_file)
        
        if account_file.exists():
            result = analyze_account(account_file)
            print(format_analysis_report(result))
        else:
            print(f"エラー: ファイルが見つかりません: {account_file}")
    else:
        # デフォルト: テスト用のアカウントファイル
        test_account = PARENT_DIR / "５０アカウント運用" / "1.ぽんこつ母ちゃん.md"
        if test_account.exists():
            result = analyze_account(test_account)
            print(format_analysis_report(result))
        else:
            parser.print_help()
