# maverick-mcp #79 "Bolt: Optimize technical analysis functions" (avoid
# full DataFrame copies). Pilot workload (hand-written, experimenter has read
# the PR): RSI, SMA and ATR on a 300,000-row OHLCV frame with capitalised
# column names (so the case-insensitive lookup runs), 10 rounds.
# Last line = SHA-256 over the rounded results.
import hashlib
import logging

import numpy as np
import pandas as pd

logging.disable(logging.CRITICAL)
from maverick_mcp.core.technical_analysis import (  # noqa: E402
    calculate_atr,
    calculate_rsi,
    calculate_sma,
)

rng = np.random.default_rng(42)
n = 300_000
close = 100 + np.cumsum(rng.normal(0, 1, n))
df = pd.DataFrame({
    "Open": close + rng.normal(0, 0.5, n),
    "High": close + np.abs(rng.normal(0, 1, n)),
    "Low": close - np.abs(rng.normal(0, 1, n)),
    "Close": close,
    "Volume": rng.integers(1_000, 1_000_000, n),
}, index=pd.date_range("2000-01-01", periods=n, freq="min"))

h = hashlib.sha256()
for _ in range(10):
    for s in (calculate_rsi(df, 14), calculate_sma(df, 50), calculate_atr(df, 14)):
        h.update(np.round(s.to_numpy(dtype=float), 8).tobytes())
# error paths (columns missing): both versions must fail the same way
bad = df.rename(columns={"High": "H", "Close": "C"})
for f in (calculate_atr, calculate_rsi):
    try:
        f(bad, 14)
        h.update(b"no error")
    except (KeyError, ValueError) as e:
        h.update(type(e).__name__.encode())
print(n)
print(h.hexdigest())
