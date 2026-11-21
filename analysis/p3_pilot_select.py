"""Select the Phase-0 pilot build PRs by a fixed rule (not by hand).

Rule (2026-11-20):
  from data/p2_classify/labels.parquet: perf_role primary, scope runtime,
  confidence high, quote verbatim (whitespace-normalised);
  every changed file with a code extension is .py (docs/config allowed);
  <= 5 changed files (AIDev file list);
  then from GitHub (read-only, gh): merged, additions <= 200.
Candidates are put in a random order (seed 42); the experimenter walks the
order and records, for each, "build" or a skip reason, until 10 builds.

Usage: python -I analysis/p3_pilot_select.py  -> data/p3_pilot/candidates.jsonl
"""

import json
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_fetch_shas as gh  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "p3_pilot"
CODE_EXT = {"py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "kt", "c", "cc", "cpp", "h",
            "hpp", "cs", "rb", "php", "swift", "scala", "m", "mm", "sh", "pyx", "pxd", "cu"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lab = pd.read_parquet(ROOT / "data" / "p2_classify" / "labels.parquet")
    with open(ROOT / "data" / "p2_classify" / "inputs.jsonl", encoding="utf-8") as f:
        inputs = {x["id"]: x for x in map(json.loads, f)}
    sel = lab[(lab.status == "ok") & (lab.perf_role == "primary") & (lab.perf_scope == "runtime")
              & (lab.confidence == "high") & (lab.quote_ws_normalised == True)]  # noqa: E712

    def py_only(i):
        x = inputs[i]
        exts = {f.rsplit(".", 1)[-1].lower() for f in x["files"] if "." in f}
        return x["n_files"] <= 5 and (exts & CODE_EXT) <= {"py"} and "py" in exts

    sel = sel[sel["id"].map(py_only)]
    ids = sorted(sel["id"])
    random.Random(42).shuffle(ids)
    print(f"rule-based pool before GitHub checks: {len(ids)}")
    kept = []
    with open(OUT / "candidates.jsonl", "w", encoding="utf-8") as f:
        for i in ids:
            x = inputs[i]
            meta = gh.fetch(x["html_url"])
            rec = {"order": len(kept), "id": i, "agent": x["agent"], "html_url": x["html_url"],
                   "title": x["title"], "files": x["files"], **meta}
            if "error" in meta or not meta.get("merged") or meta.get("additions", 999) > 200:
                continue
            rec["order"] = len(kept)
            kept.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if len(kept) >= 30:  # enough to walk to 10 builds
                break
    print(f"merged, <= 200 added lines: {len(kept)} kept (stopped at 30)")


if __name__ == "__main__":
    main()
