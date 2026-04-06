---
nexus: nexus-ai-chat-importer
plugin_version: "1.3.3"
provider: chatgpt
aliases: Untitled
conversation_id: 68978eb6-25ac-832a-a3c0-b527bb33e0bf
create_time: 2025-08-09T18:09:04.862Z
update_time: 2025-08-09T18:32:59.455Z
---

# Title: 初心者向け実行手順

Created: 2025/08/10 at 03:09:04
Last Updated: 2025/08/10 at 03:32:59
Chat URL: https://chatgpt.com/c/68978eb6-25ac-832a-a3c0-b527bb33e0bf


>[!nexus_user] **User** - 2025/08/10 at 03:09:04
> この内容をプログラミング初心者でも実行できるように説明して。
>
> 現状まとめ（共有用）
> 目的:
> 「恋愛系の有料 note」で、
> 過去24 時間以内に “買われています” が付いた記事 ✕ 価格 ¥980 以上 だけを自動収集し、CSV に追記する。
>
> 1. ざっくり全体像
> ┌─ 起点 URL（恋愛×有料検索） ─┐
>  │ 例: https://note.com/search?... │
>  └──────────────┬─────────────┘ 
>
> ▼ ① 候補収集（Playwright） 
> ├─ 検索カードをスクロール & <もっと見る> 
> ├─ 恋愛キーワードを含むカードだけ残す 
> └─ **カード内の金額が ¥980 以上** でないものは捨てる 
>
> ▼ ② 1st パス ── “買われています” 高速確認 
> ├─ 0.2 s スクロール → 2 – 4 s 待機 
> ├─ 無料判定 (ヘッダ価格なし & フォロー有) なら捨てる 
> └─ トーストが出た URL だけ通過 
>
> ▼ ③ 2nd パス ── 詳細チェック 
> ├─ ヘッダ価格を再抽出 (月額/¥300 は除外) 
> ├─ 恋愛キーワード再確認 ├─ “買われています” を再確認 
> └─ **条件をすべて満たせば CSV へ追記** 
>
> ▼ CSV: note_purchased_love_980plus.csv
>  (date, title, url, price, bought_24h)
>
> copy
> 2. 主な判定ロジック
> ▶︎ カード収集
> 何を見ているか：検索結果のカード文字列
>
> フィルタ内容
> - 恋愛系キーワード
> - 行に “月額 / /月 / メンバー / ¥300” 等があれば除外
> - 抽出した金額が ¥980 以上でないと除外
>
> ▶︎ 無料判定
> 何を見ているか：記事ヘッダ
>
> フィルタ内容
> ・ヘッダに価格が無い かつ “フォロー” ボタンが見える
> ・または 無料/¥0/0円 表記
>
> ▶︎ 価格抽出
> 何を見ているか：記事ヘッダ
>
> フィルタ内容
> ・月額/会員行を除外後、¥980 以上の最小値を採用
>
> ▶︎ 買われています
> 何を見ているか：トースト or 本文
>
> フィルタ内容
> ・“買われています / 過去24時間” の文字を検出
>
> 3. 設定ファイル / ディレクトリ
> note_playwright_scraper.py
> 本体スクリプト（v1.4.2-love）
>
> start_urls.txt
> 起点 URL を 1 行 1 件で列挙（無ければデフォルト 5 本）
>
> note_purchased_love_980plus.csv
> 収集結果を追記保存
>
> .venv/
> 任意。依存 (playwright, pandas) を入れた仮想環境
>
> note_profile
> /USE_PERSISTENT_CONTEXT=True で使うブラウザプロファイル
>
> ▶︎主要パラメータ（上部で編集可）
>
> MIN_PRICE = 980 # 価格しきい値 
>
> RAW_MAX_CANDIDATES = 220 # 1 周回あたりカード候補の上限 
>
> BOUGHT_WAIT_MS = (2000,4000) # “買われています” 待機範囲(ms) 
>
> HEADLESS = True # False にするとブラウザ可視
>
> copy
> 4. １分セットアップ & 実行手順
> # ① 依存インストール（1回だけ）
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium # 自動 DL
>
> # ② ディレクトリを Desktop に置く
> cd ~/Desktop
>
> # ③ (任意) 起点 URL を編集
> nano start_urls.txt # popular / recent など自由に追加
>
> # ④ 実行
> python3 note_playwright_scraper.py
>
> # ⑤ 結果確認
> tail -n 5 note_purchased_love_980plus.csv
>
> copy
> 5. 改良ポイント（必要に応じて）
> 件数が少ない
> - start_urls.txt に sort=recent を追加
> - RAW_MAX_CANDIDATES を増やす (例: 400)
> - BOUGHT_WAIT_MS を 3000–5000ms へ
>
> まだ ¥300 が混入
> - その URL を確認 → カード or ヘッダの DOM を基にフィルタ語を追加
>
> PC 負荷を下げたい
> - HEADLESS=True のまま
> - RAW_MAX_CANDIDATES を下げる (例: 120)
> - 1 日 2 回に分割実行
>
> ねこりんメモ
> note_playwright_scraper.py　の中身（8/3 19:30現在）
>
> やりたいことチャッピーに伝えて、書いてもらったので、中身は意味不明ですが、＃で補足してくれてます。
>
> あと、買われてます。はJSとかのポップアップだから、コードのこのテーブルから探してきね。とかは自分で指定しました
>
> cat > note_playwright_scraper.py <<'PY'
> #!/usr/bin/env python3
> # -*- coding: utf-8 -*-
> """
> note 『買われています』収集（Playwright版 / v1.4.2-love）
> - 対象: 恋愛系のみ（恋愛/婚活/復縁/マッチングアプリ/結婚 など）
> - 候補: 検索カード段階で【¥980以上】だけ通す（カード文字列から月額/会員系は除外）
> - 記事: ヘッダの価格が【¥980以上】＆『買われています』表示があるものだけ保存
> - 無料判定: ヘッダ価格が無い AND フォローボタンが見える（またはヘッダに 無料/¥0/0円/全体公開/誰でも読める）
> - 起点: start_urls.txt（無ければ 恋愛×popular の for_sale 検索）
> """
> import csv, os, re, time, random
> from datetime import datetime
> from typing import List, Optional, Dict
> from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
>
> CSV_PATH = "note_purchased_love_980plus.csv"
> START_URLS_TXT = "start_urls.txt"
>
> # ---- 設定 ----
> RAW_MAX_CANDIDATES = 220
> NAV_TIMEOUT_MS = 25_000
> WAIT_SETTLE_SEC = (1.0, 1.6)
> POLITE_SLEEP_SEC = (1.6, 3.0)
> BOUGHT_WAIT_MS = (2000, 4000)
>
> HEADLESS = True
> USE_PERSISTENT_CONTEXT = False
> USER_DATA_DIR = "note_profile"
>
> MIN_PRICE = 980
> STRICT_CARD_PRICE = True
>
> LOVE_KWS = ["恋愛","婚活","結婚","出会い","復縁","片思い","告白","マッチングアプリ","彼氏","彼女","カップル","パートナー","恋活"]
> NEGATIVE_FREE = ["無料","全体公開","誰でも読める","¥0","0円","¥ 0"]
>
> def load_start_urls() -> List[str]:
>  if os.path.exists(START_URLS_TXT):
>  with open(START_URLS_TXT, "r", encoding="utf-8") as f:
>  urls = [u.strip() for u in f if u.strip() and not u.startswith("#")]
>  if urls:
>  return urls
>  return [
>  "https://note.com/search?context=note_for_sale&q=恋愛&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=婚活&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=復縁&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=結婚&sort=popular",
>  ]
>
> def unique(seq):
>  seen=set(); out=[]
>  for x in seq:
>  if x not in seen:
>  out.append(x); seen.add(x)
>  return out
>
> def _polite_wait(): time.sleep(random.uniform(*POLITE_SLEEP_SEC))
>
> def _lazy_scroll(page, steps:int=4):
>  for _ in range(steps):
>  page.evaluate("window.scrollBy(0, Math.max(400, window.innerHeight*0.7));")
>  time.sleep(random.uniform(*WAIT_SETTLE_SEC))
>
> def _try_click_more(page):
>  sels = ["text=もっと見る", "text=さらに表示", "text=もっとみる", "button:has-text('もっと')", "a:has-text('もっと')"]
>  for sel in sels:
>  try:
>  if page.locator(sel).first.is_visible(timeout=800):
>  page.locator(sel).first.click(timeout=800)
>  return True
>  except Exception:
>  pass
>  return False
>
> def _anchor_href(page, i:int) -> str:
>  try:
>  href = page.locator("a[href*='/n/']").nth(i).get_attribute("href") or ""
>  if href.startswith("/"):
>  href = "https://note.com" + href
>  return href.split("?")[0]
>  except Exception:
>  return ""
>
> def _anchor_card_text(page, i:int) -> str:
>  js = """
>  (el) => {
>  const card = el.closest('article') || el.closest('[role="article"]') || el.parentElement;
>  return (card ? card.innerText : el.innerText) || '';
>  }
>  """
>  try:
>  return page.locator("a[href*='/n/']").nth(i).evaluate(js) or ""
>  except Exception:
>  return ""
>
> def _topic_match(text: str) -> bool:
>  t = (text or "")
>  return any(kw in t for kw in LOVE_KWS)
>
> def _extract_price_from_card_text(text: str) -> Optional[int]:
>  if not text: return None
>  monthly_tokens = ["月額","/月","月/","／月","membership","メンバー","メンバーシップ","年額","/年","年/"]
>  lines = [ln for ln in text.splitlines() if ln.strip()]
>  cands = []
>  for ln in lines:
>  ln_nospace = ln.replace(" ", "")
>  if any(tok in ln_nospace for tok in monthly_tokens):
>  continue
>  for m in re.finditer(r"¥\s*(\d{1,3}(?:,\d{3})*)", ln):
>  val = int(m.group(1).replace(",", ""))
>  if val >= MIN_PRICE:
>  cands.append(val)
>  return min(cands) if cands else None
>
> def collect_raw_candidates(page, start_urls: List[str]) -> List[str]:
>  urls=[]
>  for su in start_urls:
>  try:
>  page.goto(su, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  _polite_wait()
>  stable=0; last=0
>  for _ in range(24):
>  try: cnt = page.locator("a[href*='/n/']").count()
>  except Exception: cnt = 0
>  if cnt >= 200: break
>  clicked = _try_click_more(page)
>  _lazy_scroll(page, steps=3)
>  _polite_wait()
>  try: new_cnt = page.locator("a[href*='/n/']").count()
>  except Exception: new_cnt = cnt
>  if new_cnt <= last and not clicked: stable += 1
>  else: stable = 0
>  last = new_cnt
>  if stable >= 3: break
>  anchors = page.locator("a[href*='/n/']")
>  for i in range(anchors.count()):
>  href = _anchor_href(page, i)
>  if not (href.startswith("https://note.com") and "/n/" in href):
>  continue
>  card_text = _anchor_card_text(page, i)
>  if not _topic_match(card_text):
>  continue
>  if STRICT_CARD_PRICE:
>  _cp = _extract_price_from_card_text(card_text)
>  if _cp is None or _cp < MIN_PRICE:
>  continue
>  urls.append(href)
>  except PWTimeoutError:
>  print(f"⚠️ タイムアウト: {su}")
>  except Exception as e:
>  print(f"⚠️ 起点取得エラー: {su} -> {e}")
>  urls = unique(urls)
>  if len(urls) > RAW_MAX_CANDIDATES: urls = urls[:RAW_MAX_CANDIDATES]
>  return urls
>
> def _has_follow_button(page) -> bool:
>  try:
>  btn = page.locator(
>  "div[class*='o-noteContentHeader__followButton'] .a-button, "
>  ".m-follow .a-button, "
>  "button:has-text('フォロー')"
>  )
>  return btn.count() > 0 and btn.first.is_visible(timeout=1200)
>  except Exception:
>  return False
>
> def _extract_price_from_header(page) -> Optional[int]:
>  try:
>  status = page.locator("div[class*='o-noteContentHeader__status']")
>  if status.count() == 0: return None
>  txt = status.inner_text(timeout=1500) or ""
>  monthly_tokens = ["月額", "/月", "月/", "／月", "membership", "メンバー", "メンバーシップ", "年額", "/年", "年/"]
>  lines = [ln for ln in (txt.splitlines()) if ln.strip()]
>  cands = []
>  for line in lines:
>  ln = line.replace(" ", "")
>  if any(tok in ln for tok in monthly_tokens): continue
>  for m in re.finditer(r"¥\s*(\d{1,3}(?:,\d{3})*)", line):
>  val = int(m.group(1).replace(",", ""))
>  if val >= MIN_PRICE: cands.append(val)
>  if not cands: return None
>  return min(cands)
>  except Exception:
>  return None
>
> def _is_free_in_header(page) -> bool:
>  try:
>  header = page.locator("div[class*='o-noteContentHeader__status']")
>  if header.count() > 0:
>  txt = header.inner_text(timeout=1200) or ""
>  if any(k in txt for k in ["無料","全体公開","誰でも読める"]) or re.search(r"¥\s*0|0\s*円", txt):
>  return True
>  except Exception:
>  pass
>  price = _extract_price_from_header(page)
>  if price is None and _has_follow_button(page):
>  return True
>  return False
>
> def _has_bought_quick(context, url: str) -> bool:
>  page = context.new_page()
>  try:
>  page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  page.evaluate("window.scrollBy(0, 180);")
>  if _is_free_in_header(page): return False
>  price = _extract_price_from_header(page)
>  if price is None or price < MIN_PRICE: return False
>  try:
>  qt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=800) or "")
>  except Exception: qt = page.title() or ""
>  if not any(kw in qt for kw in LOVE_KWS): return False
>  end_time = time.time() + random.randint(*BOUGHT_WAIT_MS)/1000
>  while time.time() < end_time:
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=300): return True
>  except Exception: pass
>  try:
>  bt = page.locator("body").inner_text(timeout=500)
>  if any(k in bt for k in ["買われています","買われている","過去24時間"]): return True
>  except Exception: pass
>  time.sleep(0.15)
>  return False
>  except Exception:
>  return False
>  finally:
>  try: page.close()
>  except: pass
>
> def detail_check_and_save(context, url: str) -> Optional[Dict]:
>  page = context.new_page()
>  try:
>  page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  page.evaluate("window.scrollBy(0, 220);")
>  time.sleep(random.uniform(*WAIT_SETTLE_SEC))
>  if _is_free_in_header(page):
>  print(" ✗ SKIP: free_header_follow")
>  return None
>  price = _extract_price_from_header(page)
>  if price is None or price < MIN_PRICE:
>  print(" ✗ SKIP: price<980_or_header_missing")
>  return None
>  try:
>  txt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=1500) or "")
>  except Exception: txt = page.title() or ""
>  if not any(kw in txt for kw in LOVE_KWS):
>  print(" ✗ SKIP: out_of_topic")
>  return None
>  bought = False
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=1000): bought = True
>  except Exception: pass
>  if not bought and any(k in txt for k in ["買われています","買われている","過去24時間"]): bought = True
>  if not bought:
>  print(" ✗ SKIP: no_bought")
>  return None
>  title = (page.title() or "").strip()
>  row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, url, str(price), "True"]
>  if int(price) < MIN_PRICE:
>  print(f" ✗ SKIP: final_guard price={price} < {MIN_PRICE}")
>  return None
>  with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
>  csv.writer(f).writerow(row)
>  print(" ✓ SAVE")
>  return {"date": row[0], "title": title, "url": url, "price": str(price), "bought_24h": "True"}
>  except PWTimeoutError:
>  print(f"⏳ 記事タイムアウト: {url}")
>  return None
>  except Exception as e:
>  print(f"⚠️ 記事処理エラー: {url} -> {e}")
>  return None
>  finally:
>  try: page.close()
>  except: pass
>  _polite_wait()
>
> def ensure_csv_header(path: str):
>  if not os.path.exists(path):
>  with open(path, "w", encoding="utf-8", newline="") as f:
>  csv.writer(f).writerow(["date","title","url","price","bought_24h"])
>
> def already_recorded(path: str, url: str) -> bool:
>  if not os.path.exists(path): return False
>  try:
>  with open(path, "r", encoding="utf-8") as f:
>  for line in f:
>  if url in line: return True
>  except: return False
>  return False
>
> def run():
>  print("🎯 note『買われています』収集（Playwright版 / v1.4.2-love）")
>  start_urls = load_start_urls()
>  print(f"🧭 起点: {start_urls}")
>  ensure_csv_header(CSV_PATH)
>  with sync_playwright() as p:
>  if USE_PERSISTENT_CONTEXT:
>  context = p.chromium.launch_persistent_context(
>  USER_DATA_DIR, headless=HEADLESS,
>  viewport={"width":1280,"height":900}, locale="ja-JP"
>  )
>  else:
>  browser = p.chromium.launch(headless=HEADLESS)
>  context = browser.new_context(viewport={"width":1280,"height":900}, locale="ja-JP")
>  page = context.new_page()
>  try:
>  raw_candidates = collect_raw_candidates(page, start_urls)
>  print(f"🔎 生候補URL（カード¥980+ & トピック適合）: {len(raw_candidates)}件")
>  bought_urls = []
>  for idx, url in enumerate(raw_candidates, 1):
>  if already_recorded(CSV_PATH, url): continue
>  print(f" [screen {idx}/{len(raw_candidates)}] {url}")
>  if _has_bought_quick(context, url):
>  bought_urls.append(url)
>  _polite_wait()
>  print(f"📌 『買われています』一次通過: {len(bought_urls)}件")
>  saved=0
>  for jdx, url in enumerate(bought_urls, 1):
>  print(f" [detail {jdx}/{len(bought_urls)}] {url}")
>  info = detail_check_and_save(context, url)
>  if info: saved += 1
>  print(f"✅ 収集完了: {saved}件 追加")
>  print(f"📦 出力: {os.path.abspath(CSV_PATH)}")
>  finally:
>  try: page.close()
>  except: pass
>
> copy
>
> 追記
>
> 買われてますを出してるcss特定したので、より指示を厳密にできるようになった↓
>
> ---- 『買われています』バッジ検出 ----
> def _has_bought_badge(page, timeout_ms=800) -> bool:
> selectors = [
> ".m-purchasedWithinLast24HoursBalloon", # ご指定のクラス
> "[class*='purchasedWithinLast24Hours']", # 命名揺れ対策
> "[data-testid='purchasedWithinLast24Hours']",
> "[data-testid='purchased-within-last-24-hours']",
> ]
<!-- UID: 60587bf5-9cda-46a4-b978-4a1bb96dc053 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:09:05
> 了解。いただいた仕様を、Mac（macOS）で「プログラミング初心者でも迷わず動かせる」手順に落とし込みます。作業は上から順に進めれば大丈夫です。
>
> # 0. これが何をしているか（超ざっくり）
> noteの検索画面から「恋愛系」かつ「価格980円以上」の候補だけ拾い、記事を開いて「過去24時間に買われています」表示の有無をチェックし、条件を満たした記事だけをCSVに追記します。 
> イメージとしては、掃除機に三重フィルターが付いていて「恋愛系」→「980円以上」→「買われています」の順にゴミではなく“欲しい記事だけ”を残す感じです。
>
> 出力CSVの列は次の5つです： 
> `date, title, url, price, bought_24h`
>
> ---
>
> # 1. 一度だけの準備（約5〜10分）
>
> ① ターミナルを開く 
> Launchpad →「ターミナル」を起動。
>
> ② 作業用フォルダを作る
> ```bash
> cd ~/Desktop
> mkdir note_love_scraper && cd note_love_scraper
> ```
>
> ③ スクリプト・設定ファイルを置く 
> - もらっている `note_playwright_scraper.py` を、このフォルダに保存します。
> - 起点URLを書ける `start_urls.txt` を用意（空でもOK）:
> ```bash
> printf "https://note.com/search?context=note_for_sale&q=恋愛&sort=popular\n" > start_urls.txt
> ```
>
> ④ 仮想環境を作って入る（トラブルが減ります）
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> ```
> 以後、このフォルダで作業するときは毎回 `source .venv/bin/activate` を実行してから使います。やめるときは `deactivate`。
>
> ⑤ 必要ライブラリを入れる（最初の1回だけ）
> ```bash
> python3 -m pip install --upgrade pip
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium
> ```
> ここで数分待つことがあります。完了すれば準備OK。
>
> ---
>
> # 2. まずは“見える”状態で試走する（初回おすすめ）
>
> 最初は動作が分かるように、ブラウザを表示して確認します。
>
> 1) スクリプト上部の設定を一時変更 
> - `HEADLESS = False` にする（ブラウザが見える）
> - もしログインが必要なら `USE_PERSISTENT_CONTEXT = True` にし初回だけアカウントでログイン。以後は `note_profile/` が使われます。
>
> 2) 実行
> ```bash
> python3 note_playwright_scraper.py
> ```
>
> 3) 画面の見え方
> - 検索一覧でスクロール・「もっと見る」クリック
> - 各カードから恋愛キーワードと価格を確認
> - 記事を開いてヘッダ価格・「買われています」表示を確認
> - 条件OKな記事が見つかると `note_purchased_love_980plus.csv` に追記されます
>
> 4) 出力の確認
> ```bash
> tail -n 5 note_purchased_love_980plus.csv
> ```
>
> 問題なく動いたら、次回以降は `HEADLESS = True` に戻すと静かに速く回せます。
>
> ---
>
> # 3. よく使う操作（編集ポイント）
>
> ■ 起点URLを増やす 
> `start_urls.txt` を開いて、1行1URLで追記します。例（最近順・キーワード分散）:
> ```
> https://note.com/search?context=note_for_sale&q=恋愛&sort=recent
> https://note.com/search?context=note_for_sale&q=復縁&sort=recent
> https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=recent
> ```
>
> ■ 主なパラメータ（スクリプト上部）
> - `MIN_PRICE = 980` … 価格の下限
> - `RAW_MAX_CANDIDATES = 220` … 1周で検査する候補URL上限
> - `BOUGHT_WAIT_MS = (2000, 4000)` … 「買われています」待ち時間レンジ
> - `HEADLESS = True/False` … ブラウザ表示のON/OFF
> - `USE_PERSISTENT_CONTEXT = True` … ログイン継続したい場合はTrue（`note_profile/`使用）
>
> 変更したら保存して、もう一度 `python3 note_playwright_scraper.py` で実行します。
>
> ---
>
> # 4. 「買われています」バッジをCSSで厳密検出する（任意の精度アップ）
>
> 追記でいただいたクラス選択子に対応するなら、関数を追加して使います。
>
> 1) スクリプトの関数群の近くに、これを追記
> ```python
> def _has_bought_badge(page, timeout_ms=800) -> bool:
>  selectors = [
>  ".m-purchasedWithinLast24HoursBalloon",
>  "[class*='purchasedWithinLast24Hours']",
>  "[data-testid='purchasedWithinLast24Hours']",
>  "[data-testid='purchased-within-last-24-hours']",
>  ]
>  deadline = time.time() + (timeout_ms/1000)
>  while time.time() < deadline:
>  for sel in selectors:
>  try:
>  loc = page.locator(sel)
>  if loc.count() > 0 and loc.first.is_visible(timeout=200):
>  return True
>  except Exception:
>  pass
>  time.sleep(0.05)
>  return False
> ```
>
> 2) 既存の判定箇所で使う 
> - `detail_check_and_save()` 内の `bought` 判定の最初に:
> ```python
> bought = _has_bought_badge(page, timeout_ms=800)
> ```
> - それで `True` なら保存処理へ。`False` のときだけ従来のテキスト検出（フォールバック）に回す、という順番にすると誤検出が減ります。
>
> ---
>
> # 5. うまくいかないとき（代表的な原因と対処）
>
> 1) `playwright._impl... Timeout` が出る 
> - 回線が遅い/サイトが重いと起きます。`NAV_TIMEOUT_MS` を 35_000 に上げる、`HEADLESS=False` で様子を見る、起点URLを少なくする。
>
> 2) CSVに何も追加されない 
> - そもそも条件に合う記事が少ない日があります。`start_urls.txt` に `sort=recent` のURLを足す。`LOVE_KWS` に語を足す（例:「デート」「失恋」など）。 
> - 価格しきい値が厳しければ `MIN_PRICE=800` などに下げてテスト（最終的に980に戻す）。
>
> 3) 会員制の月額記事が混ざる 
> - 既に月額/会員系の単語は除外していますが、漏れたら `monthly_tokens` に語を追加。ヘッダ側・カード側の両方に入れてください。
>
> 4) ログインが必要で弾かれる 
> - `USE_PERSISTENT_CONTEXT=True` にして実行→一度ブラウザでログイン→以後はログイン状態が `note_profile/` に保存されます。
>
> 5) Macが熱い/遅い 
> - `HEADLESS=True` のまま、`RAW_MAX_CANDIDATES` を 120 へ下げる、実行を朝晩2回に分ける。
>
> ---
>
> # 6. 日次で自動化したい（任意）
>
> ## 6-1. 手動で1日2回回す（簡単）
> 朝と夜に、フォルダへ行って実行するだけです。
> ```bash
> cd ~/Desktop/note_love_scraper
> source .venv/bin/activate
> python3 note_playwright_scraper.py
> ```
>
> ## 6-2. 完全自動化（launchd）
> crontabよりmacOS標準のlaunchdが安定です。最短ルートだけ記します。
>
> 1) シェルを作る
> ```bash
> cd ~/Desktop/note_love_scraper
> printf '#!/bin/bash\nsource %s/.venv/bin/activate\npython3 %s/note_playwright_scraper.py\n' "$(pwd)" "$(pwd)" > run_scraper.sh
> chmod +x run_scraper.sh
> ```
>
> 2) ジョブ定義（例: 9時・21時に実行）
> `~/Library/LaunchAgents/com.mimi.note.scraper.plist` を作成して次を保存:
> ```xml
> <?xml version="1.0" encoding="UTF-8"?>
> <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
> <plist version="1.0">
>  <dict>
>  <key>Label</key><string>com.mimi.note.scraper</string>
>  <key>ProgramArguments</key>
>  <array><string>/bin/bash</string><string>-lc</string><string>cd ~/Desktop/note_love_scraper && ./run_scraper.sh</string></array>
>  <key>StartCalendarInterval</key>
>  <array>
>  <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
>  <dict><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
>  </array>
>  <key>StandardOutPath</key><string>~/Desktop/note_love_scraper/launchd.out.log</string>
>  <key>StandardErrorPath</key><string>~/Desktop/note_love_scraper/launchd.err.log</string>
>  <key>RunAtLoad</key><true/>
>  </dict>
> </plist>
> ```
>
> 3) 読み込み
> ```bash
> launchctl load ~/Library/LaunchAgents/com.mimi.note.scraper.plist
> launchctl list | grep com.mimi.note.scraper
> ```
> 止めたいときは `launchctl unload ~/Library/LaunchAgents/com.mimi.note.scraper.plist`。
>
> ---
>
> # 7. 品質をさらに上げる小ワザ
>
> - 取得件数が少ない日は、`LOVE_KWS` に「デート」「同棲」「失恋」「遠距離」「喧嘩」「婚約」「夫婦」などを追加。
> - 誤検出が続くURLは、一時的にブラックリストにしてスキップするロジックを足せます（URLの前方一致で除外）。
> - 保存前にCSV重複チェックを行っていますが、長期運用ならURL→ハッシュの簡易DB化も有効です。
>
> ---
>
> # 8. 実行の最短チートシート（コピペ用）
>
> 初回だけ:
> ```bash
> cd ~/Desktop
> mkdir note_love_scraper && cd note_love_scraper
> python3 -m venv .venv && source .venv/bin/activate
> python3 -m pip install --upgrade pip
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium
> printf "https://note.com/search?context=note_for_sale&q=恋愛&sort=recent\n" > start_urls.txt
> # ここで note_playwright_scraper.py をこのフォルダに保存
> python3 note_playwright_scraper.py
> tail -n 5 note_purchased_love_980plus.csv
> ```
>
> 2回目以降（毎回）:
> ```bash
> cd ~/Desktop/note_love_scraper
> source .venv/bin/activate
> python3 note_playwright_scraper.py
> ```
>
> ---
>
> # 9. 最後に（要点まとめ）
> - まずは仮想環境を作って Playwright と Chromium を入れる。 
> - `HEADLESS=False` で初回は目視確認→問題なければ `HEADLESS=True` に戻す。 
> - 取りこぼしは `start_urls.txt` と `LOVE_KWS` の拡充、誤検出は月額ワードやCSSバッジ検出で抑える。 
> - 自動化は `launchd` を使えば朝夕に安定運転できる。 
>
> 不明点があれば、今どのステップで止まっているか（エラーメッセージ含め）を教えてください。最短で解消します。
<!-- UID: 6eadebbc-0ef5-42ae-896e-67720315b979 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:11:59
> これはどこに追加すべき？
>
> def _has_bought_badge(page, timeout_ms=800) -> bool:
>  selectors = [
>  ".m-purchasedWithinLast24HoursBalloon",
>  "[class*='purchasedWithinLast24Hours']",
>  "[data-testid='purchasedWithinLast24Hours']",
>  "[data-testid='purchased-within-last-24-hours']",
>  ]
>  deadline = time.time() + (timeout_ms/1000)
>  while time.time() < deadline:
>  for sel in selectors:
>  try:
>  loc = page.locator(sel)
>  if loc.count() > 0 and loc.first.is_visible(timeout=200):
>  return True
>  except Exception:
>  pass
>  time.sleep(0.05)
>  return False
<!-- UID: b40d24cd-e252-4012-a8f3-391b13ed738c -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:12:01
> 結論：その関数は「小さい判定ユーティリティ群」と並べて置くのが安全です。あなたのファイル構成だと、次の場所がベストです。
>
> 1) 追加場所（関数本体）
> - `_is_free_in_header(page)` の直後、`_has_bought_quick(...)` より前。
> - ここに置くと、後続の `_has_bought_quick` と `detail_check_and_save` の両方から呼べます。
>
> 具体的な挿入位置（抜粋）：
> ```python
> def _is_free_in_header(page) -> bool:
>  ...
>  return False
>
> # ここに追加 ↓↓↓
> def _has_bought_badge(page, timeout_ms=800) -> bool:
>  selectors = [
>  ".m-purchasedWithinLast24HoursBalloon",
>  "[class*='purchasedWithinLast24Hours']",
>  "[data-testid='purchasedWithinLast24Hours']",
>  "[data-testid='purchased-within-last-24-hours']",
>  ]
>  deadline = time.time() + (timeout_ms/1000)
>  while time.time() < deadline:
>  for sel in selectors:
>  try:
>  loc = page.locator(sel)
>  if loc.count() > 0 and loc.first.is_visible(timeout=200):
>  return True
>  except Exception:
>  pass
>  time.sleep(0.05)
>  return False
> # ここまで追加 ↑↑↑
>
> def _has_bought_quick(context, url: str) -> bool:
>  ...
> ```
>
> 2) 呼び出し箇所の差し替え（推奨）
> テキスト探索より先にCSSバッジで即判定→ダメなら従来のテキスト検出にフォールバック、という順序にすると誤検出が減ります。
>
> `_has_bought_quick` の中：
> ```diff
>  def _has_bought_quick(context, url: str) -> bool:
>  page = context.new_page()
>  try:
>  page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  page.evaluate("window.scrollBy(0, 180);")
>  if _is_free_in_header(page): return False
>  price = _extract_price_from_header(page)
>  if price is None or price < MIN_PRICE: return False
> - try:
> - qt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=800) or "")
> - except Exception: qt = page.title() or ""
> - if not any(kw in qt for kw in LOVE_KWS): return False
> + # まずCSSバッジで高速判定
> + if _has_bought_badge(page, timeout_ms=800):
> + return True
> +
> + # バッジが無い場合はテキスト検出にフォールバック
> + try:
> + qt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=800) or "")
> + except Exception:
> + qt = page.title() or ""
> + if not any(kw in qt for kw in LOVE_KWS):
> + return False
> ```
>
> `detail_check_and_save` の中：
> ```diff
> - bought = False
> - try:
> - loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
> - if loc and loc.first.is_visible(timeout=1000): bought = True
> - except Exception: pass
> - if not bought and any(k in txt for k in ["買われています","買われている","過去24時間"]): bought = True
> + # まずCSSバッジ
> + bought = _has_bought_badge(page, timeout_ms=800)
> + # なければテキスト検出
> + if not bought:
> + try:
> + loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
> + if loc and loc.first.is_visible(timeout=1000):
> + bought = True
> + except Exception:
> + pass
> + if not bought and any(k in txt for k in ["買われています","買われている","過去24時間"]):
> + bought = True
> ```
>
> 3) インポートについて
> この関数は `time` を使うので、冒頭の `import` に `import time` が含まれていればOK（既に入っています）。追加のインポートは不要です。
>
> 4) 小さな確認ポイント
> - 初回は `HEADLESS=False` で実行し、対象記事を開いたときにバッジが実際に見えているか確認。
> - note側のDOMがA/Bテストで変わることがあるため、セレクタ配列は複数残しておくのが安全です（現在の配列は良い構成です）。
>
> 要点まとめ
> - 置き場所は `_is_free_in_header` の直後が最適。
> - `quick` と `detail` の両パスで「CSS→テキスト」の順で判定に使う。 
> - 追加のライブラリは不要、`time` だけ確認すればOK。
<!-- UID: 659ad639-aeb5-47a5-b3cc-1af3e1fed9e2 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:15:59
> Traceback (most recent call last):
>  File "/Users/sasaki/Desktop/note_love_scraper/note_playwright_scraper.py", line 1, in <module>
>  cat > note_playwright_scraper.py <<'PY'
>  ^^^
> NameError: name 'cat' is not defined
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper %
<!-- UID: 0f9e8355-0933-4540-9ae3-66d4a6eca3b1 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:16:00
> これはエラーというより、 
> シェル（ターミナル）用のコマンドを**Pythonの中で実行しちゃった**ことが原因です。
>
> `cat > note_playwright_scraper.py <<'PY'` はターミナルでファイルを作るためのコマンドなので、 
> Pythonスクリプトとして実行すると「catって何？」となって NameError になります。
>
> ---
>
> ## 解決方法
> 1. **ターミナルに戻す** 
>  その行（`cat > ... <<'PY'` 〜 `PY` のブロック）はPythonじゃなくて、ターミナルに直接貼り付けて実行します。
>
>  例:
>  ```bash
>  cat > note_playwright_scraper.py <<'PY'
>  # ここにPythonのコード本文…
>  PY
>  ```
>
>  そうすると `note_playwright_scraper.py` というファイルにコードが保存されます。
>
> 2. もしもうPythonコードを別の方法で保存できるなら、 
>  普通にエディタ（VSCode、メモ帳、テキストエディット等）で `note_playwright_scraper.py` を作成して貼り付け保存すればOKです。
>
> ---
>
> もしこのまま進めるなら、 
> 私から**完成済みの `note_playwright_scraper.py` 全文**を渡して、それを直接ファイルに貼って保存する方法がおすすめです。 
> そしたらターミナルでは単に
>
> ```bash
> python3 note_playwright_scraper.py
> ```
>
> で動きます。
>
> ---
>
> 必要なら、バッジ検出追加済みの最新版コードをまとめて渡しますが、どうしますか？
<!-- UID: 44935a5e-f40b-420f-b472-1b92366ee941 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:17:54
> 上手く動作しません・・・
<!-- UID: 01a6ab39-74ec-4d8c-b025-ae93febe3715 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:17:57
> 了解。まず“どこで”止まっているかを特定しましょう。下の順にチェックすれば、原因をほぼ必ず潰せます。必要なコマンドはそのままコピペでOKです。
>
> # 1) Playwright自体が動くかの健全性チェック
> ターミナルでプロジェクトフォルダに入り、仮想環境を有効化してから最小テストを回します。
> ```bash
> cd ~/Desktop/note_love_scraper
> source .venv/bin/activate
> python3 - <<'PY'
> from playwright.sync_api import sync_playwright
> with sync_playwright() as p:
>  b = p.chromium.launch(headless=False)
>  page = b.new_page()
>  page.goto("https://example.com", timeout=30000)
>  print("TITLE:", page.title())
>  b.close()
> PY
> ```
> 期待値: ブラウザが開き、タイトルが `Example Domain` と表示されます。 
> 失敗する場合:
> - `ModuleNotFoundError: playwright` → 仮想環境内で `pip install playwright` をやり直す
> - タイムアウト系 → ネットワークかセキュリティソフトを確認、`python3 -m playwright install chromium` を再実行
>
> # 2) スクリプトの“保存ミス”を除外
> 過去の NameError は「シェル用の `cat <<'PY'` をPythonに入れた」ことが原因でした。ファイル頭にその文字列が残っていないか確認します。
> ```bash
> sed -n '1,30p' note_playwright_scraper.py
> ```
> 先頭行が `#!/usr/bin/env python3` から始まり、`cat > ... <<'PY'` のような行が1つも無いことを確認してください。あれば削除して保存。
>
> # 3) 初回は“見える化”して原因を目視
> 設定を一時変更して可視モードで動かします。エディタで `note_playwright_scraper.py` 冒頭の設定を次のように。
> ```
> HEADLESS = False
> USE_PERSISTENT_CONTEXT = True
> ```
> 実行:
> ```bash
> python3 note_playwright_scraper.py
> ```
> ポイント
> - ログインを求められたら、noteにログイン。以後は `note_profile/` に状態保存。
> - 検索一覧→「もっと見る」→カード抽出→記事判定の流れが見えるか確認。
>
> # 4) 典型エラー別の対処
>
> ■ 4-1. インポートや未定義エラー
> - `NameError: cat` → 1つ上の「保存ミス」。削除して再実行
> - `ImportError: cannot import name 'sync_playwright'` → `pip show playwright` でインストール確認。入っていなければ再インストール
> ```bash
> python3 -m pip install --upgrade pip
> python3 -m pip install --force-reinstall playwright pandas
> python3 -m playwright install chromium
> ```
>
> ■ 4-2. タイムアウトや要素が見つからない
> - `TimeoutError` が多発 → 待ち時間を延ばす
>  - `NAV_TIMEOUT_MS = 35000`
>  - `BOUGHT_WAIT_MS = (3000, 6000)`
> - 「もっと見る」を押せていない → 画面が英語UI等で文言ズレの可能性。`_try_click_more` のセレクタに `text=More` を1行追加
> ```python
> sels = ["text=もっと見る", "text=さらに表示", "text=もっとみる", "button:has-text('もっと')", "a:has-text('もっと')", "text=More"]
> ```
> - スクロール不足 → `_lazy_scroll(page, steps=6)` に増やす
>
> ■ 4-3. 収集ゼロ件（CSVが増えない）
> - まず可視で見て、検索一覧に「恋愛系×¥980以上」が十分並んでいるか確認
> - `start_urls.txt` に recent を追加
> ```
> https://note.com/search?context=note_for_sale&q=恋愛&sort=recent
> https://note.com/search?context=note_for_sale&q=復縁&sort=recent
> https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=recent
> ```
> - キーワードを増やす（`LOVE_KWS` に「デート」「失恋」「同棲」「喧嘩」「夫婦」「婚約」など）
> - 一時的に `STRICT_CARD_PRICE=False` にして候補を広げ、後段のヘッダ価格で絞る。原因切り分けに有効
>
> ■ 4-4. 「買われています」検出が安定しない
> - 追加してもらったCSSバッジ関数を必ず“テキスト検出より先”に使う
>  - `_has_bought_quick` と `detail_check_and_save` の両方で、最初に:
>  ```python
>  bought = _has_bought_badge(page, timeout_ms=1000)
>  ```
>  - ダメなら既存のテキスト検出にフォールバック
> - スクロールしてから待つ
>  - `_has_bought_quick` で `page.evaluate("window.scrollBy(0, 250);")` の直後に `time.sleep(0.6)` を挿入
> - ビジビリティが遅いページ対策
>  - `timeout_ms=1500` に一時的に拡大
>
> # 5) ログを濃くして原因を絞る
> PlaywrightのAPIログを出して動きを追います。
> ```bash
> DEBUG=pw:api python3 note_playwright_scraper.py 2> debug.log
> ```
> あるいはインスペクタで手動確認:
> ```bash
> PWDEBUG=1 python3 note_playwright_scraper.py
> ```
> 失敗箇所の直前ログを見れば、セレクタ不一致か、待ち不足かが分かります。
>
> # 6) スクリプト内の“差分”チェック（重要）
> あなたの最新版に以下3点が入っているか確認してください。
>
> ① バッジ関数が `_is_free_in_header` の直後に定義されている 
> ② `_has_bought_quick` の冒頭判定順が「バッジ → テキスト」になっている 
> ③ `detail_check_and_save` でも同様に「バッジ優先」にしている
>
> 差分の最小パッチ例（抜粋）:
> ```python
> # 1) まずCSSバッジを試す
> bought = _has_bought_badge(page, timeout_ms=1000)
>
> # 2) 無ければテキスト
> if not bought:
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=1000):
>  bought = True
>  except Exception:
>  pass
> if not bought and any(k in txt for k in ["買われています","買われている","過去24時間"]):
>  bought = True
> ```
>
> # 7) どうしても動かない時の“クリーン再構築”
> ```bash
> cd ~/Desktop
> rm -rf note_love_scraper
> mkdir note_love_scraper && cd note_love_scraper
> python3 -m venv .venv && source .venv/bin/activate
> python3 -m pip install --upgrade pip
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium
> printf "https://note.com/search?context=note_for_sale&q=恋愛&sort=recent\n" > start_urls.txt
> # エディタで note_playwright_scraper.py を貼り付け保存（最新版）
> python3 note_playwright_scraper.py
> ```
>
> ――
>
> ここまで試してもダメなら、表示されたエラー文の最初の3〜5行（Tracebackの先頭部分）と、止まる“段階”（検索一覧/記事オープン/保存直前など）を教えてください。こちらで該当箇所をピンポイント修正します。
<!-- UID: 1a424fc1-4f64-471d-ba03-891b3518acea -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:18:55
> ごめんよくわかりません。とりあえずもっかい最初から、簡単に最短で実行できるように教えて欲しい
<!-- UID: b6467846-89e3-4bd1-8792-69749faa7196 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:18:56
> OK、じゃあ「プログラミング初心者がMacで最短で動かす」手順だけに絞って説明します。 
> 余計な設定は全部省きます。 
>
> ---
>
> ## 1. フォルダを作る
> ターミナルで：
> ```bash
> cd ~/Desktop
> mkdir note_love_scraper
> cd note_love_scraper
> ```
>
> ---
>
> ## 2. Python環境を作る
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> ```
>
> ---
>
> ## 3. 必要なライブラリを入れる
> ```bash
> pip install --upgrade pip
> pip install playwright pandas
> playwright install chromium
> ```
>
> ---
>
> ## 4. スクリプトファイルを作る
> ターミナルで：
> ```bash
> nano note_playwright_scraper.py
> ```
> 開いた画面に**もらったPythonコード全文**をコピペして、 
> `Ctrl + O` → Enter → `Ctrl + X` で保存して閉じます。
>
> ---
>
> ## 5. 実行
> ```bash
> python3 note_playwright_scraper.py
> ```
>
> ---
>
> ## 6. 結果を見る
> ```bash
> tail -n 5 note_purchased_love_980plus.csv
> ```
> （最新5件が見えます）
>
> ---
>
> この流れなら、 
> 「ターミナルにコマンド貼る → エディタにコード貼る → 実行する」だけで動くはずです。 
>
> もしこれでエラーが出たら、出たエラー文をそのまま貼ってくれれば、その箇所だけ直す説明をします。 
>
> ---
>
> このやり方でコード貼り付けるところから一緒にやりますか？ 
> そうすれば確実に動くようにできます。
<!-- UID: f911b967-1bc1-47fe-a7ad-061b23410191 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:22:45
> Traceback (most recent call last):
>  File "/Users/sasaki/Desktop/note_love_scraper/note_playwright_scraper.py", line 1, in <module>
>  cat > note_playwright_scraper.py <<'PY'
>  ^^^
> NameError: name 'cat' is not defined
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper %
<!-- UID: 6077e427-1455-4e73-bc97-da368aee8044 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:22:46
> このエラーは、 
> `note_playwright_scraper.py` の1行目に「`cat > note_playwright_scraper.py <<'PY'`」という **ターミナル用コマンド** が残ってしまっているせいです。 
> Pythonはそれを知らないので「NameError」になります。
>
> ---
>
> ## 修正方法
> 1. ターミナルでファイルを開く
> ```bash
> nano note_playwright_scraper.py
> ```
>
> 2. 開いたら、**最初の数行**にある 
> ```
> cat > note_playwright_scraper.py <<'PY'
> ```
> や `PY` などのコマンド行を削除します。
>
> 3. 代わりに、純粋なPythonコード（`#!/usr/bin/env python3` から始まる）だけを残します。 
> もし元のコードが全部ない場合は、もらったスクリプト全文をここに貼り直します。
>
> 4. 保存して終了 
> `Ctrl + O` → Enter → `Ctrl + X`
>
> ---
>
> ## 再実行
> ```bash
> python3 note_playwright_scraper.py
> ```
>
> ---
>
> 今のエラーは「Pythonコードではなく、シェルのコマンドがファイルの中に混じってる」のが原因なので、 
> それを消して正しいPythonコードだけにすれば動きます。
>
> ---
>
> このあと、元のコードを丸ごと貼り直す形でやり直しますか？ 
> 私がエラーのない状態の `note_playwright_scraper.py` をそのまま渡せます。
<!-- UID: 45ca4fff-ad9e-4277-91a0-6afb0ce791b8 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:24:15
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper % python3 note_playwright_scraper.py
>
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper %
<!-- UID: c3a2902d-1ad6-4ba4-814c-7ba11e4dbb97 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:24:16
> コマンドを実行しても何も表示されなかったということは、 
>
> - スクリプト内に `print()` などの出力処理がない 
> - または、関数定義だけがあって最後に `run()` を呼んでいない 
>
> このどちらかです。
>
> ---
>
> ## 確認方法
>
> 1. ファイルを開く
> ```bash
> nano note_playwright_scraper.py
> ```
>
> 2. 一番下までスクロールして、 
> ```python
> if __name__ == "__main__":
>  run()
> ```
> この行があるかを確認してください。 
>
> なければ、**最後の行にこれを追加**します：
> ```python
> if __name__ == "__main__":
>  run()
> ```
>
> 3. 保存して閉じる（`Ctrl + O` → Enter → `Ctrl + X`）
>
> ---
>
> ## 実行
> ```bash
> python3 note_playwright_scraper.py
> ```
> これでスクリプトが動き、進行状況や結果がターミナルに表示されます。
>
> ---
>
> たぶん、今のファイルは「関数定義だけの状態」になっていて、 
> `run()` が呼ばれてないから静かに終わってしまってます。
>
> ---
>
> もし希望あれば、**修正版のコード全文（バッジ検出も入れた最新版）** を私から渡して、そのまま貼れば即動く状態にできます。 
> そうすれば余計な確認なしで動かせますが、どうしますか？
<!-- UID: a3f01f83-1c1e-4c4e-99f0-61a5cc74d9ee -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:25:25
> #!/usr/bin/env python3
> # -*- coding: utf-8 -*-
> """
> note 『買われています』収集（Playwright版 / v1.4.2-love）
> - 対象: 恋愛系のみ（恋愛/婚活/復縁/マッチングアプリ/結婚 など）
> - 候補: 検索カード段階で【¥980以上】だけ通す（カード文字列から月額/会員系は除外）
> - 記事: ヘッダの価格が【¥980以上】＆『買われています』表示があるものだけ保存
> - 無料判定: ヘッダ価格が無い AND フォローボタンが見える（またはヘッダに 無料/¥0/0円/全体公開/誰でも読める）
> - 起点: start_urls.txt（無ければ 恋愛×popular の for_sale 検索）
> """
> import csv, os, re, time, random
> from datetime import datetime
> from typing import List, Optional, Dict
> from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
>
> CSV_PATH = "note_purchased_love_980plus.csv"
> START_URLS_TXT = "start_urls.txt"
>
> # ---- 設定 ----
> RAW_MAX_CANDIDATES = 220
> NAV_TIMEOUT_MS = 25_000
> WAIT_SETTLE_SEC = (1.0, 1.6)
> POLITE_SLEEP_SEC = (1.6, 3.0)
> BOUGHT_WAIT_MS = (2000, 4000)
>
> HEADLESS = True
> USE_PERSISTENT_CONTEXT = False
> USER_DATA_DIR = "note_profile"
>
> MIN_PRICE = 980
> STRICT_CARD_PRICE = True
>
> LOVE_KWS = ["恋愛","婚活","結婚","出会い","復縁","片思い","告白","マッチングアプリ","彼氏","彼女","カップル","パートナー","恋活"]
> NEGATIVE_FREE = ["無料","全体公開","誰でも読める","¥0","0円","¥ 0"]
>
> def load_start_urls() -> List[str]:
>  if os.path.exists(START_URLS_TXT):
>  with open(START_URLS_TXT, "r", encoding="utf-8") as f:
>  urls = [u.strip() for u in f if u.strip() and not u.startswith("#")]
>  if urls:
>  return urls
>  return [
>  "https://note.com/search?context=note_for_sale&q=恋愛&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=婚活&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=復縁&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=popular",
>  "https://note.com/search?context=note_for_sale&q=結婚&sort=popular",
>  ]
>
> def unique(seq):
>  seen=set(); out=[]
>  for x in seq:
>  if x not in seen:
>  out.append(x); seen.add(x)
>  return out
>
> def _polite_wait(): time.sleep(random.uniform(*POLITE_SLEEP_SEC))
>
> def _lazy_scroll(page, steps:int=4):
>  for _ in range(steps):
>  page.evaluate("window.scrollBy(0, Math.max(400, window.innerHeight*0.7));")
>  time.sleep(random.uniform(*WAIT_SETTLE_SEC))
>
> def _try_click_more(page):
>  sels = ["text=もっと見る", "text=さらに表示", "text=もっとみる", "button:has-text('もっと')", "a:has-text('もっと')"]
>  for sel in sels:
>  try:
>  if page.locator(sel).first.is_visible(timeout=800):
>  page.locator(sel).first.click(timeout=800)
>  return True
>  except Exception:
>  pass
>  return False
>
> def _anchor_href(page, i:int) -> str:
>  try:
>  href = page.locator("a[href*='/n/']").nth(i).get_attribute("href") or ""
>  if href.startswith("/"):
>  href = "https://note.com" + href
>  return href.split("?")[0]
>  except Exception:
>  return ""
>
> def _anchor_card_text(page, i:int) -> str:
>  js = """
>  (el) => {
>  const card = el.closest('article') || el.closest('[role="article"]') || el.parentElement;
>  return (card ? card.innerText : el.innerText) || '';
>  }
>  """
>  try:
>  return page.locator("a[href*='/n/']").nth(i).evaluate(js) or ""
>  except Exception:
>  return ""
>
> def _topic_match(text: str) -> bool:
>  t = (text or "")
>  return any(kw in t for kw in LOVE_KWS)
>
> def _extract_price_from_card_text(text: str) -> Optional[int]:
>  if not text: return None
>  monthly_tokens = ["月額","/月","月/","／月","membership","メンバー","メンバーシップ","年額","/年","年/"]
>  lines = [ln for ln in text.splitlines() if ln.strip()]
>  cands = []
>  for ln in lines:
>  ln_nospace = ln.replace(" ", "")
>  if any(tok in ln_nospace for tok in monthly_tokens):
>  continue
>  for m in re.finditer(r"¥\s*(\d{1,3}(?:,\d{3})*)", ln):
>  val = int(m.group(1).replace(",", ""))
>  if val >= MIN_PRICE:
>  cands.append(val)
>  return min(cands) if cands else None
>
> def collect_raw_candidates(page, start_urls: List[str]) -> List[str]:
>  urls=[]
>  for su in start_urls:
>  try:
>  page.goto(su, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  _polite_wait()
>  stable=0; last=0
>  for _ in range(24):
>  try: cnt = page.locator("a[href*='/n/']").count()
>  except Exception: cnt = 0
>  if cnt >= 200: break
>  clicked = _try_click_more(page)
>  _lazy_scroll(page, steps=3)
>  _polite_wait()
>  try: new_cnt = page.locator("a[href*='/n/']").count()
>  except Exception: new_cnt = cnt
>  if new_cnt <= last and not clicked: stable += 1
>  else: stable = 0
>  last = new_cnt
>  if stable >= 3: break
>  anchors = page.locator("a[href*='/n/']")
>  for i in range(anchors.count()):
>  href = _anchor_href(page, i)
>  if not (href.startswith("https://note.com") and "/n/" in href):
>  continue
>  card_text = _anchor_card_text(page, i)
>  if not _topic_match(card_text):
>  continue
>  if STRICT_CARD_PRICE:
>  _cp = _extract_price_from_card_text(card_text)
>  if _cp is None or _cp < MIN_PRICE:
>  continue
>  urls.append(href)
>  except PWTimeoutError:
>  print(f"⚠️ タイムアウト: {su}")
>  except Exception as e:
>  print(f"⚠️ 起点取得エラー: {su} -> {e}")
>  urls = unique(urls)
>  if len(urls) > RAW_MAX_CANDIDATES: urls = urls[:RAW_MAX_CANDIDATES]
>  return urls
>
> def _has_follow_button(page) -> bool:
>  try:
>  btn = page.locator(
>  "div[class*='o-noteContentHeader__followButton'] .a-button, "
>  ".m-follow .a-button, "
>  "button:has-text('フォロー')"
>  )
>  return btn.count() > 0 and btn.first.is_visible(timeout=1200)
>  except Exception:
>  return False
>
> def _extract_price_from_header(page) -> Optional[int]:
>  try:
>  status = page.locator("div[class*='o-noteContentHeader__status']")
>  if status.count() == 0: return None
>  txt = status.inner_text(timeout=1500) or ""
>  monthly_tokens = ["月額", "/月", "月/", "／月", "membership", "メンバー", "メンバーシップ", "年額", "/年", "年/"]
>  lines = [ln for ln in (txt.splitlines()) if ln.strip()]
>  cands = []
>  for line in lines:
>  ln = line.replace(" ", "")
>  if any(tok in ln for tok in monthly_tokens): continue
>  for m in re.finditer(r"¥\s*(\d{1,3}(?:,\d{3})*)", line):
>  val = int(m.group(1).replace(",", ""))
>  if val >= MIN_PRICE: cands.append(val)
>  if not cands: return None
>  return min(cands)
>  except Exception:
>  return None
>
> def _is_free_in_header(page) -> bool:
>  try:
>  header = page.locator("div[class*='o-noteContentHeader__status']")
>  if header.count() > 0:
>  txt = header.inner_text(timeout=1200) or ""
>  if any(k in txt for k in ["無料","全体公開","誰でも読める"]) or re.search(r"¥\s*0|0\s*円", txt):
>  return True
>  except Exception:
>  pass
>  price = _extract_price_from_header(page)
>  if price is None and _has_follow_button(page):
>  return True
>  return False
>
> def _has_bought_quick(context, url: str) -> bool:
>  page = context.new_page()
>  try:
>  page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  page.evaluate("window.scrollBy(0, 180);")
>  if _is_free_in_header(page): return False
>  price = _extract_price_from_header(page)
>  if price is None or price < MIN_PRICE: return False
>  try:
>  qt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=800) or "")
>  except Exception: qt = page.title() or ""
>  if not any(kw in qt for kw in LOVE_KWS): return False
>  end_time = time.time() + random.randint(*BOUGHT_WAIT_MS)/1000
>  while time.time() < end_time:
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=300): return True
>  except Exception: pass
>  try:
>  bt = page.locator("body").inner_text(timeout=500)
>  if any(k in bt for k in ["買われています","買われている","過去24時間"]): return True
>  except Exception: pass
>  time.sleep(0.15)
>  return False
>  except Exception:
>  return False
>  finally:
>  try: page.close()
>  except: pass
>
> def detail_check_and_save(context, url: str) -> Optional[Dict]:
>  page = context.new_page()
>  try:
>  page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
>  page.evaluate("window.scrollBy(0, 220);")
>  time.sleep(random.uniform(*WAIT_SETTLE_SEC))
>  if _is_free_in_header(page):
>  print(" ✗ SKIP: free_header_follow")
>  return None
>  price = _extract_price_from_header(page)
>  if price is None or price < MIN_PRICE:
>  print(" ✗ SKIP: price<980_or_header_missing")
>  return None
>  try:
>  txt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=1500) or "")
>  except Exception: txt = page.title() or ""
>  if not any(kw in txt for kw in LOVE_KWS):
>  print(" ✗ SKIP: out_of_topic")
>  return None
>  bought = False
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=1000): bought = True
>  except Exception: pass
>  if not bought and any(k in txt for k in ["買われています","買われている","過去24時間"]): bought = True
>  if not bought:
>  print(" ✗ SKIP: no_bought")
>  return None
>  title = (page.title() or "").strip()
>  row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, url, str(price), "True"]
>  if int(price) < MIN_PRICE:
>  print(f" ✗ SKIP: final_guard price={price} < {MIN_PRICE}")
>  return None
>  with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
>  csv.writer(f).writerow(row)
>  print(" ✓ SAVE")
>  return {"date": row[0], "title": title, "url": url, "price": str(price), "bought_24h": "True"}
>  except PWTimeoutError:
>  print(f"⏳ 記事タイムアウト: {url}")
>  return None
>  except Exception as e:
>  print(f"⚠️ 記事処理エラー: {url} -> {e}")
>  return None
>  finally:
>  try: page.close()
>  except: pass
>  _polite_wait()
>
> def ensure_csv_header(path: str):
>  if not os.path.exists(path):
>  with open(path, "w", encoding="utf-8", newline="") as f:
>  csv.writer(f).writerow(["date","title","url","price","bought_24h"])
>
> def already_recorded(path: str, url: str) -> bool:
>  if not os.path.exists(path): return False
>  try:
>  with open(path, "r", encoding="utf-8") as f:
>  for line in f:
>  if url in line: return True
>  except: return False
>  return False
>
> def run():
>  print("🎯 note『買われています』収集（Playwright版 / v1.4.2-love）")
>  start_urls = load_start_urls()
>  print(f"🧭 起点: {start_urls}")
>  ensure_csv_header(CSV_PATH)
>  with sync_playwright() as p:
>  if USE_PERSISTENT_CONTEXT:
>  context = p.chromium.launch_persistent_context(
>  USER_DATA_DIR, headless=HEADLESS,
>  viewport={"width":1280,"height":900}, locale="ja-JP"
>  )
>  else:
>  browser = p.chromium.launch(headless=HEADLESS)
>  context = browser.new_context(viewport={"width":1280,"height":900}, locale="ja-JP")
>  page = context.new_page()
>  try:
>  raw_candidates = collect_raw_candidates(page, start_urls)
>  print(f"🔎 生候補URL（カード¥980+ & トピック適合）: {len(raw_candidates)}件")
>  bought_urls = []
>  for idx, url in enumerate(raw_candidates, 1):
>  if already_recorded(CSV_PATH, url): continue
>  print(f" [screen {idx}/{len(raw_candidates)}] {url}")
>  if _has_bought_quick(context, url):
>  bought_urls.append(url)
>  _polite_wait()
>  print(f"📌 『買われています』一次通過: {len(bought_urls)}件")
>  saved=0
>  for jdx, url in enumerate(bought_urls, 1):
>  print(f" [detail {jdx}/{len(bought_urls)}] {url}")
>  info = detail_check_and_save(context, url)
>  if info: saved += 1
>  print(f"✅ 収集完了: {saved}件 追加")
>  print(f"📦 出力: {os.path.abspath(CSV_PATH)}")
>  finally:
>  try: page.close()
>  except: pass
<!-- UID: 471c5a9e-0513-42cf-823b-c33e8e9fde3b -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:25:25
> 今のコードを見ると、最後に `run()` を呼び出していないので、 
> `python3 note_playwright_scraper.py` を実行しても何も動かずに終了します。 
>
> ---
>
> ## 修正方法
>
> このファイルの**一番下**に次の2行を追加してください。
>
> ```python
> if __name__ == "__main__":
>  run()
> ```
>
> ---
>
> ### 手順
>
> 1. ターミナルで編集 
> ```bash
> nano note_playwright_scraper.py
> ```
>
> 2. 一番下までスクロールして、この2行を追加 
> ```python
> if __name__ == "__main__":
>  run()
> ```
>
> 3. 保存して閉じる 
> `Ctrl + O` → Enter → `Ctrl + X`
>
> ---
>
> これで、
>
> ```bash
> python3 note_playwright_scraper.py
> ```
>
> を実行すれば、ターミナルに進行状況（🎯起点URLや🔎候補件数など）が表示されるようになります。
>
> ---
>
> このままやって動かしてみますか？
<!-- UID: cce3f777-0d6d-4559-9c22-9f2dc5707651 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:26:10
> Traceback (most recent call last):
>  File "/Users/sasaki/Desktop/note_love_scraper/note_playwright_scraper.py", line 1, in <module>
>  cat > note_playwright_scraper.py <<'PY'
>  ^^^
> NameError: name 'cat' is not defined
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper % nano note_playwright_scraper.py
>
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper % python3 note_playwright_scraper.py
>
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper % python3 note_playwright_scraper.py
>
>  File "/Users/sasaki/Desktop/note_love_scraper/note_playwright_scraper.py", line 201
>  selectors = [
>  ^^^^^^^^^
> IndentationError: expected an indented block after function definition on line 200
> (.venv) sasaki@sasakinoMacBook-Pro note_love_scraper %
<!-- UID: 2dfe8f94-0591-48c2-9104-b49ddec1a55e -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:26:11
> 今のエラーは 
>
> ```
> IndentationError: expected an indented block after function definition
> ```
>
> なので、「関数の中身が空」または「インデントが崩れている」のが原因です。 
> 具体的には、`def _has_bought_badge(...):` の直後に中身が正しく入っていないか、字下げがバラバラになっています。
>
> ---
>
> ## 修正版の入れ方
>
> もうファイルの中身が混乱しているようなので、 
> ここから「動く完成版」をまるごと貼り直したほうが早いです。
>
> ### 手順
> 1. ターミナルで開く
> ```bash
> nano note_playwright_scraper.py
> ```
>
> 2. **全部削除**（`Ctrl + K` を押し続けると行ごと消せます）
>
> 3. 私が渡す完成版コード全文をそのまま貼る（バッジ検出入り・`run()` 呼び出し付き）
>
> ---
>
> 貼り直すコードを用意しますが、 
> バッジ検出（`_has_bought_badge`）も入れた最新版にしますか？ 
> それともまずはシンプルに動く最小版でテストしてみますか？
<!-- UID: dd27b67d-67b7-428f-81da-6280c1428609 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:27:01
> ここだけ修正して
>
> def _has_bought_badge(page, timeout_ms=800) -> bool:
> selectors = [
> ".m-purchasedWithinLast24HoursBalloon", # ご指定のクラス
> "[class*='purchasedWithinLast24Hours']", # 命名揺れ対策
> "[data-testid='purchasedWithinLast24Hours']",
> "[data-testid='purchased-within-last-24-hours']",
> ]
<!-- UID: f87ce7e4-1920-4bc9-b42f-652d02b704ac -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:27:02
> OK、インデントが正しい形に直します。 
> `def` の中身は必ず半角スペース4つ分下げる必要があります。 
>
> 修正版はこうです。 
> ```python
> def _has_bought_badge(page, timeout_ms=800) -> bool:
>  selectors = [
>  ".m-purchasedWithinLast24HoursBalloon", # ご指定のクラス
>  "[class*='purchasedWithinLast24Hours']", # 命名揺れ対策
>  "[data-testid='purchasedWithinLast24Hours']",
>  "[data-testid='purchased-within-last-24-hours']",
>  ]
>  deadline = time.time() + (timeout_ms / 1000)
>  while time.time() < deadline:
>  for sel in selectors:
>  try:
>  loc = page.locator(sel)
>  if loc.count() > 0 and loc.first.is_visible(timeout=200):
>  return True
>  except Exception:
>  pass
>  time.sleep(0.05)
>  return False
> ```
>
> ---
>
> ### 修正の入れ方
> 1. ターミナルでファイルを開く
> ```bash
> nano note_playwright_scraper.py
> ```
> 2. 今の `_has_bought_badge` 関数部分を、上のコードに置き換える 
> 3. 保存して閉じる（`Ctrl + O` → Enter → `Ctrl + X`）
>
> ---
>
> この修正版を入れれば、もう `IndentationError` は出ないはずです。 
> 入れ終わったら、もう一度 
> ```bash
> python3 note_playwright_scraper.py
> ``` 
> を実行してみてください。 
>
> やりますか？
<!-- UID: 37ad6678-0815-4785-989a-c25a403864f2 -->

---
>[!nexus_user] **User** - 2025/08/10 at 03:27:31
> 🎯 note『買われています』収集（Playwright版 / v1.4.2-love）
> 🧭 起点: ['https://note.com/search?context=note_for_sale&q=恋愛&sort=popular', 'https://note.com/search?context=note_for_sale&q=婚活&sort=popular', 'https://note.com/search?context=note_for_sale&q=復縁&sort=popular', 'https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=popular', 'https://note.com/search?context=note_for_sale&q=結婚&sort=popular']
<!-- UID: 24115dda-729c-41b3-bf8e-02cf1085887a -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 03:27:31
> よかった、今度はちゃんと動き始めています。 
> この表示はスクリプトの「準備フェーズ」で、 
> これから起点URLごとにPlaywrightがブラウザを開き、記事カードを読み込んでいく段階です。 
>
> ---
>
> ### このあと出るメッセージの流れ
> 1. **生候補URLの件数表示** 
>  ```
>  🔎 生候補URL（カード¥980+ & トピック適合）: XX件
>  ```
>  ここで最初のフィルターを通った件数が表示されます。
>
> 2. **一次通過（買われていますチェック）** 
>  ```
>  📌 『買われています』一次通過: YY件
>  ```
>  ここで「買われています」が見つかった候補件数。
>
> 3. **詳細保存（CSV書き込み）** 
>  ```
>  ✓ SAVE
>  ```
>  と出たものは `note_purchased_love_980plus.csv` に追記されています。
>
> 4. **完了** 
>  ```
>  ✅ 収集完了: ZZ件 追加
>  📦 出力: /Users/～～/note_love_scraper/note_purchased_love_980plus.csv
>  ```
>
> ---
>
> もしここから先が進まない（ずっと止まる）ようなら、
> - 回線が遅くて読み込み待ちになっている
> - ブラウザが見えないので動作が分からない
>
> という可能性があります。 
> その場合は `HEADLESS = False` にしてブラウザ表示ありで試すと進行が見えます。
>
> ---
>
> このまま最後まで回すか、 
> 一度 `HEADLESS=False` にしてブラウザ表示ありで流れを確認しますか？
<!-- UID: eb8f456b-61af-489b-bd8c-e7d746a50a2a -->

---