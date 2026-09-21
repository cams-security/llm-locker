#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

cp ../server/mcp_server.py ../server/client.py ../server/crypto.py src/

rm -f llm-locker.mcpb
zip -9 -r llm-locker.mcpb manifest.json pyproject.toml src -x '*.pyc' -x '__pycache__/*'

echo "Built desktop-extension/llm-locker.mcpb"
