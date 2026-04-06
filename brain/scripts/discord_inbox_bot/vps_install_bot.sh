#!/usr/bin/env bash
# Vault を VPS に置いたあと: venv・pip・systemd 登録
# 前提: brain/scripts/discord_inbox_bot に bot.py と requirements.txt がある
# 使い方:
#   VAULT_ROOT=/opt/vault bash vps_install_bot.sh
#   デフォルト VAULT_ROOT=/opt/vault
set -euo pipefail

VAULT_ROOT="${VAULT_ROOT:-/opt/vault}"
BOT_DIR="${VAULT_ROOT}/brain/scripts/discord_inbox_bot"
SERVICE_NAME="discord-inbox-bot"

if [[ ! -f "${BOT_DIR}/bot.py" ]]; then
  echo "エラー: ${BOT_DIR}/bot.py がありません。"
  echo "先に Vault を clone し、パスを確認してください。"
  echo "例: cd /opt && git clone <URL> vault"
  exit 1
fi

if [[ ! -f "${BOT_DIR}/.env" ]]; then
  echo "警告: ${BOT_DIR}/.env がありません。nano で作成してから再実行してください。"
  exit 1
fi

cd "${BOT_DIR}"

echo "==> venv"
python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

UNIT="/etc/systemd/system/${SERVICE_NAME}.service"
echo "==> systemd ユニット: ${UNIT}"

cat > "${UNIT}" <<EOF
[Unit]
Description=Discord inbox bot for Obsidian
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_DIR}
EnvironmentFile=${BOT_DIR}/.env
ExecStart=${BOT_DIR}/.venv/bin/python ${BOT_DIR}/bot.py
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
sleep 2
systemctl status "${SERVICE_NAME}" --no-pager || true

echo
echo "ログ: journalctl -u ${SERVICE_NAME} -f"
echo "Mac の同じ Bot を止める: launchctl bootout gui/\$(id -u)/com.sasaki.discord-inbox-bot"
