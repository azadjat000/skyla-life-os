#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "       Skyla Life OS Installer"
echo "======================================"
echo

cd "$APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 is required."
    exit 1
fi

echo "🟢 Python found: $(python3 --version)"

if [ ! -f ".env" ]; then
    echo "🔐 Creating secure Skyla environment..."
    SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    printf 'SKYLA_SECRET_KEY=%s\n' "$SECRET_KEY" > .env
    chmod 600 .env
    echo "🟢 Secure .env created."
else
    echo "🟢 Existing .env found — keeping it unchanged."
fi

if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
else
    echo "🟢 Existing virtual environment found."
fi

echo "📦 Installing Python dependencies..."
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "🧪 Checking Skyla..."
python -m compileall -q app
python -c "from app import create_app; create_app(); print('🟢 Skyla application initialized successfully.')"

echo
echo "🚀 Creating launcher..."

cat > launch.sh <<'LAUNCH'
#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

source "$APP_DIR/.venv/bin/activate"

echo "🚀 Starting Skyla Life OS..."
python "$APP_DIR/run.py"
LAUNCH

chmod +x launch.sh

echo
echo "======================================"
echo "🟢 Skyla Life OS installation complete"
echo "======================================"
echo
echo "Start Skyla with:"
echo "  ./launch.sh"
echo
echo "Then open:"
echo "  http://127.0.0.1:5000"
