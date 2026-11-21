"""Smoke test of the full trace profile (run as root on the VM).

One traced run each of the alloc and file_reads controls: checks no lost
events/packets, compares LTTng page-fault events with perf's fault count,
shows per-file attribution, interference counters and trace size.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_controls as rc  # noqa: E402

subprocess.run(["pgrep", "-x", "lttng-sessiond"], capture_output=True).returncode == 0 or \
    rc.sh(["lttng-sessiond", "--daemonize"])
available = rc.sh(["lttng", "list", "--kernel"]).stdout
missing = [e for e in rc.KERNEL_EVENTS if e not in available]
print("missing kernel events:", missing or "none")
for name in ("alloc", "file_reads"):
    for v in ("a", "b"):
        argv = ["python3", str(rc.HERE / "controls.py"), name, v]
        out = rc.TRACES / "smoke" / name / v
        c = rc.trace(argv, "2", out)
        pf = rc.perf(argv, "2", "minor-faults,major-faults")
        size = subprocess.run(["du", "-sh", str(out)], capture_output=True, text=True).stdout.split()[0]
        files = json.loads((out / "files.json").read_text())
        top = max(files.items(), key=lambda kv: kv[1].get("read_bytes", 0), default=("-", {}))
        print(f"{name}/{v}: lost events {c.get('discarded')} packets {c.get('discarded_packets')} | "
              f"lttng page faults {c.get('ev:x86_exceptions_page_fault_user', 0)} vs perf "
              f"{pf.get('minor-faults', 0) + pf.get('major-faults', 0):.0f} | page alloc "
              f"{c.get('ev:kmem_mm_page_alloc', 0)} | bytes_read {c.get('bytes_read', 0)} | "
              f"irq {c.get('irq_on_cpus', 0)} softirq {c.get('softirq_on_cpus', 0)} foreign "
              f"{c.get('foreign_switch_in_on_cpus', 0)} | traced {c['traced_wall_s']:.2f}s | {size}")
        print(f"   top file: {top[0][:60]} {top[1]}")
