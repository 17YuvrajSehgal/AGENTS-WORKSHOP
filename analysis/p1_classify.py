"""Stage 2 of perf-PR selection: LLM classification with the codebook.

Pilot (decision 2026-11-20): a simple random sample of 2,000 keyword
candidates (seed 42), sent through the Message Batches API. Measures the
real cost per PR and the yield before deciding on the remaining ~106k.

Steps (each writes to data/p1_classify/):
  python -I analysis/p1_classify.py sample        # draw the sample, build inputs
  python -I analysis/p1_classify.py dryrun        # print request count + size, no API call
  python -I analysis/p1_classify.py submit        # create the batch (spends money)
  python -I analysis/p1_classify.py fetch         # poll, collect, validate, score cost

Rules:
  * the evidence quote must occur verbatim in the PR text; rows that fail
    are kept and flagged, never repaired
  * every request, raw response and usage record is saved
  * text is never cut silently: inputs over MAX_CHARS are cut and flagged
"""

import json
import random
import sys
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "p1_classify"
CODEBOOK = ROOT / "labels" / "codebook-perf-v0.md"
MODEL = "claude-opus-5-5"
EFFORT = "low"
N_PILOT, SEED = 2000, 42
MAX_CHARS = 12000  # per field; p90 of title+body is ~5,000 chars
MAX_FILES = 60

SCHEMA = {
    "type": "object",
    "properties": {
        "perf_role": {"type": "string",
                      "enum": ["primary", "secondary", "measurement_only", "none"]},
        "perf_scope": {"type": "string",
                       "enum": ["runtime", "build_or_ci", "test_suite", "other",
                                "not_applicable"]},
        "evidence_quote": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["perf_role", "perf_scope", "evidence_quote", "confidence"],
    "additionalProperties": False,
}


def cut(text, limit):
    text = text if isinstance(text, str) else ""
    return (text[:limit], True) if len(text) > limit else (text, False)


def sample():
    OUT.mkdir(parents=True, exist_ok=True)
    cand = pd.read_parquet(ROOT / "data" / "p1_candidates.parquet",
                           columns=["id", "agent", "repo_id", "title",
                                    "body_clean", "commit_msgs", "html_url",
                                    "kw_any"])
    ids = sorted(cand["id"].tolist())
    picked = set(random.Random(SEED).sample(ids, N_PILOT))
    s = cand[cand["id"].isin(picked)].copy()

    files = pq.read_table(ROOT / "data" / "aidev-v5" / "pr_commit_details.parquet",
                          columns=["pr_id", "filename"],
                          filters=[("pr_id", "in", list(picked))]).to_pandas()
    flist = files.dropna().groupby("pr_id")["filename"].apply(
        lambda f: sorted(set(f)))
    s["files"] = s["id"].map(flist)

    rows = []
    for r in s.itertuples():
        body, tb = cut(r.body_clean, MAX_CHARS)
        msgs, tm = cut(r.commit_msgs, MAX_CHARS)
        fl = r.files if isinstance(r.files, list) else []
        rows.append({"id": int(r.id), "agent": r.agent, "repo_id": int(r.repo_id),
                     "html_url": r.html_url, "title": r.title or "",
                     "body": body, "commit_msgs": msgs,
                     "files": fl[:MAX_FILES], "n_files": len(fl),
                     "cut_body": tb, "cut_commits": tm,
                     "kw_any": list(r.kw_any)})
    with open(OUT / "pilot_input.jsonl", "w", encoding="utf-8") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    meta = {"n": len(rows), "seed": SEED, "population": len(ids),
            "by_agent": pd.Series([x["agent"] for x in rows]).value_counts().to_dict(),
            "cut_body": sum(x["cut_body"] for x in rows),
            "cut_commits": sum(x["cut_commits"] for x in rows),
            "no_file_list": sum(1 for x in rows if not x["files"])}
    (OUT / "pilot_sample_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


def load_inputs():
    with open(OUT / "pilot_input.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def system_prompt():
    return ("You label GitHub pull requests for a research study, following "
            "the codebook below exactly. Answer only with the JSON object.\n\n"
            + CODEBOOK.read_text(encoding="utf-8"))


def user_prompt(x):
    files = "\n".join(x["files"]) or "(no file list available)"
    more = f"\n... and {x['n_files'] - len(x['files'])} more files" \
        if x["n_files"] > len(x["files"]) else ""
    return (f"TITLE:\n{x['title']}\n\nDESCRIPTION:\n{x['body'] or '(empty)'}\n\n"
            f"COMMIT MESSAGES:\n{x['commit_msgs'] or '(none)'}\n\n"
            f"CHANGED FILES:\n{files}{more}")


def build_requests(inputs):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    sys_blocks = [{"type": "text", "text": system_prompt(),
                   "cache_control": {"type": "ephemeral"}}]
    return [Request(custom_id=f"pr-{x['id']}",
                    params=MessageCreateParamsNonStreaming(
                        model=MODEL, max_tokens=4096,
                        system=sys_blocks,
                        output_config={"effort": EFFORT,
                                       "format": {"type": "json_schema",
                                                  "schema": SCHEMA}},
                        messages=[{"role": "user", "content": user_prompt(x)}]))
            for x in inputs]


def dryrun():
    inputs = load_inputs()
    sys_chars = len(system_prompt())
    user_chars = [len(user_prompt(x)) for x in inputs]
    print(f"requests: {len(inputs)}  model: {MODEL}  effort: {EFFORT}")
    print(f"system prompt: {sys_chars} chars (cached after the first request)")
    print(f"user prompts: total {sum(user_chars):,} chars, "
          f"median {sorted(user_chars)[len(user_chars) // 2]:,}, max {max(user_chars):,}")
    print("rough input tokens (chars/4):", f"{(sum(user_chars)) // 4:,}",
          "+ system prompt per request")


def submit():
    import anthropic
    client = anthropic.Anthropic()
    reqs = build_requests(load_inputs())
    batch = client.messages.batches.create(requests=reqs)
    rec = {"batch_id": batch.id, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "n": len(reqs), "model": MODEL, "effort": EFFORT}
    (OUT / "batch.json").write_text(json.dumps(rec, indent=1))
    print(rec)


def fetch():
    import anthropic
    client = anthropic.Anthropic()
    rec = json.loads((OUT / "batch.json").read_text())
    while True:
        b = client.messages.batches.retrieve(rec["batch_id"])
        if b.processing_status == "ended":
            break
        print("status:", b.processing_status, b.request_counts, flush=True)
        time.sleep(60)
    inputs = {f"pr-{x['id']}": x for x in load_inputs()}
    rows, usage = [], {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    with open(OUT / "pilot_raw.jsonl", "w", encoding="utf-8") as raw:
        for res in client.messages.batches.results(rec["batch_id"]):
            raw.write(res.model_dump_json() + "\n")
            x = inputs[res.custom_id]
            row = {"id": x["id"], "agent": x["agent"], "result": res.result.type}
            if res.result.type == "succeeded":
                msg = res.result.message
                u = msg.usage
                usage["input"] += u.input_tokens
                usage["output"] += u.output_tokens
                usage["cache_read"] += u.cache_read_input_tokens or 0
                usage["cache_write"] += u.cache_creation_input_tokens or 0
                row["stop_reason"] = msg.stop_reason
                text = next((blk.text for blk in msg.content if blk.type == "text"), "")
                try:
                    row.update(json.loads(text))
                except json.JSONDecodeError:
                    row["parse_error"] = True
                q = row.get("evidence_quote", "")
                hay = "\n".join([x["title"], x["body"], x["commit_msgs"]])
                row["quote_found"] = (q == "" and row.get("perf_role") == "none") \
                    or (q != "" and q in hay)
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "pilot_labels.parquet", index=False)
    summary = {"results": df["result"].value_counts().to_dict(), "usage": usage,
               "stop_reason": df.get("stop_reason", pd.Series()).value_counts().to_dict(),
               "perf_role": df.get("perf_role", pd.Series()).value_counts().to_dict(),
               "perf_scope": df.get("perf_scope", pd.Series()).value_counts().to_dict(),
               "quote_not_found": int((df.get("quote_found") == False).sum())}  # noqa: E712
    (OUT / "pilot_summary.json").write_text(json.dumps(summary, indent=1, default=int))
    print(json.dumps(summary, indent=1, default=int))


if __name__ == "__main__":
    {"sample": sample, "dryrun": dryrun, "submit": submit, "fetch": fetch}[sys.argv[1]]()
