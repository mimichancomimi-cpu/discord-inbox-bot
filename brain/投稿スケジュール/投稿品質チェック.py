#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成された投稿の品質をチェックするスクリプト
アカウント設計に合っているかを自動判定
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path

def check_post_quality(post: str, account_info: Dict) -> Dict:
    """
    投稿の品質をチェック
    
    Args:
        post: チェックする投稿
        account_info: アカウント情報（プロンプト生成モジュールから取得）
    
    Returns:
        チェック結果の辞書
    """
    results = {
        'score': 0,
        'max_score': 0,
        'checks': [],
        'warnings': [],
        'errors': []
    }
    
    # 1. トーン&マナーのチェック
    tone_checks = _check_tone_manner(post, account_info)
    results['checks'].extend(tone_checks)
    
    # 2. キーワードの含有チェック
    keyword_checks = _check_keywords(post, account_info)
    results['checks'].extend(keyword_checks)
    
    # 3. 投稿構造のチェック
    structure_checks = _check_structure(post)
    results['checks'].extend(structure_checks)
    
    # 4. 文字数のチェック
    length_checks = _check_length(post)
    results['checks'].extend(length_checks)
    
    # 5. 絵文字のチェック
    emoji_checks = _check_emoji(post, account_info)
    results['checks'].extend(emoji_checks)
    
    # スコアを計算
    for check in results['checks']:
        results['max_score'] += check.get('weight', 1)
        if check.get('passed', False):
            results['score'] += check.get('weight', 1)
    
    # 警告とエラーを分類
    for check in results['checks']:
        if not check.get('passed', False):
            if check.get('severity') == 'error':
                results['errors'].append(check)
            elif check.get('severity') == 'warning':
                results['warnings'].append(check)
    
    return results

def _check_tone_manner(post: str, account_info: Dict) -> List[Dict]:
    """トーン&マナーのチェック"""
    checks = []
    tone_manner = account_info.get('tone_manner', '')
    
    # 謙虚な語り口のチェック（例）
    if '謙虚' in tone_manner or '控えめ' in tone_manner:
        humble_patterns = ['あの、', 'よかったら', '〜なんですが', '〜かもしれません']
        has_humble = any(pattern in post for pattern in humble_patterns)
        checks.append({
            'name': '謙虚な語り口',
            'passed': has_humble,
            'weight': 2,
            'severity': 'warning',
            'message': '謙虚で控えめな語り口が含まれているか' if has_humble else '謙虚で控えめな語り口が不足しています'
        })
    
    # 口語調のチェック
    casual_patterns = ['〜だよ', '〜じゃん', '〜だよね', '〜なの', '〜です', '〜ます']
    has_casual = any(pattern in post for pattern in casual_patterns)
    checks.append({
        'name': '口語調',
        'passed': has_casual,
        'weight': 2,
        'severity': 'warning',
        'message': '口語調が使用されているか' if has_casual else '口語調が不足しています'
    })
    
    return checks

def _check_keywords(post: str, account_info: Dict) -> List[Dict]:
    """キーワードの含有チェック"""
    checks = []
    keywords_str = account_info.get('keywords', '')
    
    if keywords_str:
        # キーワードを抽出（/区切り）
        keywords = [kw.strip() for kw in keywords_str.split('/') if kw.strip()]
        
        # 投稿に含まれるキーワードをカウント
        found_keywords = []
        for keyword in keywords:
            if keyword in post:
                found_keywords.append(keyword)
        
        # キーワードの含有率
        keyword_ratio = len(found_keywords) / len(keywords) if keywords else 0
        
        checks.append({
            'name': 'キーワード含有',
            'passed': keyword_ratio >= 0.2,  # 20%以上のキーワードが含まれている
            'weight': 3,
            'severity': 'warning',
            'message': f'キーワード含有率: {len(found_keywords)}/{len(keywords)} ({keyword_ratio*100:.1f}%)',
            'found_keywords': found_keywords
        })
    
    return checks

def _check_structure(post: str) -> List[Dict]:
    """投稿構造のチェック"""
    checks = []
    
    # 改行のチェック
    lines = post.split('\n')
    line_count = len([line for line in lines if line.strip()])
    
    # 問いかけのチェック
    question_patterns = ['？', '?', 'ですか', 'ですか？', 'どう', 'どう？', 'いる？', 'いる', 'ある？', 'ある']
    has_question = any(pattern in post for pattern in question_patterns)
    
    checks.append({
        'name': '問いかけの有無',
        'passed': has_question,
        'weight': 3,
        'severity': 'warning',
        'message': '問いかけが含まれているか（コメント数を増やすため）' if has_question else '問いかけが不足しています（コメント数を増やすために推奨）'
    })
    
    # CTA（行動喚起）のチェック
    cta_patterns = ['フォロー', 'いいね', 'コメント', '教えて', '一緒に', '試して']
    has_cta = any(pattern in post for pattern in cta_patterns)
    
    checks.append({
        'name': 'CTA（行動喚起）',
        'passed': has_cta,
        'weight': 2,
        'severity': 'warning',
        'message': 'CTA（行動喚起）が含まれているか' if has_cta else 'CTA（行動喚起）が不足しています'
    })
    
    return checks

def _check_length(post: str) -> List[Dict]:
    """文字数のチェック"""
    checks = []
    char_count = len(post)
    
    # 適切な文字数範囲（200-400文字程度を推奨）
    is_appropriate = 100 <= char_count <= 600
    
    checks.append({
        'name': '文字数',
        'passed': is_appropriate,
        'weight': 1,
        'severity': 'warning' if char_count < 100 or char_count > 600 else 'info',
        'message': f'文字数: {char_count}文字（推奨: 200-400文字）'
    })
    
    return checks

def _check_emoji(post: str, account_info: Dict) -> List[Dict]:
    """絵文字のチェック"""
    checks = []
    
    # 絵文字をカウント
    emoji_pattern = re.compile(
        r'[\U0001F300-\U0001F9FF]|'  # 絵文字
        r'[\U0001F600-\U0001F64F]|'  # 顔文字
        r'[\U0001F680-\U0001F6FF]|'  # 交通・地図
        r'[\U00002600-\U000026FF]|'  # その他記号
        r'[\U00002700-\U000027BF]'   # 装飾記号
    )
    emoji_count = len(emoji_pattern.findall(post))
    char_count = len(post)
    emoji_ratio = emoji_count / char_count if char_count > 0 else 0
    
    # 絵文字の使用方針を確認（アカウント設計から）
    tone_manner = account_info.get('tone_manner', '')
    emoji_policy = '最小限'
    if '絵文字' in tone_manner:
        if '使用しない' in tone_manner:
            emoji_policy = '使用しない'
        elif '使用する' in tone_manner:
            emoji_policy = '使用する'
    
    # 絵文字の使用が適切かチェック
    if emoji_policy == '使用しない':
        is_appropriate = emoji_count == 0
    elif emoji_policy == '最小限':
        is_appropriate = emoji_count <= 5
    else:  # 使用する
        is_appropriate = emoji_count >= 1
    
    checks.append({
        'name': '絵文字の使用',
        'passed': is_appropriate,
        'weight': 1,
        'severity': 'warning',
        'message': f'絵文字数: {emoji_count}個（方針: {emoji_policy}）'
    })
    
    return checks

def format_check_results(results: Dict) -> str:
    """チェック結果をフォーマット"""
    output = []
    output.append("=" * 60)
    output.append("投稿品質チェック結果")
    output.append("=" * 60)
    output.append(f"\nスコア: {results['score']}/{results['max_score']} ({results['score']/results['max_score']*100:.1f}%)")
    
    if results['errors']:
        output.append("\n【エラー】")
        for error in results['errors']:
            output.append(f"  ✗ {error['name']}: {error['message']}")
    
    if results['warnings']:
        output.append("\n【警告】")
        for warning in results['warnings']:
            output.append(f"  ⚠ {warning['name']}: {warning['message']}")
    
    if results['checks']:
        passed = [c for c in results['checks'] if c.get('passed', False)]
        output.append(f"\n【チェック項目】")
        output.append(f"  合格: {len(passed)}/{len(results['checks'])}")
        for check in results['checks']:
            status = "✓" if check.get('passed', False) else "✗"
            output.append(f"  {status} {check['name']}: {check['message']}")
    
    output.append("\n" + "=" * 60)
    return "\n".join(output)

if __name__ == '__main__':
    # テスト用
    import sys
    from pathlib import Path
    
    SCRIPT_DIR = Path(__file__).parent
    PARENT_DIR = SCRIPT_DIR.parent
    sys.path.insert(0, str(SCRIPT_DIR))
    
    # プロンプト生成モジュールをインポート
    import importlib.util
    prompt_module_file = SCRIPT_DIR / "プロンプト生成.py"
    spec = importlib.util.spec_from_file_location("プロンプト生成", prompt_module_file)
    prompt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prompt_module)
    
    # テスト用のアカウント情報を取得
    test_account = PARENT_DIR / "５０アカウント運用" / "1.ぽんこつ母ちゃん.md"
    if test_account.exists():
        account_info = prompt_module.extract_account_info(test_account)
        
        # テスト用の投稿
        test_post = """あの、私ドがつくほどの機械音痴なんですが、最近めちゃくちゃやらかして凹んでるので、よかったらみなさんの機械音痴エピソードを教えてください😂"""
        
        results = check_post_quality(test_post, account_info)
        print(format_check_results(results))
