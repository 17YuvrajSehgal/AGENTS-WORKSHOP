"""Stratified classification of .py-changing candidates with a stop rule.

Design (RESEARCH-PLAN.md section 4.5, 2026-11-20):
  * population: keyword candidates that change >= 1 `.py` file
  * one stratum per agent; each stratum has ONE fixed order, saved once in
    order.parquet: the pilot's PRs of that stratum first (shuffled), then
    all others (shuffled), seed 42. Any prefix of this order is a simple
    random sample of the stratum (pilot = random draw, rest = random draw
    from the remainder).
  * a stratum is classified down its order until it has `target`
    runtime-perf labels (role primary/secondary + scope runtime), or to
    the end when its target is "all".
  * to grow the sample later: raise a target in targets.json and rerun.
    The run continues down the same order; nothing is redone.
Same codebook, schema, model, flags and quote check as the pilot
(p1_classify_cc.py); pilot raw results are reused, after checking the
system prompt hash matches.

Usage:
  python -I analysis/p2_classify.py prepare     # once: inputs + order + targets
  python -I analysis/p2_classify.py run [WORKERS]
  python -I analysis/p2_classify.py status
"""

import hashlib
import json
import random
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_classify as base  # noqa: E402
import p1_classify_cc as cc  # noqa: E402

ROOT = base.ROOT
OUT = ROOT / "data" / "p2_classify"
SEED = 42
CHUNK = 30  # PRs per stratum between stop-rule checks

# p1_classify_cc.one() reads these module globals; point them at this run
cc.OUT, cc.RAW, cc.WORK = OUT, OUT / "cc_raw", OUT / "cc_cwd"
# Model switch 2026-11-20 (user decision): PRs labelled so far (1,131, Opus
# 5.5) are kept; every PR labelled from now on uses Haiku 5.5 (~1/40 of the
# usage). Each raw file records its model in `modelUsage`.
cc.MODEL = "claude-haiku-5-5"


def is_runtime_perf(so):
    return so.get("perf_role") in ("primary", "secondary") and so.get("perf_scope") == "runtime"


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    cand = pd.read_parquet(ROOT / "data" / "p1_candidates.parquet",
                           columns=["id", "agent", "repo_id", "title", "body_clean",
                                    "commit_msgs", "html_url", "kw_any"])
    files = pq.read_table(ROOT / "data" / "aidev-v5" / "pr_commit_details.parquet",
                          columns=["pr_id", "filename"]).to_pandas().dropna()
    files = files[files["pr_id"].isin(set(cand["id"]))]
    py = set(files.loc[files["filename"].str.lower().str.endswith(".py"), "pr_id"])
    pop = cand[cand["id"].isin(py)].copy()
    flist = files[files["pr_id"].isin(py)].groupby("pr_id")["filename"].apply(lambda f: sorted(set(f)))
    pop["files"] = pop["id"].map(flist)

    with open(OUT / "inputs.jsonl", "w", encoding="utf-8") as f:
        for r in pop.itertuples():
            body, tb = base.cut(r.body_clean, base.MAX_CHARS)
            msgs, tm = base.cut(r.commit_msgs, base.MAX_CHARS)
            fl = r.files
            f.write(json.dumps({"id": int(r.id), "agent": r.agent, "repo_id": int(r.repo_id),
                                "html_url": r.html_url, "title": r.title or "", "body": body,
                                "commit_msgs": msgs, "files": fl[:base.MAX_FILES],
                                "n_files": len(fl), "cut_body": tb, "cut_commits": tm,
                                "kw_any": list(r.kw_any)}, ensure_ascii=False) + "\n")

    pilot = {json.loads(line)["id"] for line in
             open(ROOT / "data" / "p1_classify" / "pilot_input.jsonl", encoding="utf-8")}
    rows = []
    for agent, g in pop.groupby("agent"):
        ids = sorted(g["id"])
        first = [i for i in ids if i in pilot]
        rest = [i for i in ids if i not in pilot]
        rng = random.Random(f"{SEED}-{agent}")
        rng.shuffle(first)
        rng.shuffle(rest)
        rows += [{"agent": agent, "rank": k, "id": i, "from_pilot": i in pilot}
                 for k, i in enumerate(first + rest)]
    pd.DataFrame(rows).to_parquet(OUT / "order.parquet", index=False)

    tpath = OUT / "targets.json"
    if not tpath.exists():  # never overwrite: raising targets later is done by hand
        tpath.write_text(json.dumps(
            {"_note": "runtime-perf PRs to collect per stratum; 'all' = whole stratum. "
                      "Raise a number and rerun to extend the sample.",
             "Claude_Code": 463, "Copilot": 250, "OpenAI_Codex": 250,
             "Devin": "all", "Cursor": "all", "Google_Jules": "all"}, indent=1))

    # reuse pilot results (identical prompt, model and flags) for pilot PRs in the population
    prec = json.loads((ROOT / "data" / "p1_classify" / "cc_run.json").read_text())
    digest = hashlib.sha256(base.system_prompt().encode("utf-8")).hexdigest()
    assert prec["system_prompt_sha256"] == digest, "codebook changed since the pilot"
    cc.RAW.mkdir(parents=True, exist_ok=True)
    reused = 0
    for i in set(pop["id"]) & pilot:
        src = ROOT / "data" / "p1_classify" / "cc_raw" / f"{i}.json"
        if src.exists() and not (cc.RAW / src.name).exists():
            shutil.copy(src, cc.RAW / src.name)
            reused += 1
    print(f"population {len(pop)}; strata {pop['agent'].value_counts().to_dict()}; "
          f"pilot PRs in population {len(set(pop['id']) & pilot)}, raw reused {reused}")


def load_inputs():
    with open(OUT / "inputs.jsonl", encoding="utf-8") as f:
        return {x["id"]: x for x in map(json.loads, f)}


def result(i):
    p = cc.RAW / f"{i}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("structured_output") or {}


def guard():
    digest = hashlib.sha256(base.system_prompt().encode("utf-8")).hexdigest()
    ver = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    rp = OUT / "cc_run.json"
    if rp.exists():
        rec = json.loads(rp.read_text())
        if rec["system_prompt_sha256"] != digest:
            sys.exit("system prompt changed; start a new run directory")
        if rec["model"] != cc.MODEL:
            rec.setdefault("model_changes", []).append(
                {"from": rec["model"], "to": cc.MODEL, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "labels_before": len(list(cc.RAW.glob("*.json")))})
            rec["model"] = cc.MODEL
            rec["flags"] = cc.flags()
        if rec["claude_code_version"] != ver:
            rec.setdefault("version_changes", []).append(
                {"from": rec["claude_code_version"], "to": ver, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
            rec["claude_code_version"] = ver
    else:
        rec = {"claude_code_version": ver, "model": cc.MODEL, "effort": base.EFFORT,
               "flags": cc.flags(), "system_prompt_sha256": digest,
               "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    rp.write_text(json.dumps(rec, indent=1))
    cc.WORK.mkdir(parents=True, exist_ok=True)
    (cc.WORK / "system.txt").write_text(base.system_prompt(), encoding="utf-8")


def stratum_state(order, targets):
    """Per stratum: next PRs to classify, or None if done."""
    state = {}
    for agent, g in order.sort_values("rank").groupby("agent"):
        tgt = targets.get(agent, 0)
        hits, todo = 0, []
        for i in g["id"]:
            r = result(i)
            if r is None:
                todo.append(i)
            elif is_runtime_perf(r):
                hits += 1
        done = len(g) - len(todo)
        finished = (tgt != "all" and hits >= tgt) or not todo
        state[agent] = {"size": len(g), "classified": done, "runtime_perf": hits,
                        "target": tgt, "finished": finished, "todo": todo}
    return state


def single_instance():
    """Exit if another runner holds the lock. The Task Scheduler once lost
    track of a live run (state Ready while it was working), so its
    IgnoreNew setting alone cannot stop a second copy."""
    import msvcrt
    f = open(OUT / "run.lock", "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print(time.strftime("%H:%M:%S"), "another runner is active; exiting", flush=True)
        sys.exit(0)
    return f  # keep the handle open: the lock lasts until this process ends


def run(workers=3):
    lock = single_instance()  # noqa: F841
    guard()
    inputs = load_inputs()
    order = pd.read_parquet(OUT / "order.parquet")
    targets = {k: v for k, v in json.loads((OUT / "targets.json").read_text()).items()
               if not k.startswith("_")}
    streak = 0
    with ThreadPoolExecutor(max_workers=int(workers)) as ex:
        while True:
            st = stratum_state(order, targets)
            open_ = [a for a, s in st.items() if not s["finished"]]
            print(time.strftime("%H:%M:%S"), {a: f"{s['runtime_perf']}/{s['target']} "
                                              f"({s['classified']}/{s['size']})" for a, s in st.items()},
                  flush=True)
            if not open_:
                print("all strata finished", flush=True)
                return
            # next chunk: CHUNK PRs from each open stratum, in order
            batch = [i for a in open_ for i in st[a]["todo"][:CHUNK]]
            for _, status in ex.map(lambda i: cc.one(inputs[i]), batch):
                streak = streak + 1 if status == "failed" else 0
                if streak >= 10:
                    print("stopping: 10 failures in a row (usage limit?)", flush=True)
                    return


def status():
    order = pd.read_parquet(OUT / "order.parquet")
    targets = {k: v for k, v in json.loads((OUT / "targets.json").read_text()).items()
               if not k.startswith("_")}
    st = stratum_state(order, targets)
    for a, s in st.items():
        s.pop("todo")
        print(a, s)


def collect():
    """One row per classified PR (labeller, label, quote check, usage) + summary."""
    inputs = load_inputs()
    order = pd.read_parquet(OUT / "order.parquet").set_index("id")
    rows = []
    for p in cc.RAW.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        i, mu = int(p.stem), d.get("modelUsage") or {}
        x, so = inputs[i], d.get("structured_output")
        row = {"id": i, "agent": x["agent"], "rank": int(order.loc[i, "rank"]),
               "from_pilot": bool(order.loc[i, "from_pilot"]),
               "labeller": ",".join(sorted(mu)),
               "status": "ok" if so else ("fallback" if d.get("fallback_output") else "no_label"),
               "list_usd": sum(v.get("costUSD", 0.0) for v in mu.values())}
        if so:
            q = so["evidence_quote"]
            hay = "\n".join([x["title"], x["body"], x["commit_msgs"]])
            row.update(so)
            row["quote_verbatim"] = (q == "" and so["perf_role"] == "none") or (q != "" and q in hay)
            row["quote_ws_normalised"] = row["quote_verbatim"] or " ".join(q.split()) in " ".join(hay.split())
            row["runtime_perf"] = is_runtime_perf(so)
        rows.append(row)
    df = pd.DataFrame(rows).sort_values(["agent", "rank"])
    df.to_parquet(OUT / "labels.parquet", index=False)
    ok = df[df["status"] == "ok"]
    by = ok.groupby("agent").agg(classified=("id", "size"), runtime_perf=("runtime_perf", "sum"))
    by["rate"] = (by["runtime_perf"] / by["classified"]).round(4)
    by["stratum_size"] = order.groupby("agent").size()
    lab = ok.groupby(["agent", "labeller"]).agg(n=("id", "size"), runtime_perf=("runtime_perf", "sum"))
    s = {"classified": len(df), "status": df["status"].value_counts().to_dict(),
         "labeller": df["labeller"].value_counts().to_dict(),
         "runtime_perf_total": int(ok["runtime_perf"].sum()),
         "by_agent": by.reset_index().to_dict(orient="records"),
         "by_agent_and_labeller": lab.reset_index().to_dict(orient="records"),
         "role": ok["perf_role"].value_counts().to_dict(),
         "quote_not_verbatim": int((ok["quote_verbatim"] == False).sum()),  # noqa: E712
         "quote_not_found_even_ws_normalised": int((ok["quote_ws_normalised"] == False).sum()),  # noqa: E712
         "list_usd_by_labeller": df.groupby("labeller")["list_usd"].sum().round(2).to_dict()}
    (OUT / "summary.json").write_text(json.dumps(s, indent=1, default=int))
    print(json.dumps(s, indent=1, default=int))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"prepare": prepare, "run": run, "status": status, "collect": collect}[cmd](*args)
