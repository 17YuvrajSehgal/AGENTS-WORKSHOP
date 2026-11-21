import asyncio
import hashlib
import json
import os
import shutil
import sqlite3

from datasette.app import Datasette

TMP = "/tmp/kt_2533"


def make_dbs():
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    paths = []
    for d in range(3):
        p = os.path.join(TMP, f"db{d}.db")
        conn = sqlite3.connect(p)
        for t in range(15):
            conn.execute(f"create table t{t} (id integer primary key, name text)")
            conn.executemany(
                f"insert into t{t} (name) values (?)",
                [(f"n{i}",) for i in range(5)],
            )
        conn.commit()
        conn.close()
        paths.append(p)
    return paths


CONFIG = {
    "databases": {
        "db0": {
            "allow": {"id": ["alice", "root"]},
            "tables": {"t3": {"allow": {"id": "root"}}},
        },
        "db1": {
            "tables": {
                "t1": {"allow": {"id": "bob"}},
                "t2": {"allow": False},
            },
            "queries": {"q1": {"sql": "select 1", "allow": {"id": "alice"}}},
        },
    },
    "permissions": {"debug-menu": {"id": "alice"}},
}


async def run(ds):
    await ds.invoke_startup()
    out = []
    actors = [None, {"id": "alice"}, {"id": "bob"}, {"id": "root"}]
    paths = ["/", "/db0", "/db1", "/db2", "/db0/t1", "/db0/t3", "/db1/t1",
             "/db1/t2", "/db2/t5", "/db1/q1", "/-/actions.json" if False else "/db2/t0.json",
             "/.json", "/db1.json"]
    for rep in range(3):
        for actor in actors:
            cookies = {}
            if actor:
                cookies = {"ds_actor": ds.client.actor_cookie(actor)}
            for p in paths:
                r = await ds.client.get(p, cookies=cookies)
                out.append((rep, json.dumps(actor), p, r.status_code))
    return out


def main():
    paths = make_dbs()
    ds = Datasette(paths, config=CONFIG)
    ds.root_enabled = True
    out = asyncio.run(run(ds))
    for o in out[: len(out) // 3]:
        print(o)
    print(hashlib.sha256(repr(out).encode()).hexdigest())


main()
