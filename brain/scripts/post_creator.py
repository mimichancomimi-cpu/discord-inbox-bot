#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アカウント設計を読み込んで投稿を作成し、スプレッドシートに自動記入するスクリプト
"""

import re
import os
import json
import random
from datetime import datetime, date
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from typing import Dict, List, Optional


class AccountDesignParser:
    """アカウント設計ファイルを解析するクラス"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = self._read_file()
        self.account_info = self._parse()
    
    def _read_file(self) -> str:
        """ファイルを読み込む"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse(self) -> Dict:
        """マークダウンファイルからアカウント情報を抽出"""
        info = {
            'name': '',
            'genre': '',
            'keywords': [],
            'bio': '',
            'persona': {},
            'target_audience': {},
            'content_pillars': [],
            'templates': [],
            'post_examples': []  # 実際の投稿例
        }
        
        # 名前を抽出
        name_match = re.search(r'\*\*名前:\*\*\s*(.+)', self.content)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        # ジャンルを抽出
        genre_match = re.search(r'\*\*ジャンル:\*\*\s*(.+)', self.content)
        if genre_match:
            info['genre'] = genre_match.group(1).strip()
        
        # キーワードを抽出
        keywords_match = re.search(r'\*\*キーワード:\*\*\s*(.+)', self.content, re.DOTALL)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            info['keywords'] = [k.strip() for k in keywords_text.split('/')]
        
        # 自己紹介文を抽出
        bio_match = re.search(r'\*\*自己紹介文:\*\*\s*(.+)', self.content, re.DOTALL)
        if bio_match:
            info['bio'] = bio_match.group(1).strip()
        
        # コンテンツの柱を抽出
        pillars_section = re.search(r'#### 1\.\s*コンテンツの柱.*?#### 2\.', self.content, re.DOTALL)
        if pillars_section:
            pillar_items = re.findall(r'\d+\.\s*\*\*(.+?)\*\*', pillars_section.group(0))
            info['content_pillars'] = pillar_items
        
        # 投稿テンプレートを抽出
        template_section = re.search(r'#### 2\.\s*投稿テンプレート.*?#### 3\.', self.content, re.DOTALL)
        if template_section:
            template_blocks = re.findall(r'```\s*(.+?)```', template_section.group(0), re.DOTALL)
            info['templates'] = template_blocks
        
        # リライト済み投稿コンテンツから実際の投稿例を抽出
        post_examples_section = re.search(r'## リライト済み投稿コンテンツ.*?(?=##|$)', self.content, re.DOTALL)
        if post_examples_section:
            # 投稿例を抽出（### 投稿1：... の形式）
            post_matches = re.findall(r'### 投稿\d+[：:](.+?)(?=---|### 投稿|\Z)', post_examples_section.group(0), re.DOTALL)
            for post_match in post_matches:
                # 投稿内容をクリーンアップ（余分な空白や改行を削除）
                post_text = post_match.strip()
                # 「本文：」や「**分析：**」以降を削除
                post_text = re.split(r'本文[：:]|分析[：:]|\*\*分析', post_text)[0].strip()
                if post_text and len(post_text) > 20:  # 20文字以上の投稿のみ
                    info['post_examples'].append(post_text)
        
        # 投稿例は使わない（テンプレート例から抽出しない）
        
        return info


class InsightsLoader:
    """投稿インサイトから過去の投稿情報を読み込むクラス"""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Google Sheetsに接続"""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            print(f"投稿インサイト接続エラー: {e}")
            raise
    
    def load_insights(self, worksheet_name: str = "投稿インサイト", limit: int = 50) -> List[Dict]:
        """投稿インサイトから過去の投稿情報を読み込む"""
        if not self.spreadsheet:
            return []
        
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
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
                for i, header in enumerate(headers):
                    if i < len(row) and row[i]:
                        header_clean = header.strip()
                        if header_clean == '投稿本文':
                            insight['post_content'] = row[i].strip()
                        elif header_clean == 'いいね数':
                            try:
                                insight['likes'] = int(str(row[i]).replace(',', ''))
                            except:
                                insight['likes'] = 0
                        elif header_clean == '再生数/表示数':
                            try:
                                insight['views'] = int(str(row[i]).replace(',', ''))
                            except:
                                insight['views'] = 0
                        elif header_clean == '返信数':
                            try:
                                insight['replies'] = int(str(row[i]).replace(',', ''))
                            except:
                                insight['replies'] = 0
                        elif header_clean == 'ポストURL':
                            insight['post_url'] = row[i].strip()
                        elif header_clean == 'インサイト取得日時':
                            insight['insight_date'] = row[i].strip()
                
                # 投稿本文がある場合のみ追加
                if insight.get('post_content') and len(insight['post_content']) > 10:
                    insights.append(insight)
            
            return insights
        except Exception as e:
            print(f"投稿インサイト読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_insights_cache(self, account_name: str, insights: List[Dict], cache_dir: str = "."):
        """過去の投稿情報をキャッシュファイルに保存"""
        cache_file = Path(cache_dir) / f"{account_name}_insights_cache.json"
        cache_data = {
            'last_updated': date.today().isoformat(),
            'insights': insights
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"投稿インサイトをキャッシュに保存しました: {cache_file}")
            return True
        except Exception as e:
            print(f"キャッシュ保存エラー: {e}")
            return False
    
    def load_insights_cache(self, account_name: str, cache_dir: str = ".") -> Optional[List[Dict]]:
        """キャッシュファイルから過去の投稿情報を読み込む"""
        cache_file = Path(cache_dir) / f"{account_name}_insights_cache.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 更新日をチェック（1日1回更新）
            last_updated = cache_data.get('last_updated')
            if last_updated:
                last_date = date.fromisoformat(last_updated)
                today = date.today()
                
                # 今日更新されている場合はキャッシュを使用
                if last_date == today:
                    print(f"キャッシュから投稿インサイトを読み込みました（最終更新: {last_updated}）")
                    return cache_data.get('insights', [])
                else:
                    print(f"キャッシュが古いです（最終更新: {last_updated}）。再読み込みします。")
                    return None
            
            return cache_data.get('insights', [])
        except Exception as e:
            print(f"キャッシュ読み込みエラー: {e}")
            return None


class PostGenerator:
    """アカウント設計に基づいて投稿を生成するクラス"""
    
    def __init__(self, account_info: Dict, api_key: Optional[str] = None, insights: Optional[List[Dict]] = None):
        self.account_info = account_info
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.insights = insights or []  # 過去の投稿インサイト
    
    def generate_post(self, theme: Optional[str] = None) -> str:
        """投稿を生成"""
        if not self.api_key:
            # APIキーがない場合は、テンプレートベースで生成
            return self._generate_from_template(theme)
        
        # OpenAI APIを使用して生成
        return self._generate_with_ai(theme)
    
    def generate_multiple_posts(self, count: int = 10, theme: Optional[str] = None) -> List[str]:
        """複数の投稿を生成（長さ別にバランスよく）"""
        posts = []
        seen = set()  # 完全一致のみチェック
        
        # 長さ別のカテゴリを定義
        short_posts = []  # 短文（1〜3行）
        medium_posts = []  # 中文（3〜6行）
        long_posts = []  # 長文（6行以上）
        
        # まず、十分な数の投稿を生成してカテゴリ分け
        for i in range(count * 3):  # 余裕を持って生成
            post = self.generate_post(theme)
            if post and len(post) > 15 and post not in seen:
                seen.add(post)
                # 行数をカウント
                line_count = len([line for line in post.split('\n') if line.strip()])
                
                if line_count <= 3:
                    short_posts.append(post)
                elif line_count <= 6:
                    medium_posts.append(post)
                else:
                    long_posts.append(post)
        
        # バランスよく選択（短文:中文:長文 = 3:5:2 の比率）
        target_short = max(1, int(count * 0.3))
        target_medium = max(1, int(count * 0.5))
        target_long = max(1, count - target_short - target_medium)
        
        # 各カテゴリから選択
        posts.extend(random.sample(short_posts, min(target_short, len(short_posts))))
        posts.extend(random.sample(medium_posts, min(target_medium, len(medium_posts))))
        posts.extend(random.sample(long_posts, min(target_long, len(long_posts))))
        
        # 足りない場合は残りをランダムに追加
        remaining = count - len(posts)
        if remaining > 0:
            all_posts = short_posts + medium_posts + long_posts
            additional = [p for p in all_posts if p not in posts]
            posts.extend(random.sample(additional, min(remaining, len(additional))))
        
        # ランダムにシャッフル
        random.shuffle(posts)
        
        return posts[:count]  # 指定された数だけ返す
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """2つのテキストの類似度を計算（簡易版）"""
        # 単語レベルでの類似度を計算
        words1 = set(re.findall(r'[\w\u3040-\u309F\u30A0-\u30FF]+', text1))
        words2 = set(re.findall(r'[\w\u3040-\u309F\u30A0-\u30FF]+', text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _generate_from_template(self, theme: Optional[str] = None) -> str:
        """テンプレートから投稿を生成（創造的で多様に）"""
        # アカウント設計の情報を取得
        bio = self.account_info.get('bio', '')
        keywords = self.account_info.get('keywords', [])
        content_pillars = self.account_info.get('content_pillars', [])
        persona = self.account_info.get('persona', '')
        target_audience = self.account_info.get('target_audience', '')
        
        # テーマを決定
        if not theme and content_pillars:
            theme = random.choice(content_pillars)
        
        # 創造的な投稿を生成（テンプレートに依存しない）
        all_options = []
        
        # 1. キーワードの組み合わせから生成
        if keywords and len(keywords) >= 2:
            for _ in range(5):
                kw1, kw2 = random.sample(keywords, 2)
                all_options.extend([
                    f"{kw1}と{kw2}、両方大切。でも無理しない。",
                    f"{kw1}しながら{kw2}する。それでいい。",
                    f"{kw1}も{kw2}も、難しく考えなくていい。",
                    f"{kw1}と{kw2}、自然に。それだけでいい。",
                    f"{kw1}の前に{kw2}する。大切な時間。",
                    f"{kw1}と{kw2}、両方大事。"
                ])
        
        # 2. キーワードから直接生成（より多様に）
        if keywords:
            for keyword in random.sample(keywords, min(5, len(keywords))):
                # 様々なパターンで表現
                all_options.extend([
                    f"{keyword}、難しく考えなくていい。",
                    f"{keyword}って、実はシンプルなこと。",
                    f"{keyword}は自然に起こる。無理しない。",
                    f"{keyword}のコツは、ゆるーく考えること。",
                    f"{keyword}に大事なのは、自然体でいること。",
                    f"{keyword}は強く願うより、自然に受け取る。",
                    f"{keyword}を意識しすぎない。自然体で。",
                    f"{keyword}より、自分らしく。",
                    f"{keyword}は自然に整う。無理しない。",
                    f"{keyword}を意識するより、今を大切に。",
                    f"{keyword}を大切に。それが一番。",
                    f"{keyword}を持って生きる。それだけでいい。",
                    f"{keyword}を失わない。それが大事。",
                    f"{keyword}、毎日少しずつ。",
                    f"{keyword}は日常から。無理しない。",
                    f"{keyword}って、小さなことから始めよう。",
                    f"{keyword}、それだけでいい。",
                    f"{keyword}の時間、大切にしたい。",
                    f"{keyword}、無理しない。",
                    f"{keyword}を整える。それだけでいい。"
                ])
        
        # 3. 自己紹介文から新しい表現を生成
        if bio:
            bio_sentences = [s.strip() for s in re.split(r'[。！？\n]', bio) if s.strip() and len(s.strip()) > 5]
            for sentence in random.sample(bio_sentences, min(3, len(bio_sentences))):
                if sentence:
                    all_options.extend([
                        f"{sentence}。それが大事。",
                        f"{sentence}。それでいい。",
                        f"{sentence}。自然体で。"
                    ])
        
        # 4. コンテンツの柱から生成
        if content_pillars:
            for pillar in random.sample(content_pillars, min(3, len(content_pillars))):
                all_options.extend([
                    f"{pillar}について、もっと知りたい。",
                    f"{pillar}、毎日が発見。",
                    f"{pillar}、小さな幸せを大切に。",
                    f"{pillar}の中に幸せがある。それでいい。",
                    f"{pillar}の小さなこと、大切にしたい。",
                    f"{pillar}を大切に。それが一番。"
                ])
        
        # 5. 長さ別のバリエーションを動的に生成
        base_phrases = [
            "今日も自分らしく", "無理しない", "完璧じゃなくていい", "自分を大切に",
            "自然体で", "前向きに", "今を大切に", "小さな幸せを", "自分を許す",
            "完璧を目指さない", "自分のペースで", "それでいい", "それだけでいい",
            "これが一番", "これ、大事", "自然に", "ゆるーく", "今の自分でいい"
        ]
        
        # 短文（1行）
        for _ in range(10):
            all_options.append(random.choice(base_phrases) + "。")
        
        # 中文（2-4行）
        for _ in range(15):
            selected = random.sample(base_phrases, random.randint(2, 4))
            all_options.append('\n'.join([p + "。" for p in selected]))
        
        # 長文（5-8行）
        for _ in range(10):
            selected = random.sample(base_phrases, random.randint(5, 8))
            all_options.append('\n'.join([p + "。" for p in selected]))
        
        # 6. 完全にランダムな組み合わせ
        if keywords:
            for _ in range(10):
                selected_keywords = random.sample(keywords, random.randint(1, 3))
                lines = []
                for kw in selected_keywords:
                    pattern = random.choice([
                        f"{kw}、難しく考えなくていい。",
                        f"{kw}って、実はシンプル。",
                        f"{kw}は自然に起こる。",
                        f"{kw}、無理しない。",
                        f"{kw}を大切に。"
                    ])
                    lines.append(pattern)
                lines.append(random.choice(["それでいい。", "それだけでいい。", "これが一番。"]))
                all_options.append('\n'.join(lines))
        
        # ランダムに選択
        if all_options:
            return random.choice(all_options).strip()
        
        # フォールバック
        return "今日もゆるーく、前向きに。"
                    post_templates.extend([
                        # 短文
                        "完璧を目指さなくていい。自分らしく生きよう。",
                        "無理しない。それが一番大事。",
                        "完璧じゃなくていい。今の自分でいい。",
                        "無理しなくていい。自分のペースで。",
                        # 中文
                        "頑張りすぎない。ゆるーく、でも前向きに。\n完璧を目指さなくていい。\n自分らしく生きよう。",
                        "完璧主義を手放す。それだけで楽になる。\n無理しない。それが一番大事。",
                        "頑張りすぎて疲れたら、一度立ち止まろう。\n完璧を目指すより、自分らしさを大切に。",
                        # 長文
                        "完璧を目指さなくていい。自分らしく生きよう。\n無理しない。それが一番大事。\n頑張りすぎない。ゆるーく、でも前向きに。\n完璧じゃなくていい。今の自分でいい。\n無理しなくていい。自分のペースで。"
                    ])
                elif '寝る' in keyword or '睡眠' in keyword:
                    post_templates.extend([
                        # 短文
                        "疲れたら休む。それが一番のケア。",
                        "睡眠は最強のメンタルケア。しっかり寝よう。",
                        "疲れたら無理せず寝る。これが一番。",
                        "疲れたら休む。それが正解。",
                        # 中文
                        "悩んでる時は寝る。考えすぎる前に休む。\n寝ることでリセットできる。\n無理しない。",
                        "睡眠不足は機嫌が悪くなる原因。しっかり寝よう。\n疲れたら休む。それが正解。",
                        "寝る前に心を整える時間、大切にしたい。\n睡眠は最強のメンタルケア。\nしっかり寝よう。",
                        # 長文
                        "疲れたら休む。それが一番のケア。\n睡眠は最強のメンタルケア。しっかり寝よう。\n悩んでる時は寝る。考えすぎる前に休む。\n寝ることでリセットできる。無理しない。\n睡眠不足は機嫌が悪くなる原因。しっかり寝よう。"
                    ])
                elif '引き寄せ' in keyword:
                    post_templates.extend([
                        # 短文
                        "引き寄せの法則、難しく考えなくていい。",
                        "欲しいものがあるなら、まずは行動。",
                        "引き寄せって、実はシンプルなこと。",
                        "引き寄せは自然に起こる。無理しない。",
                        # 中文
                        "引き寄せのコツは、ゆるーく考えること。\n引き寄せに大事なのは、自然体でいること。\n難しく考えすぎない。",
                        "引き寄せは強く願うより、自然に受け取る。\n引き寄せの法則、難しく考えなくていい。\n欲しいものがあるなら、まずは行動。",
                        # 長文
                        "引き寄せの法則、難しく考えなくていい。\n欲しいものがあるなら、まずは行動。\n引き寄せって、実はシンプルなこと。\n引き寄せは自然に起こる。無理しない。\n引き寄せのコツは、ゆるーく考えること。\n引き寄せに大事なのは、自然体でいること。"
                    ])
                elif 'メンタル' in keyword or 'デトックス' in keyword:
                    post_templates.extend([
                        # 短文
                        "メンタルケア、難しく考えなくていい。",
                        "心のデトックス、毎日少しずつ。",
                        "メンタルヘルス、自分を大切にすることから。",
                        "心を整える。それだけでいい。",
                        # 中文
                        "心を整える時間、大切にしたい。\nメンタルケアは日常から。\n無理しない。",
                        "心のデトックス、無理しない。\nメンタルケアって、小さなことから始めよう。\n心を整える。それだけでいい。",
                        # 長文
                        "メンタルケア、難しく考えなくていい。\n心のデトックス、毎日少しずつ。\nメンタルヘルス、自分を大切にすることから。\n心を整える時間、大切にしたい。\nメンタルケアは日常から。無理しない。\n心のデトックス、無理しない。"
                    ])
                elif '波動' in keyword:
                    post_templates.extend([
                        # 短文
                        "波動を上げるって、難しく考えなくていい。",
                        "良い波動を出すには、自然体でいること。",
                        "波動は自然に上がる。無理しない。",
                        "波動を意識しすぎない。自然体で。",
                        # 中文
                        "良い波動って、自分らしくいること。\n波動を上げるより、自分らしく。\n波動は自然に整う。",
                        "波動を意識するより、今を大切に。\n波動を上げるって、難しく考えなくていい。\n良い波動を出すには、自然体でいること。",
                        # 長文
                        "波動を上げるって、難しく考えなくていい。\n良い波動を出すには、自然体でいること。\n波動は自然に上がる。無理しない。\n波動を意識しすぎない。自然体で。\n良い波動って、自分らしくいること。\n波動を上げるより、自分らしく。"
                    ])
                elif '自分軸' in keyword:
                    post_templates.extend([
                        # 短文
                        "自分軸を大切に。それが一番。",
                        "自分軸を持って生きる。それだけでいい。",
                        "自分軸を失わない。それが大事。",
                        "自分軸を大切にしたい。",
                        # 中文
                        "自分軸を持って生きよう。\n自分軸を失わないように。\n自分軸を大切にする。それが一番。",
                        "自分軸を持って生きる。自然体で。\n自分軸を大切に。それが一番。\n自分軸を持って生きる。それだけでいい。",
                        # 長文
                        "自分軸を大切に。それが一番。\n自分軸を持って生きる。それだけでいい。\n自分軸を失わない。それが大事。\n自分軸を大切にしたい。\n自分軸を持って生きよう。\n自分軸を失わないように。"
                    ])
        
        # コンテンツの柱からも生成
        if content_pillars:
            for pillar in content_pillars:
                if 'スマホ' in pillar or 'ポイ活' in pillar:
                    post_templates.extend([
                        "スマホひとつでできること、意外と多い。",
                        "スマホで完結する作業、隙間時間にできる。",
                        "スマホひとつでお小遣いゲット。簡単でいい。",
                        "スマホでできること、もっと知りたい。",
                        "スマホひとつで完結。それでいい。"
                    ])
                elif '日常' in pillar or '母ちゃん' in pillar:
                    post_templates.extend([
                        "アラフォー母ちゃんの日常、毎日が発見。",
                        "母ちゃんの日常、小さな幸せを大切に。",
                        "日常の中に幸せがある。それでいい。",
                        "日常の小さなこと、大切にしたい。",
                        "日常を大切に。それが一番。"
                    ])
        
        # 自己紹介文からもインスピレーションを得る
        if bio:
            bio_sentences = [s.strip() for s in re.split(r'[。！？\n]', bio) if s.strip() and len(s.strip()) > 10]
            for sentence in bio_sentences[:3]:
                # 自己紹介文の一部を新しい表現に変換
                if 'ゆる' in sentence:
                    post_templates.append("ゆるーく生きる。それだけでいい。")
                if '寝る' in sentence:
                    post_templates.append("寝る前に心を整える。大切な時間。")
                if '引き寄せ' in sentence:
                    post_templates.append("引き寄せは自然に起こる。無理しない。")
        
        # 汎用的な投稿パターンも追加（長さ別に分類）
        post_templates.extend([
            # 短文
            "今日も自分らしく。それでいい。",
            "無理しない。それが一番大事。",
            "完璧じゃなくていい。今の自分でいい。",
            "自分を大切に。それだけでいい。",
            "自然体で生きる。それが一番。",
            "前向きに。でも無理しない。",
            "自分らしく生きる。それでいい。",
            "今を大切に。それだけでいい。",
            "小さな幸せを大切に。",
            "自分を許す。それも大事。",
            # 中文
            "完璧を目指さない。自分らしく。\n無理しすぎない。自分のペースで。\n自然体でいる。それが一番。",
            "自分を大切にする。それだけでいい。\n今の自分を受け入れる。それでいい。\n今日も自分らしく。それでいい。",
            "無理しない。それが一番大事。\n完璧じゃなくていい。今の自分でいい。\n自分を大切に。それだけでいい。",
            # 長文
            "今日も自分らしく。それでいい。\n無理しない。それが一番大事。\n完璧じゃなくていい。今の自分でいい。\n自分を大切に。それだけでいい。\n自然体で生きる。それが一番。\n前向きに。でも無理しない。"
        ])
        
        # ランダムに選択（シンプルに）
        if post_templates:
            return random.choice(post_templates).strip()
        
        # フォールバック
        return "今日もゆるーく、前向きに。"
    
    def _generate_with_ai(self, theme: Optional[str] = None) -> str:
        """AIを使用して投稿を生成"""
        if not self.client:
            return self._generate_from_template(theme)
        
        prompt = self._create_prompt(theme)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはSNS投稿の専門家です。指定されたアカウント設計に基づいて、魅力的な投稿を作成してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI生成エラー: {e}")
            return self._generate_from_template(theme)
    
    def _create_prompt(self, theme: Optional[str] = None) -> str:
        """AI用のプロンプトを作成"""
        # 過去の投稿インサイトを参考として含める
        insights_text = ""
        if self.insights:
            # 高パフォーマンス投稿を選択
            sorted_insights = sorted(
                self.insights,
                key=lambda x: (x.get('likes', 0) + x.get('views', 0) // 10),
                reverse=True
            )
            top_insights = sorted_insights[:3]
            examples = [insight.get('post_content', '') for insight in top_insights if insight.get('post_content')]
            if examples:
                insights_text = "\n\n参考となる過去の高パフォーマンス投稿（実際に投稿されたもの）:\n" + "\n---\n".join(examples)
        
        # 投稿例がある場合はそれも含める
        post_examples_text = ""
        if self.account_info.get('post_examples'):
            examples = self.account_info['post_examples'][:3]  # 最初の3つまで
            post_examples_text = "\n\n参考となる投稿例:\n" + "\n---\n".join(examples)
        
        # 両方ある場合は結合
        if insights_text and post_examples_text:
            post_examples_text = insights_text + "\n\n" + post_examples_text
        elif insights_text:
            post_examples_text = insights_text
        
        bio = self.account_info.get('bio', '')
        if len(bio) > 200:
            bio = bio[:200] + "..."
        
        prompt = f"""
以下のアカウント設計に基づいて、Threads用の投稿を作成してください。

アカウント名: {self.account_info.get('name', '')}
ジャンル: {self.account_info.get('genre', '')}
キーワード: {', '.join(self.account_info.get('keywords', []))}
自己紹介: {bio}
{post_examples_text}
"""
        
        if theme:
            prompt += f"\nテーマ: {theme}\n"
        elif self.account_info.get('content_pillars'):
            prompt += f"\nコンテンツの柱: {', '.join(self.account_info.get('content_pillars', []))}\n"
        
        prompt += """
以下の要件を満たす投稿を作成してください：
- 親しみやすく、共感を呼ぶ内容
- 絵文字を適度に使用（2-5個程度）
- 簡潔で読みやすい（200-400文字程度）
- CTA（行動喚起）を含める
- 機械音痴でも理解できる表現
- 分析や説明は含めず、実際の投稿内容のみ
- マークダウン形式は使わず、プレーンテキストで

重要：
1. アカウント設計の分析部分や説明は含めず、実際にThreadsに投稿する内容のみを生成してください。
2. 過去の投稿をそのままコピーするのではなく、過去投稿のスタイルや傾向を参考にしながら、**必ず新しい内容**を生成してください。
3. 過去投稿と同じ表現や文章を繰り返さないでください。
4. 過去投稿のテーマやトーンは参考にしつつ、新しい視点や表現で投稿を作成してください。
"""
        
        return prompt


class SpreadsheetManager:
    """Google Sheetsへの記入を管理するクラス"""
    
    # 既存のスプレッドシートID（デフォルト値）
    DEFAULT_SPREADSHEET_ID = "1uj5a4GVcxMTzW8aoCIQL8Oj9Y8qvY3Wsn3bYGfEPymw"
    
    # 利用可能なシート名のリスト
    AVAILABLE_SHEETS = ["自動投稿", "無限投稿", "曜日投稿", "ランダム投稿", "予約枠投稿"]
    
    def __init__(self, credentials_path: str, spreadsheet_id: str = None, worksheet_name: str = "自動投稿"):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id or self.DEFAULT_SPREADSHEET_ID
        self.worksheet_name = worksheet_name
        self.client = None
        self.worksheet = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Google Sheetsに接続"""
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            # ワークシートが存在するか確認
            try:
                self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                print(f"シート '{self.worksheet_name}' に接続しました")
            except gspread.exceptions.WorksheetNotFound:
                print(f"警告: シート '{self.worksheet_name}' が見つかりません")
                print(f"利用可能なシート: {', '.join(self.get_available_sheets())}")
                raise
        except Exception as e:
            print(f"スプレッドシート接続エラー: {e}")
            raise
    
    def get_available_sheets(self) -> List[str]:
        """利用可能なシートのリストを取得"""
        if not self.spreadsheet:
            return []
        try:
            return [sheet.title for sheet in self.spreadsheet.worksheets()]
        except:
            return []
    
    def get_sheet_structure(self) -> Dict:
        """シートの構造を確認（ヘッダー行を読み取る）"""
        if not self.worksheet:
            return {}
        
        try:
            # 最初の10行を確認してヘッダー行を探す
            all_values = self.worksheet.get_all_values()
            
            # ヘッダー行を探す（「ポスト文」「予約投稿日時」などのキーワードを含む行）
            headers = None
            header_row_index = 0
            
            for i in range(min(10, len(all_values))):
                row = all_values[i]
                # ヘッダー行の可能性があるキーワードをチェック
                row_text = ' '.join([str(cell) for cell in row if cell]).lower()
                # Threads予約投稿ツールのヘッダーを探す（「ポスト文」が含まれる行）
                if 'ポスト文' in ' '.join([str(cell) for cell in row if cell]):
                    headers = row
                    header_row_index = i
                    print(f"[デバッグ] ヘッダー行を発見: 行 {i+1}")
                    break
            
            # ヘッダーが見つからない場合は、最初の空でない行を使用
            if not headers:
                for i in range(min(5, len(all_values))):
                    row = all_values[i]
                    if any(cell for cell in row):
                        headers = row
                        header_row_index = i
                        break
            
            # それでも見つからない場合は1行目を使用
            if not headers and len(all_values) > 0:
                headers = all_values[0]
                header_row_index = 0
            
            return {
                'headers': headers or [],
                'header_row_index': header_row_index,
                'has_data': len(all_values) > header_row_index + 1,
                'row_count': len(all_values)
            }
        except Exception as e:
            print(f"シート構造の取得エラー: {e}")
            return {}
    
    def add_post(self, account_name: str, genre: str, post_content: str, 
                 theme: str = '', keywords: str = '', status: str = '作成済み',
                 scheduled_time: str = '', image_path: str = ''):
        """投稿をスプレッドシートに追加"""
        if not self.worksheet:
            print("スプレッドシートに接続できていません")
            return False
        
        try:
            # シートの構造を確認
            structure = self.get_sheet_structure()
            headers = structure.get('headers', [])
            
            # デバッグ: ヘッダーを表示
            print(f"\n[デバッグ] シートのヘッダー: {headers}")
            print(f"[デバッグ] ヘッダー行のインデックス: {structure.get('header_row_index', 0)}")
            
            # 既存のシート構造に合わせてデータを配置
            # 一般的なThreads予約投稿ツールの構造を想定
            row_data = {}
            
            # ヘッダーに基づいてデータをマッピング（Threads予約投稿ツールの構造に対応）
            if headers:
                for i, header in enumerate(headers):
                    if not header or not str(header).strip():
                        continue
                    header_str = str(header).strip()
                    header_lower = header_str.lower()
                    
                    # 投稿内容の列を探す（「ポスト文」）- 列2（インデックス1）に固定
                    if 'ポスト文' in header_str or ('post' in header_lower and '文' in header_str):
                        # 列2（インデックス1）に投稿内容を記入
                        row_data[1] = post_content
                        print(f"[デバッグ] 投稿内容を列 2 (ポスト文) にマッピング")
                    # 予約投稿日時の列
                    elif '予約投稿日時' in header_str or ('予約投稿' in header_str and '日時' in header_str):
                        row_data[i] = scheduled_time or datetime.now().strftime('%Y/%m/%d')
                        print(f"[デバッグ] 予約投稿日時を列 {i+1} ({header_str[:30]}...) にマッピング")
                    # 予約投稿時間(時)の列
                    elif '予約投稿時間(時)' in header_str or ('予約投稿' in header_str and '時間' in header_str and '時' in header_str and '分' not in header_str):
                        if scheduled_time:
                            try:
                                dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                                row_data[i] = str(dt.hour)
                            except:
                                row_data[i] = ''
                        print(f"[デバッグ] 予約投稿時間(時)を列 {i+1} ({header_str[:30]}...) にマッピング")
                    # 予約投稿時間(分)の列
                    elif '予約投稿時間(分)' in header_str or ('予約投稿' in header_str and '時間' in header_str and '分' in header_str):
                        if scheduled_time:
                            try:
                                dt = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')
                                row_data[i] = str(dt.minute)
                            except:
                                row_data[i] = ''
                        print(f"[デバッグ] 予約投稿時間(分)を列 {i+1} ({header_str[:30]}...) にマッピング")
                    # 画像1の列（最初の画像列のみ）
                    elif '画像1' in header_str or ('画像' in header_str and '1' in header_str and 'or' in header_str):
                        if image_path and 9 not in row_data:  # 列9（インデックス8）に既にマッピングされていない場合のみ
                            row_data[8] = image_path  # 列9はインデックス8
                            print(f"[デバッグ] 画像1を列 9 ({header_str[:30]}...) にマッピング")
            
            # 最初の空の行を見つける（ヘッダー行の次の行から）
            header_row_index = structure.get('header_row_index', 0)
            all_values = self.worksheet.get_all_values()
            
            # ヘッダー行の次の行から最初の空の行を探す
            next_row_index = header_row_index + 1
            for i in range(next_row_index, min(next_row_index + 1000, len(all_values))):
                row = all_values[i]
                # 列2（ポスト文）が空の行を見つける
                if len(row) < 2 or not row[1] or not row[1].strip():
                    next_row_index = i
                    break
            else:
                # 空の行が見つからない場合は、次の行を使用
                # ただし、既存のデータの最後の行の次を確認
                if len(all_values) > next_row_index:
                    # 最後の行を確認して、空でない場合は次の行を使用
                    last_row = all_values[-1]
                    if any(cell.strip() for cell in last_row if cell):
                        next_row_index = len(all_values)
                    else:
                        # 最後の行が空の場合は、その行を使用
                        next_row_index = len(all_values) - 1
                else:
                    next_row_index = len(all_values)
            
            # データがマッピングされていない場合の処理
            if not row_data:
                print("[デバッグ] ヘッダーにマッチする列が見つかりません。列2（ポスト文）に投稿内容を記入します。")
                # Threads予約投稿ツールの構造に合わせて、列2に投稿内容を記入
                max_col = max(len(headers), 10) if headers else 10
                row = [''] * max_col
                # 列2（インデックス1）に投稿内容を記入
                if max_col > 1:
                    row[1] = post_content
                print(f"[デバッグ] 行 {next_row_index + 1} にデータを記入")
                # 指定した行に書き込む
                self.worksheet.update(f'A{next_row_index + 1}', [row])
            else:
                # マッピングされたデータで行を作成
                max_col = max(row_data.keys()) + 1 if row_data else len(headers) if headers else 10
                row = [''] * max_col
                for col_idx, value in row_data.items():
                    if col_idx < max_col:
                        row[col_idx] = value
                print(f"[デバッグ] 行 {next_row_index + 1} にデータを記入（列{list(row_data.keys())}）")
                # 指定した行に書き込む
                self.worksheet.update(f'A{next_row_index + 1}', [row])
            
            print(f"✓ スプレッドシート '{self.worksheet_name}' に記入しました: {account_name}")
            return True
        except Exception as e:
            print(f"✗ スプレッドシート記入エラー: {e}")
            import traceback
            traceback.print_exc()
            return False


def load_config(config_path: str = 'config.json') -> Dict:
    """設定ファイルを読み込む"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_account_mapping(account_name: str, config: Dict) -> Dict:
    """アカウント名からスプレッドシートIDとシート名のマッピングを取得"""
    account_mappings = config.get('account_mappings', {})
    
    # 完全一致
    if account_name in account_mappings:
        mapping = account_mappings[account_name]
        return {
            'spreadsheet_id': mapping.get('spreadsheet_id'),
            'worksheet_name': mapping.get('worksheet_name', '自動投稿')
        }
    
    # 部分一致（アカウント名に含まれるキーワードで検索）
    for key, mapping in account_mappings.items():
        if key in account_name or account_name in key:
            return {
                'spreadsheet_id': mapping.get('spreadsheet_id'),
                'worksheet_name': mapping.get('worksheet_name', '自動投稿')
            }
    
    # デフォルト値
    return {
        'spreadsheet_id': config.get('spreadsheet_id'),
        'worksheet_name': config.get('worksheet_name', '自動投稿')
    }


def process_single_account(account_file: str, config: Dict, 
                           credentials_path: str, openai_key: Optional[str] = None,
                           theme: Optional[str] = None, scheduled_time: Optional[str] = None,
                           image_path: Optional[str] = None, load_insights: bool = True,
                           spreadsheet_id_override: Optional[str] = None, generate_count: int = 1) -> bool:
    """単一のアカウントを処理"""
    try:
        # アカウント設計を読み込む
        print(f"\n{'='*60}")
        print(f"処理中: {account_file}")
        print(f"{'='*60}")
        parser_obj = AccountDesignParser(account_file)
        account_info = parser_obj.account_info
        account_name = account_info.get('name', '不明')
        
        print(f"アカウント名: {account_name}")
        print(f"ジャンル: {account_info.get('genre', '不明')}")
        
        # アカウントマッピングを取得
        mapping = get_account_mapping(account_name, config)
        # コマンドライン引数で指定された場合は優先
        spreadsheet_id = spreadsheet_id_override or mapping.get('spreadsheet_id')
        worksheet_name = mapping.get('worksheet_name', '自動投稿')
        
        print(f"スプレッドシートID: {spreadsheet_id or 'デフォルト'}")
        print(f"シート名: {worksheet_name}")
        
        # デバッグ: マッピング情報を表示
        if not spreadsheet_id:
            print(f"[デバッグ] アカウントマッピングが見つかりませんでした。アカウント名: {account_name}")
            print(f"[デバッグ] config内のaccount_mappings: {list(config.get('account_mappings', {}).keys())}")
        
        # 投稿インサイトを読み込む（1日1回更新）
        insights = []
        if load_insights and spreadsheet_id:
            print("\n投稿インサイトを読み込んでいます...")
            try:
                insights_loader = InsightsLoader(credentials_path, spreadsheet_id)
                
                # まずキャッシュを確認
                cache_insights = insights_loader.load_insights_cache(account_name)
                
                if cache_insights is None:
                    # キャッシュがない、または古い場合は再読み込み
                    print("投稿インサイトをスプレッドシートから読み込んでいます...")
                    insights = insights_loader.load_insights(worksheet_name="投稿インサイト", limit=50)
                    if insights:
                        insights_loader.save_insights_cache(account_name, insights)
                        print(f"✓ {len(insights)}件の過去投稿を読み込みました")
                    else:
                        print("⚠ 過去の投稿が見つかりませんでした")
                else:
                    insights = cache_insights
                    print(f"✓ キャッシュから{len(insights)}件の過去投稿を読み込みました")
            except Exception as e:
                print(f"⚠ 投稿インサイトの読み込みに失敗しました: {e}")
                import traceback
                traceback.print_exc()
                print("  投稿インサイトなしで続行します...")
        
        # 投稿を生成（複数生成するかどうか）
        print(f"\n投稿を生成しています...（{generate_count}個）")
        generator = PostGenerator(account_info, api_key=openai_key, insights=insights)
        
        if generate_count > 1:
            # 複数の投稿を生成
            posts = generator.generate_multiple_posts(count=generate_count, theme=theme)
            print(f"\n生成された投稿（{len(posts)}個）:")
            print("=" * 60)
            for i, post in enumerate(posts, 1):
                print(f"{i}. {post}")
            print("=" * 60)
            
            # スプレッドシートに接続
            print("\nスプレッドシートに記入しています...")
            spreadsheet = SpreadsheetManager(
                credentials_path=credentials_path,
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name
            )
            
            keywords_str = ' / '.join(account_info.get('keywords', []))
            
            # すべての投稿をスプレッドシートに追加
            success_count = 0
            for i, post_content in enumerate(posts, 1):
                print(f"\n[{i}/{len(posts)}] スプレッドシートに記入しています...")
                success = spreadsheet.add_post(
                    account_name=account_name,
                    genre=account_info.get('genre', ''),
                    post_content=post_content,
                    theme=theme or '',
                    keywords=keywords_str,
                    status='作成済み',
                    scheduled_time=scheduled_time or '',
                    image_path=image_path or ''
                )
                if success:
                    success_count += 1
                    # 少し待機（API制限を避けるため）
                    import time
                    time.sleep(0.5)
            
            if success_count > 0:
                print(f"\n✓ {account_name} の処理が完了しました（{success_count}/{len(posts)}個追加）")
            else:
                print(f"\n✗ {account_name} の処理に失敗しました")
            
            return success_count > 0
        else:
            # 単一の投稿を生成
            post_content = generator.generate_post(theme=theme)
            
            print("\n生成された投稿:")
            print("-" * 50)
            print(post_content)
            print("-" * 50)
            
            # スプレッドシートに記入
            print("\nスプレッドシートに記入しています...")
            spreadsheet = SpreadsheetManager(
                credentials_path=credentials_path,
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name
            )
            
            keywords_str = ' / '.join(account_info.get('keywords', []))
            success = spreadsheet.add_post(
                account_name=account_name,
                genre=account_info.get('genre', ''),
                post_content=post_content,
                theme=theme or '',
                keywords=keywords_str,
                status='作成済み',
                scheduled_time=scheduled_time or '',
                image_path=image_path or ''
            )
            
            if success:
                print(f"✓ {account_name} の処理が完了しました")
            else:
                print(f"✗ {account_name} の処理に失敗しました")
            
            return success
        
    except Exception as e:
        print(f"✗ エラー: {account_file} の処理中にエラーが発生しました")
        print(f"  エラー内容: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_batch(account_dir: str, config: Dict, credentials_path: str,
                  openai_key: Optional[str] = None, theme: Optional[str] = None,
                  scheduled_time: Optional[str] = None, image_path: Optional[str] = None,
                  pattern: str = "*.md", load_insights: bool = True) -> Dict:
    """複数のアカウントを一括処理"""
    account_dir_path = Path(account_dir)
    
    if not account_dir_path.exists():
        print(f"エラー: ディレクトリが見つかりません: {account_dir}")
        return {'success': 0, 'failed': 0, 'total': 0}
    
    # マークダウンファイルを取得
    account_files = list(account_dir_path.glob(pattern))
    
    if not account_files:
        print(f"警告: {account_dir} にマッチするファイルが見つかりませんでした")
        return {'success': 0, 'failed': 0, 'total': 0}
    
    print(f"\n{'='*60}")
    print(f"バッチ処理を開始します")
    print(f"ディレクトリ: {account_dir}")
    print(f"対象ファイル数: {len(account_files)}")
    print(f"{'='*60}")
    
    results = {'success': 0, 'failed': 0, 'total': len(account_files), 'details': []}
    
    for i, account_file in enumerate(account_files, 1):
        print(f"\n[{i}/{len(account_files)}] {account_file.name}")
        success = process_single_account(
            str(account_file),
            config,
            credentials_path,
            openai_key,
            theme,
            scheduled_time,
            image_path,
            load_insights
        )
        
        if success:
            results['success'] += 1
            results['details'].append({'file': str(account_file), 'status': 'success'})
        else:
            results['failed'] += 1
            results['details'].append({'file': str(account_file), 'status': 'failed'})
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print(f"バッチ処理が完了しました")
    print(f"成功: {results['success']}/{results['total']}")
    print(f"失敗: {results['failed']}/{results['total']}")
    print(f"{'='*60}")
    
    return results


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='アカウント設計から投稿を作成してスプレッドシートに記入')
    parser.add_argument('account_file', nargs='?', help='アカウント設計ファイルのパス（バッチモードの場合は不要）')
    parser.add_argument('--batch', help='バッチ処理モード: 指定したディレクトリ内の全ファイルを処理')
    parser.add_argument('--spreadsheet-id', help='Google SheetsのスプレッドシートID（デフォルト: 既存のThreads予約投稿ツール）')
    parser.add_argument('--credentials', help='Google認証情報のJSONファイルパス')
    parser.add_argument('--worksheet', default='自動投稿', help='ワークシート名（デフォルト: 自動投稿）')
    parser.add_argument('--openai-key', help='OpenAI APIキー（オプション）')
    parser.add_argument('--theme', help='投稿のテーマ（オプション）')
    parser.add_argument('--scheduled-time', help='投稿予定日時（YYYY-MM-DD HH:MM:SS形式）')
    parser.add_argument('--image-path', help='画像ファイルのパス（オプション）')
    parser.add_argument('--config', default='config.json', help='設定ファイルのパス（デフォルト: config.json）')
    parser.add_argument('--list-sheets', action='store_true', help='利用可能なシートの一覧を表示')
    parser.add_argument('--pattern', default='*.md', help='バッチ処理時のファイルパターン（デフォルト: *.md）')
    parser.add_argument('--skip-insights', action='store_true', help='投稿インサイトの読み込みをスキップ')
    parser.add_argument('--generate-count', type=int, default=1, help='生成する投稿の数（デフォルト: 1）')
    
    args = parser.parse_args()
    
    # 設定ファイルを読み込む
    config = load_config(args.config)
    
    # コマンドライン引数が指定されていない場合は設定ファイルから読み込む
    # コマンドライン引数で明示的に指定された場合のみ使用
    spreadsheet_id = args.spreadsheet_id if args.spreadsheet_id else None
    credentials_path = args.credentials or config.get('credentials_path')
    worksheet_name = args.worksheet or config.get('worksheet_name', '自動投稿')
    openai_key = args.openai_key or config.get('openai_api_key')
    
    if not credentials_path:
        print("=" * 60)
        print("エラー: 認証情報ファイルが指定されていません")
        print("=" * 60)
        print("\n以下のいずれかの方法で認証情報を設定してください：")
        print("\n1. コマンドライン引数で指定:")
        print("   --credentials /path/to/credentials.json")
        print("\n2. config.jsonで指定:")
        print('   "credentials_path": "/path/to/credentials.json"')
        print("\n詳細は SETUP_GUIDE.md を参照してください。")
        print("=" * 60)
        return
    
    # 認証情報ファイルの存在確認
    if not os.path.exists(credentials_path):
        print("=" * 60)
        print(f"エラー: 認証情報ファイルが見つかりません: {credentials_path}")
        print("=" * 60)
        print("\n認証情報ファイルの取得方法:")
        print("1. Google Cloud Consoleでサービスアカウントを作成")
        print("2. JSONキーをダウンロード")
        print("3. credentials.jsonとして保存")
        print("\n詳細は SETUP_GUIDE.md を参照してください。")
        print("=" * 60)
        return
    
    # スプレッドシートに接続（シート一覧表示の場合）
    if args.list_sheets:
        try:
            spreadsheet = SpreadsheetManager(
                credentials_path=credentials_path,
                spreadsheet_id=spreadsheet_id
            )
            sheets = spreadsheet.get_available_sheets()
            print("\n利用可能なシート:")
            for sheet in sheets:
                print(f"  - {sheet}")
            return
        except Exception as e:
            print(f"エラー: {e}")
            return
    
    # バッチ処理モード
    if args.batch:
        if not credentials_path:
            print("エラー: 認証情報ファイルが指定されていません（--credentialsまたはconfig.jsonで指定）")
            return
        
        results = process_batch(
            account_dir=args.batch,
            config=config,
            credentials_path=credentials_path,
            openai_key=openai_key,
            theme=args.theme,
            scheduled_time=args.scheduled_time,
            image_path=args.image_path,
            pattern=args.pattern
        )
        return
    
    # 単一ファイル処理モード
    if not args.account_file:
        parser.print_help()
        print("\nエラー: アカウント設計ファイルのパスを指定するか、--batchオプションを使用してください")
        return
    
    # 単一アカウント処理
    process_single_account(
        account_file=args.account_file,
        config=config,
        credentials_path=credentials_path,
        openai_key=openai_key,
        theme=args.theme,
        scheduled_time=args.scheduled_time,
        image_path=args.image_path,
        load_insights=not args.skip_insights if hasattr(args, 'skip_insights') else True,
        spreadsheet_id_override=spreadsheet_id,
        generate_count=args.generate_count if hasattr(args, 'generate_count') else 1
    )
    
    print("\n完了しました！")


if __name__ == '__main__':
    main()
