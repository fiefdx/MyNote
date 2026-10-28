#!/usr/bin/env bash
# Build the MyNote Python backend as a self-contained PyInstaller "onedir"
# bundle in dist/MyNote (it ships its own CPython interpreter).
# The Electron shell (electron/main.js) runs dist/MyNote/MyNote in dev mode and
# <Resources>/backend/MyNote in the packaged app.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VENV="${VENV:-$ROOT/.venv-electron}"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
# shellcheck disable=SC1090
source "$VENV/bin/activate"

pip install --upgrade pip setuptools wheel
pip install -r requires/requirements.txt
pip install pyinstaller

rm -rf build dist/MyNote
python -m PyInstaller --noconfirm MyNoteElectron.spec

echo ""
echo "Backend bundle ready: $ROOT/dist/MyNote/$( [ "$(uname)" = MINGW* ] && echo MyNote.exe || echo MyNote )"
