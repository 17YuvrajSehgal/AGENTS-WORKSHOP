import hashlib, json, os, sys, shutil
from pathlib import Path

SRC = Path(sys.executable).parent.parent.parent / "src"
SIDE = SRC.parent.name
WORK = Path(f"/tmp/kt_1168/{SIDE}")
shutil.rmtree(WORK, ignore_errors=True)
WORK.mkdir(parents=True, exist_ok=True)
os.environ["HISTORIFY_DATABASE_PATH"] = str(WORK / "historify.duckdb")
os.chdir(WORK)
sys.path.insert(0, str(SRC))

import logging
logging.disable(logging.CRITICAL)

from flask import Flask
from database import historify_db as hdb
from utils import plugin_loader

results = []

# Broker capabilities loading (plugin.json parsing)
app = Flask("openalgo", root_path=str(SRC))
with app.app_context():
    for _ in range(200):
        caps = plugin_loader.load_broker_capabilities()
results.append(json.dumps(caps, sort_keys=True))

# Historify DB schema init on fresh databases + re-init
for i in range(6):
    db = WORK / "historify.duckdb"
    for p in WORK.glob("historify.duckdb*"):
        p.unlink()
    hdb.init_database()
    hdb.init_database()
    with hdb.get_connection() as conn:
        tables = conn.execute(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "ORDER BY table_name, column_name").fetchall()
        idx = conn.execute("SELECT index_name, table_name FROM duckdb_indexes() ORDER BY index_name").fetchall()
    results.append(repr(tables) + repr(idx))

print("brokers:", len(caps))
print("tables:", len({t[0] for t in tables}))
print(hashlib.sha256("\n".join(results).encode()).hexdigest())
