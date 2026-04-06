#!/usr/bin/env bash
# VPS で「GitHub の main に完全同期 → Bot 再起動」を一発でやる。
# Bot が追記した未コミット差分は消える（GitHub が正）。使い方:
#   sudo bash /opt/vault/brain/scripts/discord_inbox_bot/vps_pull_restart.sh
# リポジトリの場所が違うとき:
#   sudo env VAULT_ROOT=/path/to/repo bash vps_pull_restart.sh

set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-/opt/vault}"
cd "$VAULT_ROOT"

if [[ ! -d .git ]]; then
  echo "エラー: $VAULT_ROOT に .git がありません。VAULT_ROOT を指定してください。"
  exit 1
fi

echo "== 1. GitHub の origin/main に合わせる（ローカル未コミットは破棄）==="
git fetch origin
git reset --hard origin/main

echo "== 2. discord-inbox-bot 再起動 ==="
systemctl restart discord-inbox-bot
systemctl --no-pager -l status discord-inbox-bot || true

echo "== 3. 新しい bot.py の確認（strip_all_bracket_tags があれば OK）==="
if grep -q strip_all_bracket_tags brain/scripts/discord_inbox_bot/bot.py 2>/dev/null; then
  echo "  OK: strip_all_bracket_tags が見つかりました"
else
  echo "  注意: strip_all_bracket_tags が見つかりません（古い bot.py の可能性）"
fi

echo "完了"
