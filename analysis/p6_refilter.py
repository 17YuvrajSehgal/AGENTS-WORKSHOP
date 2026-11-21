"""Keep only jobs whose FINAL PR diff touches Python (2026-11-20).

AIDev's pr_commit_details lists files of every commit in a PR, including
commits merged in from the base branch, so a PR can be "py-changing" in
AIDev while its final diff has no .py file (first build test: elodin #525,
207 AIDev files incl. 3 .py, final diff 16 files, 0 .py). GitHub's
`pulls/<n>/files` is the final diff (what the PR page shows). Read-only.

Usage: python -I analysis/p6_refilter.py   (rewrites harness/agent/jobs/*.jsonl,
       originals kept as *.all.jsonl; funnel counts in _refilter_stats.json)
"""
import json
import subprocess
from pathlib import Path

JOBS = Path(__file__).resolve().parents[1] / "harness" / "agent" / "jobs"
CACHE = JOBS / "_pr_files_cache.jsonl"


def pr_files(repo, number):
    p = subprocess.run(["gh", "api", "--paginate", f"repos/{repo}/pulls/{number}/files",
                        "--jq", ".[].filename"], capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        return None, (p.stderr or p.stdout).strip()[:200]
    return [l for l in p.stdout.splitlines() if l], None


def main():
    cache = {}
    if CACHE.exists():
        cache = {json.loads(l)["id"]: json.loads(l) for l in CACHE.open(encoding="utf-8")}
    stats = {}
    with CACHE.open("a", encoding="utf-8") as cf:
        for f in sorted(JOBS.glob("kt-measure-*.jsonl")):
            if f.name.endswith(".all.jsonl"):
                continue
            src = f.with_name(f.stem + ".all.jsonl")
            if not src.exists():
                f.rename(src)
            jobs = [json.loads(l) for l in src.open(encoding="utf-8")]
            kept, s = [], {"jobs": len(jobs), "kept": 0, "no_py_in_final_diff": 0,
                           "github_error": 0, "final_diff_over_3000_files": 0}
            for j in jobs:
                if j["id"] not in cache:
                    files, err = pr_files(j["repo"], j["number"])
                    cache[j["id"]] = {"id": j["id"], "files": files, "error": err}
                    cf.write(json.dumps(cache[j["id"]]) + "\n")
                c = cache[j["id"]]
                if c["error"] or c["files"] is None:
                    s["github_error"] += 1
                    continue
                if len(c["files"]) >= 3000:  # GitHub caps the list at 3,000 files
                    s["final_diff_over_3000_files"] += 1
                if not any(x.endswith(".py") for x in c["files"]):
                    s["no_py_in_final_diff"] += 1
                    continue
                j["final_diff_files"] = c["files"]
                kept.append(j)
            with f.open("w", encoding="utf-8") as out:
                for j in kept:
                    out.write(json.dumps(j) + "\n")
            s["kept"] = len(kept)
            stats[f.stem] = s
            print(f.stem, s, flush=True)
    (JOBS / "_refilter_stats.json").write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
