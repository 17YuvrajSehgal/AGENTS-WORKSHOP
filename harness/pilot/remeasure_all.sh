#!/usr/bin/env bash
# Re-run Phase-0 controls and the 9 measurable pilot PRs with the full trace
# profile (2026-11-20). Raw traces go to /srv/kt/traces/{controls,pilot_v2}.
# openfisca #1367 (order 20) is not measured: its changed code is unreachable.
set -u
cd "$(dirname "$(readlink -f "$0")")/.."  # the user home with controls/, pilot/, prs/ (not $HOME: sudo sets it to /root)
log() { echo "$(date +%H:%M:%S) $*" | tee -a remeasure.log; }
log "controls (5 runs, full profile)"
(cd controls && python3 run_controls.py 5 > ../remeasure_controls.log 2>&1)
log "controls exit $?"
# order  workload                              cpus  runs
while read -r id wl cpus runs; do
  log "PR $id"
  python3 pilot/measure_pr.py "prs/$id" "pilot/workloads/$wl" "$cpus" "$runs" > "remeasure_$id.log" 2>&1
  log "PR $id exit $?"
  mkdir -p results_v2 && cp "prs/$id/measure.json" "results_v2/${id}_measure.json" \
    && cp "prs/$id/env.json" "results_v2/${id}_env.json" && cp "prs/$id/coverage.json" "results_v2/${id}_coverage.json"
done <<'EOF'
02 02_pythainlp.py 2 10
19 19_mlflow.py 2 10
10 10_iphotron_scan.py 2 10
14 14_iphotron_thumb.py 2 10
16 16_maverick.py 2 10
01 01_staticframe.py 2 10
08 08_pandas.py 2 10
09 09_smda.py 2 5
15 15_prefect.py 2,3 5
EOF
cp controls/results/controls.json results_v2/controls.json; cp controls/results/env.json results_v2/controls_env.json
du -sh /srv/kt/traces/* > results_v2/trace_sizes.txt
log "all done"
touch remeasure.done
