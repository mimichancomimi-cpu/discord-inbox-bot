#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threadsアカウントの投稿をすべてCSVに抽出するツール（ツリー投稿含む）

使い方: ユーザーID（または me）を指定するだけで、そのアカウントの全投稿＋ツリーをCSVに出力します。

【重要】Threads API の制限
- 取得できるのは「このトークンでログインしているアカウント（認証ユーザー）自身の投稿」のみです。
- 他アカウントのIDを指定しても投稿は取得できません。複数アカウント分を取りたい場合は、
  各アカウントのアクセストークンでそれぞれ実行してください。

必要: Threads API のアクセストークン（threads_basic 権限）
取得方法: https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions/
"""

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests が必要です: pip install requests", file=sys.stderr)
    sys.exit(1)

# Threads Graph API
BASE_URL = "https://graph.threads.net/v1.0"
THREADS_FIELDS = "id,media_type,text,timestamp,permalink,username,media_url,has_replies"
CONVERSATION_FIELDS = "id,text,timestamp,username,media_type,permalink,is_reply,replied_to,root_post,media_url"

# Threads プロフィールURLのパターン（@ユーザー名 を抽出）
THREADS_URL_PATTERN = re.compile(r"threads\.com/@([a-zA-Z0-9_.]+)", re.IGNORECASE)


def normalize_user_input(s: str) -> tuple[str, bool]:
    """
    位置引数を正規化する。(user_id_or_username, is_likely_id) を返す。
    is_likely_id が True のときはそのまま user_id として使う。False のときは username なので profile_lookup でID解決する。
    """
    s = (s or "").strip()
    if not s or s == "me":
        return ("me", True)
    if s.isdigit() and len(s) >= 10:
        return (s, True)
    m = THREADS_URL_PATTERN.search(s)
    if m:
        return (m.group(1), False)
    return (s.lstrip("@"), False)


def profile_lookup(access_token: str, username: str) -> str:
    """ユーザー名から Threads ユーザーID を取得する（Profile Lookup API）"""
    url = f"{BASE_URL}/profile_lookup"
    params = {"username": username, "access_token": access_token}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    # レスポンス形式: {"data": [{"id": "123...", "username": "..."}]} 等を想定
    if "data" in data and data["data"]:
        entry = data["data"][0] if isinstance(data["data"], list) else data["data"]
        return str(entry.get("id", ""))
    if "id" in data:
        return str(data["id"])
    raise ValueError(f"ユーザー名 '{username}' からIDを取得できませんでした: {data}")


def get_user_threads(access_token: str, user_id: str = "me", after: str | None = None) -> dict:
    """ユーザーの投稿一覧を取得（ページネーション対応）"""
    url = f"{BASE_URL}/{user_id}/threads"
    params = {
        "fields": THREADS_FIELDS,
        "access_token": access_token,
    }
    if after:
        params["after"] = after
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def get_conversation(media_id: str, access_token: str, after: str | None = None) -> dict:
    """指定投稿の会話（ツリー全体）をフラットリストで取得"""
    url = f"{BASE_URL}/{media_id}/conversation"
    params = {
        "fields": CONVERSATION_FIELDS,
        "access_token": access_token,
        "reverse": "true",  # 新しい順で取得
    }
    if after:
        params["after"] = after
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_all_threads(access_token: str, user_id: str = "me") -> list[dict]:
    """全投稿をページネーションで取得"""
    threads = []
    after = None
    while True:
        data = get_user_threads(access_token, user_id=user_id, after=after)
        for item in data.get("data", []):
            threads.append(item)
        paging = data.get("paging", {})
        cursors = paging.get("cursors", {})
        after = cursors.get("after")
        if not after:
            break
        time.sleep(0.3)  # レート制限対策
    return threads


def fetch_full_conversation(media_id: str, access_token: str) -> list[dict]:
    """1投稿分の会話（親＋全リプライ）をすべて取得"""
    items = []
    after = None
    while True:
        data = get_conversation(media_id, access_token, after=after)
        for item in data.get("data", []):
            items.append(item)
        paging = data.get("paging", {})
        cursors = paging.get("cursors", {})
        after = cursors.get("after")
        if not after:
            break
        time.sleep(0.2)
    return items


def row_from_media(item: dict, root_id: str | None = None, parent_id: str | None = None, depth: int = 0) -> dict:
    """APIの1件をCSV用の1行に変換"""
    return {
        "post_id": item.get("id", ""),
        "parent_id": parent_id or item.get("replied_to", ""),
        "root_post_id": root_id or item.get("root_post", "") or item.get("id", ""),
        "depth": depth,
        "is_reply": "1" if item.get("is_reply") else "0",
        "text": (item.get("text") or "").replace("\r\n", "\n").replace("\n", " ").strip(),
        "timestamp": item.get("timestamp", ""),
        "username": item.get("username", ""),
        "media_type": item.get("media_type", ""),
        "permalink": item.get("permalink", ""),
        "media_url": item.get("media_url", ""),
    }


def export_to_csv(
    access_token: str,
    output_path: Path,
    user_id: str = "me",
    include_trees: bool = True,
    max_posts: int | None = None,
) -> int:
    """
    全投稿＋ツリーをCSVに出力する。
    include_trees=True のとき、各投稿の会話（conversation）も取得してツリーとして追記する。
    戻り値: 出力した行数（ヘッダ除く）
    """
    threads = fetch_all_threads(access_token, user_id=user_id)
    if max_posts is not None:
        threads = threads[:max_posts]

    fieldnames = [
        "post_id", "parent_id", "root_post_id", "depth", "is_reply",
        "text", "timestamp", "username", "media_type", "permalink", "media_url",
    ]
    total_rows = 0

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for i, post in enumerate(threads):
            root_id = post.get("id", "")
            # 親投稿を1行出力
            writer.writerow(row_from_media(post, root_id=root_id, depth=0))
            total_rows += 1

            if include_trees:
                conv = []
                try:
                    conv = fetch_full_conversation(root_id, access_token)
                except requests.HTTPError as e:
                    if e.response.status_code == 429:
                        time.sleep(2)
                        try:
                            conv = fetch_full_conversation(root_id, access_token)
                        except requests.HTTPError:
                            print(f"Warning: conversation for {root_id} skipped (rate limit)", file=sys.stderr)
                    else:
                        print(f"Warning: conversation for {root_id}: {e}", file=sys.stderr)
                for node in conv:
                    if node.get("id") == root_id:
                        continue
                    writer.writerow(row_from_media(node, root_id=root_id, parent_id=node.get("replied_to", ""), depth=1))
                    total_rows += 1
                time.sleep(0.3)

    return total_rows


def main():
    parser = argparse.ArgumentParser(
        description="Threadsアカウントの投稿をすべてCSVに抽出（ツリー投稿含む）。IDを指定するだけで実行できます。",
        epilog="※取得できるのは、使用するアクセストークンに紐づく「認証ユーザー自身」の投稿のみです。他アカウントの投稿はAPI仕様で取得できません。",
    )
    parser.add_argument(
        "user_id",
        nargs="?",
        default="me",
        help="抽出したいユーザー: ユーザーID / ユーザー名（例: nangoku3333）/ ThreadsプロフィールURL（省略時は me）",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="出力CSVファイルパス（未指定時は threads_<user_id>_export.csv）",
    )
    parser.add_argument(
        "-t", "--token",
        default=os.environ.get("THREADS_ACCESS_TOKEN"),
        help="Threads API アクセストークン（未指定時は環境変数 THREADS_ACCESS_TOKEN）",
    )
    parser.add_argument(
        "--no-trees",
        action="store_true",
        help="ツリー（リプライ）を取得せず、親投稿のみCSVに出力する",
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=None,
        metavar="N",
        help="取得する投稿数の上限（テスト用）",
    )
    args = parser.parse_args()

    if not args.token:
        print("エラー: アクセストークンが必要です。", file=sys.stderr)
        print("  -t TOKEN または環境変数 THREADS_ACCESS_TOKEN を設定してください。", file=sys.stderr)
        print("  取得方法: https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions/", file=sys.stderr)
        sys.exit(1)

    raw_input = (args.user_id or "me").strip() if isinstance(args.user_id, str) else "me"
    user_id_resolved, is_likely_id = normalize_user_input(raw_input)

    if not is_likely_id:
        print(f"ユーザー名 '{user_id_resolved}' からIDを解決しています…")
        try:
            user_id_resolved = profile_lookup(args.token, user_id_resolved)
            print(f"解決したユーザーID: {user_id_resolved}")
        except (requests.HTTPError, ValueError) as e:
            print(f"エラー: {e}", file=sys.stderr)
            sys.exit(1)

    user_id = user_id_resolved
    output_path = args.output or Path(f"threads_{user_id}_export.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"対象: {user_id}")
    print("投稿を取得しています…")

    try:
        n = export_to_csv(
            args.token,
            output_path,
            user_id=user_id,
            include_trees=not args.no_trees,
            max_posts=args.max_posts,
        )
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            err = e.response.json() if e.response.content else {}
            msg = err.get("error", {}).get("message", str(e))
            print(f"エラー: {msg}", file=sys.stderr)
            print("※他アカウントの投稿は取得できません。使用中のアクセストークンに紐づく「認証ユーザー自身」の投稿のみ取得可能です。", file=sys.stderr)
        else:
            print(f"APIエラー: {e}", file=sys.stderr)
        sys.exit(1)

    if n == 0:
        print("0件でした。指定したIDが認証ユーザー自身のものであるか、投稿が存在しない可能性があります。")
        print("※他アカウントのIDを指定しても投稿は取得できません。")
    else:
        print(f"完了: {n} 行を {output_path} に出力しました。")


if __name__ == "__main__":
    main()
