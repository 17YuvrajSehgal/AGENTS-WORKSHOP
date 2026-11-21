"""Gate check for one PR (used by the build agent AND re-run by the harness).

  python3 check.py <pr_dir> <workload.py>

Prints and writes <pr_dir>/check.json with "pass" and the reasons:
  * both venvs import-ready (workload exits 0 on both sides)
  * coverage of changed lines (cover.py): head share >= 0.8; for large
    PRs (> 200 changed executable lines on head) >= 0.5   [rule fixed
    2026-11-20 before the study; see RESEARCH-PLAN harness lesson 3]
  * base run time (median of 3) within 0.5-30 s
  * the workload also passes with NO network (fresh network namespace,
    loopback only), so measurements cannot depend on the network
  * last stdout line present (output digest); base vs head equality is
    recorded, not gated
"""
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

pr, workload = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
COVER = Path.home() / "pilot" / "cover.py"
reasons, out = [], {}


def py(side):
    return str(pr / side / "venv" / "bin" / "python")


def run(side, no_net=False, timeout=120):
    cmd = [py(side), str(workload)]
    if no_net:  # fresh net namespace with only loopback up, then drop back to this user
        uid, gid = os.getuid(), os.getgid()
        cmd = ["sudo", "unshare", "--net", "--", "sh", "-c",
               f"ip link set lo up && exec setpriv --reuid={uid} --regid={gid} --init-groups "
               + " ".join(f"'{c}'" for c in cmd)]
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=pr)
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    return time.perf_counter() - t0, p.stdout, p.stderr if p.returncode else ""


# 1. runs on both sides
for side in ("base", "head"):
    t, so, err = run(side)
    out[f"{side}_exit_ok"] = t is not None and not err
    if not out[f"{side}_exit_ok"]:
        reasons.append(f"{side} workload failed: {err[-400:]}")
    out[f"{side}_last_line"] = so.strip().splitlines()[-1] if so.strip() else ""
    if out[f"{side}_exit_ok"] and not out[f"{side}_last_line"]:
        reasons.append(f"{side}: no output digest (last line empty)")

if out["base_exit_ok"] and out["head_exit_ok"]:
    # 2. base run time
    times = [run("base")[0] for _ in range(3)]
    out["base_time_s"] = round(statistics.median(times), 3)
    out["head_time_s"] = round(run("head")[0], 3)
    if not 0.5 <= out["base_time_s"] <= 30:
        reasons.append(f"base run time {out['base_time_s']} s outside 0.5-30 s")
    # 3. no network
    t, so, err = run("base", no_net=True)
    out["no_network_ok"] = t is not None and not err
    if not out["no_network_ok"]:
        reasons.append(f"fails without network: {err[-300:]}")
    # 4. coverage of changed lines + output equality
    c = subprocess.run(["python3", str(COVER), str(pr), str(pr / "pr.diff"), str(workload)],
                       capture_output=True, text=True)
    if c.returncode != 0:
        reasons.append(f"coverage run failed: {c.stdout[-300:]}{c.stderr[-300:]}")
    else:
        cov = json.loads((pr / "coverage.json").read_text())
        out["coverage"] = cov
        head = cov["head"]
        need = 0.5 if (head["changed_executable_lines"] or 0) > 200 else 0.8
        out["coverage_needed"] = need
        if head["share"] is not None and head["share"] < need:
            reasons.append(f"head coverage {head['share']} < {need}")
        if head["share"] is None and cov["base"]["share"] is not None and cov["base"]["share"] < need:
            reasons.append(f"base coverage {cov['base']['share']} < {need} (no added lines)")
        out["output_equal"] = cov["output_equal"]

out["pass"] = not reasons
out["reasons"] = reasons
(pr / "check.json").write_text(json.dumps(out, indent=1))
print(json.dumps({"pass": out["pass"], "reasons": reasons,
                  "base_time_s": out.get("base_time_s"), "head_time_s": out.get("head_time_s"),
                  "coverage_head": out.get("coverage", {}).get("head"),
                  "coverage_base": out.get("coverage", {}).get("base"),
                  "output_equal": out.get("output_equal"),
                  "no_network_ok": out.get("no_network_ok")}, indent=1))
