#!/usr/bin/env bash
# Smoke test: trace a small known workload, then count events with bt2.
# The workload opens and reads one file 1,000 times, so openat and read
# counts for python3 must be at least 1,000 each.
#
# Page faults are NOT traced with LTTng on this kernel: Ubuntu's headers
# package omits arch/x86/include/asm/trace/exceptions.h, so lttng-modules
# skips lttng-probe-x86-exceptions. Page faults come from perf stat instead.
set -euo pipefail
sudo pgrep -x lttng-sessiond >/dev/null || sudo lttng-sessiond --daemonize

EVENTS="sched_switch sched_wakeup sched_process_fork sched_process_exec block_rq_issue block_rq_complete"
# guard: lttng accepts unknown event names silently, which would give zeros
AVAILABLE=$(sudo lttng list --kernel)
for e in $EVENTS; do
  grep -qw "$e" <<<"$AVAILABLE" || { echo "MISSING kernel event: $e"; exit 1; }
done
echo "all $(wc -w <<<"$EVENTS") kernel events present"

OUT=/tmp/smoke-trace; sudo rm -rf "$OUT"
sudo lttng destroy smoke >/dev/null 2>&1 || true
sudo lttng create smoke --output="$OUT" >/dev/null
sudo lttng enable-channel --kernel --subbuf-size=16M --num-subbuf=8 k >/dev/null
sudo lttng enable-event --kernel --channel=k --syscall --all >/dev/null
sudo lttng enable-event --kernel --channel=k "${EVENTS// /,}" >/dev/null
sudo lttng add-context --kernel --channel=k -t procname -t pid -t tid >/dev/null
sudo lttng start >/dev/null
python3 -c "
for _ in range(1000):
    with open('/etc/os-release') as f: f.read()
"
sudo lttng stop >/dev/null
sudo lttng destroy >/dev/null
sudo chmod -R a+rX "$OUT"

python3 - "$OUT" <<'EOF'
import sys, collections, bt2
c = collections.Counter()
discarded = 0
for msg in bt2.TraceCollectionMessageIterator(sys.argv[1]):
    if type(msg) is bt2._DiscardedEventsMessageConst:
        discarded += msg.count or 0
    if type(msg) is not bt2._EventMessageConst:
        continue
    ev = msg.event
    if str(ev.common_context_field["procname"]) == "python3":
        c[ev.name] += 1
print("discarded events:", discarded)
for k in ("syscall_entry_openat", "syscall_entry_read", "syscall_entry_close",
          "sched_switch", "sched_process_exec"):
    print(f"{k:34s} {c[k]}")
EOF

echo "== page faults from perf stat (same workload)"
sudo perf stat -e minor-faults,major-faults -- python3 -c "
for _ in range(1000):
    with open('/etc/os-release') as f: f.read()
" 2>&1 | grep -E 'faults'
