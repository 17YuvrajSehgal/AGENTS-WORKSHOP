"""Coverage check: does the workload execute the lines the PR changed?

  python3 cover.py <pr_dir> <diff_file> <workload.py> [cpus]

Runs the workload under coverage.py in base and head. Lines changed by the
diff: removed lines (base side, old line numbers) and added lines (head
side, new line numbers), in non-test .py files. Reports the share executed
on each side. Gate (RESEARCH-PLAN 6.2): head share >= 0.8 of changed
executable lines; base share reported. Also compares the workload's output
digest (last stdout line) between base and head.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

pr, diff, workload = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]).resolve()


def changed_lines(text):
    """{file: {'base': set(old lines), 'head': set(new lines)}} for non-test .py files."""
    out, f, old, new = {}, None, 0, 0
    for line in text.splitlines():
        if line.startswith("+++ "):
            name = line[6:] if line.startswith("+++ b/") else None
            f = name if name and name.endswith(".py") and "test" not in name.lower() else None
            if f:
                out.setdefault(f, {"base": set(), "head": set()})
        elif line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", line)
            old, new = int(m.group(1)), int(m.group(2))
        elif f and line.startswith("+") and not line.startswith("+++"):
            if line[1:].strip() and not line[1:].strip().startswith("#"):
                out[f]["head"].add(new)
            new += 1
        elif f and line.startswith("-") and not line.startswith("---"):
            if line[1:].strip() and not line[1:].strip().startswith("#"):
                out[f]["base"].add(old)
            old += 1
        elif f and not line.startswith("\\"):
            old += 1
            new += 1
    return out


def run(side, files):
    py = pr / side / "venv" / "bin" / "python"
    data = pr / side / ".coverage"
    # match by package path, so editable and normal installs both work
    p = subprocess.run([str(py), "-m", "coverage", "run", f"--data-file={data}",
                        f"--include={','.join('*/' + f for f in files)}", str(workload)],
                       capture_output=True, text=True, cwd=pr)
    if p.returncode != 0:
        sys.exit(f"{side} workload failed:\n{p.stderr[-2000:]}")
    rep = subprocess.run([str(py), "-m", "coverage", "json", f"--data-file={data}", "-o", "-"],
                         capture_output=True, text=True, cwd=pr)
    cov = json.loads(rep.stdout)["files"] if rep.stdout.strip() else {}
    executed = {}
    for f in files:
        key = next((k for k in cov if k.endswith(f)), None)
        if key is None:  # file never imported by the workload
            executed[f] = (set(), set())
            continue
        ran = set(cov[key]["executed_lines"])
        executed[f] = (ran, ran | set(cov[key]["missing_lines"]))  # (executed, executable)
    return executed, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""


ch = changed_lines(diff.read_text(encoding="utf-8"))
res = {"changed_files": sorted(ch)}
digests = {}
for side in ("base", "head"):
    ex, digests[side] = run(side, sorted(ch))
    want = hit = 0
    for f, d in ch.items():
        executed, executable = ex[f]
        target = d[side] & executable  # ignore non-executable changed lines
        want += len(target)
        hit += len(target & executed)
    res[side] = {"changed_executable_lines": want, "executed": hit,
                 "share": round(hit / want, 3) if want else None}
res["output_digest_base"], res["output_digest_head"] = digests["base"], digests["head"]
res["output_equal"] = digests["base"] == digests["head"]
head_share = res["head"]["share"]
res["coverage_gate_pass"] = head_share is None or head_share >= 0.8
print(json.dumps(res, indent=1))
(pr / "coverage.json").write_text(json.dumps(res, indent=1))
