"""Fetch base/head commits and outcome for PRs from the GitHub API (read-only).

AIDev v5 has no base SHA, so the harness needs it from GitHub. Uses the
logged-in `gh` CLI. Resumable: PRs already in the output are skipped.

Usage: python -I analysis/p1_fetch_shas.py pilot-python-runtime
  -> data/p1_pr_meta.jsonl (one JSON object per PR, including failures)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "p1_pr_meta.jsonl"
FIELDS = ("number", "state", "merged", "merged_at", "merge_commit_sha", "additions",
          "deletions", "changed_files", "commits")


def select(which):
    if which != "pilot-python-runtime":
        sys.exit(f"unknown selection {which}")
    lab = pd.read_parquet(ROOT / "data" / "p1_classify" / "pilot_labels_cc.parquet")
    cand = pd.read_parquet(ROOT / "data" / "p1_candidates.parquet", columns=["id", "repo_id", "html_url"])
    repo = pd.read_parquet(ROOT / "data" / "aidev-v5" / "repository.parquet",
                           columns=["id", "language"]).rename(columns={"id": "repo_id"})
    df = lab.merge(cand, on="id").merge(repo, on="repo_id")
    rt = df["perf_role"].isin(["primary", "secondary"]) & (df["perf_scope"] == "runtime")
    return df[rt & (df["language"] == "Python")][["id", "html_url", "perf_role", "agent"]]


def fetch(url):
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    owner, repo, num = m.groups()
    p = subprocess.run(["gh", "api", f"repos/{owner}/{repo}/pulls/{num}"],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        return {"error": (p.stderr or p.stdout).strip()[:300]}
    d = json.loads(p.stdout)
    rec = {k: d.get(k) for k in FIELDS}
    rec.update({"base_sha": d["base"]["sha"], "base_ref": d["base"]["ref"],
                "head_sha": d["head"]["sha"],
                "head_repo": (d["head"].get("repo") or {}).get("full_name"),
                "base_repo": d["base"]["repo"]["full_name"]})
    return rec


def main(which):
    done = set()
    if OUT.exists():
        done = {json.loads(line)["id"] for line in OUT.open(encoding="utf-8")}
    rows = select(which)
    with OUT.open("a", encoding="utf-8") as f:
        for r in rows.itertuples():
            if r.id in done:
                continue
            rec = {"id": int(r.id), "html_url": r.html_url, "agent": r.agent,
                   "llm_role": r.perf_role, **fetch(r.html_url)}
            f.write(json.dumps(rec) + "\n")
    allr = [json.loads(line) for line in OUT.open(encoding="utf-8")]
    ok = [x for x in allr if "error" not in x]
    print(f"selected {len(rows)}, fetched ok {len(ok)}, errors {len(allr) - len(ok)}")
    print("merged:", sum(1 for x in ok if x["merged"]), " head repo gone:",
          sum(1 for x in ok if x["head_repo"] is None))


if __name__ == "__main__":
    main(sys.argv[1])
