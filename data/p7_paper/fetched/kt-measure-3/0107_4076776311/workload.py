import hashlib, logging, shutil, sys
from pathlib import Path
import numpy as np
import duckdb
import pandas as pd
from eth_defi.hyperliquid.trader_stats import TraderStatsDatabase

logging.disable(logging.CRITICAL)
ROOT = Path("/tmp/kt_842")
SRC = ROOT / "source.duckdb"
N_TRADERS = 150
FILLS = 400
REPEAT = 10

def build_source():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    con = duckdb.connect(str(SRC))
    con.execute("CREATE TABLE accounts (address VARCHAR PRIMARY KEY, label VARCHAR, is_vault BOOLEAN NOT NULL DEFAULT TRUE, added_at BIGINT NOT NULL)")
    con.execute("CREATE TABLE fills (address VARCHAR NOT NULL, trade_id BIGINT NOT NULL, ts BIGINT NOT NULL, coin VARCHAR NOT NULL, side TINYINT NOT NULL, sz FLOAT NOT NULL, px FLOAT NOT NULL, closed_pnl FLOAT, start_position FLOAT, fee FLOAT, oid BIGINT, PRIMARY KEY (address, trade_id))")
    con.execute("CREATE TABLE funding (address VARCHAR NOT NULL, ts BIGINT NOT NULL, coin VARCHAR NOT NULL, usdc FLOAT NOT NULL, sz FLOAT, rate FLOAT, PRIMARY KEY (address, ts, coin))")
    con.execute("CREATE TABLE ledger (address VARCHAR NOT NULL, ts BIGINT NOT NULL, event_type VARCHAR NOT NULL, usdc FLOAT NOT NULL, vault VARCHAR, PRIMARY KEY (address, ts, event_type))")
    rng = np.random.default_rng(842)
    base_ts = 1_700_006_400_000  # 2023-11-15 (Wed) UTC midnight
    day = 86_400_000
    accts, fills, funding, ledger = [], [], [], []
    for i in range(N_TRADERS + 5):
        addr = "0x%040x" % (i + 1)
        is_vault = i >= N_TRADERS
        accts.append((addr, f"t{i}", is_vault, base_ts))
        pattern = i % 7
        n_days = int(rng.integers(20, 200))
        days = rng.integers(0, n_days, FILLS)
        if pattern == 0:      # 24/7
            hours = rng.integers(0, 24, FILLS)
        elif pattern == 1:    # session 08-16
            hours = rng.integers(8, 16, FILLS)
        elif pattern == 2:    # 24h weekdays
            hours = rng.integers(0, 24, FILLS)
            dow = (days + 2) % 7
            days = np.where(dow >= 5, days - (dow - 4), days)
            days = np.where(days < 0, days + 7 - 2, days)
        elif pattern == 3:    # session on weekdays
            hours = rng.integers(13, 21, FILLS)
            dow = (days + 2) % 7
            days = np.where(dow >= 5, days - (dow - 4), days)
            days = np.where(days < 0, days + 7 - 2, days)
        elif pattern == 4:    # sparse hours
            hours = rng.choice([2, 3, 22], FILLS)
        elif pattern == 5:    # 24h on weekends only
            hours = rng.integers(0, 24, FILLS)
            days = (rng.integers(0, n_days // 7 + 1, FILLS) * 7) + 3 + rng.integers(0, 2, FILLS)
        else:                 # session on Mon/Tue/Wed only
            hours = rng.integers(6, 12, FILLS)
            days = (rng.integers(0, n_days // 7 + 1, FILLS) * 7) + 5 + rng.integers(0, 3, FILLS)
        ts = base_ts + days * day + hours * 3_600_000 + rng.integers(0, 3_600_000, FILLS)
        for j in range(FILLS):
            fills.append((addr, j, int(ts[j]), "BTC", int(j % 2), float(rng.uniform(0.01, 1)),
                          float(rng.uniform(30000, 60000)), float(rng.normal(5, 50)),
                          float(rng.normal(0, 2)), float(rng.uniform(0, 2)), j))
        for d in range(0, n_days, 3):
            funding.append((addr, base_ts + d * day, "BTC", float(rng.normal(0, 3)), 1.0, 0.0001))
        ledger.append((addr, base_ts - day, "deposit", float(rng.uniform(5000, 50000)), None))
    con.executemany("INSERT INTO accounts VALUES (?,?,?,?)", accts)
    fdf = pd.DataFrame(fills, columns=["address","trade_id","ts","coin","side","sz","px","closed_pnl","start_position","fee","oid"])
    con.register("fdf", fdf)
    con.execute("INSERT INTO fills SELECT * FROM fdf")
    udf = pd.DataFrame(funding, columns=["address","ts","coin","usdc","sz","rate"])
    con.register("udf", udf)
    con.execute("INSERT INTO funding SELECT * FROM udf")
    ldf = pd.DataFrame(ledger, columns=["address","ts","event_type","usdc","vault"]).astype({"vault": "object"})
    con.register("ldf", ldf)
    con.execute("INSERT INTO ledger SELECT address, ts, event_type, usdc, CAST(vault AS VARCHAR) FROM ldf")
    con.close()

def build_cache():
    # Pre-fill the daily_pnl cache table (same content refresh_daily_pnl would
    # produce) in bulk, since refresh_daily_pnl (unchanged by the PR) is slow.
    con = duckdb.connect(str(ROOT / "cache.duckdb"))
    con.execute(f"ATTACH '{SRC}' AS src (READ_ONLY)")
    con.execute("""
        CREATE TABLE daily_pnl (
            address VARCHAR NOT NULL, trade_date DATE NOT NULL,
            daily_closed_pnl DOUBLE, daily_funding_pnl DOUBLE, daily_fees DOUBLE,
            daily_net_pnl DOUBLE, PRIMARY KEY (address, trade_date))
    """)
    con.execute("""
        INSERT INTO daily_pnl
        WITH tr AS (
            SELECT f.address FROM src.fills f JOIN src.accounts a ON f.address = a.address
            WHERE a.is_vault = FALSE GROUP BY f.address HAVING COUNT(*) >= 10),
        fl AS (SELECT address, CAST(epoch_ms(ts) AS DATE) d, SUM(closed_pnl) cp, SUM(fee) fe
               FROM src.fills GROUP BY 1, 2),
        fu AS (SELECT address, CAST(epoch_ms(ts) AS DATE) d, SUM(usdc) fp
               FROM src.funding GROUP BY 1, 2),
        j AS (SELECT COALESCE(fl.address, fu.address) address, COALESCE(fl.d, fu.d) d,
                     COALESCE(cp, 0.0) cp, COALESCE(fp, 0.0) fp, COALESCE(fe, 0.0) fe
              FROM fl FULL OUTER JOIN fu ON fl.address = fu.address AND fl.d = fu.d)
        SELECT j.address, d, cp, fp, fe, cp + fp - fe FROM j JOIN tr ON j.address = tr.address
    """)
    con.close()

build_source()
build_cache()
out = hashlib.sha256()
db = TraderStatsDatabase(cache_path=ROOT / "cache.duckdb", source_path=SRC)
for _ in range(REPEAT):
    n = db.compute_metrics()
m = db.get_metrics(order_by="address")
db.close()
common = ["address","label","fill_count","active_days","net_pnl","total_closed_pnl","total_funding_pnl",
          "total_fees","trades_per_day","max_notional_exposure","initial_capital","cagr","sharpe",
          "sortino","max_drawdown","calmar"]
print("traders", n, len(m))
if "trading_time" in m.columns:
    print("trading_time", m["trading_time"].value_counts().sort_index().to_dict())
out.update(m[common].round(6).to_csv(index=False).encode())
print(out.hexdigest())
