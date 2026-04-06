#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidianボールト内の画像を1フォルダ（attachments）に集約し、
md内の参照を ![[attachments/ファイル名]] に更新する。

実行: リポジトリルート（Documents）がボールトの場合、
  python tools/vault-image-utils/consolidate_images.py
"""
import os
import re
import shutil
from pathlib import Path

# スクリプトは tools/vault-image-utils/ に置く。ボールト = Documents（attachments と brain の親）
VAULT = Path(__file__).resolve().parents[2]
ATTACHMENTS_DIR = VAULT / "attachments"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS

def vault_rel(path: Path) -> str:
    """絶対パスをボールト相対パスに（スラッシュ区切り）"""
    try:
        return path.resolve().relative_to(VAULT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()

def main():
    # 1) 画像ファイルを列挙（.obsidian は除く）
    image_files = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d != ".obsidian" and not d.startswith(".")]
        rootp = Path(root)
        for f in files:
            if Path(f).suffix.lower() in IMAGE_EXTS:
                image_files.append(rootp / f)

    print(f"画像ファイル数: {len(image_files)}")

    ATTACHMENTS_DIR.mkdir(exist_ok=True)
    # 2) 移動と名前衝突対策 → old_vault_rel -> new_basename のマップ
    old_to_new = {}
    used_basenames = {}

    for absp in sorted(image_files):
        try:
            rel = vault_rel(absp)
        except Exception:
            continue
        if rel.startswith("attachments/"):
            continue  # 既に attachments 内はスキップ
        base = absp.name
        # 衝突時: name_stem_1.ext, name_stem_2.ext ...
        dest_name = base
        if dest_name in used_basenames:
            stem, ext = os.path.splitext(base)
            n = used_basenames[base]
            while True:
                n += 1
                dest_name = f"{stem}_{n}{ext}"
                if dest_name not in used_basenames:
                    used_basenames[base] = n
                    used_basenames[dest_name] = 0
                    break
        else:
            used_basenames[dest_name] = 0
        dest_path = ATTACHMENTS_DIR / dest_name
        if absp.resolve() != dest_path.resolve():
            if dest_path.exists() and absp.resolve() != dest_path.resolve():
                # 既に別ソースで同名がある場合はリネーム
                stem, ext = os.path.splitext(dest_name)
                c = 1
                while dest_path.exists():
                    dest_name = f"{stem}_{c}{ext}"
                    dest_path = ATTACHMENTS_DIR / dest_name
                    c += 1
            shutil.move(str(absp), str(dest_path))
        rel_norm = rel.replace("\\", "/")
        old_to_new[rel_norm] = dest_name
        # brain/ なしの別名も登録（Nexus などが ![[Nexus/Attachments/...]] と書くため）
        if rel_norm.startswith("brain/"):
            old_to_new[rel_norm[6:]] = dest_name

    print(f"移動済み: {len(set(old_to_new.values()))} 件 → attachments/")

    # 3) マークダウン内の画像参照を置換
    # ![[path]] または [[path]] で .png/.jpg/.jpeg/.gif/.webp を含むもの
    wikilink_pattern = re.compile(
        r'!?\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp))(?:\|[^\]]*)?\]\]',
        re.IGNORECASE
    )
    md_link_pattern = re.compile(
        r'!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|gif|webp))\)',
        re.IGNORECASE
    )

    md_files = list(VAULT.rglob("*.md"))
    updated_count = 0
    for md_path in md_files:
        if ".obsidian" in md_path.parts or "attachments" in md_path.parts:
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception:
            continue
        note_dir_rel = vault_rel(md_path.parent)
        changed = False

        def replace_wikilink(m):
            ref = m.group(1).split("|")[0].strip()
            ref = ref.strip()
            if not ref:
                return m.group(0)
            # 試すパス: ボールト相対(refそのまま)、ノート相対(note_dir/ref)
            candidates = [ref.replace("\\", "/"), (Path(note_dir_rel) / ref).as_posix()]
            new_name = None
            for c in candidates:
                new_name = old_to_new.get(c)
                if new_name:
                    break
            if new_name:
                return ("!" if m.group(0).startswith("!") else "") + f"[[attachments/{new_name}]]"
            return m.group(0)

        def replace_md_link(m):
            alt, url = m.group(1), m.group(2).strip()
            if url.startswith("http"):
                return m.group(0)
            if "/" in url:
                resolved = (Path(note_dir_rel) / url).as_posix()
            else:
                resolved = (Path(note_dir_rel) / url).as_posix()
            resolved_norm = resolved.replace("\\", "/")
            new_name = old_to_new.get(resolved_norm) or old_to_new.get(resolved)
            if new_name:
                return f'![{alt}](attachments/{new_name})'
            return m.group(0)

        new_text = wikilink_pattern.sub(replace_wikilink, text)
        new_text = md_link_pattern.sub(replace_md_link, new_text)
        if new_text != text:
            md_path.write_text(new_text, encoding="utf-8")
            updated_count += 1

    print(f"更新した md ファイル数: {updated_count}")

if __name__ == "__main__":
    main()
