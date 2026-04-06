#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
サービスアカウントで Google カレンダーに予定を1件追加する。

前提:
  - Google Cloud で Calendar API 有効化済み
  - 対象カレンダーをサービスアカウントの client_email に共有済み

接続確認（共有済みカレンダーが一覧に出るか）:
  python scripts/add_calendar_event.py --list-calendars

例（brain フォルダで実行）:
  python scripts/add_calendar_event.py \\
    --calendar-id "あなた@gmail.com" \\
    --summary "テスト" \\
    --start "2026-03-30T15:00:00" \\
    --end "2026-03-30T16:00:00"

calendar_config.json を置くと --calendar-id を省略できます（中身は calendar_config.example.json 参照）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def brain_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def default_credentials_path() -> Path:
    return brain_dir() / "credentials.json"


def load_calendar_config() -> dict[str, Any]:
    path = brain_dir() / "calendar_config.json"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_service(credentials_path: Path):
    creds = Credentials.from_service_account_file(
        str(credentials_path), scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def cmd_list_calendars(credentials_path: Path) -> None:
    if not credentials_path.is_file():
        raise SystemExit(f"認証ファイルが見つかりません: {credentials_path}")
    service = build_service(credentials_path)
    result = service.calendarList().list().execute()
    items = result.get("items", [])
    if not items:
        print(
            "カレンダーが0件です。Googleカレンダーで、対象カレンダーを"
            "サービスアカウントのメールに「予定の変更」で共有しているか確認してください。"
        )
        return
    print("アクセス可能なカレンダー（--calendar-id に使うのは「ID」列）:\n")
    for item in items:
        cid = item.get("id", "")
        summary = item.get("summary", "(無題)")
        primary = " ★primary" if item.get("primary") else ""
        print(f"  ID: {cid}")
        print(f"  名前: {summary}{primary}\n")


def main() -> None:
    cfg = load_calendar_config()
    cfg_creds = cfg.get("credentials_path")
    default_creds = Path(cfg_creds) if cfg_creds else default_credentials_path()
    if cfg_creds and not default_creds.is_absolute():
        default_creds = brain_dir() / default_creds

    parser = argparse.ArgumentParser(description="Google Calendar に予定を1件追加")
    parser.add_argument(
        "--list-calendars",
        action="store_true",
        help="サービスアカウントが触れるカレンダー一覧を表示して終了",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=default_creds,
        help="サービスアカウント JSON（デフォルト: brain/credentials.json または calendar_config.json）",
    )
    parser.add_argument(
        "--calendar-id",
        default=cfg.get("calendar_id") or None,
        help="カレンダー ID（calendar_config.json の calendar_id でも可）",
    )
    parser.add_argument("--summary", help="予定のタイトル")
    parser.add_argument(
        "--description",
        default="",
        help="説明（省略可）",
    )
    parser.add_argument(
        "--start",
        help="開始日時 ISO 8601 例: 2026-03-30T15:00:00",
    )
    parser.add_argument(
        "--end",
        help="終了日時 ISO 8601 例: 2026-03-30T16:00:00",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Tokyo",
        help="タイムゾーン（デフォルト: Asia/Tokyo）",
    )
    args = parser.parse_args()

    if args.list_calendars:
        cmd_list_calendars(args.credentials)
        return

    if not args.credentials.is_file():
        raise SystemExit(f"認証ファイルが見つかりません: {args.credentials}")

    if not args.calendar_id:
        raise SystemExit(
            "--calendar-id を指定するか、brain/calendar_config.json に calendar_id を書いてください。"
        )
    if not args.summary or not args.start or not args.end:
        raise SystemExit("--summary / --start / --end は必須です。")

    service = build_service(args.credentials)

    body: dict = {
        "summary": args.summary,
        "start": {"dateTime": args.start, "timeZone": args.timezone},
        "end": {"dateTime": args.end, "timeZone": args.timezone},
    }
    if args.description:
        body["description"] = args.description

    created = (
        service.events().insert(calendarId=args.calendar_id, body=body).execute()
    )
    link = created.get("htmlLink", "")
    print("作成しました:", link or created.get("id", created))


if __name__ == "__main__":
    main()
