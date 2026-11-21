# pandas #64575 "PERF: use np.unique instead of pd.unique in
# _FrequencyInferer". Pilot workload (hand-written, experimenter has read the
# PR): pd.infer_freq on indexes that reach the changed code: daily and hourly
# spacing (day_deltas / hour_deltas), annual (_get_annual_rule) and
# week-of-month (_get_wom_rule), including irregular ones. The PR also changes
# `/` to `//` in day_deltas and hour_deltas, so results are compared.
# Last line = SHA-256 over all inferred frequencies.
import hashlib

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
indexes = []
for start in pd.date_range("2000-01-01", periods=40, freq="17D"):
    for freq, n in (("D", 400), ("3D", 300), ("h", 500), ("5h", 300), ("YS", 30), ("YE", 30),
                    ("WOM-2TUE", 60), ("WOM-1MON", 60), ("MS", 120), ("B", 400)):
        idx = pd.date_range(start, periods=n, freq=freq)
        indexes.append(idx)
        # irregular version: drop a few points, so inference has to reject rules
        keep = np.sort(rng.choice(n, n - 3, replace=False))
        indexes.append(idx[keep])

out = []
for _ in range(3):
    for idx in indexes:
        out.append(str(pd.infer_freq(idx)))
print(len(out), sum(o != "None" for o in out))
print(hashlib.sha256("|".join(out).encode()).hexdigest())
