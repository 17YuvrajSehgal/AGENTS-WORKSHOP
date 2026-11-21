# iPhotron #468 "Bolt: Optimize asset scanning IO with partial hashing".
# Pilot workload (hand-written, experimenter has read the PR): build the
# scanner's base row (which hashes each file for its id) for 24 large files
# (32 MB: partial hashing applies) and 24 small files (1 MB: whole file).
# Last line = SHA-256 over the produced rows. The PR changes how ids are
# computed, so the digest is EXPECTED to differ between base and head.
import hashlib
import json
import os
import random
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # module imports Qt; no display
from iPhoto.io.scanner import _build_base_row  # noqa: E402

ROOT = Path("/tmp/kt_iphotron")
files = []
for i in range(48):
    p = ROOT / f"img_{i:02d}.jpg"
    size = (32 if i < 24 else 1) * 1024 * 1024
    if not p.exists():  # created once, deterministic content
        ROOT.mkdir(parents=True, exist_ok=True)
        p.write_bytes(random.Random(i).randbytes(size))
    files.append(p)

rows = [_build_base_row(ROOT, p, p.stat()) for p in files]
for r in rows:  # timestamps depend on file creation time, not on the code
    r.pop("dt"), r.pop("ts")
print(rows[0]["id"], rows[-1]["id"])
print(hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest())
