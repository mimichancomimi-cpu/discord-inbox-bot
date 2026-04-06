#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
13個のアカウント設計をもとに投稿を生成し、スプレッドシートに転記するスクリプト
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials
import openai


class AccountDesign:
    """アカウント設計を読み込むクラス"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = self._read_file()
        self.account_name = self._extract_account_name()
        self.genre = self._extract_genre()
        self.keywords = self._extract_keywords()
        self.intro = self._extract_intro()
        self.persona = self._extract_section("## ペルソナ設定")
        self.target_audience = self._extract_section("## ターゲットオーディエンス設定")
        self.content_pillars = self._extract_content_pillars()
        self.templates = self._extract_templates()
        self.cta = self._extract_section("## CTA（行動喚起）")
        self.tone = self._extract_section("## トンマナ・世界観・理念")
    
    def _read_file(self) -> str:
        """ファイルを読み込む"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_account_name(self) -> str:
        """アカウント名を抽出"""
        match = re.search(r'\*\*アカウント名:\*\*\s*(.+)', self.content)
        if match:
            return match.group(1).strip()
        # ファイル名から抽出を試みる
        filename = Path(self.file_path).stem
        match = re.search(r'^\d+\.(.+)', filename)
        if match:
            return match.group(1).strip()
        return filename
    
    def _extract_genre(self) -> str:
        """ジャンルを抽出"""
        match = re.search(r'\*\*ジャンル:\*\*\s*(.+)', self.content)
        return match.group(1).strip() if match else ""
    
    def _extract_keywords(self) -> List[str]:
        """キーワードを抽出"""
        match = re.search(r'\*\*キーワード:\*\*\s*(.+?)(?=\n\n|\*\*|$)', self.content, re.DOTALL)
        if match:
            keywords_str = match.group(1).strip()
            # スラッシュで分割（改行は無視）
            keywords = re.split(r'\s*/\s*', keywords_str)
            # 改行で分割された部分も処理
            all_keywords = []
            for kw in keywords:
                # 改行が含まれている場合は最初の行だけ
                kw_clean = kw.split('\n')[0].strip()
                if kw_clean:
                    all_keywords.append(kw_clean)
            return all_keywords
        return []
    
    def _extract_intro(self) -> str:
        """自己紹介文を抽出"""
        match = re.search(r'\*\*自己紹介文:\*\*\s*(.+)', self.content, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_section(self, section_title: str) -> str:
        """指定されたセクションを抽出"""
        pattern = rf'{re.escape(section_title)}\s*\n\n(.*?)(?=\n\n---|\n\n##|\Z)'
        match = re.search(pattern, self.content, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_content_pillars(self) -> List[Dict]:
        """コンテンツの柱を抽出"""
        pillars = []
        pattern = r'### (\d+)\.\s*(.+?)\n\n(.*?)(?=\n\n### |\n\n---|\Z)'
        matches = re.finditer(pattern, self.content, re.DOTALL)
        
        for match in matches:
            pillar_num = match.group(1)
            pillar_title = match.group(2).strip()
            pillar_content = match.group(3).strip()
            
            # 投稿例を抽出
            post_examples = re.findall(r'\*\*投稿例:\*\*\s*\n(.*?)(?=\n\n|$)', pillar_content, re.DOTALL)
            examples = []
            for ex in post_examples:
                examples.extend([e.strip() for e in ex.split('\n') if e.strip() and e.strip().startswith('-')])
            
            pillars.append({
                'number': pillar_num,
                'title': pillar_title,
                'content': pillar_content,
                'examples': examples
            })
        
        return pillars
    
    def _extract_templates(self) -> List[Dict]:
        """投稿テンプレートを抽出"""
        templates = []
        # テーマごとのテンプレートを抽出
        pattern = r'#### テーマ：(.+?)\n\n```\n(.*?)\n```'
        matches = re.finditer(pattern, self.content, re.DOTALL)
        
        for match in matches:
            theme = match.group(1).strip()
            template = match.group(2).strip()
            
            # 本文部分を抽出（「本文：」から「CTA」または終わりまで）
            body_match = re.search(r'本文：\s*\n(.*?)(?=\n\nCTA|\n```|$)', template, re.DOTALL)
            if not body_match:
                # 「本文：」の後のすべてを取得
                body_match = re.search(r'本文：\s*\n(.*)', template, re.DOTALL)
            
            body = body_match.group(1).strip() if body_match else ""
            
            # CTA部分を抽出（テンプレート内にCTAがある場合）
            cta_match = re.search(r'CTA.*?：(.*?)(?=\n```|$)', template, re.DOTALL)
            cta = cta_match.group(1).strip() if cta_match else ""
            
            # 本文に既にCTAが含まれている場合は、CTAを分離
            if not cta and body:
                # 本文の最後の行がCTAっぽい場合（「フォローして」などが含まれる）
                lines = body.split('\n')
                if len(lines) > 1:
                    last_line = lines[-1].strip()
                    if any(word in last_line for word in ['フォロー', 'いいね', 'コメント', '待ってて']):
                        body = '\n'.join(lines[:-1]).strip()
                        cta = last_line
            
            templates.append({
                'theme': theme,
                'template': template,
                'body': body,
                'cta': cta
            })
        
        return templates
    
    def to_prompt_context(self) -> str:
        """投稿生成用のプロンプトコンテキストを生成"""
        context = f"""# アカウント設計: {self.account_name}

## 基本情報
- ジャンル: {self.genre}
- キーワード: {', '.join(self.keywords)}
- 自己紹介文: {self.intro}

## ペルソナ設定
{self.persona[:800]}

## ターゲットオーディエンス
{self.target_audience[:800]}

## コンテンツの柱
"""
        for pillar in self.content_pillars:
            context += f"\n### {pillar['title']}\n"
            context += f"{pillar['content'][:400]}\n"
            if pillar['examples']:
                # 投稿例を整形
                examples_text = '\n'.join([ex.replace('- ', '').replace('「', '').replace('」', '') for ex in pillar['examples'][:3]])
                context += f"\n投稿例:\n{examples_text}\n"
        
        context += f"\n## トンマナ・世界観\n{self.tone[:1000]}\n"
        
        if self.templates:
            context += "\n## 投稿テンプレート例（参考にしてください）\n"
            for template in self.templates[:3]:  # 最初の3つ
                context += f"\n### テーマ: {template['theme']}\n"
                if template.get('body'):
                    context += f"本文例:\n{template['body'][:300]}\n"
                if template.get('cta'):
                    context += f"CTA例: {template['cta'][:100]}\n"
        
        # CTAセクションも追加
        if self.cta:
            context += f"\n## CTA（行動喚起）の例\n{self.cta[:500]}\n"
        
        return context


def load_all_account_designs(accounts_dir: str) -> List[AccountDesign]:
    """すべてのアカウント設計を読み込む"""
    accounts = []
    accounts_path = Path(accounts_dir)
    
    # 1から13までのアカウント設計ファイルを読み込む
    for i in range(1, 14):
        # ファイル名のパターンを試す
        patterns = [
            f"{i}.*.md",
            f"{i:02d}.*.md"
        ]
        
        found = False
        for pattern in patterns:
            files = list(accounts_path.glob(pattern))
            if files:
                account = AccountDesign(str(files[0]))
                accounts.append(account)
                found = True
                break
        
        if not found:
            print(f"⚠ 警告: {i}番目のアカウント設計ファイルが見つかりません")
    
    return accounts


def generate_posts_with_ai(account: AccountDesign, num_posts: int = 5, api_key: str = "") -> List[str]:
    """AIを使って投稿を生成"""
    if not api_key:
        print(f"⚠ OpenAI APIキーが設定されていません。サンプル投稿を生成します。")
        return generate_sample_posts(account, num_posts)
    
    openai.api_key = api_key
    
    context = account.to_prompt_context()
    
    # コンテンツの柱からテーマを選ぶ
    themes = [pillar['title'] for pillar in account.content_pillars]
    
    prompt = f"""{context}

上記のアカウント設計に基づいて、{num_posts}つの投稿を作成してください。

【重要な指示】
1. 各投稿は、アカウントのペルソナ設定、トンマナ、文体の特徴を完全に再現すること
2. コンテンツの柱のテーマを参考にしつつ、バリエーションを持たせること
3. 投稿テンプレート例の文体や構成を参考にすること
4. 自然で共感を呼ぶ内容にすること
5. 絵文字を適切に使用すること（過度に使わない）
6. CTA（行動喚起）を含むこと
7. 280文字以内（X/Twitter形式）であること
8. 【】で囲まれたタイトルは不要。本文のみで作成すること
9. 各投稿は異なるテーマやアプローチにすること

【出力形式】
各投稿は以下の形式で出力してください（番号と投稿内容のみ）:

POST 1:
[投稿本文のみ。改行は適切に使用。CTAも含める]

POST 2:
[投稿本文のみ]

...

必ず{num_posts}つの投稿を作成してください。
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはSNSマーケティングの専門家です。アカウント設計に基づいて、自然で共感を呼ぶ投稿を作成します。指定されたトンマナと文体を完全に再現してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,  # より多様な投稿を生成
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        posts = extract_posts_from_response(content)
        
        # 足りない場合は追加生成
        if len(posts) < num_posts:
            print(f"  ⚠ {len(posts)}件しか生成されませんでした。サンプル投稿で補完します。")
            additional = generate_sample_posts(account, num_posts - len(posts))
            posts.extend(additional)
        
        return posts[:num_posts]
    
    except Exception as e:
        print(f"⚠ AI生成エラー: {e}")
        print("サンプル投稿を生成します。")
        return generate_sample_posts(account, num_posts)


def extract_posts_from_response(response: str) -> List[str]:
    """AIのレスポンスから投稿を抽出"""
    posts = []
    # POST 1:, POST 2: などのパターンで分割
    pattern = r'POST\s+\d+:\s*\n(.*?)(?=POST\s+\d+:|$)'
    matches = re.finditer(pattern, response, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        post = match.group(1).strip()
        # 余分な記号や改行を整理
        post = re.sub(r'^[-*]\s*', '', post, flags=re.MULTILINE)
        post = re.sub(r'\n{3,}', '\n\n', post)
        if post and len(post) > 10:
            posts.append(post)
    
    # パターンが見つからない場合、改行で分割して試す
    if not posts:
        lines = response.split('\n')
        current_post = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('POST'):
                current_post.append(line)
            elif current_post:
                post = ' '.join(current_post)
                if len(post) > 10:
                    posts.append(post)
                current_post = []
        if current_post:
            post = ' '.join(current_post)
            if len(post) > 10:
                posts.append(post)
    
    return posts


def generate_sample_posts(account: AccountDesign, num_posts: int = 5) -> List[str]:
    """サンプル投稿を生成（AIが使えない場合）"""
    posts = []
    
    # まずテンプレートから生成（より正確）
    if account.templates:
        for i, template in enumerate(account.templates[:num_posts]):
            if template.get('body') and len(template['body'].strip()) > 20:
                post = template['body'].strip()
                
                # 本文に既にCTAが含まれていない場合のみ追加
                has_cta_in_body = any(word in post for word in ['フォロー', 'いいね', 'コメント', '待ってて', '集合'])
                
                if not has_cta_in_body:
                    # CTAを追加
                    if template.get('cta') and template['cta'].strip():
                        post += f"\n\n{template['cta'].strip()}"
                    elif account.cta:
                        # CTAセクションから適切なものを選ぶ
                        cta_lines = [line for line in account.cta.split('\n') 
                                   if line.strip() and not line.strip().startswith('#') 
                                   and not line.strip().startswith('###')]
                        if cta_lines:
                            # フォロー促進のCTAを優先
                            follow_cta = [line for line in cta_lines if 'フォロー' in line]
                            if follow_cta:
                                cta_text = follow_cta[0].replace('- ', '').replace('「', '').replace('」', '').strip()
                                if cta_text:
                                    post += f"\n\n{cta_text}"
                            else:
                                cta_text = cta_lines[0].replace('- ', '').replace('「', '').replace('」', '').strip()
                                if cta_text:
                                    post += f"\n\n{cta_text}"
                
                posts.append(post)
    
    # テンプレートが足りない場合はコンテンツの柱から生成
    if len(posts) < num_posts:
        remaining = num_posts - len(posts)
        used_pillars = set()
        
        for i, pillar in enumerate(account.content_pillars):
            if len(posts) >= num_posts:
                break
            
            # 既に使用したテーマはスキップ
            if pillar['title'] in used_pillars:
                continue
            used_pillars.add(pillar['title'])
            
            if pillar['examples']:
                # 投稿例をベースに生成（最初の例を使用）
                base_example = pillar['examples'][0].replace('- ', '').replace('「', '').replace('」', '').strip()
                post = base_example
                
                # 投稿例が短すぎる場合は、別の例を追加
                if len(post) < 80 and len(pillar['examples']) > 1:
                    second_example = pillar['examples'][1].replace('- ', '').replace('「', '').replace('」', '').strip()
                    if second_example and second_example != base_example:
                        post = f"{base_example}\n\n{second_example[:100]}"
            else:
                # コンテンツの柱の説明から生成
                pillar_desc = pillar['content'][:200].replace('**', '').strip()
                post = f"{pillar['title']}について、{pillar_desc}"
            
            # CTAが含まれていない場合のみ追加
            has_cta = any(word in post for word in ['フォロー', 'いいね', 'コメント', '待ってて', '集合'])
            if not has_cta and account.cta:
                cta_lines = [line for line in account.cta.split('\n') 
                           if line.strip() and not line.strip().startswith('#')
                           and not line.strip().startswith('###')]
                if cta_lines:
                    follow_cta = [line for line in cta_lines if 'フォロー' in line]
                    if follow_cta:
                        cta_text = follow_cta[0].replace('- ', '').replace('「', '').replace('」', '').strip()
                        if cta_text:
                            post += f"\n\n{cta_text}"
                    else:
                        cta_text = cta_lines[0].replace('- ', '').replace('「', '').replace('」', '').strip()
                        if cta_text:
                            post += f"\n\n{cta_text}"
            
            posts.append(post)
    
    # まだ足りない場合は自己紹介文ベースで生成
    while len(posts) < num_posts:
        post = f"{account.intro[:150]}"
        has_cta = any(word in post for word in ['フォロー', 'いいね', 'コメント', '待ってて', '集合'])
        if not has_cta and account.cta:
            cta_lines = [line for line in account.cta.split('\n') 
                       if line.strip() and not line.strip().startswith('#')
                       and not line.strip().startswith('###')]
            if cta_lines:
                cta_text = cta_lines[0].replace('- ', '').replace('「', '').replace('」', '').strip()
                if cta_text:
                    post += f"\n\n{cta_text}"
        posts.append(post)
    
    return posts[:num_posts]


def save_to_spreadsheet(posts: List[Dict], account_name: str, config: Dict):
    """生成した投稿をスプレッドシートに転記"""
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(
            config['credentials_path'], scopes=scope
        )
        client = gspread.authorize(creds)
        
        # アカウントマッピングからスプレッドシートIDを取得
        account_mappings = config.get('account_mappings', {})
        account_mapping = account_mappings.get(account_name)
        
        if not account_mapping:
            print(f"⚠ 警告: {account_name}のスプレッドシート設定が見つかりません")
            return False
        
        spreadsheet_id = account_mapping['spreadsheet_id']
        worksheet_name = account_mapping.get('worksheet_name', '自動投稿')
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            # ワークシートが存在しない場合は作成
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            # ヘッダーを設定
            worksheet.append_row(['投稿日時', '投稿内容', 'ステータス', 'いいね数', '返信数', '再生数', '作成日時'])
        
        # 投稿を追加
        now = datetime.now()
        for i, post_data in enumerate(posts):
            post_content = post_data['content']
            # 投稿日時を設定（1日ごとに分散）
            post_datetime = now + timedelta(days=i)
            
            row = [
                post_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                post_content,
                '下書き',  # ステータス
                '',  # いいね数
                '',  # 返信数
                '',  # 再生数
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 作成日時
            ]
            worksheet.append_row(row)
        
        print(f"✓ {len(posts)}件の投稿をスプレッドシートに転記しました")
        return True
    
    except Exception as e:
        print(f"⚠ スプレッドシート転記エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン処理"""
    print("=" * 60)
    print("投稿生成スクリプト")
    print("=" * 60)
    
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
    
    print(f"\n✓ {len(accounts)}個のアカウント設計を読み込みました\n")
    
    # OpenAI APIキーを取得
    api_key = config.get('openai_api_key', '')
    if not api_key:
        print("⚠ OpenAI APIキーが設定されていません。config.jsonにopenai_api_keyを設定してください。")
        print("   サンプル投稿を生成します。\n")
    
    # 各アカウントについて投稿を生成
    all_posts = []
    for account in accounts:
        print(f"📝 {account.account_name} の投稿を生成中...")
        
        posts = generate_posts_with_ai(account, num_posts=5, api_key=api_key)
        
        # スプレッドシートに転記
        post_data_list = [{'content': post} for post in posts]
        success = save_to_spreadsheet(post_data_list, account.account_name, config)
        
        if success:
            print(f"  ✓ 5件の投稿を生成し、スプレッドシートに転記しました\n")
        else:
            print(f"  ⚠ 投稿の生成は完了しましたが、スプレッドシートへの転記に失敗しました\n")
        
        all_posts.append({
            'account': account.account_name,
            'posts': posts
        })
    
    # サマリーを表示
    print("=" * 60)
    print("完了！")
    print("=" * 60)
    total_posts = sum(len(item['posts']) for item in all_posts)
    print(f"総投稿数: {total_posts}件")
    print(f"アカウント数: {len(accounts)}個")
    print("\n各アカウントの投稿数:")
    for item in all_posts:
        print(f"  - {item['account']}: {len(item['posts'])}件")


if __name__ == '__main__':
    main()
