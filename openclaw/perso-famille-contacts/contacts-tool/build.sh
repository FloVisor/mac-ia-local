#!/bin/sh
# Compile perso-contacts (lecture seule du carnet iCloud).
# Usage: ./build.sh [--install]
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="${OUT:-$HERE/build/perso-contacts}"

mkdir -p "$(dirname "$OUT")"
swiftc -O -o "$OUT" "$HERE"/Sources/PersoContacts/*.swift

echo "built: $OUT"

if [ "${1:-}" = "--install" ]; then
  DEST="$HOME/.local/bin/perso-contacts"
  mkdir -p "$(dirname "$DEST")"
  cp "$OUT" "$DEST"
  chmod 755 "$DEST"
  echo "installed: $DEST"
fi
