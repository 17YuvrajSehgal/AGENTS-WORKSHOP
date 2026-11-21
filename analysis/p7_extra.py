"""Extra checks asked for by the internal review (REVIEW-1), on the analysed PRs.

  python -I analysis/p7_extra.py   -> paper/extra.tex (+ prints a report)

1. A/A false-positive rate: apply the "moved" rule (>=10%, complete separation)
   to base vs base-again for every kernel/hardware signal of Table I.
2. Specificity: how often the signals of mechanisms a PR did NOT claim also
   "hold", compared with the claimed ones (all analysed PRs, and faster ones).
3. Table II split by output unchanged / changed.
4. Per-agent counts.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.argv = [sys.argv[0], str(ROOT / "data" / "p7_paper" / "fetched")]
sys.path.insert(0, str(ROOT / "analysis"))
import p7_results as R  # noqa: E402

V = {v["id"]: v for v in json.loads((ROOT / "data" / "p7_paper" / "per_pr_verdicts.json").read_text())}
REV = json.loads((ROOT / "data" / "p7_paper" / "review.json").read_text())
an_ids = [i for i, v in V.items()
          if not v["integrity"] and not REV.get(str(i), {}).get("exclude")
          and 0.95 <= v["aa_ratio"] <= 1.05 and v["checkable"] and (v["py_share"] or 1) >= 0.5]
meas = {}
for mp in (ROOT / "data" / "p7_paper" / "fetched").glob("*/*/measure.json"):
    pid = int(mp.parent.name.split("_", 1)[1])
    if pid in an_ids:
        meas[pid] = json.loads(mp.read_text())["variants"]
assert len(meas) == len(an_ids), (len(meas), len(an_ids))

SIGNALS = sorted({k for sigs in R.MECH.values() for k, d in sigs if k != "parallel"})


def held(V3, mech, a="base", b="head"):
    """same rule as p7_results, between any two variants."""
    W = {"base": V3[a], "head": V3[b]}
    ok = False
    for key, direction in R.MECH[mech]:
        if key == "parallel":
            w = R.moved(W, "wall_s", "down")[0]
            tc = R.compare(R.series(W["base"], "task-clock"), R.series(W["head"], "task-clock"))
            ok = ok or (w and tc is not None and tc[0] >= 0.9)
        else:
            ok = ok or R.moved(W, key, direction)[0]
    return ok


# 1. A/A false positives per signal (base vs base_aa), each signal tested both directions
tests = hits = 0
per_sig = {}
for pid, V3 in meas.items():
    W = {"base": V3["base"], "head": V3["base_aa"]}
    for k in SIGNALS:
        if not R.series(W["base"], k) or not R.series(W["head"], k):
            continue
        h = R.moved(W, k, "any")[0]
        tests += 1
        hits += h
        per_sig.setdefault(k, [0, 0])
        per_sig[k][0] += h
        per_sig[k][1] += 1
# A/A false positives at the mechanism level (what the paper actually counts)
mech_tests = mech_hits = 0
for pid, V3 in meas.items():
    for m in R.MECH:
        mech_tests += 1
        mech_hits += held(V3, m, "base", "base_aa")

# 2. specificity: claimed vs unclaimed mechanisms, base vs head
def rates(ids):
    c_t = c_h = u_t = u_h = 0
    for pid in ids:
        claimed = set(V[pid]["checkable"]) & set(R.MECH)
        for m in R.MECH:
            h = held(meas[pid], m)
            if m in claimed:
                c_t += 1; c_h += h
            else:
                u_t += 1; u_h += h
    return c_h, c_t, u_h, u_t


all_r = rates(an_ids)

# 2b. the same test with kernel-trace signals only (no hardware counters):
# does the kernel tell mechanisms apart where the instruction count cannot?
HW = {"instructions", "L1-dcache-load-misses", "l2_rqsts.miss", "maxrss_kb", "minor-faults",
      "context-switches", "cycles", "branch-misses"}
KMECH = {m: [(k, d) for k, d in sigs if k not in HW and k != "parallel"] for m, sigs in R.MECH.items()}
KMECH = {m: s for m, s in KMECH.items() if s}


def kheld(V3, mech):
    W = {"base": V3["base"], "head": V3["head"]}
    return any(R.moved(W, k, d)[0] for k, d in KMECH[mech])


def krates(ids):
    c_t = c_h = u_t = u_h = 0
    for pid in ids:
        claimed = set(V[pid]["checkable"]) & set(KMECH)
        for m in KMECH:
            h = kheld(meas[pid], m)
            if m in claimed:
                c_t += 1; c_h += h
            else:
                u_t += 1; u_h += h
    return c_h, c_t, u_h, u_t


k_all = krates(an_ids)
k_fast = krates([i for i in an_ids if V[i]["speed"] == "faster"])
k_nfast = krates([i for i in an_ids if V[i]["speed"] != "faster"])
# instruction-count-only version for contrast
IMECH = [m for m, s in R.MECH.items() if any(k == "instructions" for k, _ in s)]


def irates(ids):
    c_t = c_h = u_t = u_h = 0
    for pid in ids:
        h = R.moved({"base": meas[pid]["base"], "head": meas[pid]["head"]}, "instructions", "down")[0]
        claimed = set(V[pid]["checkable"]) & set(IMECH)
        for m in IMECH:
            if m in claimed:
                c_t += 1; c_h += h
            else:
                u_t += 1; u_h += h
    return c_h, c_t, u_h, u_t


i_fast = irates([i for i in an_ids if V[i]["speed"] == "faster"])

# 2c. how many "holds" survive with kernel-trace signals only (no hardware counters)
k_held_ids = [i for i in an_ids if V[i]["mechanism_held"]
              and any(kheld(meas[i], m) for m in set(V[i]["checkable"]) & set(KMECH))]
k_held_fast = [i for i in k_held_ids if V[i]["speed"] == "faster"]
held_fast = [i for i in an_ids if V[i]["mechanism_held"] and V[i]["speed"] == "faster"]
# held PRs whose claimed mechanisms have no kernel signal at all (only counters can show them)
held_hw_only = [i for i in an_ids if V[i]["mechanism_held"]
                and not (set(V[i]["checkable"]) & set(KMECH))]

# 5. outcome by the evidence the agent offered (claims_pr.parquet)
import pandas as pd  # noqa: E402
ev = pd.read_parquet(ROOT / "data" / "p5_claims" / "all_v1" / "claims_pr.parquet").set_index("id")["evidence"]
by_ev = {}
for i in an_ids:
    e = ev.get(i, "missing")
    by_ev.setdefault(e, [0, 0, 0])
    by_ev[e][0] += 1
    by_ev[e][1] += V[i]["speed"] == "faster"
    by_ev[e][2] += bool(V[i]["mechanism_held"])
fast_ids = [i for i in an_ids if V[i]["speed"] == "faster"]
fast_r = rates(fast_ids)

# 3. split by output change
def quad(ids):
    out = {}
    for i in ids:
        v = V[i]
        key = (v["speed"], bool(v["mechanism_held"]))
        out[key] = out.get(key, 0) + 1
    return out


same = [i for i in an_ids if not V[i]["behaviour_change"]]
chg = [i for i in an_ids if V[i]["behaviour_change"]]
qs, qc = quad(same), quad(chg)

# 4. per agent
agents = {}
for i in an_ids:
    a = V[i]["agent"]
    agents.setdefault(a, [0, 0, 0])
    agents[a][0] += 1
    agents[a][1] += V[i]["speed"] == "faster"
    agents[a][2] += bool(V[i]["mechanism_held"])

pct = lambda a, b: f"{100 * a / b:.1f}\\%" if b else "-"  # noqa: E731
L = ["% generated by analysis/p7_extra.py; do not edit"]
def m(name, val):
    L.append(f"\\newcommand{{\\{name}}}{{{val}\\xspace}}")


m("aaSigTests", f"{tests:,}"); m("aaSigHits", hits); m("aaSigRate", pct(hits, tests))
m("aaMechTests", f"{mech_tests:,}"); m("aaMechHits", mech_hits); m("aaMechRate", pct(mech_hits, mech_tests))
m("spClaimedRate", pct(all_r[0], all_r[1])); m("spUnclaimedRate", pct(all_r[2], all_r[3]))
m("spClaimedRateFast", pct(fast_r[0], fast_r[1])); m("spUnclaimedRateFast", pct(fast_r[2], fast_r[3]))
for tag, q, ids in (("Same", qs, same), ("Chg", qc, chg)):
    m(f"n{tag}", len(ids))
    for sp, sh in (("faster", "F"), ("no_change", "N"), ("slower", "S")):
        for h, hh in ((True, "H"), (False, "N")):
            m(f"q{sh}{hh}{tag}", q.get((sp, h), 0))
m("nAgentsAnalysed", len(agents))
m("kClaimedFast", pct(k_fast[0], k_fast[1])); m("kUnclaimedFast", pct(k_fast[2], k_fast[3]))
m("kClaimedSlow", pct(k_nfast[0], k_nfast[1])); m("kUnclaimedSlow", pct(k_nfast[2], k_nfast[3]))
m("iClaimedFast", pct(i_fast[0], i_fast[1])); m("iUnclaimedFast", pct(i_fast[2], i_fast[3]))
m("kRatioFast", f"{(k_fast[0] / k_fast[1]) / (k_fast[2] / k_fast[3]):.1f}")
m("kRatioSlow", f"{(k_nfast[0] / k_nfast[1]) / (k_nfast[2] / k_nfast[3]):.1f}")
m("iRatioFast", f"{(i_fast[0] / i_fast[1]) / (i_fast[2] / i_fast[3]):.2f}")
m("nHeldKernel", len(k_held_ids)); m("nHeldFastKernel", len(k_held_fast))
m("nHeldFast", len(held_fast)); m("nHeldHwOnly", len(held_hw_only))
# Table III body: outcome by agent and by evidence offered
NAMES = {"Claude_Code": "Claude Code", "Google_Jules": "Jules", "OpenAI_Codex": "Codex",
         "Copilot": "Copilot", "Devin": "Devin", "Cursor": "Cursor"}
EVN = {"benchmark": "benchmark", "test": "test", "reasoning": "reasoning only",
       "none": "no evidence", "profile": "profile"}
rows = []
for a, (n, f, h) in sorted(agents.items(), key=lambda x: -x[1][0]):
    rows.append(f"{NAMES.get(a, a)} & {n} & {f} & {h} \\\\")
rows.append("\\midrule")
for e, (n, f, h) in sorted(by_ev.items(), key=lambda x: -x[1][0]):
    rows.append(f"{EVN.get(e, e)} & {n} & {f} & {h} \\\\")
# the whole tabular lives here: \input inside a tabular breaks \midrule
(ROOT / "paper" / "table_agents.tex").write_text(
    "% generated by analysis/p7_extra.py; do not edit\n"
    "\\begin{tabular}{@{}lrrr@{}}\n\\toprule\n & PRs & faster & held \\\\\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")
(ROOT / "paper" / "extra.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

print(f"analysed PRs: {len(an_ids)}")
print(f"1. A/A signal tests: {hits}/{tests} = {pct(hits, tests)}; mechanism-level A/A: {mech_hits}/{mech_tests} = {pct(mech_hits, mech_tests)}")
print("   noisiest signals:", sorted(((h / t, k, h, t) for k, (h, t) in per_sig.items()), reverse=True)[:5])
print(f"2. claimed held {all_r[0]}/{all_r[1]} = {pct(all_r[0], all_r[1])}; unclaimed held {all_r[2]}/{all_r[3]} = {pct(all_r[2], all_r[3])}")
print(f"   faster PRs only: claimed {fast_r[0]}/{fast_r[1]} = {pct(fast_r[0], fast_r[1])}; unclaimed {fast_r[2]}/{fast_r[3]} = {pct(fast_r[2], fast_r[3])}")
print(f"3. output unchanged n={len(same)}: {qs}")
print(f"   output changed   n={len(chg)}: {qc}")
print("4. per agent (n, faster, held):", agents)
print("2b. kernel-only mechanisms:", sorted(KMECH))
print(f"   kernel-only, all: claimed {k_all[0]}/{k_all[1]} = {pct(k_all[0], k_all[1])}; unclaimed {k_all[2]}/{k_all[3]} = {pct(k_all[2], k_all[3])}")
print(f"   kernel-only, faster: claimed {k_fast[0]}/{k_fast[1]} = {pct(k_fast[0], k_fast[1])}; unclaimed {k_fast[2]}/{k_fast[3]} = {pct(k_fast[2], k_fast[3])}")
print(f"   kernel-only, not faster: claimed {k_nfast[0]}/{k_nfast[1]} = {pct(k_nfast[0], k_nfast[1])}; unclaimed {k_nfast[2]}/{k_nfast[3]} = {pct(k_nfast[2], k_nfast[3])}")
print(f"   instructions-only, faster: claimed {i_fast[0]}/{i_fast[1]} = {pct(i_fast[0], i_fast[1])}; unclaimed {i_fast[2]}/{i_fast[3]} = {pct(i_fast[2], i_fast[3])}")
print("5. by evidence (n, faster, held):", by_ev)
print(f"2c. held with kernel signals only: {len(k_held_ids)} of {sum(bool(V[i]['mechanism_held']) for i in an_ids)}; "
      f"faster & held: {len(k_held_fast)} of {len(held_fast)}; held but mechanism has no kernel signal: {len(held_hw_only)}")
