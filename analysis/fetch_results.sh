#!/usr/bin/env bash
# Copy every PR's small result files from the 3 VMs into data/p7_paper/fetched/<vm>/
# (verdict/check for all PRs; measure/coverage/env for measured ones). Read-only on the VMs.
set -u
cd "$(dirname "$0")/.."
P=project-ba99825a-df02-4405-af4
for vz in kt-measure-1:us-central1-a kt-measure-2:us-central1-a kt-measure-3:us-east1-b; do
  V=${vz%%:*}; Z=${vz##*:}
  timeout 180 gcloud compute ssh "$V" --project $P --zone "$Z" --quiet --command \
    'cd prs && tar czf ~/res.tgz $(for d in */; do for f in verdict.json check.json measure.json coverage.json env.json workload.py; do [ -f $d$f ] && echo $d$f; done; done) 2>/dev/null' >/dev/null 2>&1
  rm -rf "data/p7_paper/fetched/$V"; mkdir -p "data/p7_paper/fetched/$V"
  timeout 180 gcloud compute scp "$V:res.tgz" "data/p7_paper/fetched/$V/res.tgz" --project $P --zone "$Z" --quiet >/dev/null 2>&1
  tar xzf "data/p7_paper/fetched/$V/res.tgz" -C "data/p7_paper/fetched/$V/" && rm "data/p7_paper/fetched/$V/res.tgz"
  echo "$V: $(ls data/p7_paper/fetched/$V | wc -l) PR dirs, $(ls data/p7_paper/fetched/$V/*/measure.json 2>/dev/null | wc -l) measured"
done
