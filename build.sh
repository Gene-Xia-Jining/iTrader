#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== iTrader Mac App Build ==="

if [[ -f iTrader.spec ]]; then
    echo "Found generated iTrader.spec; use ./build.sh with specs/mac.spec." >&2
    exit 1
fi

# dist 若已存在则先清理，避免旧产物残留；清理失败不阻断构建
if [[ -d dist ]] && [[ -n "$(ls -A dist 2>/dev/null)" ]]; then
    echo "dist 目录非空，清理后继续构建"
    rm -rf build dist || true
else
    rm -rf build || true
fi

./.venv/bin/pyinstaller \
    --workpath=build \
    --distpath=dist \
    --noconfirm specs/mac.spec

echo "=== Build complete: $(pwd)/dist/iTrader.app ==="
