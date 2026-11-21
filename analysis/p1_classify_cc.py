"""Run the pilot classification through headless Claude Code (the user's
Claude account) instead of paid API calls. Decision 2026-11-20.

Same codebook, schema, inputs and quote check as p1_classify.py. One clean
`claude -p` call per PR:
  --system-prompt-file   our codebook prompt replaces Claude Code's own
  --tools ""             no tools
  --setting-sources ""   no user/project/local settings
  disableAllHooks        no plugin hooks (checked: no CLAUDE.md, memory or
                         hook text reaches the call)
  --strict-mcp-config    no MCP servers
Not removable without --bare (which cannot use an account login): a fixed
~740-token Claude Code environment block (date, OS, model name, working
directory, user email, file-safety guidance). It is identical for every
PR; measured 2026-11-20.

Resumable: a PR whose raw file exists is skipped.

Usage:
  python -I analysis/p1_classify_cc.py run [N] [WORKERS]   # N = first N of the sample
  python -I analysis/p1_classify_cc.py collect
"""

import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_classify as base  # noqa: E402

OUT = base.OUT
RAW = OUT / "cc_raw"
WORK = OUT / "cc_cwd"  # empty working directory: no project CLAUDE.md
MODEL, EFFORT = base.MODEL, base.EFFORT
# Task definition; other runs (e.g. claim extraction) replace these two.
SCHEMA, USER_PROMPT = base.SCHEMA, base.user_prompt


def flags():
    return ["-p", "--system-prompt-file", str(WORK / "system.txt"),
            "--json-schema", json.dumps(SCHEMA),
            "--settings", json.dumps({"disableAllHooks": True}),
            "--model", MODEL, "--effort", EFFORT, "--tools", "",
            "--strict-mcp-config", "--setting-sources", "",
            "--no-session-persistence", "--exclude-dynamic-system-prompt-sections",
            "--output-format", "json"]


def one(x, retries=3):
    out = RAW / f"{x['id']}.json"
    for attempt in range(retries):
        t0 = time.time()
        p = subprocess.run(["claude", *flags()], input=USER_PROMPT(x),
                           capture_output=True, text=True, encoding="utf-8",
                           cwd=WORK, timeout=600)
        try:
            d = json.loads(p.stdout)
        except json.JSONDecodeError:
            d = {"is_error": True, "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
        d["_wall_s"] = round(time.time() - t0, 1)
        d["_attempt"] = attempt + 1
        if not d.get("is_error") and d.get("structured_output"):
            # After a safety stop Claude Code can silently answer with another
            # model (seen: Opus 4.8). Such an answer is kept for the record but
            # is not a label: the PR counts as seen, with no valid label.
            if set(d.get("modelUsage") or {}) != {MODEL}:
                d["fallback_output"] = d.pop("structured_output")
                out.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
                return x["id"], "fallback"
            out.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            return x["id"], "ok"
        # safety stops are recorded, not retried
        if d.get("safety_stops") or "safeguards" in str(d.get("result", "")):
            out.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            return x["id"], "safety_stop"
        time.sleep(30 * (attempt + 1))
    (OUT / "cc_failed").mkdir(exist_ok=True)
    (OUT / "cc_failed" / f"{x['id']}.json").write_text(json.dumps(d, ensure_ascii=False))
    return x["id"], "failed"


def run(n=None, workers=3):
    RAW.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    prompt = base.system_prompt()
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    ver = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    rec_path = OUT / "cc_run.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        # every PR of one run must see the same prompt, model and CLI version
        if rec.get("system_prompt_sha256", digest) != digest:
            sys.exit("system prompt changed since the run started; start a new run directory")
        if rec["claude_code_version"] != ver or rec["model"] != MODEL:
            sys.exit(f"CLI/model changed: {rec['claude_code_version']} -> {ver}")
        rec["system_prompt_sha256"] = digest
    else:
        rec = {"claude_code_version": ver, "model": MODEL, "effort": EFFORT,
               "flags": flags(), "codebook": str(base.CODEBOOK.name),
               "system_prompt_sha256": digest,
               "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    rec_path.write_text(json.dumps(rec, indent=1))
    (WORK / "system.txt").write_text(prompt, encoding="utf-8")
    inputs = base.load_inputs()[: int(n) if n else None]
    todo = [x for x in inputs if not (RAW / f"{x['id']}.json").exists()]
    print(f"{len(inputs) - len(todo)} done, {len(todo)} to do, {workers} workers", flush=True)
    counts, streak = {}, 0
    with ThreadPoolExecutor(max_workers=int(workers)) as ex:
        futs = [ex.submit(one, x) for x in todo]
        for i, f in enumerate(as_completed(futs), 1):
            _, status = f.result()
            counts[status] = counts.get(status, 0) + 1
            streak = streak + 1 if status == "failed" else 0
            if i % 25 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} {counts}", flush=True)
            if streak >= 10:  # e.g. usage limit reached: stop instead of churning
                print(f"stopping: 10 failures in a row at {i}/{len(todo)} {counts}", flush=True)
                for g in futs:
                    g.cancel()
                break


def collect():
    inputs = {x["id"]: x for x in base.load_inputs()}
    rows = []
    for f in sorted(RAW.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        x = inputs[int(f.stem)]
        row = {"id": x["id"], "agent": x["agent"], "wall_s": d.get("_wall_s")}
        so = d.get("structured_output")
        if so:
            row.update(so)
            q = so.get("evidence_quote", "")
            hay = "\n".join([x["title"], x["body"], x["commit_msgs"]])
            row["quote_found"] = (q == "" and so.get("perf_role") == "none") or (q != "" and q in hay)
            row["status"] = "ok"
        else:
            row["status"] = "safety_stop"
        # Claude Code can fall back to another model after a safety stop;
        # a label must come from MODEL alone to count
        row["models"] = ",".join(sorted((d.get("modelUsage") or {}).keys()))
        row["safety_stops"] = d.get("safety_stops", 0)
        mu = (d.get("modelUsage") or {}).get(MODEL, {})
        row["tokens_in"] = sum(mu.get(k, 0) for k in
                               ("inputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"))
        row["tokens_out"] = mu.get("outputTokens", 0)
        row["list_usd"] = mu.get("costUSD", 0.0)
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "pilot_labels_cc.parquet", index=False)
    s = {"n": len(df), "status": df["status"].value_counts().to_dict(),
         "perf_role": df["perf_role"].value_counts().to_dict(),
         "perf_scope": df["perf_scope"].value_counts().to_dict(),
         "confidence": df["confidence"].value_counts().to_dict(),
         "quote_not_found": int((df["quote_found"] == False).sum()),  # noqa: E712
         "labels_not_from_model_alone": int(((df["status"] == "ok") & (df["models"] != MODEL)).sum()),
         "runs_with_safety_stops": int((df["safety_stops"] > 0).sum()),
         "tokens_in_mean": round(df["tokens_in"].mean()),
         "tokens_out_mean": round(df["tokens_out"].mean()),
         "list_usd_total": round(df["list_usd"].sum(), 2),
         "wall_s_median": df["wall_s"].median()}
    (OUT / "pilot_summary_cc.json").write_text(json.dumps(s, indent=1, default=int))
    print(json.dumps(s, indent=1, default=int))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"run": run, "collect": collect}[cmd](*args)
