#!/usr/bin/env bash
# Build the MyNote Electron desktop application.
#
# Steps:
#   1. Python backend -> PyInstaller onedir bundle in dist/MyNote
#      (self-contained: ships its own CPython interpreter)
#   2. Electron shell  -> electron-builder package in electron/dist
#      (the backend bundle is embedded as Resources/backend)
#
# Usage:
#   ./build-electron.sh [options]
#
# Options:
#   --target <t>      electron-builder target for the current OS
#                     (default: "dir"; on mac try: dir | dmg; linux: AppImage | deb;
#                     windows: nsis | portable)
#   --backend-only    only build the PyInstaller backend bundle
#   --app-only        only build the Electron package (reuse existing dist/MyNote)
#   --skip-install    skip "npm install" in electron/
#   --sign            enable macOS code signing auto-discovery (default: off)
#   --arch <a>        mac arch: x64 | arm64 (default: native)
#   -h, --help        show this help
#
# Requirements: python3 (venv module), node + npm. PyInstaller does NOT
# cross-compile: build/package on the OS+arch you are distributing for.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

TARGET="dir"
BUILD_BACKEND=1
BUILD_APP=1
SKIP_INSTALL=0
SIGN=0
ARCH_OPT=()

usage() {
    sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
    case "$1" in
        --target)       TARGET="$2"; shift 2 ;;
        --backend-only) BUILD_APP=0; shift ;;
        --app-only)     BUILD_BACKEND=0; shift ;;
        --skip-install) SKIP_INSTALL=1; shift ;;
        --sign)         SIGN=1; shift ;;
        --arch)         ARCH_OPT=(--arch "$2"); shift 2 ;;
        -h|--help)      usage; exit 0 ;;
        *)              echo "unknown option: $1" >&2; usage; exit 1 ;;
    esac
done

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

# ---------- 0. sanity checks ----------
command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }
if [ "$BUILD_APP" = 1 ]; then
    command -v npm >/dev/null || { echo "npm not found (node.js required)" >&2; exit 1; }
fi

# ---------- 1. Python backend (PyInstaller) ----------
if [ "$BUILD_BACKEND" = 1 ]; then
    log "Building Python backend with PyInstaller (this takes a few minutes)"
    bash electron/build-backend.sh
    EXE_NAME="MyNote"; [ "$(uname)" = MINGW* ] && EXE_NAME="MyNote.exe"
    [ -x "dist/MyNote/$EXE_NAME" ] || { echo "backend build failed: dist/MyNote/$EXE_NAME missing" >&2; exit 1; }
    log "Backend bundle: $ROOT/dist/MyNote ($EXE_NAME + _internal/)"
else
    log "Skipping backend build (--app-only)"
fi

# ---------- 2. Electron shell ----------
if [ "$BUILD_APP" = 1 ]; then
    cd electron
    if [ "$SKIP_INSTALL" = 0 ] || [ ! -d node_modules ]; then
        log "Installing npm dependencies"
        npm install --no-audit --no-fund
    else
        log "Skipping npm install (--skip-install)"
    fi

    case "$(uname)" in
        Darwin) OS_FLAG="--mac" ;;
        Linux)  OS_FLAG="--linux" ;;
        *)      OS_FLAG="--win" ;;
    esac

    log "Packaging Electron app (target: $OS_FLAG $TARGET)"
    if [ "$SIGN" = 0 ] && [ "$OS_FLAG" = "--mac" ]; then
        CSC_IDENTITY_AUTO_DISCOVERY=false npx electron-builder "$OS_FLAG" "$TARGET" ${ARCH_OPT[@]+"${ARCH_OPT[@]}"}
    else
        npx electron-builder "$OS_FLAG" "$TARGET" ${ARCH_OPT[@]+"${ARCH_OPT[@]}"}
    fi

    log "Desktop package output: $ROOT/electron/dist"
    ls -1 dist | grep -Ev '^$' | sed 's/^/  /'
fi

log "Done"
