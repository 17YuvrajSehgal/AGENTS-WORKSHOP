# static-frame #1140 "Use `_weak_cache` in `StoreXLSX.read_many()`".
# Pilot workload (hand-written, experimenter has read the PR): write an XLSX
# store with 4 frames once, then call read_many() on it 15 times while
# keeping the results alive (the weak cache only helps while references
# exist). Last line = SHA-256 over the frames read.
import hashlib
from pathlib import Path

import numpy as np

import static_frame as sf
from static_frame.core.store_config import StoreConfig
from static_frame.core.store_xlsx import StoreXLSX

FP = Path("/tmp/kt_staticframe.xlsx")
labels = ("a", "b", "c", "d")
config = StoreConfig(index_depth=1, columns_depth=1)
if not FP.exists():  # created once, deterministic content
    rng = np.random.default_rng(42)
    frames = [sf.Frame(rng.random((2000, 8)), columns=[f"c{j}" for j in range(8)],
                       index=[f"r{i}" for i in range(2000)], name=lab) for lab in labels]
    StoreXLSX(FP, config=config).write((f.name, f) for f in frames)

st = StoreXLSX(FP, config=config)
kept = []
h = hashlib.sha256()
for _ in range(15):
    got = list(st.read_many(labels))
    kept.append(got)
    for f in got:
        h.update(f.values.astype(float).tobytes())
print(len(kept))
print(h.hexdigest())
