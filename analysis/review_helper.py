"""Print one compact review card per measured PR (manual batch review).

  python -I analysis/review_helper.py [only_unreviewed]

Shows the agent's notes, stub/patch hints in workload.py, gates, claimed
mechanisms with quotes, the per-mechanism verdict, and the signals that
changed most. Decisions go into data/p7_paper/review.json by hand:
{"<pr id>": {"exclude": true/false, "why": "..."}}.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "data" / "p7_paper" / "fetched"
rev_path = ROOT / "data" / "p7_paper" / "review.json"
review = json.loads(rev_path.read_text()) if rev_path.exists() else {}
verd = {r["id"]: r for r in json.loads((ROOT / "data" / "p7_paper" / "per_pr_verdicts.json").read_text())}
claims = pd.read_parquet(ROOT / "data" / "p5_claims" / "all_v1" / "claims_mech.parquet")
only_new = len(sys.argv) > 1
STUB = re.compile(r"(monkeypatch|mock\.|MagicMock|patch\(|setattr\(|stub|fake)", re.I)

for mp in sorted(F.glob("*/*/measure.json")):
    d = mp.parent
    v = json.loads((d / "verdict.json").read_text())
    pid = v["job"]["id"]
    if only_new and str(pid) in review:
        continue
    a, c, r = v.get("agent") or {}, v.get("check") or {}, verd.get(pid, {})
    cov = c.get("coverage") or {}
    wl = (d / "workload.py").read_text(encoding="utf-8", errors="replace") if (d / "workload.py").exists() else ""
    stubs = sorted({m.group(1) for m in STUB.finditer(wl)})
    print(f"\n### {pid} {v['job']['repo']} #{v['job']['number']} ({d.parent.name}) tier={a.get('tier')}")
    print("  notes:", (a.get("notes") or "")[:330])
    print(f"  gates: base {c.get('base_time_s')}s head {c.get('head_time_s')}s | cov head "
          f"{(cov.get('head') or {}).get('share')} base {(cov.get('base') or {}).get('share')} | equal "
          f"{c.get('output_equal')} | py_share {v.get('python_share_of_code_change')} | stub words {stubs}")
    for q in claims[claims.id == pid].itertuples():
        print(f"  claim {q.mechanism}: \"{q.quote[:120]}\"")
    print(f"  verdict: speed {r.get('speed')} (wall {r.get('wall_ratio')}, A/A {r.get('aa_ratio')}) | "
          f"held {r.get('held')} | costs {r.get('hidden_costs')}")
    meas = json.loads(mp.read_text())["variants"]
    ch = []
    for k, b in meas["base"].items():
        h = meas["head"].get(k)
        if not b or not h or any(x is None for x in b + h) or k.startswith("pcnt"):
            continue
        sb, sh = sorted(b), sorted(h)
        mb, mh = sb[len(sb) // 2], sh[len(sh) // 2]
        if mb > 0 and abs(mh / mb - 1) >= 0.10:
            sep = "sep" if (max(h) < min(b) or min(h) > max(b)) else "ovl"
            ch.append((abs(mh / mb - 1), f"{k} {mh / mb:.2f}{'' if sep == 'sep' else '?'}"))
    print("  top changes:", ", ".join(x for _, x in sorted(ch, reverse=True)[:10]))
