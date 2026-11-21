#!/usr/bin/env bash
# Prove a fleet VM is identical where measurements depend on it. One line of
# key=value facts; compare across VMs. Includes the exact-instruction counter
# check (dec+jnz loop: instructions:u(2e9) - instructions:u(1e9) = 2e9).
set -u
k() { printf '%s=%s | ' "$1" "$2"; }
k host "$(hostname)"
k kernel "$(uname -r)"
k cpu "$(lscpu | sed -n 's/^Model name: *//p')"
k microcode "$(grep -m1 microcode /proc/cpuinfo | awk '{print $3}')"
k cpus "$(nproc)"
k cmdline "$(grep -oE 'nohz_full=[^ ]*|rcu_nocbs=[^ ]*|isolcpus=[^ ]*' /proc/cmdline | tr '\n' ' ')"
k slices "$(systemctl show -p AllowedCPUs system.slice user.slice | tr '\n' ' ')"
k sysctl "$(sysctl -n kernel.perf_event_paranoid kernel.nmi_watchdog | tr '\n' ',')"
sudo pgrep -x lttng-sessiond >/dev/null || sudo lttng-sessiond --daemonize
k lttng "$(lttng --version | head -1 | awk '{print $3}')"
k probes "$(ls /lib/modules/$(uname -r)/updates/probes/ | wc -l)"
k events "$(sudo lttng list --kernel | wc -l)"
k pagefault_event "$(sudo lttng list --kernel | grep -c x86_exceptions_page_fault_user)"
k bt2 "$(python3 -c 'import bt2; print(bt2.__version__)')"
k perf "$(perf --version | awk '{print $3}')"
cd ~/controls && gcc -O1 -o counters counters.c
i1=$(sudo perf stat -x, -e instructions:u -- ./counters 1000000000 2>&1 >/dev/null | cut -d, -f1)
i2=$(sudo perf stat -x, -e instructions:u -- ./counters 2000000000 2>&1 >/dev/null | cut -d, -f1)
k counter_delta "$((i2 - i1)) (expect 2000000000)"
echo
