"""Check the paper's numbers before submission.

  python -I analysis/verify_paper.py

1. Re-runs the three generators and fails if a macro file changed
   (i.e. the PDF was built from stale numbers).
2. Fails if a section uses a macro that no generator defines.
3. Lists every number typed by hand in the sections, for a manual check.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "paper"
PY = sys.executable
GEN = [
    (["analysis/paper_numbers.py"], "numbers.tex"),
    (["analysis/p7_results.py", "data/p7_paper/fetched"], "results.tex"),
    (["analysis/p7_cases.py"], "cases.tex"),
    (["analysis/p7_extra.py"], "extra.tex"),
    (["analysis/p7_extra.py"], "table_agents.tex"),
]
bad = 0
for args, out in GEN:
    before = (P / out).read_text()
    subprocess.run([PY, "-I", *args], cwd=ROOT, check=True, capture_output=True)
    if (P / out).read_text() != before:
        print(f"STALE: {out} changed on regeneration; rebuild the PDF")
        bad += 1

defined = set()
for _, out in GEN:
    defined |= set(re.findall(r"\\newcommand\{\\(\w+)\}", (P / out).read_text()))
defined |= set(re.findall(r"\\newcommand\{\\(\w+)\}", (P / "main.tex").read_text()))
texs = [P / "main.tex", *sorted((P / "sections").glob("*.tex"))]
for t in texs:
    body = re.sub(r"(?<!\\)%.*", "", t.read_text(encoding="utf-8"))
    for m in sorted(set(re.findall(r"\\((?:n|pct|ev|mech|fun|q|aa|case|usd)[A-Z]\w*)", body))):
        if m not in defined:
            print(f"UNDEFINED: \\{m} in {t.name}")
            bad += 1
    body = re.sub(r"\\(cite|ref|label|input|cref|Cref)\{[^}]*\}", "", body)
    body = re.sub(r"\\\w+", "", body)  # drop macro names (keeps their digits out)
    nums = sorted(set(re.findall(r"\d[\d,.]*\d|\d", body)))
    if nums:
        print(f"hand-typed in {t.name}: {' '.join(nums)}")
print("FAIL" if bad else "OK: macro files current, all macros defined")
sys.exit(1 if bad else 0)
