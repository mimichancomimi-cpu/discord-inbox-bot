#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord サーバー内のメッセージを取得して Obsidian 用 Markdown に保存する。

機能:
- 指定 Guild の全テキスト系チャンネルを巡回
- 前回取得以降の差分だけ追記（state.json で管理）
- 初回は全履歴をバックフィル
- 任意で一定間隔ループ実行
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import certifi
import discord
from dotenv import load_dotenv

# python.org 版 Python での証明書エラー回避
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

VAULT_ROOT = Path(__file__).resolve().parents[3]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_jst_str(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    jst = timezone(timedelta(hours=9))
    return dt.astimezone(jst).strftime("%Y-%m-%d %H:%M:%S JST")


def sanitize_name(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|#]+', "_", name.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "unknown"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def escape_md(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def flatten_message_text(msg: discord.Message) -> str:
    parts: list[str] = []
    if msg.content:
        parts.append(msg.content)

    for emb in msg.embeds:
        if emb.title:
            parts.append(f"[embed-title] {emb.title}")
        if emb.description:
            parts.append(f"[embed] {emb.description}")
        if emb.url:
            parts.append(f"[embed-url] {emb.url}")

    for att in msg.attachments:
        parts.append(f"[attachment] {att.url}")

    return escape_md("\n".join(parts))


def message_to_block(msg: discord.Message) -> str:
    created = to_jst_str(msg.created_at)
    author = msg.author.display_name if hasattr(msg.author, "display_name") else msg.author.name
    body = flatten_message_text(msg)
    if not body:
        body = "*（本文なし）*"
    jump = msg.jump_url or ""
    return (
        f"## {created} — {author}\n\n"
        f"{body}\n\n"
        f"- message_id: `{msg.id}`\n"
        f"- jump_url: {jump}\n\n"
        f"---\n"
    )


@dataclass
class Config:
    token: str
    guild_id: int
    output_dir: Path
    state_path: Path
    include_threads: bool
    interval_sec: int


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    guild_id_raw = os.getenv("DISCORD_GUILD_ID", "").strip()
    output_dir_raw = Path(os.getenv("DISCORD_ARCHIVE_OUTPUT_DIR", "brain/つきのわハウス/Discordログ"))
    state_path_raw = Path(os.getenv("DISCORD_ARCHIVE_STATE_PATH", "brain/scripts/discord_obsidian_archiver/state.json"))
    include_threads = os.getenv("DISCORD_ARCHIVE_INCLUDE_THREADS", "1").strip() == "1"
    interval_raw = os.getenv("DISCORD_ARCHIVE_INTERVAL_SEC", "300").strip()

    if not token:
        raise ValueError("DISCORD_BOT_TOKEN が未設定です。")
    if not guild_id_raw.isdigit():
        raise ValueError("DISCORD_GUILD_ID が未設定か不正です。")
    if not interval_raw.isdigit():
        raise ValueError("DISCORD_ARCHIVE_INTERVAL_SEC は整数で設定してください。")

    output_dir = output_dir_raw if output_dir_raw.is_absolute() else VAULT_ROOT / output_dir_raw
    state_path = state_path_raw if state_path_raw.is_absolute() else VAULT_ROOT / state_path_raw

    return Config(
        token=token,
        guild_id=int(guild_id_raw),
        output_dir=output_dir,
        state_path=state_path,
        include_threads=include_threads,
        interval_sec=int(interval_raw),
    )


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"channels": {}, "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"channels": {}, "updated_at": None}


def save_state(path: Path, state: dict[str, Any]) -> None:
    ensure_parent(path)
    state["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def channel_output_path(base_dir: Path, channel: discord.abc.GuildChannel | discord.Thread) -> Path:
    cat = "threads" if isinstance(channel, discord.Thread) else "channels"
    name = sanitize_name(getattr(channel, "name", "unknown"))
    return base_dir / cat / f"{name}-{channel.id}.md"


def ensure_channel_header(path: Path, guild_name: str, channel_name: str, channel_id: int) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    ensure_parent(path)
    header = (
        f"# Discordログ: {channel_name}\n\n"
        f"- guild: {guild_name}\n"
        f"- channel_id: `{channel_id}`\n"
        f"- generated_by: `discord_obsidian_archiver`\n\n"
        f"---\n\n"
    )
    path.write_text(header, encoding="utf-8")


class ArchiverClient(discord.Client):
    def __init__(self, cfg: Config, once: bool) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.cfg = cfg
        self.once = once
        self.state = load_state(cfg.state_path)
        self._running = False

    async def on_ready(self) -> None:
        if self._running:
            return
        self._running = True
        print(f"[ready] login as {self.user}")

        try:
            if self.once:
                await self.run_sync_once()
            else:
                while True:
                    await self.run_sync_once()
                    print(f"[sleep] {self.cfg.interval_sec} sec")
                    await asyncio.sleep(self.cfg.interval_sec)
        finally:
            await self.close()

    async def run_sync_once(self) -> None:
        guild = self.get_guild(self.cfg.guild_id)
        if guild is None:
            raise RuntimeError("指定 guild が見つかりません。Botが参加済みか確認してください。")

        channels: list[discord.abc.GuildChannel | discord.Thread] = []
        for ch in guild.text_channels:
            channels.append(ch)

        if self.cfg.include_threads:
            for th in guild.threads:
                channels.append(th)

        print(f"[sync] guild={guild.name} channels={len(channels)}")

        for ch in channels:
            await self.sync_channel(guild, ch)

        save_state(self.cfg.state_path, self.state)
        print("[sync] completed")

    async def sync_channel(self, guild: discord.Guild, ch: discord.abc.GuildChannel | discord.Thread) -> None:
        cid = str(ch.id)
        last_id_raw = self.state.get("channels", {}).get(cid, {}).get("last_message_id")
        after_obj = discord.Object(id=int(last_id_raw)) if last_id_raw else None

        out = channel_output_path(self.cfg.output_dir, ch)
        ensure_channel_header(out, guild.name, getattr(ch, "name", "unknown"), ch.id)

        fetched: list[discord.Message] = []
        try:
            history_kwargs: dict[str, Any] = {"limit": None, "oldest_first": True}
            if after_obj is not None:
                history_kwargs["after"] = after_obj
            async for msg in ch.history(**history_kwargs):
                fetched.append(msg)
        except discord.Forbidden:
            print(f"[skip] no permission: {getattr(ch, 'name', ch.id)}")
            return
        except discord.HTTPException as e:
            print(f"[skip] http error {getattr(ch, 'name', ch.id)}: {e}")
            return

        if not fetched:
            print(f"[ok] {getattr(ch, 'name', ch.id)} no new messages")
            return

        blocks = [message_to_block(m) for m in fetched]
        with out.open("a", encoding="utf-8") as f:
            f.write("\n".join(blocks))

        newest = fetched[-1].id
        self.state.setdefault("channels", {})[cid] = {
            "channel_name": getattr(ch, "name", ""),
            "last_message_id": str(newest),
            "updated_at": utc_now_iso(),
        }
        print(f"[ok] {getattr(ch, 'name', ch.id)} +{len(fetched)}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Discord -> Obsidian archiver")
    p.add_argument("--once", action="store_true", help="1回だけ同期して終了")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config()
    client = ArchiverClient(cfg=cfg, once=args.once)
    client.run(cfg.token)


if __name__ == "__main__":
    main()
