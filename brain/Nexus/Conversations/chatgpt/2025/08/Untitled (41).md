---
nexus: nexus-ai-chat-importer
plugin_version: "1.3.3"
provider: chatgpt
aliases: Untitled
conversation_id: 68977b61-9748-832a-ae29-efd4586fa515
create_time: 2025-08-09T16:46:33.742Z
update_time: 2025-08-09T16:53:14.781Z
---

# Title: 使い方説明

Created: 2025/08/10 at 01:46:33
Last Updated: 2025/08/10 at 01:53:14
Chat URL: https://chatgpt.com/c/68977b61-9748-832a-ae29-efd4586fa515


>[!nexus_user] **User** - 2025/08/10 at 01:46:32
> これってどうやって使えばいいですか？
>
> 秘匿情報（APIキー／Cookie／個人識別情報）は含まれていません。
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
<!-- UID: 61aefad6-afd6-46f3-8a0e-0309f67f700f -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 01:46:34
> 了解です。いただいた構成なら、そのまま「1分セットアップ & 実行手順」で動きます。ここでは、初回セットアップから日次運用、精度チューニング、障害時の対処までを一気にまとめます。
>
> # 使い方（最短）
> 1) 依存インストール（初回のみ）
> ```
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium
> ```
> 2) フォルダを Desktop に置く（同梱ファイル一式：`note_playwright_scraper.py`、`start_urls.txt` など）
> ```
> cd ~/Desktop
> ```
> 3) 起点URLを必要に応じて編集 
> `start_urls.txt` を開き、恋愛×有料の検索URLを1行1件で列挙（空ならデフォルト5本を使用）。
> ```
> nano start_urls.txt
> ```
> 4) 実行
> ```
> python3 note_playwright_scraper.py
> ```
> 5) 結果確認 
> `note_purchased_love_980plus.csv` の末尾をチェック。
> ```
> tail -n 5 note_purchased_love_980plus.csv
> ```
>
> # 実行前に押さえるポイント
> - 価格しきい値は `MIN_PRICE = 980`。必要に応じて変更可。
> - ヘッドレス実行（画面非表示）は `HEADLESS = True`。挙動確認したいときは `False` に。
> - テーマ判定は `LOVE_KWS` を使用。恋愛語句を増やす／削ると検出範囲が変わります。
> - 1周回あたりの候補URL数は `RAW_MAX_CANDIDATES`。件数が少ない時は増やす、負荷が高ければ下げる。
>
> # 「買われています」検出の強化（CSSセレクタの追記）
> 追記のクラスを使うなら、関数を差し替えて早期に確実判定できます。以下をファイル末尾の追記ではなく、既存ロジックに組み込みます。
>
> 1) バッジ検出関数の追加
> ```python
> def _has_bought_badge(page, timeout_ms=800) -> bool:
>  selectors = [
>  ".m-purchasedWithinLast24HoursBalloon",
>  "[class*='purchasedWithinLast24Hours']",
>  "[data-testid='purchasedWithinLast24Hours']",
>  "[data-testid='purchased-within-last-24-hours']",
>  ]
>  for sel in selectors:
>  try:
>  loc = page.locator(sel)
>  if loc.count() > 0 and loc.first.is_visible(timeout=timeout_ms):
>  return True
>  except Exception:
>  pass
>  return False
> ```
>
> 2) 1stパス（高速確認）での使用 
> `_has_bought_quick` 内の while ループに「テキスト検出の前」に差し込むのが簡単です。
> ```python
> # 省略…ページ遷移後
> end_time = time.time() + random.randint(*BOUGHT_WAIT_MS)/1000
> while time.time() < end_time:
>  # まずはバッジの直接検出
>  if _has_bought_badge(page):
>  return True
>  # フォールバック：テキスト検出
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=300): 
>  return True
>  except Exception:
>  pass
>  try:
>  bt = page.locator("body").inner_text(timeout=500)
>  if any(k in bt for k in ["買われています","買われている","過去24時間"]):
>  return True
>  except Exception:
>  pass
>  time.sleep(0.15)
> ```
>
> 3) 2ndパス（詳細チェック）でも同様に先頭で呼ぶ 
> `detail_check_and_save` の `bought` 判定を次のように上書き。
> ```python
> bought = _has_bought_badge(page)
> if not bought:
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=1000): 
>  bought = True
>  except Exception:
>  pass
> if not bought:
>  txt = (page.title() or "") + " " + (page.locator("body").inner_text(timeout=1500) or "")
>  if any(k in txt for k in ["買われています","買われている","過去24時間"]):
>  bought = True
> if not bought:
>  print(" ✗ SKIP: no_bought")
>  return None
> ```
>
> こうすると、UI変更でトースト文言が見えにくいケースでも、公式が付与するクラス／data-testidから直接拾えるため、検出の安定度が上がります。
>
> # よくある調整
> - 件数が少ない 
>  - `start_urls.txt` に `sort=recent` を追加（新着寄り） 
>  - `RAW_MAX_CANDIDATES` を 220→400 程度へ 
>  - `BOUGHT_WAIT_MS` を `(2000, 4000)` → `(3000, 5000)` に延長
> - ¥300（月額会員など）が混入 
>  - 実際の該当URLを開いて、カード／ヘッダの文言を確認し、除外トークンを `monthly_tokens` に追加
> - PC負荷を下げたい 
>  - `HEADLESS=True` のまま 
>  - `RAW_MAX_CANDIDATES` を 120 程度へ 
>  - 実行を1日2回（朝・夜）に分ける
> - 既出URLの重複記録を減らす 
>  - 現状は簡易的に1行包含チェック。精度を上げるなら、CSV読み込み→URLカラムのセット管理に変更するのが無難
>
> # 運用のコツ
> - 実行タイミング 
>  「過去24時間」のバッジなので、毎日同時刻の定期実行が相性良いです（例：朝8時と夜22時の2回）。
> - 目視確認モード 
>  `HEADLESS=False` にしてUIを見ながら、`print`のログと突き合わせると原因特定が早いです。
> - 永続コンテキスト（ログインやCookie再利用） 
>  ログイン状態での表示差異がある場合は `USE_PERSISTENT_CONTEXT=True` にし、`note_profile/` を使います。初回はヘッドレスを切ってログイン→次回以降はヘッドレス可。
>
> # 自動化（例）
> - macOS（cron の例）
> ```
> crontab -e
> # 毎朝8:05と毎晩22:05に実行
> 5 8,22 * * * cd $HOME/Desktop && /usr/bin/python3 note_playwright_scraper.py >> scraper.log 2>&1
> ```
> - Windows 
>  「タスク スケジューラ」で `python.exe` を実行プログラム、引数にスクリプトパス、作業フォルダに配置ディレクトリを指定。
>
> # トラブルシュート
> - `TimeoutError` が頻発 
>  - `NAV_TIMEOUT_MS` を 25,000 → 40,000 に。 
>  - 回線が不安定な時は `WAIT_SETTLE_SEC` を少し延長。 
> - 要素が見つからない 
>  - noteのUI変更に合わせてセレクタ（特にヘッダ価格とフォローボタン、購入バッジ）を更新。 
> - CSVが文字化け 
>  - Excelで開く場合はUTF-8を指定。Numbersやスプシに取り込むのが確実。
>
> # 倫理・利用規約の注意
> - 公開情報でも、サイトの利用規約・robots.txt・レート制限は遵守してください。 
> - 大量アクセスは避け、`POLITE_SLEEP_SEC` で間引き、深夜の連続実行は控えるのが安全です。 
> - 収集データの取り扱い（外部共有・再配布）は慎重に。
>
> # 目的達成のチェック（CSV仕様）
> - 出力: `note_purchased_love_980plus.csv` 
> - カラム: `date, title, url, price, bought_24h` 
> - 条件: 恋愛系×有料×¥980以上×「過去24時間で買われています」表示 → 該当URLのみ追記
>
> # 例：起点URL（`start_urls.txt`）
> ```
> https://note.com/search?context=note_for_sale&q=恋愛&sort=recent
> https://note.com/search?context=note_for_sale&q=婚活&sort=recent
> https://note.com/search?context=note_for_sale&q=復縁&sort=popular
> https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=popular
> https://note.com/search?context=note_for_sale&q=結婚&sort=recent
> ```
>
> # たとえ（全体像の理解補助）
> 検索ページ＝「市場」、カード収集＝「仕入れの目利き」、1stパス＝「棚出し前の超速チェック」、2ndパス＝「レジでの年齢確認」のイメージです。最初は粗く広く拾って、バッジ（買われています）を見つけたものだけ最後に厳密チェック→CSVに在庫登録、という流れ。
>
> # まとめ（Key takeaways）
> - そのまま動きます。まずは既存の手順どおり実行。 
> - 「買われています」検出はCSSバッジ関数を入れると安定。1st/2nd両方に差し込む。 
> - 件数は `start_urls` と `RAW_MAX_CANDIDATES`、待機時間で調整。 
> - 定期実行してCSVを育てる。UI変更時はセレクタを更新。 
>
> 必要なら、上記の差分を組み込んだ完全版スクリプト（パッチ適用済み）も作成します。
<!-- UID: 54f7429f-aa66-4403-b393-086ebf95c12e -->

---
>[!nexus_user] **User** - 2025/08/10 at 01:47:58
> プログラミング初心者です。使用OSはMac iOS
<!-- UID: 177e5018-d795-4083-bed8-fb5ee863037d -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 01:47:59
> なるほど、Mac（macOS）でプログラミング初心者向けに、このスクリプトの**「設置から実行まで」**を一番かんたんな形で説明しますね。 
> （iOS＝iPhoneやiPadでは動かせません。Macのノートやデスクトップでの説明です）
>
> ---
>
> ## ① 事前準備
> 1. **Pythonが入っているか確認** 
>  Macは標準でPythonが入っていることが多いですが、念のため確認します。
>  ```
>  python3 --version
>  ```
>  バージョンが表示されればOK。表示されない場合は[Python公式サイト](https://www.python.org/downloads/)からインストールします。
>
> 2. **フォルダを用意する** 
>  デスクトップに「note_scraper」という名前のフォルダを作り、その中に以下のファイルを入れます。 
>  - `note_playwright_scraper.py`（スクリプト本体） 
>  - `start_urls.txt`（起点URLリスト）※空でも可 
>  - 空の `note_purchased_love_980plus.csv`（なくても実行時に自動生成） 
>
> ---
>
> ## ② 初回セットアップ（1回だけでOK）
> ターミナルを開いて、以下のコマンドを順番に入力します。
>
> ```
> cd ~/Desktop/note_scraper
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium
> ```
>
> これで必要なライブラリとブラウザエンジンが入ります。
>
> ---
>
> ## ③ 実行方法
> 1. **ターミナルでフォルダに移動**
>  ```
>  cd ~/Desktop/note_scraper
>  ```
>
> 2. **スクリプトを実行**
>  ```
>  python3 note_playwright_scraper.py
>  ```
>
> 3. 実行が終わると、同じフォルダに `note_purchased_love_980plus.csv` ができ、収集結果が追記されます。
>
> ---
>
> ## ④ 結果の見方
> - ターミナルに「✓ SAVE」と出た行が保存された記事です。
> - 最新5件だけ見たいとき：
>  ```
>  tail -n 5 note_purchased_love_980plus.csv
>  ```
> - CSVはダブルクリックでNumbersやExcelで開けます。
>
> ---
>
> ## ⑤ 毎日使うとき
> - ②のセットアップはもう不要です。
> - ターミナルでフォルダに移動して実行するだけです。
>  ```
>  cd ~/Desktop/note_scraper
>  python3 note_playwright_scraper.py
>  ```
>
> ---
>
> ## ⑥ 初心者向けの注意点
> - **iPhoneやiPadでは動きません**（Mac専用） 
> - 実行中にブラウザ画面を見たい場合は、スクリプトの冒頭にある 
>  `HEADLESS = True` を `HEADLESS = False` に変更して保存してください。
> - Macをスリープ状態にすると途中で止まります。
>
> ---
>
> もし希望があれば、 
> この「買われています」検出をより正確にする**CSSセレクタ対応版**を入れた完成スクリプトも作れます。 
>
> これ、完成版も作りますか？ 
> （入れると精度がかなり安定します）
<!-- UID: d7ea2ae1-49c7-4535-8757-af58d2b0c320 -->

---
>[!nexus_user] **User** - 2025/08/10 at 01:50:04
> Pythonいれたけどそのあとはどうしたら・・？
<!-- UID: 3f110de9-4d7d-4a3b-9668-1c419e34f8ca -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 01:50:04
> じゃあ、Pythonが入ったところから説明を続けますね。 
> Macで**初めてこのスクリプトを動かす流れ**を、順番通りに書きます。
>
> ---
>
> ## 1. フォルダを用意
> 1. Macの**デスクトップ**に `note_scraper` というフォルダを作ります。
> 2. その中に、もらったファイルを入れます。
>  - `note_playwright_scraper.py`（スクリプト本体）
>  - `start_urls.txt`（あれば。なくても動く）
>  - 空の `note_purchased_love_980plus.csv`（なくても実行時に自動で作られる）
>
> ---
>
> ## 2. ターミナルを開く
> - Macの「Launchpad」→「その他」→「ターミナル」をクリック。
> - ターミナルの黒い画面が出ます。
>
> ---
>
> ## 3. ターミナルでフォルダに移動
> デスクトップの `note_scraper` フォルダに移動します。
>
> ```
> cd ~/Desktop/note_scraper
> ```
>
> ※ここでエンターキーを押してください。 
> もし `No such file or directory` と出たら、フォルダ名が違うか場所が間違ってます。
>
> ---
>
> ## 4. 必要なライブラリを入れる（初回だけ）
> 次の2行を順番に実行します。
>
> ```
> python3 -m pip install playwright pandas
> python3 -m playwright install chromium
> ```
>
> - 1行目 → 「playwright」と「pandas」というライブラリを入れます。
> - 2行目 → playwright用のブラウザ（Chromium）をダウンロードします。
>
> ---
>
> ## 5. スクリプトを動かす
> ```
> python3 note_playwright_scraper.py
> ```
>
> - これで自動でnoteのページを見に行き、条件に合う記事を探します。
> - 実行が終わると、同じフォルダに `note_purchased_love_980plus.csv` ができます。
>
> ---
>
> ## 6. 結果を見る
> - `note_purchased_love_980plus.csv` をダブルクリックするとNumbersやExcelで開けます。
> - ターミナルでも最後の5件を見るには：
> ```
> tail -n 5 note_purchased_love_980plus.csv
> ```
>
> ---
>
> このままでも動きますが、精度を上げたいなら「買われています」検出部分を少し改良できます。 
> それも入れておくと取りこぼしが減ります。
>
> ---
>
> このあと、 
> まずは今の状態で `python3 note_playwright_scraper.py` を実行してみますか？ 
> そうすれば動作確認ができます。
<!-- UID: 3eb52285-bf71-49d3-ad2a-2431fc8b27d6 -->

---
>[!nexus_user] **User** - 2025/08/10 at 01:51:02
> もらったふぁいる・・・・？文章しかもらってません
<!-- UID: 64c324ad-4f7b-497a-972b-3b60c97b5110 -->
>[!nexus_agent] **Assistant** - 2025/08/10 at 01:51:05
> # Create the files the user needs and bundle them into a zip they can download.
>
> import os, zipfile, textwrap, json, datetime, pathlib
>
> base_dir = "/mnt/data/note_scraper"
> os.makedirs(base_dir, exist_ok=True)
>
> script_content = r"""#!/usr/bin/env python3
> # -*- coding: utf-8 -*-
> """
> note 『買われています』収集（Playwright版 / v1.4.2-love, badge-patch）
> - 対象: 恋愛系のみ（恋愛/婚活/復縁/マッチングアプリ/結婚 など）
> - 候補: 検索カード段階で【¥980以上】だけ通す（カード文字列から月額/会員系は除外）
> - 記事: ヘッダの価格が【¥980以上】＆『買われています』表示があるものだけ保存
> - 無料判定: ヘッダ価格が無い AND フォローボタンが見える（またはヘッダに 無料/¥0/0円/全体公開/誰でも読める）
> - 起点: start_urls.txt（無ければ 恋愛×popular の for_sale 検索）
> - 変更点: 『買われています』専用バッジのCSS/data-testidを優先検出
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
> # --- 追加: 『買われています』バッジ専用検出 ---
> def _has_bought_badge(page, timeout_ms=800) -> bool:
>  selectors = [
>  ".m-purchasedWithinLast24HoursBalloon",
>  "[class*='purchasedWithinLast24Hours']",
>  "[data-testid='purchasedWithinLast24Hours']",
>  "[data-testid='purchased-within-last-24-hours']",
>  ]
>  for sel in selectors:
>  try:
>  loc = page.locator(sel)
>  if loc.count() > 0 and loc.first.is_visible(timeout=timeout_ms):
>  return True
>  except Exception:
>  pass
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
>  # 1) バッジ検出を最優先
>  if _has_bought_badge(page):
>  return True
>  # 2) テキスト検出（フォールバック）
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
>  bought = _has_bought_badge(page)
>  if not bought:
>  try:
>  loc = page.get_by_text(re.compile(r"(買われています|買われている)"))
>  if loc and loc.first.is_visible(timeout=1000): bought = True
>  except Exception: pass
>  if not bought and any(k in txt for k in ["買われています","買われている","過去24時間"]):
>  bought = True
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
>  print("🎯 note『買われています』収集（Playwright版 / v1.4.2-love, badge-patch）")
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
> if __name__ == "__main__":
>  run()
> """
>
> start_urls = """https://note.com/search?context=note_for_sale&q=恋愛&sort=recent
> https://note.com/search?context=note_for_sale&q=婚活&sort=recent
> https://note.com/search?context=note_for_sale&q=復縁&sort=popular
> https://note.com/search?context=note_for_sale&q=マッチングアプリ&sort=popular
> https://note.com/search?context=note_for_sale&q=結婚&sort=recent
> """
>
> csv_header = "date,title,url,price,bought_24h\n"
>
> # Write files
> with open(os.path.join(base_dir, "note_playwright_scraper.py"), "w", encoding="utf-8") as f:
>  f.write(script_content)
>
> with open(os.path.join(base_dir, "start_urls.txt"), "w", encoding="utf-8") as f:
>  f.write(start_urls)
>
> with open(os.path.join(base_dir, "note_purchased_love_980plus.csv"), "w", encoding="utf-8") as f:
>  f.write(csv_header)
>
> # Zip the folder
> zip_path = "/mnt/data/note_scraper_mac.zip"
> with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
>  for fname in ["note_playwright_scraper.py", "start_urls.txt", "note_purchased_love_980plus.csv"]:
>  zf.write(os.path.join(base_dir, fname), arcname=f"note_scraper/{fname}")
>
> zip_path
<!-- UID: 6727376e-4c84-46ba-a260-faaa0dc16a83 -->

---
>[!nexus_agent] **Assistant** - 2025/08/10 at 01:53:01
> # Fix the previous error and recreate the downloadable zip with proper files.
>
> import os, zipfile
>
> base_dir = "/mnt/data/note_scraper_fixed"
> os.makedirs(base_dir, exist_ok=True)
>
> script_content = """#!/usr/bin/env python3
> # -*- coding: utf-8 -*-
> # note 『買われています』収集（Playwright版 / v1.4.2-love, badge-patch）
> # - 対象: 恋愛系のみ（恋愛/婚活/復縁/マッチングアプリ/結婚 など）
> # - 候補: 検索カード段階で【¥980以上】だけ通す（カード文字列から月額/会員系は除外）
> # - 記事: ヘッダの価格が【¥980以上】＆『買われています』表示があるものだけ保存
> # - 無料判定: ヘッダ価格が無い AND フォローボタンが見える（またはヘッダに 無料/¥0/0円/全体公開/誰でも読める）
> # - 起点: start_urls.txt（無ければ 恋愛
<!-- UID: dea6bea9-1c9b-41f1-9b98-c3ae53da513f -->

---