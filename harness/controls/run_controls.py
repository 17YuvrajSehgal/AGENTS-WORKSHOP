"""Phase 0 on the measurement VM: counter checks + positive controls.

Run as root on the VM:  sudo python3 run_controls.py [RUNS]
Writes results/controls.json and prints a PASS/FAIL table.

For each control and variant:
  timing runs  (RUNS)  no tracer: wall, user, sys, max RSS (wait4 rusage)
  perf runs    (RUNS)  three groups of <= 4 programmable events; a row whose
                       pcnt_running is below 100 is rejected (multiplexed)
  trace runs   (RUNS)  LTTng kernel trace; events counted for the workload's
                       process tree only (rebuilt from sched_process_fork);
                       a run with discarded events is rejected
"""
import collections
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import bt2

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
# Persistent disk: /tmp is wiped when the VM stops (the first control traces
# were lost that way, 2026-11-20). Raw traces are kept for the artifact.
TRACES = Path("/srv/kt/traces")
PERF_CSV = Path("/tmp/kt-perf.csv")
RUNS = 5  # set from the command line in main(); importing must not parse argv
PERF_GROUPS = {
    "sw": "task-clock,context-switches,cpu-migrations,minor-faults,major-faults",
    "hwA": "cycles,instructions,branch-misses,L1-dcache-load-misses",
    "hwB": "l2_rqsts.references,l2_rqsts.miss,mem_load_retired.l1_miss,mem_load_retired.l2_miss",
}
# Full kernel profile (besides all syscalls). Left out on purpose:
# kmem_kmalloc / kmem_kfree (fire on nearly every kernel operation; would
# flood the buffers). Page faults need the lttng-modules x86-exceptions probe
# (enabled via harness/vm/enable_full_probes.sh on Linux 7.0).
KERNEL_EVENTS = [
    "sched_switch", "sched_wakeup", "sched_waking", "sched_wakeup_new",
    "sched_migrate_task", "sched_stat_runtime",
    "sched_process_fork", "sched_process_exec", "sched_process_exit", "sched_process_free",
    "block_rq_issue", "block_rq_insert", "block_rq_complete", "block_bio_queue",
    "irq_handler_entry", "irq_handler_exit", "irq_softirq_entry", "irq_softirq_exit",
    "timer_hrtimer_expire_entry", "timer_hrtimer_expire_exit",
    "net_dev_xmit", "net_if_receive_skb", "power_cpu_frequency",
    "x86_exceptions_page_fault_user", "x86_exceptions_page_fault_kernel",
    "kmem_mm_page_alloc", "kmem_mm_page_free",
]
STAT_CALLS = ("newfstatat", "statx", "stat", "lstat", "fstat")
READ_CALLS = ("read", "pread64", "readv", "preadv", "preadv2")
WRITE_CALLS = ("write", "pwrite64", "writev", "pwritev", "pwritev2")


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def cmd_for(name, spec, variant):
    if spec["lang"] == "c":
        return [str(HERE / "controls_c"), name, variant]
    return ["python3", str(HERE / "controls.py"), name, variant]


def pinned(argv, cpus):
    # No isolcpus: it disables load balancing, which put both workers of a
    # 2-process pool on one CPU (measured 2026-11-20). Instead, systemd keeps
    # system/user slices on CPUs 0,1,4,5 and each workload gets its own scope
    # limited to its measurement CPUs; the kernel still balances inside it.
    # `systemd-run --scope` execs the command in place, so the pid is kept.
    # own top-level slice: system.slice/user.slice are limited to 0,1,4,5
    return ["systemd-run", "--scope", "--quiet", "--slice=measure", "-p", f"AllowedCPUs={cpus}",
            "taskset", "-c", cpus, *argv]


def timed(argv, cpus):
    t0 = time.perf_counter()
    p = subprocess.Popen(pinned(argv, cpus), stdout=subprocess.DEVNULL)
    _, status, ru = os.wait4(p.pid, 0)
    wall = time.perf_counter() - t0
    assert status == 0, f"{argv} exit {status}"
    return {"wall_s": wall, "user_s": ru.ru_utime, "sys_s": ru.ru_stime,
            "maxrss_kb": ru.ru_maxrss}


def perf(argv, cpus, events):
    out = PERF_CSV
    sh(["perf", "stat", "-x,", "--no-big-num", "-o", str(out), "-e", events,
        "--", *pinned(argv, cpus)])
    vals = {}
    for line in out.read_text().splitlines():
        f = line.split(",")
        if len(f) < 5 or line.startswith("#"):
            continue
        val, ev, pct = f[0], f[2], f[4]
        if val in ("<not supported>", "<not counted>"):
            vals[ev] = None
            continue
        vals[ev] = float(val)
        vals[f"pcnt_running:{ev}"] = float(pct) if pct else 100.0
    return vals


def tool_versions():
    v = {}
    for k, cmd in {"lttng": ["lttng", "--version"], "babeltrace2": ["babeltrace2", "--version"],
                   "perf": ["perf", "--version"]}.items():
        p = subprocess.run(cmd, capture_output=True, text=True)
        v[k] = (p.stdout or p.stderr).strip().splitlines()[0] if (p.stdout or p.stderr) else None
    v["bt2"] = bt2.__version__
    return v


def trace(argv, cpus, path):
    sess = "kt-ctl"
    subprocess.run(["lttng", "destroy", sess], capture_output=True)
    shutil.rmtree(path, ignore_errors=True)
    sh(["lttng", "create", sess, f"--output={path}"])
    sh(["lttng", "enable-channel", "--kernel", "--subbuf-size=16M", "--num-subbuf=16", "k"])
    sh(["lttng", "enable-event", "--kernel", "--channel=k", "--syscall", "--all"])
    sh(["lttng", "enable-event", "--kernel", "--channel=k", ",".join(KERNEL_EVENTS)])
    sh(["lttng", "add-context", "--kernel", "--channel=k",
        "-t", "pid", "-t", "tid", "-t", "ppid", "-t", "procname"])
    sh(["lttng", "start"])
    t0 = time.perf_counter()
    p = subprocess.Popen(pinned(argv, cpus), stdout=subprocess.DEVNULL)
    root = p.pid
    status = p.wait()
    traced_wall = time.perf_counter() - t0
    sh(["lttng", "stop"])
    sh(["lttng", "destroy", sess])
    meta = {"argv": argv, "cpus": cpus, "root_pid": root, "exit": status,
            "traced_wall_s": traced_wall, "kernel_events": KERNEL_EVENTS,
            "syscalls": "all", "contexts": ["pid", "tid", "ppid", "procname"],
            "channel": {"subbuf_size": "16M", "num_subbuf": 16}, "tools": tool_versions(),
            "uname": os.uname().release, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    assert status == 0, f"{argv} exit {status}"
    counts, files = count(path, root, cpus)
    counts["traced_wall_s"] = traced_wall  # tracer overhead = this vs untraced wall_s
    (Path(path) / "meta.json").write_text(json.dumps(meta, indent=1))
    (Path(path) / "files.json").write_text(json.dumps(files, indent=1))
    (Path(path) / "counts.json").write_text(json.dumps(counts, indent=1))
    return counts


def _cpu_set(cpus):
    out = set()
    for part in cpus.split(","):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def count(path, root, cpus="0-63"):
    """Count events for the process tree rooted at `root`, plus interference
    on the workload's CPUs and system-wide block I/O.

    Returns (counts, files): counts are numbers (comparable across runs);
    files is per-path I/O attribution built from openat/close and the fd of
    each read/write-like syscall.
    """
    pids, tids = {root}, {root}
    on_cpus = _cpu_set(cpus)
    c = collections.Counter()
    discarded_events = discarded_packets = 0
    open_sc = {}            # tid -> futex entry ts
    off_since = {}          # tid -> ts it left the CPU
    off_ns = collections.Counter()
    pending = {}            # tid -> (syscall, fd or filename) between entry and exit
    fdpath = {}             # (pid, fd) -> path
    files = collections.defaultdict(collections.Counter)
    for msg in bt2.TraceCollectionMessageIterator(str(path)):
        if type(msg) is bt2._DiscardedEventsMessageConst:
            discarded_events += msg.count or 1
            continue
        if type(msg) is bt2._DiscardedPacketsMessageConst:
            discarded_packets += msg.count or 1
            continue
        if type(msg) is not bt2._EventMessageConst:
            continue
        ev, ts = msg.event, msg.default_clock_snapshot.ns_from_origin
        name = ev.name
        pl = ev.payload_field
        try:
            cpu = int(ev.packet.context_field["cpu_id"])
        except (KeyError, TypeError, AttributeError):
            cpu = None

        # --- interference on the measurement CPUs (any task) ---
        if cpu in on_cpus:
            if name == "irq_handler_entry":
                c["irq_on_cpus"] += 1
            elif name == "irq_softirq_entry":
                c["softirq_on_cpus"] += 1
            elif name == "timer_hrtimer_expire_entry":
                c["hrtimer_on_cpus"] += 1
            elif name == "power_cpu_frequency":
                c["freq_changes_on_cpus"] += 1
        # --- system-wide block I/O (issued by kernel workers on any CPU) ---
        if name == "block_rq_issue":
            c["sys_block_rq_issue"] += 1
            if "nr_sector" in pl:
                c["sys_block_bytes"] += int(pl["nr_sector"]) * 512

        if name == "sched_process_fork":
            if int(pl["parent_pid"]) in pids:
                pids.add(int(pl["child_pid"]))
                tids.add(int(pl["child_tid"]))
                c["forks" if int(pl["child_pid"]) == int(pl["child_tid"]) else "threads"] += 1
            continue
        if name == "sched_switch":
            prev, nxt = int(pl["prev_tid"]), int(pl["next_tid"])
            if prev in tids:
                c["switch_out"] += 1
                off_since[prev] = ts
            if nxt in tids and nxt in off_since:
                off_ns[nxt] += ts - off_since.pop(nxt)
            if cpu in on_cpus and nxt != 0 and nxt not in tids:
                c["foreign_switch_in_on_cpus"] += 1
            continue
        if name == "sched_migrate_task":
            if int(pl["tid"]) in tids:
                c["migrations"] += 1
            continue
        if name == "sched_stat_runtime":
            if int(pl["tid"]) in tids:
                c["runtime_ns"] += int(pl["runtime"])
            continue
        if int(ev.common_context_field["pid"]) not in pids:
            continue
        pid, tid = int(ev.common_context_field["pid"]), int(ev.common_context_field["tid"])
        if name.startswith("syscall_entry_"):
            sc = name[len("syscall_entry_"):]
            c[f"sc:{sc}"] += 1
            if sc == "futex":
                open_sc[tid] = ts
            elif sc in ("openat", "open") and "filename" in pl:
                pending[tid] = (sc, str(pl["filename"]))
            elif (sc in READ_CALLS or sc in WRITE_CALLS or sc == "close") and "fd" in pl:
                pending[tid] = (sc, int(pl["fd"]))
        elif name.startswith("syscall_exit_"):
            sc = name[len("syscall_exit_"):]
            ret = int(pl["ret"]) if "ret" in pl else 0
            if sc in READ_CALLS and ret > 0:
                c["bytes_read"] += ret
            if sc in WRITE_CALLS and ret > 0:
                c["bytes_written"] += ret
            if sc == "futex" and tid in open_sc:
                c["futex_ns"] += ts - open_sc.pop(tid)
            got = pending.pop(tid, None)
            if got and got[0] == sc:
                if sc in ("openat", "open"):
                    if ret >= 0:
                        fdpath[(pid, ret)] = got[1]
                        files[got[1]]["opens"] += 1
                    else:
                        files[got[1]]["failed_opens"] += 1
                elif sc == "close":
                    fdpath.pop((pid, got[1]), None)
                else:
                    fd = got[1]
                    path_ = fdpath.get((pid, fd), f"<fd {fd}: not opened in trace>"
                                       if fd > 2 else f"<std fd {fd}>")
                    kind = "read" if sc in READ_CALLS else "write"
                    files[path_][f"{kind}_calls"] += 1
                    if ret > 0:
                        files[path_][f"{kind}_bytes"] += ret
        else:
            c[f"ev:{name}"] += 1  # page faults, page alloc/free, block_rq_insert, net, ...
            if name == "sched_process_exec":
                c["execs"] += 1
    c["sc:stat_any"] = sum(c[f"sc:{s}"] for s in STAT_CALLS)
    c["offcpu_ns_total"] = sum(off_ns.values())
    c["offcpu_ns_main"] = off_ns[root]
    c["discarded"] = discarded_events
    c["discarded_packets"] = discarded_packets
    c["files_touched"] = len(files)
    return dict(c), {p: dict(v) for p, v in files.items()}


def env_snapshot(dest, venvs=()):
    """Provenance for one measurement: machine, kernel, CPU set-up, tools,
    and the exact packages of each Python environment."""
    def run(cmd):
        p = subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))
        return p.stdout.strip()
    snap = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "uname": " ".join(os.uname()),
        "cmdline": Path("/proc/cmdline").read_text().strip(),
        "lscpu": run(["lscpu"]), "microcode": run("grep -m1 microcode /proc/cpuinfo"),
        "pmu": run("dmesg 2>/dev/null | grep -m2 -i 'Performance Events'"),
        "allowed_cpus": run(["systemctl", "show", "-p", "AllowedCPUs", "system.slice",
                             "user.slice", "measure.slice"]),
        "sysctl": run(["sysctl", "kernel.perf_event_paranoid", "kernel.nmi_watchdog",
                       "kernel.kptr_restrict", "kernel.randomize_va_space"]),
        "governor": run("cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor 2>/dev/null"),
        "lttng_probes": run("ls /lib/modules/$(uname -r)/updates/probes/"),
        "tools": tool_versions(), "kernel_events": KERNEL_EVENTS,
        "venvs": {str(v): {"python": run([str(Path(v) / "bin" / "python"), "--version"]),
                           "packages": run(f"VIRTUAL_ENV={v} uv pip freeze 2>/dev/null || "
                                           f"{v}/bin/python -m pip freeze")}
                  for v in venvs},
    }
    Path(dest).write_text(json.dumps(snap, indent=1))


def counter_check():
    """dec+jnz loop: instructions:u difference must equal 2 * (n2 - n1)."""
    sh(["gcc", "-O1", "-o", str(HERE / "counters"), str(HERE / "counters.c")])
    rows = {}
    for n in (1_000_000_000, 2_000_000_000):
        v = perf([str(HERE / "counters"), str(n)], "2", "instructions:u,cycles:u")
        rows[n] = v
    d_ins = rows[2_000_000_000]["instructions:u"] - rows[1_000_000_000]["instructions:u"]
    d_cyc = rows[2_000_000_000]["cycles:u"] - rows[1_000_000_000]["cycles:u"]
    return {"runs": {str(k): v for k, v in rows.items()},
            "delta_instructions": d_ins, "expected_delta": 2_000_000_000,
            "relative_error": abs(d_ins - 2e9) / 2e9, "loop_ipc": d_ins / d_cyc}


def main():
    global RUNS
    RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    RES.mkdir(exist_ok=True)
    TRACES.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pgrep", "-x", "lttng-sessiond"], capture_output=True).returncode == 0 or \
        sh(["lttng-sessiond", "--daemonize"])
    env_snapshot(RES / "env.json")
    available = sh(["lttng", "list", "--kernel"]).stdout
    missing = [e for e in KERNEL_EVENTS if e not in available]
    if missing:
        sys.exit(f"MISSING kernel events: {missing}")
    sh(["gcc", "-O2", "-pthread", "-o", str(HERE / "controls_c"), str(HERE / "controls_c.c")])

    out = {"uname": os.uname().release, "runs": RUNS, "counter_check": counter_check(),
           "controls": {}}
    print("counter check:", json.dumps({k: v for k, v in out["counter_check"].items() if k != "runs"}))
    specs = {k: v for k, v in json.loads((HERE / "controls.json").read_text()).items()
             if not k.startswith("_")}
    for name, spec in specs.items():
        res = {"a": collections.defaultdict(list), "b": collections.defaultdict(list)}
        traced = {"a": [], "b": []}
        for r in range(RUNS):  # interleave a and b
            for v in ("a", "b"):
                argv = cmd_for(name, spec, v)
                for k, x in timed(argv, spec["cpus"]).items():
                    res[v][k].append(x)
                for g in PERF_GROUPS.values():
                    for k, x in perf(argv, spec["cpus"], g).items():
                        res[v][k].append(x)
                traced[v].append(trace(argv, spec["cpus"], TRACES / "controls" / name / v / str(r)))
        # an event that never happened in a run is a count of 0, not missing
        keys = set().union(*(t for v in traced.values() for t in v))
        for v in ("a", "b"):
            for k in keys:
                res[v][k] = [t.get(k, 0) for t in traced[v]]
        out["controls"][name] = {"spec": spec, "a": dict(res["a"]), "b": dict(res["b"])}
        print(name, "measured", flush=True)
    (RES / "controls.json").write_text(json.dumps(out, indent=1))
    evaluate(out)


def evaluate(out):
    rows, bad = [], []
    for name, d in out["controls"].items():
        for sig, want in d["spec"]["expect"].items():
            a = [x for x in d["a"].get(sig, []) if x is not None]
            b = [x for x in d["b"].get(sig, []) if x is not None]
            if not a or not b:
                rows.append((name, sig, want, None, "NO DATA"))
                continue
            ma, mb = statistics.median(a), statistics.median(b)
            ratio = mb / ma if ma else float("inf")
            if want == "down":
                ok = ratio < 0.8 and max(b) < min(a)
            else:
                ok = ratio >= 0.9
            rows.append((name, sig, want, round(ratio, 4), "PASS" if ok else "FAIL"))
        for v in ("a", "b"):
            for k, xs in d[v].items():
                if k.startswith("pcnt_running:") and any(x is not None and x < 100 for x in xs):
                    bad.append(f"{name}/{v}: {k} {min(xs)}")
                if k in ("discarded", "discarded_packets") and any(xs):
                    bad.append(f"{name}/{v}: {k} {xs}")
    print(f"\n{'control':13s} {'signal':24s} {'expect':9s} {'b/a':>9s}  result")
    for r in rows:
        print(f"{r[0]:13s} {r[1]:24s} {r[2]:9s} {str(r[3]):>9s}  {r[4]}")
    print("\nmultiplexing / lost events or packets:", bad or "none")
    out["evaluation"] = rows
    out["integrity_problems"] = bad
    out["cross_checks"] = cross_checks(out)
    (RES / "controls.json").write_text(json.dumps(out, indent=1))
    attribution_check()


def attribution_check():
    """Share of bytes read that per-file attribution explains, for run 0 of
    each control variant (file_reads should be ~all one data file)."""
    print(f"\n{'control/variant':22s} {'bytes_read':>12s} {'attributed':>12s} {'share':>6s}  top file")
    for counts_p in sorted((TRACES / "controls").glob("*/*/0/counts.json")):
        run = counts_p.parent
        counts = json.loads(counts_p.read_text())
        files = json.loads((run / "files.json").read_text())
        total = counts.get("bytes_read", 0)
        named = {p: v for p, v in files.items() if not p.startswith("<")}
        attributed = sum(v.get("read_bytes", 0) for v in named.values())
        top = max(files.items(), key=lambda kv: kv[1].get("read_bytes", 0), default=("-", {}))
        share = f"{attributed / total:.3f}" if total else "-"
        print(f"{run.parent.parent.name + '/' + run.parent.name:22s} {total:12d} {attributed:12d}"
              f" {share:>6s}  {top[0][:50]}")


def cross_checks(out):
    """Do the tools agree? Page faults: LTTng event count vs perf
    minor+major faults (different runs, so compare medians). Interference:
    irq/softirq/foreign tasks on the measurement CPUs per run."""
    rows = []
    print(f"\n{'control/variant':22s} {'lttng faults':>12s} {'perf faults':>12s} {'ratio':>7s}"
          f" {'irq':>5s} {'softirq':>7s} {'foreign':>7s}")
    for name, d in out["controls"].items():
        for v in ("a", "b"):
            x = d[v]
            lt = statistics.median(x.get("ev:x86_exceptions_page_fault_user", [0]))
            pf = statistics.median([a + b for a, b in zip(x.get("minor-faults", [0]),
                                                           x.get("major-faults", [0]))])
            ratio = round(lt / pf, 3) if pf else None
            irq = statistics.median(x.get("irq_on_cpus", [0]))
            sirq = statistics.median(x.get("softirq_on_cpus", [0]))
            foreign = statistics.median(x.get("foreign_switch_in_on_cpus", [0]))
            rows.append({"control": name, "variant": v, "lttng_page_faults": lt,
                         "perf_faults": pf, "ratio": ratio, "irq_on_cpus": irq,
                         "softirq_on_cpus": sirq, "foreign_switch_in_on_cpus": foreign})
            print(f"{name + '/' + v:22s} {lt:12.0f} {pf:12.0f} {str(ratio):>7s}"
                  f" {irq:5.0f} {sirq:7.0f} {foreign:7.0f}")
    return rows


if __name__ == "__main__":
    main()
