#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既に attachments に集約済みの画像への参照を ![[attachments/ファイル名]] に更新する。

実行:
  python tools/vault-image-utils/update_image_refs.py
"""
import re
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
ATTACHMENTS_DIR = VAULT / "attachments"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

def main():
    attachment_files = {f.name for f in ATTACHMENTS_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTS}
    print(f"attachments 内の画像数: {len(attachment_files)}")

    wikilink_pattern = re.compile(
        r'!?\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp))(?:\|[^\]]*)?\]\]',
        re.IGNORECASE
    )
    md_link_pattern = re.compile(
        r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|gif|webp))\)',
        re.IGNORECASE
    )

    updated = 0
    for md_path in VAULT.rglob("*.md"):
        if ".obsidian" in md_path.parts or "attachments" in md_path.parts:
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception:
            continue
        original = text

        def replace_wikilink(m):
            ref = m.group(1).split("|")[0].strip()
            base = Path(ref.replace("\\", "/")).name
            if base in attachment_files:
                return ("!" if m.group(0).startswith("!") else "") + f"[[attachments/{base}]]"
            return m.group(0)

        def replace_md_link(m):
            alt, url = m.group(1), m.group(2).strip()
            if url.startswith("http"):
                return m.group(0)
            base = Path(url.split("?")[0].replace("\\", "/")).name
            if base in attachment_files:
                return f'![{alt}](attachments/{base})'
            return m.group(0)

        text = wikilink_pattern.sub(replace_wikilink, text)
        text = md_link_pattern.sub(replace_md_link, text)
        if text != original:
            md_path.write_text(text, encoding="utf-8")
            updated += 1

    print(f"更新した md ファイル数: {updated}")

if __name__ == "__main__":
    main()
