#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
uv run python setup.py
uv run uvicorn api:app --reload --port 8000
