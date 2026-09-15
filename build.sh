#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== iTrader Mac App Build ==="

if [[ -f iTrader.spec ]]; then
    echo "Found generated iTrader.spec; use ./build.sh with specs/mac.spec." >&2
    exit 1
fi

rm -rf build dist

./.venv/bin/pyinstaller \
    --workpath=build \
    --distpath=dist \
    --noconfirm specs/mac.spec

echo "=== Build complete: $(pwd)/dist/iTrader.app ==="
