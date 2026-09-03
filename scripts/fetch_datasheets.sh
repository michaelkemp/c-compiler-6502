#!/usr/bin/env bash
# Downloads reference datasheets for the Stage 1 breadboard build
# (docs/hardware-build.md) into a gitignored directory. Not vendored --
# these are manufacturer-copyrighted PDFs, multi-MB each; same reasoning
# as scripts/fetch_dormann_tests.sh and scripts/fetch_msbasic.sh, just
# for reference documents instead of code/ROM sources this time.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$REPO_ROOT/docs/hardware/datasheets"

mkdir -p "$DEST_DIR"

declare -A DATASHEETS=(
    ["w65c02s.pdf"]="https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf"
    ["w65c51n.pdf"]="https://www.westerndesigncenter.com/wdc/documentation/w65c51n.pdf"
    ["as6c62256.pdf"]="https://www.alliancememory.com/wp-content/uploads/AS6C62256-23-March-2016-rev1.2.pdf"
    ["at28c256.pdf"]="https://ww1.microchip.com/downloads/en/DeviceDoc/doc0006.pdf"
)

for name in "${!DATASHEETS[@]}"; do
    echo "Fetching $name..."
    # -A: some hosts reject requests with no browser-like User-Agent
    # (Jameco's own datasheet PDF returned a Cloudflare block page without
    # one -- using Microchip's own doc0006.pdf for AT28C256 instead).
    curl -sL -A "Mozilla/5.0" -o "$DEST_DIR/$name" "${DATASHEETS[$name]}"
done

echo "Saved to $DEST_DIR"
