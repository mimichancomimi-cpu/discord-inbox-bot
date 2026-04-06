#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""シナちゃん ツリー投稿1件目をしなちゃんAPI管理スプシに転記"""

import time
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# しなちゃんAPI管理スプレッドシート
SPREADSHEET_ID = "1soIzy35ouJlBtp1zCodMlgGyhB4CyjoQghMmpLZWUlI"
WORKSHEET_NAME = "自動投稿"

# ツリー1の投稿（1投目＋2投目）
POST_1 = """正直、note書くのに1時間とか2時間とかかけてる人、ちょっともったいなくないですか。私、以前は1記事3時間かかってて、お迎えの時間気づかなくて泣いた日もあるんですよね。でも今は30分。AIに大枠作ってもらって、自分の体験を肉付けするだけ。ママ友はPC持ってないのに、このやり方で初月5万超えちゃって。なんていうか、"""

POST_2 = """具体的に言うと、こういう流れです。①AIに「〇〇で悩んでる主婦向けに、私の△△体験を5000字のnote構成にして」って投げる ②出てきた見出しを自分の話で埋めていく（ここがあなたの素材） ③ SEOキーワードや「読んだ人がこう動く」はAIに設計させる。自分で考えなくていい。ポイントは「丸投げしない」こと。冒頭の共感部分とか、泣いた瞬間とか、夫に言えなかった本音とか、そういう「あなただけの感情」は自分で書く。それ以外はAI。この役割分担を知ってるかどうかで、3時間が30分になる。"""

# 今日の21:00
DATE_STR = "2026/02/07"
HOUR = 21
MINUTE = 0

root_dir = Path(__file__).resolve().parent.parent.parent
credentials_file = root_dir / "credentials.json"

creds = Credentials.from_service_account_file(
    str(credentials_file),
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# ツリー投稿: A列=1(同じ数字), B列=ポスト文, C列=日時, D列=時, E列=分
rows = [
    [1, POST_1, DATE_STR, HOUR, MINUTE],
    [1, POST_2, DATE_STR, HOUR, MINUTE],
]

for i, row in enumerate(rows):
    sheet.append_row(row, value_input_option="USER_ENTERED")
    time.sleep(1.2)
    print(f"  {'1投目' if i == 0 else '2投目'} 追加完了: {DATE_STR} {HOUR}:{MINUTE:02d}")

print("ツリー1件の転記を完了しました。")
