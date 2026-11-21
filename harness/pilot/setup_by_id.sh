#!/usr/bin/env bash
# Build a pilot PR by its order id, reading repo/SHAs/date ONLY from manifest.tsv
# (SHAs from the GitHub API; never typed by hand).
#   setup_by_id.sh <order> <python> [extra pip args...]
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ID=$1 PY=$2; shift 2
read -r _ REPO BASE HEAD DATE NUM < <(awk -F'\t' -v id="$ID" '$1==id' "$HERE/manifest.tsv")
[ -n "${REPO:-}" ] || { echo "id $ID not in manifest"; exit 1; }
echo "PR $REPO#$NUM base=$BASE head=$HEAD deps<=$DATE"
exec bash "$HERE/setup_pr.sh" "$HOME/prs/$ID" "$REPO" "$BASE" "$HEAD" "$DATE" "$PY" "$@"
