"""Build the paper's artifact (code + data) as a zip for Zenodo.

  python -I analysis/make_artifact.py    -> dist/below-artifact.zip

What goes in: all code (analysis/, harness/), the codebooks, the derived
data every paper number is computed from, the measurement results of all
91 PRs (with each workload), and the paper sources. What stays out and why
is listed in ARTIFACT-README.md. Pre-signed cloud URLs that third-party PR
descriptions contain (expired, but they look like credentials) are cut
down to their path. The script then checks that the paper's numbers can be
regenerated from the zip's contents alone.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "build"  # staging folder; the zip root is below-artifact/
INCLUDE = [
    "analysis", "harness", "labels", "requirements.txt", "requirements.lock.txt",
    "data/aidev-v5-manifest.json", "data/aidev-hf-refs.json", "data/v5_schema.json",
    "data/aidev-readme-b8dc67d.md",
    "data/p1_counts.json", "data/p1_keyword_stats.json", "data/p1_template_lines.csv",
    "data/p1_pr_meta.jsonl",
    "data/p1_classify/pilot_input.jsonl", "data/p1_classify/pilot_labels_cc.parquet",
    "data/p1_classify/pilot_sample_meta.json", "data/p1_classify/pilot_summary_cc.json",
    "data/p1_classify/cc_raw",
    "data/p2_classify/labels.parquet", "data/p2_classify/order.parquet",
    "data/p2_classify/summary.json", "data/p2_classify/targets.json",
    "data/p2_haiku_agree", "data/p5_claims",
    "data/p7_paper/fetched", "data/p7_paper/vm_controls",
    "data/p7_paper/per_pr_verdicts.json", "data/p7_paper/review.json",
    "paper",
]
SKIP_NAMES = {"__pycache__", "cc_cwd", ".idea"}
SKIP_FILES = {"REVIEW-1.MD", "key.csv", "run.lock", "res.tgz"}
SKIP_SUFFIX = {".drawio", ".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".log", ".out", ".synctex.gz", ".bkp", ".pyc"}
# paths whose content is replaced: personal cloud project id in the fetch script
SCRUB = {"analysis/fetch_results.sh": [(r"project-[0-9a-z-]+", "<your-gcp-project>")]}
PRESIGNED = re.compile(r"(https?://[^\s\"'\\)]+?)\?[^\s\"'\\)]*X-Amz-[^\s\"'\\)]*")


def wanted(p: Path) -> bool:
    if any(part in SKIP_NAMES for part in p.parts):
        return False
    if p.name in SKIP_FILES or p.name.startswith("_review_cards") or p.name.startswith(".$"):
        return False
    return not any(p.name.endswith(s) for s in SKIP_SUFFIX)


if OUT.exists():
    shutil.rmtree(OUT)
redacted = 0
for item in INCLUDE:
    src = ROOT / item
    files = [src] if src.is_file() else [f for f in src.rglob("*") if f.is_file()]
    for f in files:
        rel = f.relative_to(ROOT)
        if not wanted(rel):
            continue
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix in {".json", ".jsonl", ".py", ".sh", ".md", ".txt", ".tex", ".csv", ".bib", ".dat"}:
            text = f.read_text(encoding="utf-8", errors="surrogateescape")
            text, n = PRESIGNED.subn(r"\1", text)
            redacted += n
            for pat, rep in SCRUB.get(rel.as_posix(), []):
                text = re.sub(pat, rep, text)
            dst.write_text(text, encoding="utf-8", errors="surrogateescape", newline="\n")
        else:
            shutil.copy2(f, dst)
shutil.copy2(ROOT / "ARTIFACT-README.md", OUT / "README.md")
shutil.copy2(ROOT / "LICENSE", OUT / "LICENSE")

# check: no pre-signed URL left, and the paper numbers regenerate from the copy alone
left = [p for p in OUT.rglob("*") if p.is_file() and p.suffix in {".json", ".jsonl"}
        and "X-Amz-Credential" in p.read_text(encoding="utf-8", errors="ignore")]
assert not left, left
before = {n: (OUT / "paper" / n).read_text() for n in ("numbers.tex", "results.tex", "cases.tex", "extra.tex")}
for args in (["analysis/paper_numbers.py"], ["analysis/p7_results.py", "data/p7_paper/fetched"],
             ["analysis/p7_cases.py"], ["analysis/p7_extra.py"]):
    subprocess.run([sys.executable, "-I", *args], cwd=OUT, check=True, capture_output=True)
for n, t in before.items():
    assert (OUT / "paper" / n).read_text() == t, f"{n} differs when regenerated inside the artifact"

zpath = ROOT / "dist" / "below-artifact.zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            z.write(f, Path("below-artifact") / f.relative_to(OUT))
n = sum(1 for f in OUT.rglob("*") if f.is_file())
print(f"ok: {n} files, {zpath.stat().st_size / 1e6:.1f} MB, {redacted} pre-signed URLs cut; "
      "paper numbers regenerate identically from the artifact")
