"""Stage 1 of perf-PR selection: a broad keyword filter (recall, not precision).

Searches AIDev-pop PR titles, bodies and commit messages (v5, pinned) for
performance vocabulary. Precision comes later from the LLM classifier and
the human check, so this list is deliberately wide. The list is frozen
in this file; any change is a new git commit.

Writes data/p1_candidates.parquet (one row per matching PR, with the
keyword groups that matched and where) and prints per-group hit counts.

Usage: python -I AGENTS-WORKSHOP/analysis/p1_keyword_filter.py
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "data" / "aidev-v5"

GROUPS = {
    "perf_word": r"\bperf(?:ormance|ormant)?\b",
    "speed": r"\bfaster\b|\bspeed[\s-]?ups?\b|\bspeed\b|\bslow(?:er|ness|down|downs)?\b|\bsluggish\b",
    "latency_throughput": r"\blatenc(?:y|ies)\b|\bthroughput\b|\bresponse time\b|\bstartup time\b|\bload time\b",
    "optimize": r"\boptimi[sz](?:e|ed|es|ing|ation|ations)\b",
    "efficiency": r"\b(?:in)?efficien(?:t|tly|cy)\b",
    "memory": r"\bmemory (?:usage|leak|leaks|footprint|consumption|pressure)\b|\bout of memory\b|\bOOM\b|\bRSS\b",
    "allocation": r"\balloc(?:ate|ates|ated|ation|ations|ating)\b",
    "cache": r"\bcach(?:e|es|ed|ing)\b|\bmemoi[sz](?:e|ed|ation)\b",
    "complexity": r"\bO\(\s*n|\bquadratic\b|\bexponential\b|\bcomplexity\b|\bN\+1\b",
    "benchmark_profile": r"\bbenchmark(?:s|ed|ing)?\b|\bprofil(?:e|ed|ing|er)\b|\bflame ?graph\b|\bhot[\s-]?path\b|\bbottleneck\b",
    "batch_lazy": r"\bbatch(?:ed|es|ing)?\b|\blazy(?:[\s-]load(?:ing)?|ily)?\b|\bdebounc(?:e|ed|ing)\b|\bthrottl(?:e|ed|ing)\b",
    "redundant_work": r"\bredundant\b|\bunnecessary (?:call|calls|query|queries|request|requests|copy|copies|computation|re-?render|re-?renders|work)\b|\bavoid(?:s|ing)? (?:repeated|redundant|unnecessary)\b",
    "parallel": r"\bparalleli[sz](?:e|ed|es|ing|ation)\b|\bconcurren(?:t|tly|cy)\b|\bvectori[sz](?:e|ed|ation)\b|\bmulti-?thread(?:ed|ing)?\b",
    "cpu_io": r"\bCPU (?:usage|time|bound|load)\b|\bI/O[\s-]bound\b|\bdisk I/O\b|\bsyscalls?\b",
}
PATTERNS = {g: re.compile(p, re.IGNORECASE) for g, p in GROUPS.items()}
TEMPLATE_SHARE = 0.005  # a body line in >= 0.5% of one agent's PRs is template text


def match_groups(text):
    if not isinstance(text, str) or not text:
        return []
    return [g for g, p in PATTERNS.items() if p.search(text)]


def main():
    pr = pd.read_parquet(LOCAL / "pull_request.parquet",
                         columns=["id", "agent", "repo_id", "title", "body",
                                  "state", "merged_at", "html_url"])
    commits = pd.read_parquet(LOCAL / "pr_commits.parquet",
                              columns=["pr_id", "message"])
    msgs = commits.groupby("pr_id")["message"].apply(
        lambda s: "\n".join(m for m in s if isinstance(m, str)))
    pr["commit_msgs"] = pr["id"].map(msgs)

    # Template text: a line that appears verbatim in >= TEMPLATE_SHARE of one
    # agent's PR bodies (e.g. Copilot's "coding agent works faster ... when set
    # up" footer) is removed before matching. Removed lines are written out.
    # URLs are masked so per-repository links do not make template lines unique
    url = re.compile(r"\(https?://[^)]*\)|<a href=\"[^\"]*\"|https?://\S+")
    norm = lambda line: " ".join(url.sub("<URL>", line).split())
    lines = pr[["agent", "body"]].copy()
    lines["line"] = lines["body"].fillna("").map(
        lambda b: sorted({norm(x) for x in b.splitlines() if norm(x)}))
    exploded = lines[["agent", "line"]].explode("line").dropna()
    per_agent_n = pr["agent"].value_counts()
    counts = exploded.groupby(["agent", "line"]).size().reset_index(name="n")
    counts["share"] = counts["n"] / counts["agent"].map(per_agent_n)
    template = counts[counts["share"] >= TEMPLATE_SHARE]
    template_by_agent = template.groupby("agent")["line"].apply(set).to_dict()
    template.sort_values(["agent", "n"], ascending=[True, False]).to_csv(
        ROOT / "data" / "p1_template_lines.csv", index=False)

    def strip_template(agent, body):
        if not isinstance(body, str):
            return body
        drop = template_by_agent.get(agent, set())
        return "\n".join(x for x in body.splitlines() if norm(x) not in drop)

    pr["body_clean"] = [strip_template(a, b) for a, b in zip(pr["agent"], pr["body"])]

    pr["kw_title"] = pr["title"].map(match_groups)
    pr["kw_body"] = pr["body_clean"].map(match_groups)
    pr["kw_commits"] = pr["commit_msgs"].map(match_groups)
    pr["kw_any"] = [sorted(set(a) | set(b) | set(c)) for a, b, c in
                    zip(pr["kw_title"], pr["kw_body"], pr["kw_commits"])]
    cand = pr[pr["kw_any"].map(len) > 0]

    stats = {"pop_prs": len(pr), "candidates": len(cand),
             "template_share": TEMPLATE_SHARE,
             "template_lines_per_agent": {a: len(s) for a, s in template_by_agent.items()},
             "candidates_body_or_commit_only": int((cand["kw_title"].map(len) == 0).sum()),
             "candidates_title_match": int((cand["kw_title"].map(len) > 0).sum()),
             "per_group_any": {g: int(cand["kw_any"].map(lambda k, g=g: g in k).sum())
                               for g in GROUPS},
             "per_group_title": {g: int(cand["kw_title"].map(lambda k, g=g: g in k).sum())
                                 for g in GROUPS},
             "candidates_by_agent": cand["agent"].value_counts().to_dict()}
    print(json.dumps(stats, indent=1))
    cand.to_parquet(ROOT / "data" / "p1_candidates.parquet", index=False)
    (ROOT / "data" / "p1_keyword_stats.json").write_text(
        json.dumps(stats, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
