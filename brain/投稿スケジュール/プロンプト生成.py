#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アカウント設計ファイルからThreads投稿作成プロンプトを自動生成するスクリプト
"""

import os
import re
import sys
from pathlib import Path

# 親ディレクトリのパスを取得
SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent

def extract_account_info(file_path, include_performance_analysis=True):
    """アカウント設計ファイルから情報を抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    info = {}
    info['file_path'] = file_path  # ファイルパスを保存（パフォーマンス分析用）
    
    # アカウント名
    match = re.search(r'\*\*アカウント名:\*\*\s*(.+)', content)
    info['account_name'] = match.group(1).strip() if match else ''
    
    # ジャンル
    match = re.search(r'\*\*ジャンル:\*\*\s*(.+)', content)
    info['genre'] = match.group(1).strip() if match else ''
    
    # キーワード
    match = re.search(r'\*\*キーワード:\*\*\s*(.+)', content, re.DOTALL)
    if match:
        keywords = match.group(1).strip()
        info['keywords'] = keywords.replace('\n', ' / ')
    else:
        info['keywords'] = ''
    
    # 自己紹介文
    match = re.search(r'\*\*自己紹介文:\*\*\s*(.+)', content, re.DOTALL)
    info['bio'] = match.group(1).strip() if match else ''
    
    # ペルソナ設定
    persona_section = re.search(r'## ペルソナ設定.*?##', content, re.DOTALL)
    if persona_section:
        # 年齢層
        match = re.search(r'\*\*年齢層:\*\*\s*(.+)', persona_section.group(0))
        info['age_range'] = match.group(1).strip() if match else ''
        
        # 性別
        match = re.search(r'\*\*性別:\*\*\s*(.+)', persona_section.group(0))
        info['gender'] = match.group(1).strip() if match else ''
        
        # 特徴
        match = re.search(r'\*\*特徴:\*\*\s*(.+?)(?=\*\*|$)', persona_section.group(0), re.DOTALL)
        if match:
            features = match.group(1).strip()
            info['features'] = [line.strip() for line in features.split('\n') if line.strip() and line.strip().startswith('-')]
        else:
            info['features'] = []
    else:
        info['age_range'] = ''
        info['gender'] = ''
        info['features'] = []
    
    # ターゲットオーディエンス
    target_section = re.search(r'## ターゲットオーディエンス設定.*?##', content, re.DOTALL)
    if target_section:
        # 年齢層
        match = re.search(r'\*\*年齢層:\*\*\s*(.+)', target_section.group(0))
        info['target_age'] = match.group(1).strip() if match else ''
        
        # ライフスタイル
        match = re.search(r'\*\*ライフスタイル:\*\*\s*(.+?)(?=\*\*|$)', target_section.group(0), re.DOTALL)
        if match:
            lifestyle = match.group(1).strip()
            info['lifestyle'] = [line.strip() for line in lifestyle.split('\n') if line.strip() and line.strip().startswith('-')]
        else:
            info['lifestyle'] = []
        
        # ニーズ
        match = re.search(r'\*\*ニーズ:\*\*\s*(.+?)(?=\*\*|$)', target_section.group(0), re.DOTALL)
        if match:
            needs = match.group(1).strip()
            info['needs'] = [line.strip() for line in needs.split('\n') if line.strip() and line.strip().startswith('-')]
        else:
            info['needs'] = []
    else:
        info['target_age'] = ''
        info['lifestyle'] = []
        info['needs'] = []
    
    # コンテンツの柱
    pillars_section = re.search(r'## コンテンツの柱.*?##', content, re.DOTALL)
    if pillars_section:
        info['content_pillars'] = pillars_section.group(0).strip()
    else:
        info['content_pillars'] = ''
    
    # トーン&マナー
    tone_section = re.search(r'### トーン&マナー.*?##', content, re.DOTALL)
    if tone_section:
        info['tone_manner'] = tone_section.group(0).strip()
    else:
        info['tone_manner'] = ''
    
    # 世界観
    worldview_section = re.search(r'### 世界観.*?##', content, re.DOTALL)
    if worldview_section:
        info['worldview'] = worldview_section.group(0).strip()
    else:
        info['worldview'] = ''
    
    # 理念
    philosophy_section = re.search(r'### 理念.*?##', content, re.DOTALL)
    if philosophy_section:
        info['philosophy'] = philosophy_section.group(0).strip()
    else:
        info['philosophy'] = ''
    
    # 投稿テンプレート
    template_section = re.search(r'## 投稿テンプレート.*?##', content, re.DOTALL)
    if template_section:
        info['templates'] = template_section.group(0).strip()
    else:
        info['templates'] = ''
    
    # チェックリスト
    checklist_section = re.search(r'### 投稿作成時のチェックリスト.*?##', content, re.DOTALL)
    if checklist_section:
        info['checklist'] = checklist_section.group(0).strip()
    else:
        info['checklist'] = ''
    
    # 過去の投稿例（パフォーマンス情報付き）
    posts_section = re.search(r'## 過去投稿記録.*?(?=##|$)', content, re.DOTALL)
    post_examples = []
    post_examples_with_performance = []
    if posts_section:
        # 投稿ごとに抽出
        post_blocks = re.findall(r'### 投稿 \d+.*?(?=### 投稿|$)', posts_section.group(0), re.DOTALL)
        for post_block in post_blocks:
            # 投稿本文を抽出
            post_match = re.search(r'\*\*投稿本文:\*\*\s*(.+?)(?=\*\*パフォーマンス|\*\*URL|$)', post_block, re.DOTALL)
            if post_match:
                post_text = post_match.group(1).strip()
                if post_text and len(post_text) > 20:
                    # パフォーマンス情報を抽出
                    likes_match = re.search(r'いいね数:\s*(\d+)', post_block)
                    replies_match = re.search(r'返信数:\s*(\d+)', post_block)
                    views_match = re.search(r'表示数:\s*(\d+)', post_block)
                    
                    likes = int(likes_match.group(1)) if likes_match else 0
                    replies = int(replies_match.group(1)) if replies_match else 0
                    views = int(views_match.group(1)) if views_match else 0
                    
                    # エンゲージメント率を計算（いいね数 + 返信数 * 2）/ 表示数
                    engagement = 0
                    if views > 0:
                        engagement = (likes + replies * 2) / views
                    
                    post_examples.append(post_text)
                    post_examples_with_performance.append({
                        'text': post_text,
                        'likes': likes,
                        'replies': replies,
                        'views': views,
                        'engagement': engagement
                    })
    
    # エンゲージメント率でソート（高い順）
    post_examples_with_performance.sort(key=lambda x: x['engagement'], reverse=True)
    
    # 上位5個を選択（エンゲージメントが高い投稿を優先）
    info['post_examples'] = [p['text'] for p in post_examples_with_performance[:5]]
    if len(info['post_examples']) < 5 and post_examples:
        # エンゲージメント情報がない投稿も追加
        for post in post_examples:
            if post not in info['post_examples']:
                info['post_examples'].append(post)
                if len(info['post_examples']) >= 5:
                    break
    
    return info

def generate_prompt(account_info, theme=None, post_type=None, emoji_policy="最小限", include_performance_analysis=True):
    """プロンプトを生成"""
    
    # パフォーマンス分析を追加（オプション）
    performance_insights = ""
    if include_performance_analysis:
        try:
            # パフォーマンス分析モジュールをインポート
            import importlib.util
            perf_module_file = SCRIPT_DIR / "パフォーマンス分析.py"
            if perf_module_file.exists():
                spec_perf = importlib.util.spec_from_file_location("パフォーマンス分析", perf_module_file)
                perf_module = importlib.util.module_from_spec(spec_perf)
                spec_perf.loader.exec_module(perf_module)
                
                # アカウントファイルのパスを取得（account_infoから推測）
                # 実際のファイルパスが必要な場合は、extract_account_infoに渡す必要がある
                # ここでは簡易的にスキップ
        except:
            pass  # パフォーマンス分析が失敗しても続行
    
    # パフォーマンス分析を追加
    performance_insights = ""
    if include_performance_analysis and 'file_path' in account_info:
        try:
            import importlib.util
            perf_module_file = SCRIPT_DIR / "パフォーマンス分析.py"
            if perf_module_file.exists():
                spec_perf = importlib.util.spec_from_file_location("パフォーマンス分析", perf_module_file)
                perf_module = importlib.util.module_from_spec(spec_perf)
                spec_perf.loader.exec_module(perf_module)
                
                # パフォーマンス分析を実行
                analysis_result = perf_module.analyze_account(account_info['file_path'])
                if analysis_result.get('has_data'):
                    performance_insights = perf_module.generate_insights_prompt(analysis_result['analysis'], account_info)
        except Exception as e:
            # エラーが発生しても続行
            pass
    
    prompt = f"""あなたはThreads投稿の専門家です。以下のアカウント設計に基づいて、Threads用の投稿を作成してください.

## アカウント情報

**アカウント名:** {account_info['account_name']}
**ジャンル:** {account_info['genre']}
**キーワード:** {account_info['keywords']}
**自己紹介文:** {account_info['bio']}

## ペルソナ設定

**年齢層:** {account_info['age_range']}
**性別:** {account_info['gender']}
**特徴:**
"""
    
    for feature in account_info['features']:
        prompt += f"{feature}\n"
    
    prompt += f"""
## ターゲットオーディエンス

**年齢層:** {account_info['target_age']}
**ライフスタイル:**
"""
    
    for item in account_info['lifestyle']:
        prompt += f"{item}\n"
    
    prompt += "**ニーズ:**\n"
    for need in account_info['needs']:
        prompt += f"{need}\n"
    
    prompt += f"""
## コンテンツの柱（投稿ジャンル）

{account_info['content_pillars'][:1000] if len(account_info['content_pillars']) > 1000 else account_info['content_pillars']}

## トーン&マナー（話し方・文体）

{account_info['tone_manner'][:1500] if len(account_info['tone_manner']) > 1500 else account_info['tone_manner']}

"""
    
    # 世界観を追加
    if account_info.get('worldview'):
        prompt += f"""## 世界観（価値観・視点）

{account_info['worldview'][:1000] if len(account_info['worldview']) > 1000 else account_info['worldview']}

"""
    
    # 理念を追加
    if account_info.get('philosophy'):
        prompt += f"""## 理念（何を伝えたいか・核心的なメッセージ）

{account_info['philosophy'][:1000] if len(account_info['philosophy']) > 1000 else account_info['philosophy']}

"""
    
    # 投稿テンプレートを追加
    if account_info.get('templates'):
        prompt += f"""## 投稿テンプレート（参考）

{account_info['templates'][:1500] if len(account_info['templates']) > 1500 else account_info['templates']}

"""
    
    prompt += """## Threads投稿作成の要件

### 基本構造（3つの要素）

1. **フック（最初の一文）**
   - 目を引くワードを入れて、「え？」と思わせる
   - 共感を呼ぶ一言または問いかけ
   - 具体的な数字、状況、会話を入れる

2. **本題（ストーリー）**
   - 具体的なエピソードや状況を入れて、共感を引き出す
   - 体験談、あるある、失敗談など
   - 改行を活用して読みやすく

3. **問いかけ＆行動喚起で締める**
   - 読者がコメントしたくなる余白を作る
   - 「これって私だけ？」「みんなはどう？」などの問いかけ
   - CTA（行動喚起）を含める

### 重要なポイント

- **コメント数を増やすことが最優先**（いいね数より重要）
- **潜在率を高める**（長く読まれる構成にする）
- **会話が続く投稿**を作る（Threadsのアルゴリズムに最適化）
- **口語調**で親しみやすく
- **改行を効果的に使用**（4〜5行以上になる場合は改行しない）
- **文字形態のバランス**（漢字・ひらがな・カタカナ・絵文字・記号）
- **具体的なエピソード**（数字、場所、会話）を含める
- **ターゲットに届く単語**を入れる

### 投稿の長さ

- 短文: 1〜3行（断言型、問いかけ型）
- 中文: 3〜6行（エピソード型、論理展開型）
- 長文: 6行以上（詳細な体験談、ストーリー型）

### 絵文字の使用

{emoji_policy}

{performance_insights}

## 過去の投稿例（参考・成功パターン）

**重要**: 以下の投稿例は、エンゲージメント率（いいね数・返信数）が高い成功パターンです。スタイルや構成を参考にしつつ、**必ず新しい内容**を生成してください。

"""
    
    for i, example in enumerate(account_info['post_examples'], 1):
        # 投稿例を全文表示（切り詰めない）
        prompt += f"**投稿例 {i}:**\n{example}\n\n"
    
    # チェックリストを追加
    if account_info.get('checklist'):
        prompt += f"""## 投稿作成時のチェックリスト

以下のチェックリストを必ず確認してから投稿を生成してください：

{account_info['checklist'][:1500] if len(account_info['checklist']) > 1500 else account_info['checklist']}

"""
    
    prompt += """## 作成する投稿の要件

"""
    
    if theme:
        prompt += f"- テーマ: {theme}\n"
    if post_type:
        prompt += f"- 投稿タイプ: {post_type}\n"
    
    prompt += f"""- 絵文字: {emoji_policy}
- 文字数: 200-400文字程度（目安）

## 出力形式

実際にThreadsに投稿する内容のみを出力してください。
- 分析や説明は不要
- マークダウン形式は使わず、プレーンテキストで
- 改行は実際の投稿と同じように

## 重要な注意事項

1. **必ず新しい内容を生成**: 過去の投稿をそのままコピーするのではなく、必ず新しい視点や表現で投稿を作成してください
2. **アカウント設計に忠実に**: トーン&マナー、世界観、理念を必ず反映してください
3. **チェックリストを確認**: 生成した投稿がチェックリストの要件を満たしているか確認してください
4. **投稿内容のみを出力**: アカウント設計の分析部分や説明は含めず、実際の投稿内容のみを生成してください
5. **成功パターンを参考に**: 過去の投稿例の成功パターン（エンゲージメント率が高い投稿）のスタイルや構成を参考にしてください

## 生成プロセス

1. アカウント設計を理解する（ペルソナ、トーン&マナー、世界観、理念）
2. 過去の成功パターンを分析する（エンゲージメント率が高い投稿の特徴）
3. チェックリストを確認しながら投稿を生成する
4. 生成した投稿がアカウント設計に合っているか最終確認する
"""
    
    return prompt

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='アカウント設計ファイルからThreads投稿作成プロンプトを生成')
    parser.add_argument('account_file', help='アカウント設計ファイルのパス（親ディレクトリからの相対パス）')
    parser.add_argument('--theme', help='投稿のテーマ（オプション）')
    parser.add_argument('--post-type', choices=['短文', '中文', '長文'], help='投稿タイプ（オプション）')
    parser.add_argument('--emoji', choices=['使用する', '最小限', '使用しない'], default='最小限', help='絵文字の使用方針')
    parser.add_argument('--output', help='出力ファイル（オプション、指定しない場合は標準出力）')
    
    args = parser.parse_args()
    
    # ファイルパスを解決
    if not os.path.isabs(args.account_file):
        account_file = PARENT_DIR / args.account_file
    else:
        account_file = Path(args.account_file)
    
    if not account_file.exists():
        print(f"エラー: ファイルが見つかりません: {account_file}")
        return
    
    # アカウント情報を抽出
    print(f"アカウント設計ファイルを読み込んでいます: {account_file}")
    account_info = extract_account_info(account_file)
    
    # プロンプトを生成
    prompt = generate_prompt(
        account_info,
        theme=args.theme,
        post_type=args.post_type,
        emoji_policy=args.emoji
    )
    
    # 出力
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"\nプロンプトを保存しました: {output_file}")
    else:
        print("\n" + "="*60)
        print("生成されたプロンプト:")
        print("="*60 + "\n")
        print(prompt)

if __name__ == '__main__':
    import os
    main()
