"""Full-population classification with Haiku (user decision 2026-11-20).

All 108,708 keyword candidates of AIDev-pop v5, labelled by
claude-haiku-5-5 with the pilot's codebook, schema, flags and effort.
Kept fully separate from p1 (pilot) and p2 (stratified run): its own
directory, its own scheduled task, fresh labels for every PR (no reuse).

PRs are processed in one fixed random order (seed 42), so any finished
prefix is a simple random sample of the candidates.

Usage:
  python -I analysis/p4_full.py prepare
  python -I analysis/p4_full.py run [WORKERS]
  python -I analysis/p4_full.py status
"""

import hashlib
import json
import random
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
OUT = ROOT / "data" / "p4_full"
SEED, CHUNK = 42, 200

cc.OUT, cc.RAW, cc.WORK, cc.MODEL = OUT, OUT / "cc_raw", OUT / "cc_cwd", "claude-haiku-5-5"


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    cand = pd.read_parquet(ROOT / "data" / "p1_candidates.parquet",
                           columns=["id", "agent", "repo_id", "title", "body_clean",
                                    "commit_msgs", "html_url", "kw_any"])
    files = pq.read_table(ROOT / "data" / "aidev-v5" / "pr_commit_details.parquet",
                          columns=["pr_id", "filename"]).to_pandas().dropna()
    files = files[files["pr_id"].isin(set(cand["id"]))]
    flist = files.groupby("pr_id")["filename"].apply(lambda f: sorted(set(f)))
    ids = sorted(cand["id"])
    random.Random(SEED).shuffle(ids)
    rank = {i: k for k, i in enumerate(ids)}
    cand = cand.assign(rank=cand["id"].map(rank)).sort_values("rank")
    with open(OUT / "inputs.jsonl", "w", encoding="utf-8") as f:
        for r in cand.itertuples():
            body, tb = base.cut(r.body_clean, base.MAX_CHARS)
            msgs, tm = base.cut(r.commit_msgs, base.MAX_CHARS)
            fl = flist.get(r.id, [])
            f.write(json.dumps({"id": int(r.id), "rank": int(r.rank), "agent": r.agent,
                                "repo_id": int(r.repo_id), "html_url": r.html_url,
                                "title": r.title or "", "body": body, "commit_msgs": msgs,
                                "files": fl[:base.MAX_FILES], "n_files": len(fl),
                                "cut_body": tb, "cut_commits": tm,
                                "kw_any": list(r.kw_any)}, ensure_ascii=False) + "\n")
    print(f"inputs written: {len(cand)} PRs in random order (seed {SEED})")


def load_inputs():
    with open(OUT / "inputs.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]  # already in rank order


def single_instance():
    import msvcrt
    f = open(OUT / "run.lock", "a+")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print(time.strftime("%H:%M:%S"), "another runner is active; exiting", flush=True)
        sys.exit(0)
    return f


def guard():
    digest = hashlib.sha256(base.system_prompt().encode("utf-8")).hexdigest()
    ver = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    rp = OUT / "cc_run.json"
    rec = json.loads(rp.read_text()) if rp.exists() else {
        "claude_code_version": ver, "model": cc.MODEL, "effort": base.EFFORT, "flags": cc.flags(),
        "system_prompt_sha256": digest, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if rec["system_prompt_sha256"] != digest or rec["model"] != cc.MODEL:
        sys.exit("prompt or model changed; this run must stay homogeneous")
    if rec["claude_code_version"] != ver:
        rec.setdefault("version_changes", []).append(
            {"from": rec["claude_code_version"], "to": ver, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        rec["claude_code_version"] = ver
    rp.write_text(json.dumps(rec, indent=1))
    cc.RAW.mkdir(parents=True, exist_ok=True)
    cc.WORK.mkdir(parents=True, exist_ok=True)
    (cc.WORK / "system.txt").write_text(base.system_prompt(), encoding="utf-8")


def run(workers=4):
    lock = single_instance()  # noqa: F841
    guard()
    inputs = load_inputs()
    todo = [x for x in inputs if not (cc.RAW / f"{x['id']}.json").exists()]
    print(time.strftime("%H:%M:%S"), f"{len(inputs) - len(todo)} done, {len(todo)} to do", flush=True)
    streak, done = 0, 0
    with ThreadPoolExecutor(max_workers=int(workers)) as ex:
        for k in range(0, len(todo), CHUNK):
            for _, status in ex.map(cc.one, todo[k:k + CHUNK]):
                done += 1
                streak = streak + 1 if status == "failed" else 0
                if streak >= 10:
                    print(time.strftime("%H:%M:%S"), "stopping: 10 failures in a row (usage limit?)", flush=True)
                    return
            print(time.strftime("%H:%M:%S"), f"+{done} this run", flush=True)
    print("all PRs labelled", flush=True)


def status():
    n = sum(1 for _ in open(OUT / "inputs.jsonl", encoding="utf-8"))
    raw = list(cc.RAW.glob("*.json"))
    print(f"labelled {len(raw)} / {n} ({100 * len(raw) / n:.1f}%)")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"prepare": prepare, "run": run, "status": status}[cmd](*args)
