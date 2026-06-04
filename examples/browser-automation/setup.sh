#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> Creating Python virtualenv..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing Playwright..."
pip install -q -U pip
pip install -q -r requirements.txt

echo "==> Installing Chromium browser..."
playwright install chromium

mkdir -p output
echo ""
echo "Done. Activate and run examples:"
echo "  source $ROOT/.venv/bin/activate"
echo "  python 01_basics.py"
