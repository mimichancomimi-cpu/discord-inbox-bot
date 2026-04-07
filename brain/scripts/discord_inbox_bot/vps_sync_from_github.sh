#!/usr/bin/env bash
# VPS の /opt/vault で GitHub の main を取り込む（手でコピーした未追跡ファイルとぶつかったとき用）
# 使い方: sudo bash vps_sync_from_github.sh
# 前提: リポジトリのルートが /opt/vault（違う場合は VAULT_ROOT を変える）

set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-/opt/vault}"
BOT_DIR="$VAULT_ROOT/brain/scripts/discord_inbox_bot"
ENV_BAK="/root/discord-inbox-bot.env.bak"

cd "$VAULT_ROOT"

if [[ ! -d .git ]]; then
  echo "エラー: $VAULT_ROOT に .git がありません。cd 先を確認してください。"
  exit 1
fi

echo "== 1. .env をバックアップ =="
if [[ -f "$BOT_DIR/.env" ]]; then
  cp -a "$BOT_DIR/.env" "$ENV_BAK"
  echo "  -> $ENV_BAK"
else
  echo "  ( .env なし — スキップ )"
fi

echo "== 2. 追跡ファイルのローカル変更を捨てる（Discord自動受信箱.md）==="
git checkout -- brain/タスク管理/Discord自動受信箱.md 2>/dev/null || true

echo "== 3. 未追跡ファイルを削除（.gitignore の .env 等は残る）==="
git clean -fd brain/scripts/ brain/タスク管理/

echo "== 4. git pull =="
git pull origin main

echo "== 5. .env を戻す ==="
if [[ -f "$ENV_BAK" ]]; then
  mkdir -p "$BOT_DIR"
  cp -a "$ENV_BAK" "$BOT_DIR/.env"
  echo "  <- $ENV_BAK"
fi

echo "== 6. discord-inbox-bot 再起動 ==="
if command -v systemctl >/dev/null 2>&1; then
  systemctl restart discord-inbox-bot
  systemctl --no-pager -l status discord-inbox-bot || true
else
  echo "systemctl なし — 手で Bot を再起動してください"
fi

echo "完了"
