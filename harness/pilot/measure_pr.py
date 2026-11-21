"""Measure one PR: base vs head, plus an A/A control (base vs base).

  sudo python3 measure_pr.py <pr_dir> <workload.py> <cpus> [RUNS]

Reuses the tested measurement code of the Phase-0 controls
(../controls/run_controls.py): untimed warm-up, untraced timing runs
(wait4 rusage), perf stat groups of <= 4 events (multiplexed rows
rejected), LTTng traces counted for the workload's process tree (runs with
lost events rejected). Variants run interleaved: base, head, base-again.
"""
import collections
import json
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "controls"))
import run_controls as rc  # noqa: E402

pr, workload, cpus = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
RUNS = int(sys.argv[4]) if len(sys.argv) > 4 else 10
WARMUP = 3


def argv(side):
    return [str(pr / side / "venv" / "bin" / "python"), str(workload)]


TRACE_SET = os.environ.get("KT_TRACE_SET", "pilot_v2")  # /srv/kt/traces/<set>/<pr>/<variant>/<run>


def main():
    rc.TRACES.mkdir(parents=True, exist_ok=True)
    rc.env_snapshot(pr / "env.json", venvs=[pr / "base" / "venv", pr / "head" / "venv"])
    variants = {"base": "base", "head": "head", "base_aa": "base"}
    for side in ("base", "head"):
        for _ in range(WARMUP):
            rc.timed(argv(side), cpus)
    res = {v: collections.defaultdict(list) for v in variants}
    traced = {v: [] for v in variants}
    for r in range(RUNS):
        for v, side in variants.items():
            for k, x in rc.timed(argv(side), cpus).items():
                res[v][k].append(x)
            if r < 5:  # counters and traces are near-deterministic; 5 runs each
                for g in rc.PERF_GROUPS.values():
                    for k, x in rc.perf(argv(side), cpus, g).items():
                        res[v][k].append(x)
                traced[v].append(rc.trace(argv(side), cpus,
                                          rc.TRACES / TRACE_SET / pr.name / v / str(r)))
    keys = set().union(*(t for v in traced.values() for t in v))
    for v in variants:
        for k in keys:
            res[v][k] = [t.get(k, 0) for t in traced[v]]
    out = {"pr": pr.name, "cpus": cpus, "runs": RUNS, "warmup": WARMUP,
           "variants": {v: dict(d) for v, d in res.items()}}
    (pr / "measure.json").write_text(json.dumps(out, indent=1))
    summarize(out)


def summarize(out):
    V = out["variants"]
    rows = []
    for k in sorted(V["base"]):
        a, b, aa = V["base"][k], V["head"].get(k, []), V["base_aa"].get(k, [])
        if not a or not b or any(x is None for x in a + b) or k.startswith("pcnt_running"):
            continue
        ma, mb = statistics.median(a), statistics.median(b)
        if ma == 0 and mb == 0:
            continue
        ratio = mb / ma if ma else float("inf")
        aa_ratio = statistics.median(aa) / ma if aa and ma else None
        sep = "b<a" if max(b) < min(a) else ("b>a" if min(b) > max(a) else "overlap")
        rows.append((k, ma, mb, ratio, aa_ratio, sep))
    bad = [f"{v}:{k}" for v, d in V.items() for k, xs in d.items()
           if (k.startswith("pcnt_running:") and any(x is not None and x < 100 for x in xs))
           or (k in ("discarded", "discarded_packets") and any(xs))]
    print(f"{'signal':28s} {'base':>14s} {'head':>14s} {'head/base':>9s} {'A/A':>7s}  separation")
    for k, ma, mb, ratio, aa, sep in rows:
        if abs(ratio - 1) >= 0.05 or k in ("wall_s", "task-clock", "instructions"):
            print(f"{k:28s} {ma:14.4g} {mb:14.4g} {ratio:9.3f} {aa if aa is None else round(aa, 3)!s:>7s}  {sep}")
    print("integrity problems:", bad or "none")
    # tracer overhead: traced runs vs untraced timing runs, per variant
    for v, d in V.items():
        if d.get("traced_wall_s") and d.get("wall_s"):
            t, u = statistics.median(d["traced_wall_s"]), statistics.median(d["wall_s"])
            print(f"tracer overhead {v}: traced {t:.3f} s vs untraced {u:.3f} s = x{t / u:.3f}")
    # interference on the measurement CPUs (median per traced run)
    for k in ("irq_on_cpus", "softirq_on_cpus", "foreign_switch_in_on_cpus", "freq_changes_on_cpus"):
        print(k, {v: statistics.median(d.get(k, [0])) for v, d in V.items()})


if __name__ == "__main__":
    main()
