"""Download the AIDev v5 tables we use, pinned to one commit, and verify them.

Every file's SHA-256 is checked against the LFS hash Hugging Face publishes
for that commit. The manifest (sizes, hashes, row counts) is written to
data/aidev-v5-manifest.json and is the provenance record for the paper.

all_pull_request.parquet (6.7 GB) is not downloaded; p1_counts.py reads
only the columns it needs from it remotely.

Usage: python -I AGENTS-WORKSHOP/analysis/p1_download.py
"""

import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem, hf_hub_download

REPO = "hao-li/AIDev"
REV = "b37f9fd1613cfec55886105bb76721918d015dc7"  # tag v5
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "aidev-v5"
TABLES = [  # AIDev-pop tables + the two small full-scope tables
    "pull_request", "repository", "pr_commits", "pr_commit_details",
    "pr_timeline", "pr_reviews", "pr_review_comments", "pr_comments",
    "issue", "related_issue", "all_repository", "all_user",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fs = HfFileSystem()
    remote = {d["name"].split("/")[-1]: d
              for d in fs.ls(f"datasets/{REPO}@{REV}", detail=True)}
    manifest = {"repo": REPO, "revision": REV, "tag": "v5", "files": {}}
    bad = 0
    for t in TABLES:
        name = f"{t}.parquet"
        want = remote[name]["lfs"]["sha256"]
        local = Path(hf_hub_download(REPO, name, repo_type="dataset",
                                     revision=REV, local_dir=OUT))
        got = sha256(local)
        ok = got == want
        bad += not ok
        rows = pq.ParquetFile(local).metadata.num_rows
        manifest["files"][name] = {"bytes": local.stat().st_size,
                                   "sha256": got, "sha256_ok": ok,
                                   "rows": rows}
        print(f"{name:28s} rows={rows:>11,} sha256_ok={ok}", flush=True)
    (ROOT / "data" / "aidev-v5-manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
