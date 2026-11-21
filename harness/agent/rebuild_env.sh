#!/usr/bin/env bash
# Rebuild one side's venv from its source tree (run inside a PR dir).
#   rebuild_env.sh <base|head> <python> [editable|normal] [extra packages...]
set -euo pipefail
SIDE=$1 PY=$2 MODE=${3:-editable}; shift 2; [ $# -gt 0 ] && shift
DATE=$(python3 -c "import json; print(json.load(open('job.json'))['created'])")
export PATH=$HOME/.local/bin:$PATH
rm -rf "$SIDE/venv"
uv venv --quiet --python "$PY" "$SIDE/venv"
E=-e; [ "$MODE" = normal ] && E=
PKG=$(cat pkgdir.txt 2>/dev/null || echo .)  # python project folder chosen by setup (KT_PKGDIR overrides)
PKG=${KT_PKGDIR:-$PKG}
VIRTUAL_ENV="$PWD/$SIDE/venv" uv pip install --quiet --exclude-newer "$DATE" "$@" $E "$SIDE/src/$PKG" coverage \
  > "$SIDE/install.log" 2>&1 && echo "$SIDE rebuilt with Python $PY ($MODE)" \
  || { echo "INSTALL FAILED ($SIDE), last lines:"; tail -15 "$SIDE/install.log"; exit 1; }
echo "$(date -Is) rebuild $SIDE $PY $MODE $*" >> rebuild.log
