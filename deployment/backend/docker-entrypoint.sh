#!/usr/bin/env bash
set -e

: "${HOST_IP:=0.0.0.0}"
: "${HOST_PORT:=8000}"

cd /app

exec uv run uvicorn src.platform.api.main:app \
  --host "$HOST_IP" \
  --port "$HOST_PORT" \
  --reload
