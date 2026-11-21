"""Claim extraction: which mechanism(s) does each runtime-perf PR claim?

Input: the 1,343 runtime-perf PRs of data/p2_classify (labels.parquet).
Method (RESEARCH-PLAN 4.3): open-coding pilot on 100 PRs with an "other"
option; revise and freeze the codebook; then all PRs. Model:
claude-haiku-5-5 via headless Claude Code, same flags and safeguards as
the classifier runs (verbatim-quote check, fallback-model rule).

Usage:
  python -I analysis/p5_claims.py run <run_name> [N] [WORKERS]   # N = first N in random order
  python -I analysis/p5_claims.py collect <run_name>
"""

import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_classify as base  # noqa: E402
import p1_classify_cc as cc  # noqa: E402

ROOT = base.ROOT
CODEBOOK = ROOT / "labels" / "codebook-claims-v1.md"  # v0 = open-coding pilot (pilot100)
IDS = ["avoid_repeated_io", "cache_results", "batch_calls", "fewer_db_queries", "faster_db_query",
       "fewer_processes", "less_output", "less_memory", "algorithmic", "vectorize_locality",
       "less_locking", "parallelize", "async_io", "lazy_loading", "fewer_syscalls",
       "io_granularity", "smaller_payload", "gpu_accelerator", "skip_unneeded_work",
       "faster_library", "precompute", "reuse_resources", "concurrency_tuning", "polling_sleep",
       "streaming_output", "fewer_external_calls", "ui_rendering", "other"]
SCHEMA = {
    "type": "object",
    "properties": {
        "mechanisms": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string", "enum": IDS},
                           "quote": {"type": "string"},
                           "other_description": {"type": "string"}},
            "required": ["id", "quote", "other_description"], "additionalProperties": False}},
        "mechanism_stated": {"type": "boolean"},
        "claimed_effect": {"type": "string"},
        "evidence": {"type": "string", "enum": ["benchmark", "profile", "test", "reasoning", "none"]},
        "targets": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["mechanisms", "mechanism_stated", "claimed_effect", "evidence", "targets"],
    "additionalProperties": False,
}


def system_prompt():
    return ("You extract the performance claims of GitHub pull requests for a research study, "
            "following the codebook below exactly. Answer only with the JSON object.\n\n"
            + CODEBOOK.read_text(encoding="utf-8"))


def setup(run):
    out = ROOT / "data" / "p5_claims" / run
    cc.OUT, cc.RAW, cc.WORK = out, out / "cc_raw", out / "cc_cwd"
    cc.MODEL, cc.SCHEMA, cc.USER_PROMPT = "claude-haiku-5-5", SCHEMA, base.user_prompt
    for d in (cc.RAW, cc.WORK):
        d.mkdir(parents=True, exist_ok=True)
    (cc.WORK / "system.txt").write_text(system_prompt(), encoding="utf-8")
    return out


def population():
    lab = pd.read_parquet(ROOT / "data" / "p2_classify" / "labels.parquet")
    ids = set(lab[(lab.status == "ok") & (lab.runtime_perf == True)]["id"])  # noqa: E712
    rows = []
    with open(ROOT / "data" / "p2_classify" / "inputs.jsonl", encoding="utf-8") as f:
        for line in f:
            x = json.loads(line)
            if x["id"] in ids:
                rows.append(x)
    rows.sort(key=lambda x: x["id"])
    random.Random(42).shuffle(rows)  # fixed random order: any prefix is a random sample
    return rows


def run(name, n=None, workers=4):
    out = setup(name)
    rows = population()[: int(n) if n else None]
    (out / "run.json").write_text(json.dumps({"codebook": CODEBOOK.name, "model": cc.MODEL,
                                              "flags": cc.flags(), "n": len(rows)}, indent=1))
    todo = [x for x in rows if not (cc.RAW / f"{x['id']}.json").exists()]
    print(f"{len(rows) - len(todo)} done, {len(todo)} to do", flush=True)
    counts = {}
    with ThreadPoolExecutor(max_workers=int(workers)) as ex:
        for _, s in ex.map(cc.one, todo):
            counts[s] = counts.get(s, 0) + 1
    print(counts)


def collect(name):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = setup(name)
    inp = {x["id"]: x for x in population()}
    rows, mech = [], []
    for p in cc.RAW.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        x, so = inp[int(p.stem)], d.get("structured_output")
        if not so:
            rows.append({"id": x["id"], "status": "no_label"})
            continue
        hay = "\n".join([x["title"], x["body"], x["commit_msgs"]])
        norm = lambda s: " ".join(s.split())  # noqa: E731
        for m in so["mechanisms"]:
            mech.append({"id": x["id"], "agent": x["agent"], "mechanism": m["id"], "quote": m["quote"],
                         "other": m["other_description"], "quote_verbatim": m["quote"] in hay,
                         "quote_ws": norm(m["quote"]) in norm(hay)})
        rows.append({"id": x["id"], "agent": x["agent"], "status": "ok",
                     "n_mech": len(so["mechanisms"]), "stated": so["mechanism_stated"],
                     "claimed_effect": so["claimed_effect"], "evidence": so["evidence"],
                     "targets": json.dumps(so["targets"])})
    pr, m = pd.DataFrame(rows), pd.DataFrame(mech)
    pr.to_parquet(out / "claims_pr.parquet", index=False)
    m.to_parquet(out / "claims_mech.parquet", index=False)
    ok = pr[pr.status == "ok"]
    print("PRs:", len(pr), "| ok:", len(ok), "| no mechanism stated:", int((~ok.stated).sum()),
          "| with claimed effect:", int((ok.claimed_effect != "").sum()))
    print("evidence:", ok.evidence.value_counts().to_dict())
    print("mechanisms (share of PRs):")
    for k, v in m.groupby("mechanism").id.nunique().sort_values(ascending=False).items():
        print(f"   {k:20s} {v:4d}  {v / len(ok):.1%}")
    print("quotes not verbatim:", int((~m.quote_verbatim).sum()), "| not even after whitespace:",
          int((~m.quote_ws).sum()), "of", len(m))
    oth = m[m.mechanism == "other"]
    if len(oth):
        print(f"\n'other' descriptions ({len(oth)}):")
        for r in oth.itertuples():
            print("   -", r.other[:110])


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"run": run, "collect": collect}[cmd](*args)
