import hashlib
import numpy as np
from tsam.utils.durationRepresentation import durationRepresentation

rng = np.random.default_rng(147)
h = hashlib.sha256()
cases = []
for n_periods, n_attrs, ts, k in [(365, 4, 24, 8), (365, 6, 24, 20), (200, 3, 48, 12), (52, 5, 168, 6)]:
    t = np.arange(ts)
    base = np.sin(2 * np.pi * t / ts)[None, None, :] * rng.uniform(1, 5, (1, n_attrs, 1))
    data = base + rng.normal(0, 1, (n_periods, n_attrs, ts)) + rng.uniform(0, 10, (n_periods, n_attrs, 1))
    data = np.abs(data).reshape(n_periods, n_attrs * ts)
    order = rng.integers(0, k, n_periods)
    cases.append((data, order, ts))
    cases.append((np.round(data, 1), order, ts))

for rep in range(6):
    for data, order, ts in cases:
        for mm in (False, True):
            res = durationRepresentation(data, order, True, ts, representMinMax=mm)
            arr = np.round(np.asarray(res, dtype=float), 9)
            if rep == 0:
                h.update(arr.tobytes())
print(h.hexdigest())
