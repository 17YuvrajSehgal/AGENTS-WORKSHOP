"""Build/measure job list for the fleet (2026-11-20).

Population: the 1,030 runtime-perf PRs whose extracted claim has >= 1
mechanism with a kernel signal (data/p5_claims/all_v1, codebook v1).
One fixed random order (seed 42); assigned round-robin to the VMs, so
every batch of 50 on every VM is a random slice.

Each job holds ONLY what the blind build agent may see: repository, PR
number, API base/head SHAs (GitHub, read-only via gh), creation date
(dependency freeze), changed files. No title, body, commit messages or
claim. Labels and claims stay on the laptop for analysis.

Usage: python -I analysis/p6_jobs.py   -> harness/agent/jobs/kt-measure-{1,2,3}.jsonl
"""

import json
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_fetch_shas as gh  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "harness" / "agent" / "jobs"
VMS = ["kt-measure-1", "kt-measure-2", "kt-measure-3"]
UNMEASURABLE = {"gpu_accelerator", "fewer_external_calls", "ui_rendering", "other"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m = pd.read_parquet(ROOT / "data" / "p5_claims" / "all_v1" / "claims_mech.parquet")
    mech = m.groupby("id").mechanism.apply(set)
    ids = sorted(i for i, s in mech.items() if s - UNMEASURABLE)
    created = pd.read_parquet(ROOT / "data" / "aidev-v5" / "pull_request.parquet",
                              columns=["id", "created_at"]).set_index("id")["created_at"]
    inputs = {}
    with open(ROOT / "data" / "p2_classify" / "inputs.jsonl", encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            if x["id"] in set(ids):
                inputs[x["id"]] = x
    random.Random(42).shuffle(ids)
    cache = OUT / "_gh_cache.jsonl"
    seen = {}
    if cache.exists():
        seen = {json.loads(l)["id"]: json.loads(l) for l in cache.open(encoding="utf-8")}
    files = {vm: open(OUT / f"{vm}.jsonl", "w", encoding="utf-8") for vm in VMS}
    stats = {"population": len(ids), "fetched": 0, "github_error": 0, "per_vm": {vm: 0 for vm in VMS}}
    with cache.open("a", encoding="utf-8") as cf:
        for k, i in enumerate(ids):
            x = inputs[i]
            if i not in seen:
                meta = gh.fetch(x["html_url"])
                seen[i] = {"id": i, **meta}
                cf.write(json.dumps(seen[i]) + "\n")
            meta = seen[i]
            if "error" in meta:
                stats["github_error"] += 1
                continue
            vm = VMS[k % len(VMS)]
            job = {"order": k, "id": int(i), "agent": x["agent"], "repo": meta["base_repo"],
                   "number": meta["number"], "api_base_sha": meta["base_sha"],
                   "head_sha": meta["head_sha"], "created": str(created[i])[:10],
                   "changed_files": x["files"], "n_files": x["n_files"]}
            files[vm].write(json.dumps(job) + "\n")
            stats["per_vm"][vm] += 1
            stats["fetched"] += 1
    for f in files.values():
        f.close()
    (OUT / "_stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
