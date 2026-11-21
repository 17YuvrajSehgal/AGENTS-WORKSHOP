#!/usr/bin/env bash
# Checks for the measurement CPU setup (run on the VM).
echo "cmdline: $(grep -oE 'isolcpus[^ ]*|nohz_full=[^ ]*' /proc/cmdline | tr '\n' ' ')"
echo "isolated: '$(cat /sys/devices/system/cpu/isolated)'"
systemctl show -p AllowedCPUs system.slice user.slice init.scope | tr '\n' ' '; echo
cd "$(dirname "$0")"
S="systemd-run --scope --quiet --slice=measure -p AllowedCPUs=2,3 taskset -c 2,3"
for v in a b; do
  echo "== parallel $v"
  sudo perf stat -a -A -C 2,3 -e instructions -- $S python3 controls.py parallel $v 2>&1 | grep -E 'CPU|elapsed'
done
echo "== pid kept through systemd-run --scope:"
sudo python3 - <<'EOF'
import subprocess
p = subprocess.Popen(["systemd-run", "--scope", "--quiet", "--slice=measure",
                      "-p", "AllowedCPUs=2", "python3", "-c", "import os; print(os.getpid())"],
                     stdout=subprocess.PIPE, text=True)
child = p.communicate()[0].strip()
print("popen pid", p.pid, "workload pid", child, "same:", str(p.pid) == child)
EOF
