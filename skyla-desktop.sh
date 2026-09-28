#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

source "$APP_DIR/.venv/bin/activate"

if ! curl -fsS http://127.0.0.1:5000/ >/dev/null 2>&1; then
    nohup python "$APP_DIR/run.py" > "$APP_DIR/skyla-server.log" 2>&1 &
    SERVER_PID=$!

    for i in {1..30}; do
        if curl -fsS http://127.0.0.1:5000/ >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
fi

xdg-open "http://127.0.0.1:5000/" >/dev/null 2>&1 &
