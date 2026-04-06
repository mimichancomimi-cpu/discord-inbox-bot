#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成された投稿が過去の投稿と重複していないかチェックするスクリプト
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path
from difflib import SequenceMatcher

def extract_past_posts(file_path: Path) -> List[str]:
    """過去の投稿を抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    posts = []
    posts_section = re.search(r'## 過去投稿記録.*?(?=##|$)', content, re.DOTALL)
    
    if not posts_section:
        return posts
    
    # 投稿本文を抽出
    post_matches = re.findall(r'\*\*投稿本文:\*\*\s*(.+?)(?=\*\*パフォーマンス|\*\*URL|### 投稿|$)', posts_section.group(0), re.DOTALL)
    for post in post_matches:
        post_text = post.strip()
        if post_text and len(post_text) > 20:
            posts.append(post_text)
    
    return posts

def calculate_similarity(text1: str, text2: str) -> float:
    """2つのテキストの類似度を計算（0.0-1.0）"""
    # 空白と改行を正規化
    text1_normalized = re.sub(r'\s+', ' ', text1.strip())
    text2_normalized = re.sub(r'\s+', ' ', text2.strip())
    
    # SequenceMatcherで類似度を計算
    similarity = SequenceMatcher(None, text1_normalized, text2_normalized).ratio()
    return similarity

def check_duplicate(new_post: str, past_posts: List[str], threshold: float = 0.7) -> Tuple[bool, List[Dict]]:
    """
    新しい投稿が過去の投稿と重複していないかチェック
    
    Args:
        new_post: チェックする新しい投稿
        past_posts: 過去の投稿リスト
        threshold: 類似度の閾値（デフォルト: 0.7）
    
    Returns:
        (重複があるか, 類似投稿のリスト)
    """
    similar_posts = []
    
    for past_post in past_posts:
        similarity = calculate_similarity(new_post, past_post)
        if similarity >= threshold:
            similar_posts.append({
                'post': past_post,
                'similarity': similarity
            })
    
    # 類似度でソート
    similar_posts.sort(key=lambda x: x['similarity'], reverse=True)
    
    is_duplicate = len(similar_posts) > 0
    return is_duplicate, similar_posts

def check_keyword_overlap(new_post: str, past_posts: List[str], min_words: int = 10) -> Tuple[bool, List[str]]:
    """
    キーワードの重複をチェック（同じ単語が多く含まれているか）
    
    Args:
        new_post: チェックする新しい投稿
        past_posts: 過去の投稿リスト
        min_words: 重複とみなす最小単語数
    
    Returns:
        (重複があるか, 重複している単語のリスト)
    """
    # 単語を抽出（日本語と英語）
    def extract_words(text):
        # 日本語の単語と英語の単語を抽出
        words = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+|[a-zA-Z]+', text)
        return set(words)
    
    new_words = extract_words(new_post)
    overlapping_words = []
    
    for past_post in past_posts:
        past_words = extract_words(past_post)
        overlap = new_words & past_words
        if len(overlap) >= min_words:
            overlapping_words.extend(list(overlap))
    
    is_overlapping = len(overlapping_words) >= min_words
    return is_overlapping, list(set(overlapping_words))

def check_duplicate_for_account(new_post: str, account_file: Path, threshold: float = 0.7) -> Dict:
    """
    アカウントの過去投稿と重複チェック
    
    Returns:
        チェック結果の辞書
    """
    past_posts = extract_past_posts(account_file)
    
    if not past_posts:
        return {
            'is_duplicate': False,
            'similar_posts': [],
            'overlapping_words': [],
            'has_past_posts': False
        }
    
    # 類似度チェック
    is_duplicate, similar_posts = check_duplicate(new_post, past_posts, threshold)
    
    # キーワード重複チェック
    is_overlapping, overlapping_words = check_keyword_overlap(new_post, past_posts)
    
    return {
        'is_duplicate': is_duplicate or is_overlapping,
        'similar_posts': similar_posts[:3],  # 上位3件のみ
        'overlapping_words': overlapping_words[:10],  # 上位10件のみ
        'has_past_posts': True,
        'similarity_score': similar_posts[0]['similarity'] if similar_posts else 0
    }

def format_duplicate_check_result(result: Dict) -> str:
    """重複チェック結果をフォーマット"""
    output = []
    output.append("=" * 60)
    output.append("重複チェック結果")
    output.append("=" * 60)
    
    if not result.get('has_past_posts'):
        output.append("\n過去投稿データがありません。")
        output.append("=" * 60)
        return "\n".join(output)
    
    if result['is_duplicate']:
        output.append("\n⚠ 警告: 過去の投稿と類似している可能性があります")
        
        if result.get('similar_posts'):
            output.append(f"\n類似度: {result['similarity_score']*100:.1f}%")
            output.append("\n類似している投稿:")
            for i, similar in enumerate(result['similar_posts'], 1):
                output.append(f"\n{i}. 類似度: {similar['similarity']*100:.1f}%")
                output.append(f"   {similar['post'][:150]}...")
        
        if result.get('overlapping_words'):
            output.append(f"\n重複しているキーワード: {', '.join(result['overlapping_words'][:5])}")
    else:
        output.append("\n✓ 重複は検出されませんでした")
    
    output.append("\n" + "=" * 60)
    return "\n".join(output)

if __name__ == '__main__':
    # テスト用
    import sys
    from pathlib import Path
    
    SCRIPT_DIR = Path(__file__).parent
    PARENT_DIR = SCRIPT_DIR.parent
    
    # テスト用のアカウントファイル
    test_account = PARENT_DIR / "５０アカウント運用" / "1.ぽんこつ母ちゃん.md"
    if test_account.exists():
        # テスト用の投稿（過去の投稿と類似）
        test_post = "あの、私ドがつくほどの機械音痴なんですが、最近めちゃくちゃやらかして凹んでるので、よかったらみなさんの機械音痴エピソードを教えてください😂"
        
        result = check_duplicate_for_account(test_post, test_account)
        print(format_duplicate_check_result(result))
