#!/usr/bin/env bash
# Keyboard Chaos — Linux/macOS launcher

set -e

echo ""
echo "  ████████████████████████████████████"
echo "  ██   KEYBOARD CHAOS — Unix/macOS   ██"
echo "  ████████████████████████████████████"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] python3 not found. Install it first."
    exit 1
fi

# Install deps into venv if not done yet
if [ ! -d ".venv" ]; then
    echo "  Setting up virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
    echo "  Dependencies installed."
else
    source .venv/bin/activate
fi

echo ""

# Linux needs sudo or uinput group membership for global key hooks
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "  NOTE: On Linux, global key hooks require either:"
        echo "    1. sudo python3 main.py"
        echo "    2. Adding yourself to the 'input' group:"
        echo "       sudo usermod -aG input \$USER  (then log out and back in)"
        echo ""
        echo "  Attempting to run anyway (may fail without permissions)..."
        echo ""
    fi
fi

python3 main.py "$@"
