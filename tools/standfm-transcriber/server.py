#!/usr/bin/env python3
"""stand.fm 文字起こしサーバー — Chrome拡張機能のバックエンド"""

import json
import os
import re
import subprocess
import tempfile
import wave

import numpy as np
import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OBSIDIAN_VAULT = os.environ.get(
    "OBSIDIAN_VAULT",
    os.path.expanduser(
        "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    ),
)

MODEL_REPO = "mlx-community/whisper-large-v3-turbo"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_episode_id(url: str) -> str | None:
    m = re.search(r"/episodes/([a-f0-9]+)", url)
    return m.group(1) if m else None


def fetch_episode_info(episode_id: str) -> dict:
    r = requests.get(f"https://stand.fm/api/episodes/{episode_id}", timeout=15)
    r.raise_for_status()
    data = r.json()["response"]

    ep = data["episodes"][episode_id]
    audio_url = None
    for topic in data.get("topics", {}).values():
        if topic.get("episodeId") == episode_id:
            audio_url = topic["downloadUrl"]
            break

    return {
        "title": ep["title"],
        "duration": ep["totalDuration"] / 1000,
        "audio_url": audio_url,
    }


def download_audio(url: str, dest: str) -> None:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)


def convert_to_wav(src: str, dst: str) -> None:
    """macOS の afconvert を優先し、なければ ffmpeg にフォールバック"""
    try:
        subprocess.run(
            ["afconvert", src, dst, "-d", "LEI16", "-f", "WAVE"],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        subprocess.run(
            ["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", "-f", "wav", dst],
            check=True,
            capture_output=True,
        )


def load_and_resample(wav_path: str, target_sr: int = 16000) -> np.ndarray:
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n_ch > 1:
        audio = audio.reshape(-1, n_ch).mean(axis=1)

    if sr != target_sr:
        from scipy.signal import resample

        new_len = int(len(audio) * target_sr / sr)
        audio = resample(audio, new_len).astype(np.float32)

    return audio


def transcribe_audio(audio: np.ndarray) -> dict:
    import mlx_whisper

    return mlx_whisper.transcribe(
        audio,
        path_or_hf_repo=MODEL_REPO,
        language="ja",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.json or {}
    url = data.get("url", "")

    episode_id = extract_episode_id(url)
    if not episode_id:
        return jsonify({"error": "無効な stand.fm URL です"}), 400

    def generate():
        m4a = wav = None
        try:
            yield _ev("info", "エピソード情報を取得中...")

            info = fetch_episode_info(episode_id)
            if not info["audio_url"]:
                yield _ev("error", "音声URLが見つかりませんでした")
                return

            dur_min = int(info["duration"] // 60)
            yield _ev(
                "downloading",
                f"音声をダウンロード中... (約{dur_min}分の音声)",
                title=info["title"],
                duration=info["duration"],
            )

            m4a = tempfile.mktemp(suffix=".m4a")
            wav = tempfile.mktemp(suffix=".wav")

            download_audio(info["audio_url"], m4a)

            yield _ev("converting", "音声を変換中...")
            convert_to_wav(m4a, wav)

            audio = load_and_resample(wav)

            est = max(1, int(info["duration"] / 10))
            yield _ev("transcribing", f"文字起こし中... (推定 約{est}秒)")

            result = transcribe_audio(audio)

            segments = result.get("segments", [])
            if segments:
                text = "\n".join(
                    seg["text"].strip() for seg in segments if seg["text"].strip()
                )
            else:
                text = result["text"]

            yield _ev(
                "done", "完了", title=info["title"],
                text=text, duration=info["duration"], url=url,
            )

        except Exception as exc:
            yield _ev("error", str(exc))

        finally:
            for p in (m4a, wav):
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    return Response(
        generate(),
        mimetype="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/save", methods=["POST"])
def save():
    data = request.json or {}
    title = data.get("title", "untitled")
    text = data.get("text", "")
    url = data.get("url", "")
    duration = data.get("duration", 0)
    folder = data.get("folder", "brain")

    safe = re.sub(r'[\\/*?:"<>|]', "", title)
    save_dir = os.path.join(OBSIDIAN_VAULT, folder)
    os.makedirs(save_dir, exist_ok=True)

    path = os.path.join(save_dir, f"スタエフ文字起こし_{safe}.md")
    dur_m, dur_s = int(duration // 60), int(duration % 60)

    md = (
        f"# {title}（スタエフ文字起こし）\n\n"
        f"- **URL**: {url}\n"
        f"- **長さ**: 約{dur_m}分{dur_s}秒\n\n"
        f"---\n\n"
        f"{text}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(md)

    rel = os.path.relpath(path, OBSIDIAN_VAULT)
    return jsonify({"status": "ok", "path": rel})


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _ev(status: str, message: str, **extra) -> str:
    return json.dumps({"status": status, "message": message, **extra}, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  🎙  stand.fm 文字起こしサーバー")
    print(f"  URL : http://localhost:5555")
    print(f"  Vault: {OBSIDIAN_VAULT}")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5555)
