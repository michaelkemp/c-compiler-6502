#!/usr/bin/env bash
# Downloads beneater/msbasic (a fork of mist64/msbasic already targeting a
# 6502 + serial ACIA, no video/keyboard hardware -- close to our own
# system) into a gitignored directory. Not vendored in this repo: its
# README claims a permissive 2-clause BSD license, but there's no actual
# LICENSE file, so -- same caution as Klaus Dormann's suite -- we fetch
# on demand rather than commit it. See docs/roadmap.md.
set -euo pipefail

REPO_URL="https://github.com/beneater/msbasic.git"
PINNED_COMMIT="5de42c7b88bcde2031492137d8d976c7e83d72ee"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$REPO_ROOT/msbasic/vendor"

rm -rf "$DEST_DIR"
echo "Fetching beneater/msbasic (not vendored -- see docs/roadmap.md)..."
git clone --quiet "$REPO_URL" "$DEST_DIR"
git -C "$DEST_DIR" checkout --quiet "$PINNED_COMMIT"
echo "Fetched into $DEST_DIR at commit $PINNED_COMMIT"
echo "Run scripts/build_msbasic.sh next to build it for our system."
