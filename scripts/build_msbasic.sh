#!/usr/bin/env bash
# Builds Microsoft BASIC for our system: overlays our own platform files
# (msbasic/bios.s, defines_eater.s, eater.cfg) onto a copy of the fetched
# beneater/msbasic checkout (scripts/fetch_msbasic.sh) and assembles it
# with ca65/ld65. A real file copy is required here, not an include-path
# trick -- ca65 resolves .include relative to the invoking file's own
# directory first regardless of -I order (confirmed empirically), so our
# files have to actually replace the fetched ones on disk to take effect.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_DIR="$REPO_ROOT/msbasic/vendor"
BUILD_DIR="$REPO_ROOT/msbasic/build"

if [ ! -d "$VENDOR_DIR" ]; then
    echo "msbasic/vendor/ not found -- run scripts/fetch_msbasic.sh first." >&2
    exit 1
fi

rm -rf "$BUILD_DIR"
cp -r "$VENDOR_DIR" "$BUILD_DIR"
cp "$REPO_ROOT/msbasic/bios.s" "$REPO_ROOT/msbasic/defines_eater.s" "$REPO_ROOT/msbasic/eater.cfg" "$BUILD_DIR/"

cd "$BUILD_DIR"
mkdir -p tmp
ca65 -D eater msbasic.s -o tmp/msbasic.o
ld65 -C eater.cfg tmp/msbasic.o -o msbasic.bin -Ln tmp/msbasic.lbl

echo "Built $BUILD_DIR/msbasic.bin"
echo "Run it with: python -m c6502.run $BUILD_DIR/msbasic.bin"
