"""Fleet worker for one VM: batches of 50 jobs, build phase then measure phase.

  sudo -E python3 worker.py <jobs.jsonl> [BUILD_PARALLEL] [BATCH]   (run from ~)

Per batch k:
  build phase    run_agent.py for each job, BUILD_PARALLEL at a time
                 (nothing is measured while builds run)
  measure phase  measure_pr.py for each job that passed the harness check,
                 one at a time, alone on the machine
  report         ~/fleet/batch_<k>.json, then WAIT until the file
                 ~/fleet/batch_<k>.approved exists (manual check by the
                 experimenter, user decision 2026-11-20)
Resumable: a job with verdict.json is not rebuilt; with measure.json is
not re-measured.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = Path(os.environ.get("KT_HOME", Path.home()))
FLEET = HOME / "fleet"
jobs_file = Path(sys.argv[1])
BUILD_PARALLEL = int(sys.argv[2]) if len(sys.argv) > 2 else 3
BATCH = int(sys.argv[3]) if len(sys.argv) > 3 else 50
RUNS = 10
TRACE_SET = "study_v1"
RATE_LOCK = threading.Lock()
RESUME_AT = 0.0  # time.time() when builds may resume after a usage limit


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(FLEET / "worker.log", "a") as f:
        f.write(line + "\n")


def pr_dir(job):
    return HOME / "prs" / f"{job['order']:04d}_{job['id']}"


def wait_for_reset(message):
    """Sleep until the reset time in 'You've hit your 5-hour limit · resets 11:30pm (UTC)'
    (plus 2 minutes), or 15 minutes if no time can be read. All build threads share one
    resume time, so a thread that wakes after the reset does not sleep again; one sleep is
    capped at 6 hours."""
    global RESUME_AT
    with RATE_LOCK:
        now = time.time()
        if now < RESUME_AT:
            secs = RESUME_AT - now
        else:
            m = re.search(r"resets (\d{1,2})(?::(\d{2}))?\s*([ap]m)\s*\(UTC\)", message or "", re.I)
            if m:
                h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
                utc = datetime.datetime.now(datetime.timezone.utc)
                reset = utc.replace(hour=h, minute=int(m.group(2) or 0), second=0, microsecond=0)
                if reset <= utc:
                    reset += datetime.timedelta(days=1)
                secs = min((reset - utc).total_seconds() + 120, 6 * 3600)
            else:
                secs = 900
            RESUME_AT = now + secs
    log(f"usage limit: sleeping {int(secs)} s ({message})")
    time.sleep(secs)


def build(job):
    while not (pr_dir(job) / "verdict.json").exists():
        # the agent and its tools run as the normal user, not root
        p = subprocess.run(["sudo", "-u", os.environ.get("SUDO_USER", "17yuv"), "-H",
                            "python3", str(HOME / "agent" / "run_agent.py"), json.dumps(job)],
                           capture_output=True, text=True)
        log(f"built {job['order']} {job['id']}: {p.stdout.strip()[-300:]} {p.stderr.strip()[-200:]}")
        out = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
        try:
            res = json.loads(out)
        except json.JSONDecodeError:
            res = {}
        if res.get("status") != "rate_limited":
            return  # a real outcome (or a crash, which is logged and left for review)
        wait_for_reset(res.get("message"))


def measure(job):
    d = pr_dir(job)
    v = json.loads((d / "verdict.json").read_text())
    if not v["harness_pass"] or (d / "measure.json").exists():
        return
    cpus = "2,3" if (v.get("agent") or {}).get("uses_parallelism") else "2"
    env = {**os.environ, "KT_TRACE_SET": TRACE_SET}
    p = subprocess.run(["python3", str(HOME / "pilot" / "measure_pr.py"), str(d),
                        str(d / "workload.py"), cpus, str(RUNS)],
                       capture_output=True, text=True, env=env)
    (d / "measure.log").write_text(p.stdout + p.stderr)
    log(f"measured {job['order']} {job['id']} exit {p.returncode}")


def main():
    FLEET.mkdir(exist_ok=True)
    jobs = [json.loads(line) for line in jobs_file.open()]
    for k in range(0, len(jobs), BATCH):
        b = k // BATCH
        batch = jobs[k:k + BATCH]
        log(f"batch {b}: build phase ({len(batch)} jobs, {BUILD_PARALLEL} in parallel)")
        with ThreadPoolExecutor(max_workers=BUILD_PARALLEL) as ex:
            list(ex.map(build, batch))
        log(f"batch {b}: measure phase")
        for job in batch:  # strictly one at a time
            measure(job)
        rep = []
        for job in batch:
            d = pr_dir(job)
            v = json.loads((d / "verdict.json").read_text()) if (d / "verdict.json").exists() else {}
            rep.append({"order": job["order"], "id": job["id"], "repo": job["repo"],
                        "agent_status": (v.get("agent") or {}).get("status"),
                        "reason": (v.get("agent") or {}).get("reason"),
                        "harness_pass": v.get("harness_pass"), "measured": (d / "measure.json").exists(),
                        "audit": v.get("audit"), "usd": v.get("list_usd")})
        (FLEET / f"batch_{b}.json").write_text(json.dumps(rep, indent=1))
        log(f"batch {b} done: {sum(r['measured'] for r in rep)} measured of {len(rep)}; "
            f"waiting for {FLEET}/batch_{b}.approved")
        while not (FLEET / f"batch_{b}.approved").exists():
            time.sleep(60)
    log("all batches done")


if __name__ == "__main__":
    main()
