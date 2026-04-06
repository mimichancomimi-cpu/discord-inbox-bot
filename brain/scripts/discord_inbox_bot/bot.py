"""
Discord の指定チャンネルに投稿があったら、GitHub 上の1つの .md ファイル末尾に追記する Bot。

起動:  .env を用意してから
  cd brain/scripts/discord_inbox_bot && pip install -r requirements.txt && python bot.py

必要な Discord 設定: MESSAGE CONTENT INTENT をオン（Developer Portal → Bot）。
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import discord
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("discord_inbox")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ["GITHUB_REPO"].strip().strip("/")
FILE_PATH = os.environ.get("GITHUB_FILE_PATH", "brain/タスク管理/Discord自動受信箱.md").strip("/")
DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
STATE_FILE = Path(os.environ.get("STATE_FILE", ".state.json"))
if not STATE_FILE.is_absolute():
    STATE_FILE = Path(__file__).resolve().parent / STATE_FILE
ENABLE_CALENDAR_AUTO_ADD = os.environ.get("ENABLE_CALENDAR_AUTO_ADD", "1").strip() == "1"
CALENDAR_COMMAND_PREFIX = os.environ.get("CALENDAR_COMMAND_PREFIX", "予定:").strip()
CALENDAR_TIMEZONE = os.environ.get("CALENDAR_TIMEZONE", "Asia/Tokyo").strip() or "Asia/Tokyo"
CALENDAR_DEFAULT_DURATION_MIN = int(os.environ.get("CALENDAR_DEFAULT_DURATION_MIN", "60"))
ADD_CALENDAR_SCRIPT = Path(__file__).resolve().parents[1] / "add_calendar_event.py"
BRAIN_DIR = Path(__file__).resolve().parents[2]
TEAM_CONFIG_PATH = Path(
    os.environ.get(
        "TEAM_CONFIG_PATH",
        str(Path(__file__).resolve().parent / "team_channels.json"),
    )
)

LOCAL_FILE_PATH = Path(os.environ.get("LOCAL_FILE_PATH", "タスク管理/Discord自動受信箱.md"))
if not LOCAL_FILE_PATH.is_absolute():
    LOCAL_FILE_PATH = BRAIN_DIR / LOCAL_FILE_PATH
TASK_FILE_PATH = Path(os.environ.get("TASK_FILE_PATH", "タスク管理/自動タスク一覧.md"))
if not TASK_FILE_PATH.is_absolute():
    TASK_FILE_PATH = BRAIN_DIR / TASK_FILE_PATH

# タスク一覧 md を GitHub に同期するパス（単一チャンネルモード用）。空なら無効
_GH_TASK_RAW = os.environ.get(
    "GITHUB_TASK_FILE_PATH", "brain/タスク管理/自動タスク一覧.md"
).strip().strip("/")
GITHUB_TASK_REPO_PATH_DEFAULT: str | None = _GH_TASK_RAW if _GH_TASK_RAW else None

SUMMARY_POST_HOUR_JST = int(os.environ.get("SUMMARY_POST_HOUR_JST", "8"))
SUMMARY_POST_MINUTE_JST = int(os.environ.get("SUMMARY_POST_MINUTE_JST", "0"))

# 受信箱に「1行だけ」これらのいずれかを送ると、定時朝サマリーと同じ内容を summary_channel へ送る
_ON_DEMAND_DEFAULT = (
    "タスクサマリー",
    "タスク一覧",
    "今のタスク",
    "今のタスク一覧",
    "朝サマリー",
    "タスクまとめ",
    "サマリーテスト",  # 互換
)
_extra_kw = os.environ.get("SUMMARY_NOW_KEYWORDS", "").strip()
if _extra_kw:
    ON_DEMAND_SUMMARY_TRIGGERS = frozenset(
        _ON_DEMAND_DEFAULT + tuple(s.strip() for s in _extra_kw.split(",") if s.strip())
    )
else:
    ON_DEMAND_SUMMARY_TRIGGERS = frozenset(_ON_DEMAND_DEFAULT)

# モバイルIMEなどで混入しがちなゼロ幅文字を除く
_ZWSP_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def _normalize_on_demand_trigger_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = _ZWSP_RE.sub("", t)
    return t.strip()


def is_on_demand_summary_trigger(text: str) -> bool:
    raw = _normalize_on_demand_trigger_text(text)
    if not raw:
        return False
    # 本文が「トリガー1行だけ」（空行のみの続きは許可）
    nonempty = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if len(nonempty) != 1:
        return False
    return nonempty[0] in ON_DEMAND_SUMMARY_TRIGGERS


@dataclass(frozen=True)
class InboxRoute:
    """1 Discord チャンネル ↔ 受信箱・タスク一覧・（任意）GitHub パス。"""

    channel_id: int
    label: str
    local_path: Path
    task_path: Path
    github_repo_path: str | None
    github_task_path: str | None
    summary_channel_id: int


def _brain_rel_path(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else (BRAIN_DIR / p)


def load_inbox_routes() -> list[InboxRoute]:
    if TEAM_CONFIG_PATH.is_file():
        try:
            data = json.loads(TEAM_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            logging.getLogger("discord_inbox").exception(
                "Failed to parse team config: %s", TEAM_CONFIG_PATH
            )
        else:
            raw_channels = data.get("channels") or []
            if raw_channels:
                routes: list[InboxRoute] = []
                for idx, ch in enumerate(raw_channels):
                    cid = int(ch["discord_channel_id"])
                    label = str(ch.get("label", f"member{idx}"))
                    local_rel = str(ch.get("local_inbox", "タスク管理/Discord自動受信箱.md"))
                    task_rel = str(ch.get("task_file", "タスク管理/自動タスク一覧.md"))
                    gh = ch.get("github_file")
                    if gh is not None and str(gh).strip():
                        gh = str(gh).strip().strip("/")
                    else:
                        gh = None
                    sc = ch.get("summary_channel_id")
                    summary_cid = cid if sc is None else int(sc)
                    gh_task = ch.get("github_task_file")
                    if gh_task is not None and str(gh_task).strip():
                        gh_task = str(gh_task).strip().strip("/")
                    else:
                        gh_task = None
                    routes.append(
                        InboxRoute(
                            channel_id=cid,
                            label=label,
                            local_path=_brain_rel_path(local_rel),
                            task_path=_brain_rel_path(task_rel),
                            github_repo_path=gh,
                            github_task_path=gh_task,
                            summary_channel_id=summary_cid,
                        )
                    )
                logging.getLogger("discord_inbox").info(
                    "Team mode: %d inbox routes from %s", len(routes), TEAM_CONFIG_PATH
                )
                return routes
    cid = int(os.environ["DISCORD_CHANNEL_ID"])
    sum_cid = int(os.environ.get("SUMMARY_CHANNEL_ID", str(cid)))
    return [
        InboxRoute(
            channel_id=cid,
            label="default",
            local_path=LOCAL_FILE_PATH,
            task_path=TASK_FILE_PATH,
            github_repo_path=FILE_PATH,
            github_task_path=GITHUB_TASK_REPO_PATH_DEFAULT,
            summary_channel_id=sum_cid,
        )
    ]


INBOX_ROUTES: list[InboxRoute] = load_inbox_routes()
CHANNEL_ID = INBOX_ROUTES[0].channel_id
SUMMARY_CHANNEL_ID = INBOX_ROUTES[0].summary_channel_id

DEFAULT_HEADER = """# Discord自動受信箱（Botが追記）

GitHub 上のこのファイルに、指定 Discord チャンネルの投稿が追記されます。PC では `git pull` または Obsidian Git で取り込んでください。

---

"""

_write_lock = asyncio.Lock()
_catchup_lock = asyncio.Lock()
_summary_task: asyncio.Task | None = None


def _contents_url_for(repo_path: str) -> str:
    encoded = "/".join(quote(seg, safe="") for seg in repo_path.split("/"))
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{encoded}"


def _github_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "discord-vault-inbox-bot",
    }


def github_get_file(repo_path: str) -> tuple[str | None, str]:
    req = Request(_contents_url_for(repo_path), headers=_github_headers(), method="GET")
    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        sha = data.get("sha")
        raw = base64.b64decode(data["content"]).decode("utf-8")
        return sha, raw
    except HTTPError as e:
        if e.code == 404:
            return None, ""
        raise


def github_put_file(
    content: str, sha: str | None, commit_message: str, repo_path: str
) -> None:
    body: dict = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        body["sha"] = sha
    payload = json.dumps(body).encode("utf-8")
    req = Request(
        _contents_url_for(repo_path),
        data=payload,
        headers={**_github_headers(), "Content-Type": "application/json"},
        method="PUT",
    )
    with urlopen(req) as resp:
        resp.read()


def sanitize_for_line(text: str, max_len: int = 800) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


def strip_leading_task_tag(text: str) -> str:
    return re.sub(r"^【[^】]+】\s*", "", text.strip())


def normalize_text_for_match(text: str) -> str:
    s = text.strip()
    s = re.sub(r"(は)?(終わりました|完了しました|終わった|完了|できました|できた|done)$", "", s)
    s = re.sub(r"[\s　・,，。!！?？:：\-\(\)\[\]【】「」『』/／]+", "", s)
    return s.lower()


def is_completion_message(text: str) -> bool:
    return bool(re.search(r"(終わりました|完了しました|終わった|完了|できました|できた|done)", text))


def classify_task_bucket(text: str) -> str:
    if re.search(r"(待ち|返答待ち|返信待ち|確認待ち)", text):
        return "waiting"
    if re.search(r"(今週|今週中|今月)", text):
        return "week"
    return "today"


def _is_report_only_sentence(s: str) -> bool:
    """完了報告・自己称賛のみで、これからやる行為が含まれない文。"""
    s = s.strip()
    if not s:
        return False
    if re.match(r"^(やった|えらい)[!！]?\s*$", s):
        return True
    if re.search(
        r"(する|やる|対応|共有|連絡|作成|送る|確認|調整|予定|入れる|依頼|追加|リスト|見る|みる|シェア|送付|提案|準備|検討|決める|調べる|書く|作る)",
        s,
    ):
        return False
    core = re.sub(r"[。！？]+\s*$", "", s)
    if re.search(
        r"(書きました|できました|できた|終わった|提出した|完了しました|えらい[!！]?)\s*$",
        core,
    ):
        return True
    return False


def extract_actionable_task_memo(text: str) -> str | None:
    """
    メモ全文から、自動タスク一覧に載せるべき本文だけを取り出す。
    報告・称賛のみのときは None（一覧に追記しない）。
    """
    t = re.sub(r"\s+", " ", text.strip())
    if not t:
        return None

    marker_patterns = (
        r"後タスク\s*(.+)",
        r"次のタスク\s*(.+)",
        r"次タスク\s*(.+)",
        r"次は\s*(.+)",
        r"あと(?:で)?タスク\s*(.+)",
        r"やること\s*[:：]\s*(.+)",
        r"次やること\s*[:：]\s*(.+)",
        r"TODO\s*[:：]\s*(.+)",
        r"todo\s*[:：]\s*(.+)",
    )
    for pat in marker_patterns:
        m = re.search(pat, t, re.I)
        if m:
            rest = m.group(1).strip()
            if rest:
                return rest

    parts = re.split(r"(?<=[。！？])\s*", t)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2:
        kept = [p for p in parts if not _is_report_only_sentence(p)]
        if kept:
            merged = " ".join(kept)
            if merged != t:
                return merged
        if not kept:
            return None

    if _is_report_only_sentence(t):
        return None

    return t


def _trim_task_filler(s: str) -> str:
    """タスク行末尾の口語・依頼表現を薄める（一覧向け）。"""
    s = s.strip()
    s = re.sub(
        r"(お願いします|ください|したいです|したい|です|ます|でした|だよ|ですよ)\s*$",
        "",
        s,
    )
    return s.strip()


def summarize_memo_to_task_line(body: str, max_len: int = 120) -> str:
    """
    Discord メモ本文を、自動タスク一覧用の1行に要約・整理する。
    API は使わず、句読点・長さで圧縮する。
    """
    s = body.strip()
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)

    def finish(part: str) -> str:
        part = _trim_task_filler(part)
        if len(part) > max_len:
            return part[: max_len - 1] + "…"
        return part

    if len(s) <= max_len:
        return finish(s)

    # 最初の文（。！？まで）を優先
    m = re.match(r"^(.+?[。！？])(.+)$", s)
    if m:
        first = m.group(1).strip()
        if len(first) <= max_len:
            return finish(first)

    # 読点区切りで先頭から詰める
    if "、" in s:
        acc = ""
        for i, chunk in enumerate(s.split("、")):
            cand = chunk if not acc else acc + "、" + chunk
            if len(cand) <= max_len - 1:
                acc = cand
            else:
                break
        if acc:
            return finish(acc + ("…" if len(acc) < len(s) else ""))

    # 句点のみ長い1文
    cut = s[: max_len - 1].rstrip()
    if " " in cut:
        cut = cut[: cut.rfind(" ")].rstrip()
    return finish(cut + "…")


def parse_task_content(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^(タスク|todo|TODO)\s*[:：]?\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""
    extracted = extract_actionable_task_memo(t)
    if extracted is None or not extracted.strip():
        return ""
    extracted = extracted.strip()
    body_for_summarize = strip_leading_task_tag(extracted).strip() or extracted

    um = re.match(r"^(【[^】]+】)\s*(.+)$", t)
    if um:
        user_tag = um.group(1)
        summarized = summarize_memo_to_task_line(body_for_summarize)
        if not summarized:
            return user_tag
        return f"{user_tag} {summarized}".strip()
    tag = infer_task_tag(t)
    summarized = summarize_memo_to_task_line(body_for_summarize)
    if not summarized:
        return add_task_prefix_if_missing(extracted)
    return f"{tag} {summarized}".strip()


def add_task_prefix_if_missing(text: str) -> str:
    if re.match(r"^【[^】]+】", text):
        return text

    tag = infer_task_tag(text)
    if not tag:
        return text
    return f"{tag} {text}"


def infer_task_tag(text: str) -> str:
    if re.search(r"(つきのわ|つきのわハウス|ハウス)", text):
        return "【つ】"
    if re.search(r"(mimi|メルマガ|line|個別サポート|メソッド|宴メルマガ)", text, re.I):
        return "【m】"
    if re.search(r"(ノゾミ|のぞみ)", text):
        return "【ノ】"
    if re.search(r"(たかだ)", text):
        return "【た】"
    if re.search(r"(シナ|しな)", text):
        return "【シ】"
    if re.search(r"(私用|家|買い物|病院|プライベート)", text):
        return "【プ】"
    return "【m】"


def ensure_task_file(task_path: Path) -> None:
    if task_path.exists():
        return
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        "# 自動タスク一覧\n\n"
        "## 今日やる\n\n"
        "## 待ち\n\n"
        "## 今週\n\n"
        "## 完了ログ\n\n",
        encoding="utf-8",
    )


def add_task_to_file(task_text: str, bucket: str, task_path: Path) -> bool:
    ensure_task_file(task_path)
    content = task_path.read_text(encoding="utf-8")
    if task_text in content:
        return False

    jst = timezone(timedelta(hours=9))
    ts = datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")
    line = f"- [ ] {task_text}｜作成:{ts}"
    sections = {
        "today": "## 今日やる",
        "waiting": "## 待ち",
        "week": "## 今週",
    }
    marker = sections[bucket]
    idx = content.find(marker)
    if idx == -1:
        content += f"\n{marker}\n\n{line}\n"
    else:
        insert_at = content.find("\n## ", idx + len(marker))
        if insert_at == -1:
            insert_at = len(content)
        block = content[idx:insert_at].rstrip() + "\n" + line + "\n"
        content = content[:idx] + block + content[insert_at:]
    task_path.write_text(content, encoding="utf-8")
    return True


def complete_task_in_file(message_text: str, task_path: Path) -> bool:
    if not task_path.exists():
        return False
    content = task_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    key = normalize_text_for_match(strip_leading_task_tag(message_text))
    if not key:
        return False

    done_any = False
    jst = timezone(timedelta(hours=9))
    ts = datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")
    completed_lines: list[str] = []
    kept_lines: list[str] = []
    for ln in lines:
        if not ln.startswith("- [ ] "):
            kept_lines.append(ln)
            continue
        base = ln[6:].split("｜", 1)[0].strip()
        if not base:
            kept_lines.append(ln)
            continue
        base_norm = normalize_text_for_match(strip_leading_task_tag(base))
        if base_norm in key or key in base_norm:
            done_line = ln.replace("- [ ]", "- [x]", 1) + f"｜完了:{ts}"
            completed_lines.append(done_line)
            done_any = True
        else:
            kept_lines.append(ln)

    if not done_any:
        return False

    out = "\n".join(kept_lines)
    done_header = "## 完了ログ"
    idx = out.find(done_header)
    if idx == -1:
        out += "\n\n## 完了ログ\n\n"
        idx = out.find(done_header)
    end_idx = len(out)
    done_block = out[idx:end_idx].rstrip() + "\n" + "\n".join(completed_lines) + "\n"
    out = out[:idx] + done_block
    task_path.write_text(out + ("\n" if not out.endswith("\n") else ""), encoding="utf-8")
    return True


def format_append_line(author_name: str, text: str) -> str:
    jst = timezone(timedelta(hours=9))
    ts = datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")
    safe = sanitize_for_line(text)
    return f"- [ ] [Discord {ts}] {author_name}: {safe}"


async def append_to_github(author_name: str, text: str, repo_path: str | None) -> None:
    if not repo_path:
        return
    line = format_append_line(author_name, text)
    loop = asyncio.get_event_loop()

    def _do() -> None:
        sha, existing = github_get_file(repo_path)
        if not existing.strip():
            body = DEFAULT_HEADER + line + "\n"
            github_put_file(body, None, "discord-inbox: create file", repo_path)
            return
        body = existing.rstrip() + "\n" + line + "\n"
        github_put_file(body, sha, "discord-inbox: append message", repo_path)

    await loop.run_in_executor(None, _do)


async def append_to_local_file(author_name: str, text: str, local_path: Path) -> None:
    line = format_append_line(author_name, text)
    loop = asyncio.get_event_loop()

    def _do() -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with local_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    await loop.run_in_executor(None, _do)


async def push_task_file_to_github(route: InboxRoute) -> bool:
    """ローカルの task_path の内容を GitHub 上の github_task_path に丸ごと反映する。"""
    rpath = route.github_task_path
    if not rpath or not route.task_path.exists():
        return True
    loop = asyncio.get_event_loop()

    def _do() -> None:
        content = route.task_path.read_text(encoding="utf-8")
        sha, _ = github_get_file(rpath)
        github_put_file(content, sha, "discord-inbox: sync task list", rpath)

    try:
        await loop.run_in_executor(None, _do)
        return True
    except Exception:
        log.exception("Failed to push task file to GitHub: %s", rpath)
        return False


def parse_calendar_request(text: str) -> dict[str, str] | None:
    """
    フォーマット:
    予定: タイトル | 2026-04-01T20:00:00 | 2026-04-01T21:00:00 | 説明(任意)

    「予定」なしでも、行全体が M/D + 時刻 + 件名（または明日/金曜 + 時刻 + 件名、
    またはタイトル|ISO|ISO）ならカレンダー登録対象とする。
    例: 4/4 21:00-22:10 りささん個別コンサル
    """
    raw = text.strip()
    body = ""
    if raw.startswith(CALENDAR_COMMAND_PREFIX):
        body = raw[len(CALENDAR_COMMAND_PREFIX) :].strip()
    elif raw.startswith("予定 "):
        body = raw[len("予定 ") :].strip()
    else:
        # 予定プレフィックスなしの「日付 時刻 タイトル」行も受け付ける
        body = raw

    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)

    # かんたん入力:
    # 予定 4/1 12:00病院
    # 予定 4/1 12:00 病院
    # 予定 4/1 12:00-13:00 病院
    quick = re.match(
        r"^(?P<md>\d{1,2}/\d{1,2})\s+(?P<start>\d{1,2}:\d{2})(?:\s*[-〜~]\s*(?P<end>\d{1,2}:\d{2}))?\s*(?P<title>.+)$",
        body,
    )
    if quick:
        month, day = [int(v) for v in quick.group("md").split("/")]
        start_h, start_m = [int(v) for v in quick.group("start").split(":")]
        end_raw = quick.group("end")
        title = quick.group("title").strip()
        if not title:
            return None

        year = now_jst.year
        start_dt = datetime(year, month, day, start_h, start_m, 0, tzinfo=jst)
        # すでに大きく過去なら翌年扱いにする（年またぎ入力の取りこぼし対策）
        if start_dt < now_jst - timedelta(days=1):
            start_dt = datetime(year + 1, month, day, start_h, start_m, 0, tzinfo=jst)

        if end_raw:
            end_h, end_m = [int(v) for v in end_raw.split(":")]
            end_dt = start_dt.replace(hour=end_h, minute=end_m, second=0)
            if end_dt <= start_dt:
                end_dt = end_dt + timedelta(days=1)
        else:
            end_dt = start_dt + timedelta(minutes=CALENDAR_DEFAULT_DURATION_MIN)

        return {
            "summary": title,
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "description": "",
        }

    # 自然入力:
    # 予定 明日 10:00 歯医者
    # 予定 金曜 14:00 MTG
    natural = re.match(
        r"^(?P<dateword>明日|あした|今日|きょう|本日|(?:月|火|水|木|金|土|日)(?:曜(?:日)?)?)\s+(?P<start>\d{1,2}:\d{2})(?:\s*[-〜~]\s*(?P<end>\d{1,2}:\d{2}))?\s+(?P<title>.+)$",
        body,
    )
    if natural:
        dateword = natural.group("dateword")
        start_h, start_m = [int(v) for v in natural.group("start").split(":")]
        end_raw = natural.group("end")
        title = natural.group("title").strip()
        if not title:
            return None

        weekday_map = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}
        if dateword in {"今日", "きょう", "本日"}:
            base_date = now_jst.date()
        elif dateword in {"明日", "あした"}:
            base_date = (now_jst + timedelta(days=1)).date()
        else:
            wd = weekday_map[dateword[0]]
            delta = (wd - now_jst.weekday()) % 7
            base_date = (now_jst + timedelta(days=delta)).date()
            # 同曜日で時刻が過去なら翌週
            if delta == 0 and (start_h, start_m) <= (now_jst.hour, now_jst.minute):
                base_date = (now_jst + timedelta(days=7)).date()

        start_dt = datetime(
            base_date.year, base_date.month, base_date.day, start_h, start_m, 0, tzinfo=jst
        )
        if end_raw:
            end_h, end_m = [int(v) for v in end_raw.split(":")]
            end_dt = start_dt.replace(hour=end_h, minute=end_m, second=0)
            if end_dt <= start_dt:
                end_dt = end_dt + timedelta(days=1)
        else:
            end_dt = start_dt + timedelta(minutes=CALENDAR_DEFAULT_DURATION_MIN)

        return {
            "summary": title,
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "description": "",
        }

    # 厳密入力:
    # 予定: タイトル | 2026-04-01T20:00:00 | 2026-04-01T21:00:00 | 説明(任意)
    parts = [p.strip() for p in body.split("|")]
    if len(parts) < 3:
        return None

    summary, start_iso, end_iso = parts[:3]
    if not summary or not start_iso or not end_iso:
        return None

    description = parts[3] if len(parts) >= 4 else ""
    return {
        "summary": summary,
        "start": start_iso,
        "end": end_iso,
        "description": description,
    }


async def maybe_add_calendar_event(text: str) -> bool:
    if not ENABLE_CALENDAR_AUTO_ADD:
        return False

    req = parse_calendar_request(text)
    if req is None:
        return False

    if not ADD_CALENDAR_SCRIPT.exists():
        log.error("Calendar script not found: %s", ADD_CALENDAR_SCRIPT)
        return False

    cmd = [
        sys.executable,
        str(ADD_CALENDAR_SCRIPT),
        "--summary",
        req["summary"],
        "--start",
        req["start"],
        "--end",
        req["end"],
        "--timezone",
        CALENDAR_TIMEZONE,
    ]
    if req["description"]:
        cmd.extend(["--description", req["description"]])

    loop = asyncio.get_event_loop()

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=str(ADD_CALENDAR_SCRIPT.parent.parent),  # brain/scripts -> brain
            check=False,
        )

    result = await loop.run_in_executor(None, _run)
    if result.returncode != 0:
        log.error("Calendar add failed: %s", (result.stderr or result.stdout).strip())
        return False

    log.info("Calendar event created: %s", (result.stdout or "").strip())
    return True


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_last_message_id_for(channel_id: int) -> int | None:
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        by = data.get("last_message_by_channel") or {}
        key = str(channel_id)
        if key in by:
            return int(by[key])
        legacy = data.get("last_message_id")
        if legacy and channel_id == INBOX_ROUTES[0].channel_id:
            return int(legacy)
        return None
    except Exception:
        log.exception("Failed to read state file: %s", STATE_FILE)
        return None


def save_last_message_id_for(channel_id: int, message_id: int) -> None:
    state = load_state()
    if "last_message_by_channel" not in state:
        state["last_message_by_channel"] = {}
    state["last_message_by_channel"][str(channel_id)] = str(message_id)
    save_state(state)


def get_last_summary_date_for(channel_id: int) -> str | None:
    state = load_state()
    by = state.get("last_summary_date_by_channel") or {}
    key = str(channel_id)
    if key in by:
        return str(by[key])
    legacy = state.get("last_summary_date")
    return str(legacy) if legacy else None


def set_last_summary_date_for(channel_id: int, date_str: str) -> None:
    state = load_state()
    if "last_summary_date_by_channel" not in state:
        state["last_summary_date_by_channel"] = {}
    state["last_summary_date_by_channel"][str(channel_id)] = date_str
    state["last_summary_date"] = date_str
    save_state(state)


def _task_lines_for_display(items: list[str]) -> list[str]:
    """メタ情報（｜以降）を除いた表示用1行テキスト（全件）。"""
    return [i.split("｜", 1)[0].strip() for i in items]


def build_daily_summary_text(route: InboxRoute) -> str:
    task_path = route.task_path
    local_path = route.local_path
    name = route.label
    if task_path.exists():
        content = task_path.read_text(encoding="utf-8")
        today = re.findall(r"^- \[ \] (.+)$", _section_text(content, "## 今日やる"), flags=re.M)
        waiting = re.findall(r"^- \[ \] (.+)$", _section_text(content, "## 待ち"), flags=re.M)
        week = re.findall(r"^- \[ \] (.+)$", _section_text(content, "## 今週"), flags=re.M)

        def fmt(label: str, items: list[str]) -> str:
            if not items:
                return f"**{label}**\n- なし"
            return "**" + label + "**\n" + "\n".join(f"- {v}" for v in items)

        jst = timezone(timedelta(hours=9))
        date_str = datetime.now(jst).strftime("%Y-%m-%d")
        header = (
            f"おはようございます。{date_str} 【{name}】のタスク要約です。\n\n"
            if name != "default"
            else f"おはようございます。{date_str} のタスク要約です。\n\n"
        )
        return (
            header
            + fmt("今日やる", _task_lines_for_display(today))
            + "\n\n"
            + fmt("待ち", _task_lines_for_display(waiting))
            + "\n\n"
            + fmt("今週", _task_lines_for_display(week))
        )

    if not local_path.exists():
        return "おはようございます。まだ受信箱メモはありません。"

    text = local_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries: list[str] = []
    for ln in lines:
        if not ln.startswith("- [ ] [Discord "):
            continue
        parts = ln.split(": ", 1)
        if len(parts) != 2:
            continue
        entries.append(parts[1].strip())

    if not entries:
        return "おはようございます。まだ受信箱メモはありません。"

    today: list[str] = []
    waiting: list[str] = []
    week: list[str] = []
    for e in entries:
        if re.search(r"(待ち|返答待ち|確認待ち|返信待ち)", e):
            waiting.append(e)
        elif re.search(r"(今週|今週中)", e):
            week.append(e)
        elif re.search(r"(今日|本日|至急|明日)", e):
            today.append(e)
        else:
            today.append(e)

    def fmt(label: str, items: list[str]) -> str:
        if not items:
            return f"**{label}**\n- なし"
        return "**" + label + "**\n" + "\n".join(f"- {v}" for v in items)

    jst = timezone(timedelta(hours=9))
    date_str = datetime.now(jst).strftime("%Y-%m-%d")
    memo_header = (
        f"おはようございます。{date_str} 【{name}】のメモ要約です。\n\n"
        if name != "default"
        else f"おはようございます。{date_str} のメモ要約です。\n\n"
    )
    return (
        memo_header
        + fmt("今日やる", today)
        + "\n\n"
        + fmt("待ち", waiting)
        + "\n\n"
        + fmt("今週", week)
    )


def _section_text(content: str, header: str) -> str:
    start = content.find(header)
    if start == -1:
        return ""
    end = content.find("\n## ", start + len(header))
    if end == -1:
        end = len(content)
    return content[start:end]


async def daily_summary_loop() -> None:
    jst = timezone(timedelta(hours=9))
    while True:
        now = datetime.now(jst)
        today_target = now.replace(
            hour=SUMMARY_POST_HOUR_JST,
            minute=SUMMARY_POST_MINUTE_JST,
            second=0,
            microsecond=0,
        )
        today_key = now.strftime("%Y-%m-%d")

        if now >= today_target:
            for route in INBOX_ROUTES:
                if get_last_summary_date_for(route.channel_id) == today_key:
                    continue
                try:
                    ok = await send_summary_once(test_mode=False, route=route)
                    if ok:
                        set_last_summary_date_for(route.channel_id, today_key)
                        log.info(
                            "Posted daily summary for %s (%s)", today_key, route.label
                        )
                    else:
                        await asyncio.sleep(60)
                        break
                except Exception:
                    await asyncio.sleep(60)
                    break

        next_target = today_target if now < today_target else today_target + timedelta(days=1)
        wait_sec = max(1.0, (next_target - datetime.now(jst)).total_seconds())
        await asyncio.sleep(wait_sec)


def split_discord_message(text: str, max_len: int = 1900) -> list[str]:
    """Discord 2000文字上限を超えないよう、朝サマリーなどを複数メッセージに分割する。"""
    text = text.rstrip()
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= max_len:
            chunks.append(rest)
            break
        cut = rest.rfind("\n", 0, max_len + 1)
        if cut <= 0:
            chunks.append(rest[:max_len])
            rest = rest[max_len:].lstrip("\n")
        else:
            chunks.append(rest[:cut])
            rest = rest[cut + 1 :]
    return chunks


async def send_summary_once(
    test_mode: bool = False,
    reply_channel: discord.abc.Messageable | None = None,
    route: InboxRoute | None = None,
) -> bool:
    """
    定時朝サマリー: 各 route の summary_channel_id へ。
    随時トリガー（タスクサマリー等）: 同じく summary_channel_id へ。
    reply_channel を渡したときだけそのチャンネルへ（デバッグ用）。
    """
    r = route or INBOX_ROUTES[0]
    target_id = r.summary_channel_id
    channel: discord.abc.Messageable | None = None
    if test_mode and reply_channel is not None:
        channel = reply_channel
    else:
        channel = client.get_channel(target_id)
        if channel is None:
            try:
                channel = await client.fetch_channel(target_id)
            except Exception:
                log.exception("Failed to fetch summary channel: %s", target_id)
                return False
    if not hasattr(channel, "send"):
        log.error("Summary target cannot send: %s", getattr(channel, "id", target_id))
        return False
    if not test_mode and not isinstance(channel, discord.TextChannel):
        log.error("Scheduled summary needs a text channel: %s", target_id)
        return False

    resolved_id = getattr(channel, "id", None)
    log.info(
        "Summary post: route=%s inbox_id=%s -> target_summary_id=%s resolved_channel_id=%s test_mode=%s",
        r.label,
        r.channel_id,
        target_id,
        resolved_id,
        test_mode,
    )
    if reply_channel is None and resolved_id == r.channel_id:
        log.warning(
            "Summary posts to the SAME channel as the memo inbox (IDs match). "
            "Fix summary_channel_id in team_channels.json — Discord: right-click the DESTINATION channel → Copy ID."
        )

    text = build_daily_summary_text(r)
    if test_mode:
        text = "【随時タスクサマリー】\n\n" + text

    try:
        for part in split_discord_message(text):
            await channel.send(part)
        return True
    except Exception:
        log.exception("Failed to post summary")
        return False



async def append_message_and_mark_processed(
    message: discord.Message, route: InboxRoute
) -> tuple[bool, bool]:
    author = message.author.display_name or message.author.name
    text = message.content

    local_ok = False
    github_ok = False

    try:
        await append_to_local_file(author, text, route.local_path)
        local_ok = True
    except Exception:
        log.exception("Failed to append to local file: %s", route.local_path)

    try:
        if route.github_repo_path:
            await append_to_github(author, text, route.github_repo_path)
            github_ok = True
        else:
            github_ok = True
    except Exception:
        log.exception("Failed to append to GitHub")

    if not local_ok and not github_ok:
        raise RuntimeError("Both local and GitHub append failed")

    save_last_message_id_for(route.channel_id, message.id)
    return local_ok, github_ok


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def post_process_inbox_message(
    message: discord.Message,
    local_ok: bool,
    github_ok: bool,
    route: InboxRoute,
) -> None:
    """追記後のカレンダー・タスク同期・リアクション（on_message と catch-up 共通）。"""
    calendar_created = await maybe_add_calendar_event(message.content)
    task_added = False
    task_done = False
    try:
        text = message.content.strip()
        if not parse_calendar_request(text):
            if is_completion_message(text):
                task_done = complete_task_in_file(text, route.task_path)
            else:
                task_text = parse_task_content(text)
                if task_text:
                    task_added = add_task_to_file(
                        task_text,
                        classify_task_bucket(text),
                        route.task_path,
                    )
    except Exception:
        log.exception("Task sync failed")

    if (task_added or task_done) and route.github_task_path:
        task_gh_ok = await push_task_file_to_github(route)
        if not task_gh_ok:
            log.warning(
                "Task list not synced to GitHub (route=%s file=%s)",
                route.label,
                route.github_task_path,
            )

    try:
        if local_ok and github_ok:
            await message.add_reaction("✅")
        elif local_ok:
            await message.add_reaction("📝")
        else:
            await message.add_reaction("⚠️")
        if calendar_created:
            await message.add_reaction("🗓️")
        if task_added:
            await message.add_reaction("📌")
        if task_done:
            await message.add_reaction("☑️")
    except discord.HTTPException:
        pass


async def fetch_channel_by_id(cid: int) -> discord.TextChannel | None:
    channel = client.get_channel(cid)
    if channel is None:
        try:
            channel = await client.fetch_channel(cid)
        except Exception:
            log.exception("Failed to fetch channel %s", cid)
            return None
    if not isinstance(channel, discord.TextChannel):
        log.error("Channel %s is not a text channel", cid)
        return None
    return channel


def route_for_channel_id(channel_id: int) -> InboxRoute | None:
    for r in INBOX_ROUTES:
        if r.channel_id == channel_id:
            return r
    return None


async def run_catch_up_for_route(route: InboxRoute, reason: str) -> None:
    channel = await fetch_channel_by_id(route.channel_id)
    if channel is None:
        return

    last_message_id = load_last_message_id_for(route.channel_id)
    if last_message_id is None:
        return

    pending_messages: list[discord.Message] = []
    async for msg in channel.history(
        limit=None,
        oldest_first=True,
        after=discord.Object(id=last_message_id),
    ):
        if msg.author.bot:
            continue
        if not msg.content or not msg.content.strip():
            continue
        pending_messages.append(msg)

    if not pending_messages:
        return

    log.info(
        "Catch-up started (%s) [%s]: %d messages",
        reason,
        route.label,
        len(pending_messages),
    )
    for msg in pending_messages:
        if is_on_demand_summary_trigger(msg.content):
            # 定時朝サマリーと同じ summary_channel_id へ送る（受信箱ではなくサマリー用チャンネル）
            ok = await send_summary_once(test_mode=True, route=route)
            try:
                await msg.add_reaction("✅" if ok else "⚠️")
            except discord.HTTPException:
                pass
            save_last_message_id_for(route.channel_id, msg.id)
            continue

        local_ok = True
        github_ok = True
        async with _write_lock:
            try:
                local_ok, github_ok = await append_message_and_mark_processed(msg, route)
                log.info("Caught up [%s]: %s", route.label, msg.id)
                if not local_ok:
                    log.warning("Catch-up local append failed: %s", msg.id)
                if not github_ok:
                    log.warning("Catch-up GitHub append failed: %s", msg.id)
            except Exception:
                log.exception("Failed during catch-up for message %s", msg.id)
                break
        await post_process_inbox_message(msg, local_ok, github_ok, route)

    log.info("Catch-up finished (%s) [%s]", reason, route.label)


async def run_inbox_catch_up(reason: str) -> None:
    """
    各ルートのチャンネルを遡り、受信箱追記・カレンダー・タスクを同期する。
    """
    global _summary_task
    async with _catchup_lock:
        for route in INBOX_ROUTES:
            await run_catch_up_for_route(route, reason)
        if _summary_task is None or _summary_task.done():
            _summary_task = asyncio.create_task(daily_summary_loop())


@client.event
async def on_ready() -> None:
    log.info("Logged in as %s", client.user)
    for route in INBOX_ROUTES:
        channel = await fetch_channel_by_id(route.channel_id)
        if channel is None:
            continue
        if load_last_message_id_for(route.channel_id) is not None:
            continue
        latest = None
        async for msg in channel.history(limit=1):
            latest = msg
            break
        if latest:
            save_last_message_id_for(route.channel_id, latest.id)
            log.info(
                "Initialized state [%s] with latest message id: %s",
                route.label,
                latest.id,
            )

    await run_inbox_catch_up("on_ready")


@client.event
async def on_resumed() -> None:
    """スリープなどで接続が切れたあとセッションが RESUME されたときに再取得する。"""
    log.info("Gateway resumed; inbox catch-up")
    await run_inbox_catch_up("on_resumed")


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return
    route = route_for_channel_id(message.channel.id)
    if route is None:
        return
    if not message.content or not message.content.strip():
        return
    if is_on_demand_summary_trigger(message.content):
        ok = await send_summary_once(test_mode=True, route=route)
        try:
            await message.add_reaction("✅" if ok else "⚠️")
        except discord.HTTPException:
            pass
        save_last_message_id_for(route.channel_id, message.id)
        return

    local_ok = True
    github_ok = True
    async with _write_lock:
        try:
            local_ok, github_ok = await append_message_and_mark_processed(message, route)
            log.info("Appended from %s [%s]", message.id, route.label)
        except Exception:
            local_ok = False
            github_ok = False
            log.exception("Failed to append both local and GitHub")

    await post_process_inbox_message(message, local_ok, github_ok, route)


def main() -> None:
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
