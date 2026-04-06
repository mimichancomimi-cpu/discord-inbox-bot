#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSVチャットログと画像を時系列で1つのMarkdownにまとめる"""

import csv
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))  # brain の2つ上 = ボールト
ATTACHMENTS_DIR = os.path.join(VAULT, "attachments")
CSV_PATH = os.path.join(SCRIPT_DIR, "chatlogs-1333421829137633422-1333510266130006047.csv")
OUT_PATH = os.path.join(SCRIPT_DIR, "つきのわハウス mimiブレイン チャット履歴.md")

# attachments 内の画像ファイル名セット（画像はボールト直下の attachments に集約）
EXISTING_IMAGES = set()
if os.path.isdir(ATTACHMENTS_DIR):
    for name in os.listdir(ATTACHMENTS_DIR):
        if name.lower().endswith((".png", ".jpg", ".jpeg")) and not name.startswith("."):
            EXISTING_IMAGES.add(name)

def extract_filenames_from_attachments(attachments_str):
    """DiscordのURLからファイル名を抽出。例: .../IMG_9061.png?ex=... -> IMG_9061.png"""
    if not attachments_str or not attachments_str.strip():
        return []
    filenames = []
    # URLの形式: https://.../数字/FILENAME.png? または .../FILENAME.jpg&
    for part in re.split(r'[\s\n]+', attachments_str.strip()):
        part = part.strip().rstrip(",\"")
        if "discordapp.net" in part or "discord.com" in part:
            # 最後のスラッシュとクエリの間がファイル名
            m = re.search(r"/([^/]+\.(?:png|jpg|jpeg))(?:\?|&|$)", part, re.I)
            if m:
                fn = m.group(1)
                # ローカルに存在する場合のみ（大文字小文字・拡張子の違いを考慮）
                for existing in EXISTING_IMAGES:
                    if existing == fn or existing.lower() == fn.lower():
                        filenames.append(existing)
                        break
                else:
                    # 完全一致がなくてもファイル名そのもので存在すれば追加
                    if fn in EXISTING_IMAGES:
                        filenames.append(fn)
    return filenames

def escape_md(s):
    if not s:
        return ""
    return s.replace("\\", "\\\\")

def main():
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    lines = [
        "# つきのわハウス mimiブレイン チャット履歴",
        "",
        "ログの内容と画像を時系列で表示しています。",
        "",
        "---",
        ""
    ]

    for row in rows:
        date = (row.get("date") or "").strip()
        author = (row.get("authorName") or "").strip()
        content = (row.get("content") or "").strip()
        attachments_str = row.get("attachments") or ""

        # 見出し: 日時・投稿者
        lines.append(f"## {date} — {author}")
        lines.append("")

        if content:
            # 本文（改行をそのまま保持）
            lines.append(escape_md(content))
            lines.append("")

        filenames = extract_filenames_from_attachments(attachments_str)
        for fn in filenames:
            lines.append(f"![[attachments/{fn}]]")
            lines.append("")

        if not content and not filenames:
            lines.append("*（メッセージなし）*")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Done: {OUT_PATH}")
    print(f"Messages: {len(rows)}")

if __name__ == "__main__":
    main()
