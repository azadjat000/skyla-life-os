#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$HOME/.local/share/applications/skyla-life-os.desktop"

echo "======================================"
echo "      Skyla Life OS Uninstaller"
echo "======================================"
echo

if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo "🗑️ Desktop launcher removed."
fi

if [ -f "$APP_DIR/skyla-server.log" ]; then
    rm -f "$APP_DIR/skyla-server.log"
    echo "🧹 Runtime log removed."
fi

echo
echo "🟢 Skyla Life OS launcher has been removed."
echo
echo "Your project files, .env and database were NOT deleted."
echo "To remove the complete project manually, delete:"
echo "  $APP_DIR"
