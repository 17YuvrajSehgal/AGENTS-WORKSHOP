"""Per-PR verdicts for measured PRs + paper macros (paper/results.tex).

  python -I analysis/p7_results.py <dir with fetched PR results>

Input: for each PR, <dir>/<vm>/<order_id>/{verdict.json, check.json, measure.json}
(copied from the VMs), plus the extracted claims (data/p5_claims/all_v1).

Rules (fixed before looking at the results, 2026-11-21):
  faster       head/base wall-time median ratio <= 0.95 AND every head timing
               run faster than every base run; slower: >= 1.05 AND full
               separation the other way; else no clear change.
  moved        a signal changed by >= 10% in the claimed direction with full
               separation between head and base runs.
  mechanism    a claimed mechanism holds if ANY of its signals moved (MECH below).
  hidden cost  any of COSTS rose >= 10% with full separation.
  excluded     any multiplexed counter row or lost trace event/packet.
  flags        output digest differs (behaviour change); Python < 50% of the
               PR's changed code lines (claim may live in non-Python code).
"""
import json
import statistics
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1])
UNCHECKABLE = {"gpu_accelerator", "fewer_external_calls", "ui_rendering", "other", "streaming_output"}
# mechanism -> list of (signal, direction); "syscalls" = total syscall count
MECH = {
    "skip_unneeded_work": [("instructions", "down"), ("syscalls", "down")],
    "less_memory": [("minor-faults", "down"), ("ev:kmem_mm_page_alloc", "down"), ("maxrss_kb", "down")],
    "cache_results": [("instructions", "down"), ("syscalls", "down")],
    "algorithmic": [("instructions", "down")],
    "precompute": [("instructions", "down")],
    "faster_library": [("instructions", "down")],
    "vectorize_locality": [("instructions", "down"), ("L1-dcache-load-misses", "down"),
                           ("l2_rqsts.miss", "down")],
    "parallelize": [("parallel", "special")],
    "async_io": [("offcpu_ns_main", "down")],
    "concurrency_tuning": [("context-switches", "any"), ("futex_ns", "any"), ("threads", "any")],
    "lazy_loading": [("sc:openat", "down"), ("bytes_read", "down")],
    "reuse_resources": [("sc:socket", "down"), ("sc:connect", "down"), ("threads", "down"),
                        ("forks", "down")],
    "faster_db_query": [("sc:pread64", "down"), ("bytes_read", "down"), ("instructions", "down")],
    "fewer_db_queries": [("sc:pread64", "down"), ("sc:sendto", "down"), ("sc:recvfrom", "down"),
                         ("instructions", "down")],
    "avoid_repeated_io": [("sc:openat", "down"), ("sc:read", "down"), ("bytes_read", "down")],
    "less_locking": [("futex_ns", "down"), ("sc:futex", "down")],
    "batch_calls": [("sc:sendto", "down"), ("sc:recvfrom", "down"), ("sc:write", "down")],
    "fewer_processes": [("forks", "down"), ("sc:execve", "down")],
    "less_output": [("sc:write", "down"), ("bytes_written", "down")],
    "fewer_syscalls": [("syscalls", "down")],
    "io_granularity": [("sc:read", "down"), ("sc:write", "down")],
    "smaller_payload": [("bytes_written", "down")],
    "polling_sleep": [("sc:clock_nanosleep", "down"), ("offcpu_ns_main", "down")],
}
COSTS = ["sys_s", "maxrss_kb", "minor-faults", "syscalls", "instructions", "task-clock", "bytes_read"]


def series(var, key):
    if key == "syscalls":  # total syscalls per traced run (sc:stat_any is a derived sum: skip)
        cols = [v for k, v in var.items() if k.startswith("sc:") and k != "sc:stat_any"]
        return [sum(c[i] for c in cols) for i in range(len(cols[0]))] if cols else []
    return [x for x in var.get(key, []) if x is not None]


def compare(base, head):
    """(ratio of medians, separation) or None if no data."""
    if not base or not head:
        return None
    mb, mh = statistics.median(base), statistics.median(head)
    if mb == 0 and mh == 0:
        return 1.0, "none"
    ratio = mh / mb if mb else float("inf")
    sep = "down" if max(head) < min(base) else ("up" if min(head) > max(base) else "overlap")
    return ratio, sep


def moved(V, key, direction):
    c = compare(series(V["base"], key), series(V["head"], key))
    if c is None:
        return False, None
    r, sep = c
    down = r <= 0.9 and sep == "down"
    up = r >= 1.1 and sep == "up"
    return {"down": down, "up": up, "any": down or up}[direction], round(r, 3)


def main():
    claims = pd.read_parquet(ROOT / "data" / "p5_claims" / "all_v1" / "claims_mech.parquet")
    cl = claims.groupby("id").mechanism.apply(set).to_dict()
    rows = []
    for mpath in sorted(SRC.glob("*/*/measure.json")):
        d = mpath.parent
        v = json.loads((d / "verdict.json").read_text())
        meas = json.loads(mpath.read_text())
        V = meas["variants"]
        pid = v["job"]["id"]
        integrity = [k for var in V.values() for k, xs in var.items()
                     if (k.startswith("pcnt_running:") and any(x is not None and x < 100 for x in xs))
                     or (k in ("discarded", "discarded_packets") and any(xs))]
        wall = compare(series(V["base"], "wall_s"), series(V["head"], "wall_s"))
        aa = compare(series(V["base"], "wall_s"), series(V["base_aa"], "wall_s"))
        r = wall[0]
        speed = ("faster" if r <= 0.95 and wall[1] == "down" else
                 "slower" if r >= 1.05 and wall[1] == "up" else "no_change")
        mechs = cl.get(pid, set())
        checkable = mechs - UNCHECKABLE
        held = {}
        for mname in sorted(checkable):
            ok = False
            for key, direction in MECH.get(mname, []):
                if key == "parallel":
                    w = moved(V, "wall_s", "down")[0]
                    tc = compare(series(V["base"], "task-clock"), series(V["head"], "task-clock"))
                    ok = ok or (w and tc is not None and tc[0] >= 0.9)
                else:
                    ok = ok or moved(V, key, direction)[0]
            held[mname] = ok
        costs = {k: moved(V, k, "up")[1] for k in COSTS if moved(V, k, "up")[0]}
        chk = v.get("check") or {}
        rows.append({
            "vm": d.parent.name, "id": pid, "repo": v["job"]["repo"], "number": v["job"]["number"],
            "agent": v["job"]["agent"], "wall_ratio": round(r, 3), "wall_sep": wall[1],
            "aa_ratio": round(aa[0], 3), "speed": speed, "mechanisms": sorted(mechs),
            "checkable": sorted(checkable), "held": held,
            "mechanism_held": any(held.values()) if held else None,
            "hidden_costs": costs, "behaviour_change": chk.get("output_equal") is False,
            "py_share": v.get("python_share_of_code_change"), "integrity": integrity,
            "tier": (v.get("agent") or {}).get("tier"),
        })
    df = pd.DataFrame(rows)
    out = ROOT / "data" / "p7_paper"
    out.mkdir(parents=True, exist_ok=True)
    df.to_json(out / "per_pr_verdicts.json", orient="records", indent=1)
    print(df[["vm", "repo", "number", "speed", "wall_ratio", "aa_ratio", "checkable", "mechanism_held",
              "behaviour_change", "py_share", "integrity"]].to_string())
    write_macros(df)
    return df


def write_macros(df):
    """paper/results.tex from per-PR verdicts and all build verdicts (funnel)."""
    lines = []

    def m(name, value, src):
        v = f"{value:,}" if isinstance(value, int) else str(value)
        lines.append(f"\\newcommand{{\\{name}}}{{{v}\\xspace}}  % {src}")

    review = ROOT / "data" / "p7_paper" / "review.json"  # manual review decisions (keep/exclude)
    excl = {}
    if review.exists():
        excl = {int(k): v for k, v in json.loads(review.read_text()).items() if v.get("exclude")}
    noisy = (df.aa_ratio < 0.95) | (df.aa_ratio > 1.05)  # A/A control itself crosses the +-5% threshold
    ok = df[(df.integrity.map(len) == 0) & (~df.id.isin(list(excl))) & (~noisy)]
    an = ok[(ok.checkable.map(len) > 0) & (ok.py_share.fillna(1) >= 0.5)]
    m("nMeasured", len(df), "PRs with measure.json (fetched)")
    m("nExcludedReview", len(excl), "excluded in manual review (data/p7_paper/review.json)")
    m("nExcludedIntegrity", int((df.integrity.map(len) > 0).sum()), "multiplexed/lost events")
    m("nExcludedNoisy", int(noisy.sum()), "A/A wall ratio outside 0.95-1.05")
    m("nAnalysed", len(an), "measured, clean, >=1 checkable claimed mechanism, Python >= 50% of change")
    m("nReposAnalysed", an.repo.nunique(), "distinct repositories in nAnalysed")
    top = an.repo.value_counts()
    m("maxPerRepo", int(top.iloc[0]) if len(top) else 0, "PRs of the most frequent repository")
    m("topRepo", top.index[0].split("/")[-1] if len(top) else "-", "most frequent repository")
    for s in ("faster", "slower", "no_change"):
        m("n" + "".join(w.capitalize() for w in s.split("_")), int((an.speed == s).sum()), f"speed == {s}")
    held = an.mechanism_held.fillna(False)
    m("nHeld", int(held.sum()), "any claimed mechanism signal moved as claimed")
    q = {("faster", True): "FH", ("faster", False): "FN", ("no_change", True): "NH",
         ("no_change", False): "NN", ("slower", True): "SH", ("slower", False): "SN"}
    for (sp, h), name in q.items():
        m("q" + name, int(((an.speed == sp) & (held == h)).sum()), f"speed {sp} & held {h}")
    m("nBehaviour", int(an.behaviour_change.sum()), "output digest differs base vs head")
    m("nHiddenCost", int((an.hidden_costs.map(len) > 0).sum()), "any cost signal up >= 10%, separated")
    m("nHiddenCostFaster", int(((an.hidden_costs.map(len) > 0) & (an.speed == "faster")).sum()),
      "hidden cost among faster PRs")
    m("aaMin", f"{an.aa_ratio.min():.3f}" if len(an) else "-", "min A/A wall ratio")
    m("aaMax", f"{an.aa_ratio.max():.3f}" if len(an) else "-", "max A/A wall ratio")
    # Figure 1 data: one row per analysed PR, sorted by wall ratio
    fig = an.assign(h=held.astype(int), b=an.behaviour_change.astype(int)).sort_values("wall_ratio")
    with open(ROOT / "paper" / "fig_wall.dat", "w") as f:
        f.write("rank ratio held behaviour\n")
        for i, r in enumerate(fig.itertuples(), 1):
            f.write(f"{i} {r.wall_ratio} {r.h} {r.b}\n")
    m("nLowPy",int((ok.py_share.fillna(1) < 0.5).sum()), "clean measured PRs with Python < 50% of change")

    # funnel from ALL build verdicts (not only measured)
    vs = [json.loads(p.read_text()) for p in SRC.glob("*/*/verdict.json")]
    reasons = {}
    for v in vs:
        a = v.get("agent") or {}
        key = "passed" if v.get("harness_pass") else (a.get("reason") if a.get("status") == "unbuildable"
                                                     else "failed_check")
        reasons[key] = reasons.get(key, 0) + 1
    m("nAttempted", len(vs), "build verdicts (real outcomes; usage-limit failures excluded)")
    for k, n in sorted(reasons.items()):
        m("fun" + "".join(w.capitalize() for w in k.split("_")), n, f"funnel: {k}")
    m("pctPassed", f"{100 * reasons.get('passed', 0) / max(len(vs), 1):.0f}\\%", "passed / attempted")
    usd = sum(v.get("list_usd", 0) for v in vs)
    m("usdPerBuild", f"\\${usd / max(len(vs), 1):.2f}", "mean list-price-equivalent agent cost per build")
    (ROOT / "paper" / "results.tex").write_text(
        "% GENERATED by analysis/p7_results.py -- do not edit by hand\n" + "\n".join(lines) + "\n",
        encoding="utf-8")
    print(f"{len(lines)} result macros; funnel {reasons}")


if __name__ == "__main__":
    main()
