#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "=========================================="
echo "  🎙  stand.fm 文字起こしサーバー"
echo "=========================================="
echo ""
echo "依存パッケージを確認中..."
pip3 install -r requirements.txt -q 2>/dev/null
echo ""
echo "サーバーを起動します: http://localhost:5555"
echo "終了するには Ctrl+C を押してください"
echo ""
python3 server.py
