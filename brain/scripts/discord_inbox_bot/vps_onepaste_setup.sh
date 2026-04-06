#!/usr/bin/env bash
# VPS に SSH したあと、このファイルの「次行から最後まで」を丸ごと貼り付けて実行（scp 不要）
# Mac: このファイルを開き、bash 行から下を全選択して VPS のターミナルにペースト
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
APT_OPTS=(
  -y
  -o Dpkg::Options::="--force-confdef"
  -o Dpkg::Options::="--force-confold"
)

echo "==> apt-get update / upgrade / 必須パッケージ"
apt-get "${APT_OPTS[@]}" update
apt-get "${APT_OPTS[@]}" upgrade
apt-get "${APT_OPTS[@]}" install git python3 python3-venv python3-pip

echo "==> タイムゾーン Asia/Tokyo"
timedatectl set-timezone Asia/Tokyo
timedatectl

echo "==> /root/vps_install_bot.sh を配置"
cat > /root/vps_install_bot.sh << 'INSTALLBOT'
#!/usr/bin/env bash
# Vault を VPS に置いたあと: venv・pip・systemd 登録
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
INSTALLBOT
chmod +x /root/vps_install_bot.sh

echo
echo "=========================================="
echo "  ベース設定と vps_install_bot.sh 配置まで完了"
echo "=========================================="
echo "次の手順:"
echo "  1) mkdir -p /opt && cd /opt && git clone <あなたのリポジトリURL> vault"
echo "     （Git 未使用なら Mac から rsync/scp で brain を同じ構成で置く）"
echo "  2) nano /opt/vault/brain/scripts/discord_inbox_bot/.env"
echo "     （Mac の .env と同じ内容）"
echo "  3) bash /root/vps_install_bot.sh"
echo "  4) Mac で: launchctl bootout gui/\$(id -u)/com.sasaki.discord-inbox-bot"
echo
