"""Delete verdicts that are usage-limit failures, not PR outcomes (run on a VM).

A verdict is removed only if the agent gave no structured answer AND the
transcript's result event says usage_limit_reached / HTTP 429. Removed
verdicts are kept as verdict_ratelimited.json for the record.
"""
import glob
import json
import os

removed = kept = 0
for p in glob.glob(os.path.expanduser("~/prs/*/verdict.json")):
    v = json.load(open(p))
    if v.get("agent"):
        kept += 1
        continue
    d = os.path.dirname(p)
    tr = open(os.path.join(d, "transcript.jsonl"), encoding="utf-8", errors="replace").read()
    if '"api_error":"usage_limit_reached"' in tr or '"api_error_status":429' in tr:
        os.replace(p, os.path.join(d, "verdict_ratelimited.json"))
        removed += 1
    else:
        kept += 1
print(f"removed {removed} usage-limit verdicts, kept {kept}")
