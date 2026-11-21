"""Generate paper/numbers.tex: every number in the paper, computed from result files.

  python -I analysis/paper_numbers.py

Each macro line carries a comment with its source. Run again whenever a
result file changes; never type a number into the .tex by hand.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
out = []


def num(x):
    return f"{x:,}" if isinstance(x, int) else str(x)


def m(name, value, source):
    out.append(f"\\newcommand{{\\{name}}}{{{num(value)}\\xspace}}  % {source}")


def pct(a, b, digits=1):
    return f"{100 * a / b:.{digits}f}\\%"


# --- dataset (pinned AIDev v5) ---
counts = json.loads((D / "p1_counts.json").read_text())
m("nPop", counts["pop_prs"], "data/p1_counts.json pop_prs (AIDev v5 AIDev-pop)")
m("nPopRepos", counts["pop_repos_rows"], "data/p1_counts.json pop_repos_rows")
m("nAllPRs", counts["quick_look_measured"]["Total"]["prs"], "data/p1_counts.json all_pull_request rows")
kw = json.loads((D / "p1_keyword_stats.json").read_text())
m("nCand", kw["candidates"], "data/p1_keyword_stats.json candidates")
m("pctCand", pct(kw["candidates"], counts["pop_prs"]), "candidates / AIDev-pop")

# --- pilot classification (random 2,000 candidates) ---
ps = json.loads((D / "p1_classify" / "pilot_summary_cc.json").read_text())
lab = pd.read_parquet(D / "p1_classify" / "pilot_labels_cc.parquet")
ok = lab[lab.status == "ok"]
rt = ok[ok.perf_role.isin(["primary", "secondary"]) & (ok.perf_scope == "runtime")]
m("nPilot", ps["n"], "pilot_summary_cc.json n")
m("nPilotLabelled", len(ok), "pilot labels status ok")
m("nPilotRuntime", len(rt), "pilot runtime perf (primary|secondary + runtime)")
m("pctPilotRuntime", pct(len(rt), len(ok)), "pilot runtime perf share")
m("pctPilotNone", pct(int((ok.perf_role == "none").sum()), len(ok)), "pilot role none share")

# --- stratified classification ---
s2 = json.loads((D / "p2_classify" / "summary.json").read_text())
m("nStratClassified", s2["classified"], "p2_classify/summary.json classified")
m("nRuntimePRs", s2["runtime_perf_total"], "p2_classify/summary.json runtime_perf_total")
m("nStratHaiku", s2["labeller"].get("claude-haiku-5-5", 0), "p2 labeller counts")
m("nStratOpus", s2["labeller"].get("claude-opus-5-5", 0), "p2 labeller counts")
agree = json.loads((D / "p2_haiku_agree" / "agreement.json").read_text())
m("haikuKappa", f"{agree['runtime_perf_kappa']:.2f}", "p2_haiku_agree/agreement.json runtime_perf_kappa")
m("haikuAgreeN", agree["n_compared"], "agreement n_compared")
m("haikuAgree", pct(agree["runtime_perf_agreement"], 1, 0), "agreement runtime_perf_agreement")

# --- claims (codebook v1, all runtime-perf PRs) ---
pr = pd.read_parquet(D / "p5_claims" / "all_v1" / "claims_pr.parquet")
mech = pd.read_parquet(D / "p5_claims" / "all_v1" / "claims_mech.parquet")
okc = pr[pr.status == "ok"]
n = len(okc)
m("nClaims", n, "p5_claims/all_v1/claims_pr.parquet ok")
m("nNoMech", int((~okc.stated).sum()), "claims: mechanism_stated false")
m("pctNoMech", pct(int((~okc.stated).sum()), n), "share")
m("nEffect", int((okc.claimed_effect != "").sum()), "claims: claimed_effect non-empty")
m("pctEffect", pct(int((okc.claimed_effect != "").sum()), n), "share")
ev = okc.evidence.value_counts()
for k in ("benchmark", "test", "reasoning", "none", "profile"):
    m(f"ev{k.capitalize()}", int(ev.get(k, 0)), f"claims evidence == {k}")
m("pctReasonNone", pct(int(ev.get("reasoning", 0) + ev.get("none", 0)), n), "evidence reasoning|none share")
m("pctBenchmark", pct(int(ev.get("benchmark", 0)), n), "evidence benchmark share")
byid = mech.groupby("mechanism").id.nunique()
for k in byid.index:
    mk = "mech" + "".join(w.capitalize() for w in k.split("_"))
    m(mk, f"{100 * byid[k] / n:.1f}\\%", f"claims_mech: PRs with mechanism {k} / nClaims")
UNMEAS = {"gpu_accelerator", "fewer_external_calls", "ui_rendering", "other"}
g = mech.groupby("id").mechanism.apply(set)
measurable = sum(1 for s in g if s - UNMEAS)
m("nMeasurableClaims", measurable, "PRs with >= 1 mechanism outside {gpu, external API, UI, other}")
m("nQuotes", len(mech), "claims_mech rows")
m("nQuotesNotFound", int((~mech.quote_ws).sum()), "quotes not found after whitespace normalisation")

# --- job funnel ---
js = json.loads((ROOT / "harness" / "agent" / "jobs" / "_stats.json").read_text())
rf = json.loads((ROOT / "harness" / "agent" / "jobs" / "_refilter_stats.json").read_text())
m("nGhError", js["github_error"], "jobs/_stats.json github_error (repo/PR unavailable)")
m("nNoPyFinal", sum(v["no_py_in_final_diff"] for v in rf.values()), "jobs/_refilter_stats.json no_py_in_final_diff")
m("nJobs", sum(v["kept"] for v in rf.values()), "jobs/_refilter_stats.json kept")

# --- harness validation: per-VM calibration (12 controls, full profile, 5 runs) ---
import statistics  # noqa: E402

vms = sorted((D / "p7_paper" / "vm_controls").glob("kt-measure-*.json"))
passes, totals, errs, faults_ratio, integrity = [], [], [], [], 0
for f in vms:
    d = json.loads(f.read_text())
    ev = d["evaluation"]
    passes.append(sum(r[4] == "PASS" for r in ev))
    totals.append(len(ev))
    errs.append(d["counter_check"]["relative_error"])
    integrity += len(d["integrity_problems"])
    faults_ratio += [x["ratio"] for x in d.get("cross_checks", []) if x.get("ratio")]
m("nVMs", len(vms), "data/p7_paper/vm_controls/*.json")
m("nControls", len(json.loads(vms[0].read_text())["controls"]), "controls per VM")
m("nChecks", totals[0], "expectation checks per VM")
m("ctrlPassMin", min(passes), "min PASS over VMs")
m("ctrlPassMax", max(passes), "max PASS over VMs")
m("nIntegrityProblems", integrity, "multiplexed counters + lost events/packets, all VMs")
m("counterErrMax", f"{max(errs):.1e}".replace("e-0", "\\times10^{-").replace("e-", "\\times10^{-") + "}",
  "max relative error of the exact-instruction check over VMs")
m("faultRatioMin", f"{min(faults_ratio):.3f}", "LTTng page-fault events / perf faults, min over controls+VMs")
m("faultRatioMed", f"{statistics.median(faults_ratio):.3f}", "median of the same")

(ROOT / "paper" / "numbers.tex").write_text(
    "% GENERATED by analysis/paper_numbers.py -- do not edit by hand\n" + "\n".join(out) + "\n",
    encoding="utf-8")
print(f"{len(out)} macros written")
