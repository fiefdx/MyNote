#!/bin/bash
# Installs MyNote from this disk image into /Applications and clears the
# macOS quarantine flag (the app is ad-hoc signed, so Gatekeeper would
# otherwise report it as "damaged" on downloaded copies).
set -e
cd "$(dirname "$0")"

echo "Installing MyNote to /Applications ..."
rm -rf "/Applications/MyNote.app"
cp -R "MyNote.app" "/Applications/"
xattr -dr com.apple.quarantine "/Applications/MyNote.app" 2>/dev/null || true
xattr -d com.apple.quarantine "$0" 2>/dev/null || true
echo "Done. Launching MyNote."
open "/Applications/MyNote.app"
