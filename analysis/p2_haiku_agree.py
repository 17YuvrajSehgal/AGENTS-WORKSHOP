"""Does Claude Haiku 5.5 label like Claude Opus 5.5? (2026-11-20, user idea)

Haiku uses far less of the plan per token. Before switching, Haiku labels
exactly the PRs Opus already labelled in data/p2_classify/ (same codebook,
schema, inputs, flags, effort, quote check) and agreement is measured.

Usage:
  python -I analysis/p2_haiku_agree.py run [WORKERS] [N]
  python -I analysis/p2_haiku_agree.py compare
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_classify as base  # noqa: E402
import p1_classify_cc as cc  # noqa: E402

ROOT = base.ROOT
OPUS = ROOT / "data" / "p2_classify"
OUT = ROOT / "data" / "p2_haiku_agree"
HAIKU = "claude-haiku-5-5"

# p1_classify_cc reads these module globals at call time
cc.OUT, cc.RAW, cc.WORK, cc.MODEL = OUT, OUT / "cc_raw", OUT / "cc_cwd", HAIKU


def opus_ids():
    return sorted(int(p.stem) for p in (OPUS / "cc_raw").glob("*.json"))


def run(workers=3, n=None):
    cc.RAW.mkdir(parents=True, exist_ok=True)
    cc.WORK.mkdir(parents=True, exist_ok=True)
    (cc.WORK / "system.txt").write_text(base.system_prompt(), encoding="utf-8")
    with open(OPUS / "inputs.jsonl", encoding="utf-8") as f:
        inputs = {x["id"]: x for x in map(json.loads, f)}
    ids = opus_ids()[: int(n) if n else None]
    todo = [i for i in ids if not (cc.RAW / f"{i}.json").exists()]
    print(f"{len(ids) - len(todo)} done, {len(todo)} to do", flush=True)
    with ThreadPoolExecutor(max_workers=int(workers)) as ex:
        counts = {}
        for k, (_, s) in enumerate(ex.map(lambda i: cc.one(inputs[i]), todo), 1):
            counts[s] = counts.get(s, 0) + 1
            if k % 100 == 0 or k == len(todo):
                print(f"{k}/{len(todo)} {counts}", flush=True)


def load(raw_dir, model, inputs):
    rows = {}
    for p in raw_dir.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        so = d.get("structured_output")
        mu = (d.get("modelUsage") or {})
        x = inputs[int(p.stem)]
        row = {"models": ",".join(sorted(mu)), "list_usd": mu.get(model, {}).get("costUSD", 0.0),
               "tokens_out": mu.get(model, {}).get("outputTokens", 0)}
        if so:
            q = so["evidence_quote"]
            hay = "\n".join([x["title"], x["body"], x["commit_msgs"]])
            row.update(so)
            row["quote_ok"] = (q == "" and so["perf_role"] == "none") or (q != "" and q in hay)
            row["rt"] = so["perf_role"] in ("primary", "secondary") and so["perf_scope"] == "runtime"
        rows[int(p.stem)] = row
    return pd.DataFrame.from_dict(rows, orient="index")


def kappa(a, b):
    a, b = pd.Series(a).astype(str), pd.Series(b).astype(str)
    po = (a.values == b.values).mean()
    cats = set(a) | set(b)
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0


def compare():
    with open(OPUS / "inputs.jsonl", encoding="utf-8") as f:
        inputs = {x["id"]: x for x in map(json.loads, f)}
    o = load(OPUS / "cc_raw", base.MODEL, inputs)
    h = load(OUT / "cc_raw", HAIKU, inputs)
    both = o.join(h, lsuffix="_o", rsuffix="_h", how="inner")
    both = both[both["perf_role_o"].notna() & both["perf_role_h"].notna()]
    tp = int((both.rt_o & both.rt_h).sum())
    s = {"n_compared": len(both),
         "runtime_perf_opus": int(both.rt_o.sum()), "runtime_perf_haiku": int(both.rt_h.sum()),
         "runtime_perf_agreement": round((both.rt_o == both.rt_h).mean(), 4),
         "runtime_perf_kappa": kappa(both.rt_o, both.rt_h),
         "haiku_precision_vs_opus": round(tp / both.rt_h.sum(), 4) if both.rt_h.sum() else None,
         "haiku_recall_vs_opus": round(tp / both.rt_o.sum(), 4) if both.rt_o.sum() else None,
         "role_agreement": round((both.perf_role_o == both.perf_role_h).mean(), 4),
         "role_kappa": kappa(both.perf_role_o, both.perf_role_h),
         "scope_kappa": kappa(both.perf_scope_o, both.perf_scope_h),
         "role_confusion_opus_rows_haiku_cols": pd.crosstab(both.perf_role_o, both.perf_role_h).to_dict(),
         "haiku_quote_not_verbatim": int((~h["quote_ok"].astype(bool)).sum()),
         "haiku_not_model_alone": int((h["models"] != HAIKU).sum()),
         "haiku_no_label": int(h["perf_role"].isna().sum()),
         "usd_per_pr_opus": round(o["list_usd"].mean(), 4),
         "usd_per_pr_haiku": round(h["list_usd"].mean(), 4),
         "tokens_out_mean_opus": round(o["tokens_out"].mean(), 1),
         "tokens_out_mean_haiku": round(h["tokens_out"].mean(), 1)}
    (OUT / "agreement.json").write_text(json.dumps(s, indent=1, default=str))
    print(json.dumps(s, indent=1, default=str))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"run": run, "compare": compare}[cmd](*args)
