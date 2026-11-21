#!/usr/bin/env bash
# Build base and head of one PR into two virtual environments.
#   setup_pr.sh <dir> <owner/repo> <base_sha> <head_sha> <exclude_newer_date> <python> [extra pip args...]
# Dependencies are frozen at the PR's creation date (uv --exclude-newer).
# Result: <dir>/{base,head}/src (git worktrees) and <dir>/{base,head}/venv.
# EDITABLE= (empty) installs a normal wheel: needed for packages with C
# extensions whose editable install rebuilds on import (e.g. pandas).
# Both sides are always set up, even if an install fails, so the build
# agent can repair it (exit status 1 if any install failed).
set -uo pipefail
DIR=$1 REPO=$2 BASE=$3 HEAD=$4 DATE=$5 PY=$6; shift 6
mkdir -p "$DIR"; cd "$DIR" || exit 2
if [ ! -d repo ]; then
  git clone --quiet --filter=blob:none "https://github.com/$REPO.git" repo || { echo "CLONE FAILED"; exit 2; }
fi
git -C repo fetch --quiet origin "$BASE" "$HEAD" 2>/dev/null || git -C repo fetch --quiet origin
# The API's base.sha is the base branch tip, which can be later than the
# commit the PR branched from; comparing it with head would mix in unrelated
# changes (seen: pandas #64575, 69 files vs the PR's 1). Use the merge base.
MB=$(git -C repo merge-base "$BASE" "$HEAD") || { echo "NO MERGE BASE"; exit 2; }
[ "$MB" = "$BASE" ] || echo "note: API base $BASE is not the merge base; using merge base $MB"
echo "$MB" > base_commit.txt
git -C repo diff "$MB" "$HEAD" > pr.diff
for side in base head; do
  sha=$MB; [ "$side" = head ] && sha=$HEAD
  [ -d "$side/src" ] && git -C repo worktree remove --force "$DIR/$side/src" 2>/dev/null || true
  rm -rf "$side"; mkdir "$side"
  git -C repo worktree add --quiet --force --detach "$DIR/$side/src" "$sha" || { echo "WORKTREE FAILED ($side)"; exit 2; }
done
# Python project dir: the nearest folder with pyproject.toml/setup.py above
# the changed .py files (most common one; repository root if none). Same
# folder for both sides, recorded in pkgdir.txt.
PKG=$(python3 - <<'EOF'
import collections, os, re
files = re.findall(r"^diff --git a/\S+ b/(\S+\.py)$", open("pr.diff").read(), re.M)
votes = collections.Counter()
for f in files:
    d = os.path.dirname(f)
    while True:
        if any(os.path.exists(os.path.join("head/src", d, m)) for m in ("pyproject.toml", "setup.py")):
            votes[d] += 1
            break
        if not d:
            break
        d = os.path.dirname(d)
print(votes.most_common(1)[0][0] if votes else "")
EOF
)
echo "${PKG:-.}" > pkgdir.txt
STATUS=0
for side in base head; do
  uv venv --quiet --python "$PY" "$side/venv"
  VIRTUAL_ENV="$DIR/$side/venv" uv pip install --quiet --exclude-newer "$DATE" "$@" ${EDITABLE--e} "$side/src/$PKG" coverage \
    > "$side/install.log" 2>&1 \
    && echo "$side: $(git -C "$side/src" rev-parse HEAD) $("$side/venv/bin/python" --version) pkg=${PKG:-.}" \
    || { echo "INSTALL FAILED ($side), see $side/install.log"; tail -3 "$side/install.log"; STATUS=1; }
done
exit $STATUS
