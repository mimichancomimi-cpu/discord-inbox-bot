#!/usr/bin/env bash
# VPS 初回: apt・git・Python・タイムゾーン（対話なし）
# 使い方: bash vps_setup_base.sh
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
APT_OPTS=(
  -y
  -o Dpkg::Options::="--force-confdef"
  -o Dpkg::Options::="--force-confold"
)

echo "==> apt-get update"
apt-get "${APT_OPTS[@]}" update

echo "==> apt-get upgrade（数分かかることがあります）"
apt-get "${APT_OPTS[@]}" upgrade

echo "==> パッケージ追加"
apt-get "${APT_OPTS[@]}" install git python3 python3-venv python3-pip

echo "==> タイムゾーン Asia/Tokyo"
timedatectl set-timezone Asia/Tokyo

echo "==> 完了"
timedatectl
echo
echo "次: Vault を /opt/vault などに clone したあと、"
echo "    bash vps_install_bot.sh"
echo "  （または VAULT_ROOT=/path/to/vault bash vps_install_bot.sh）"
