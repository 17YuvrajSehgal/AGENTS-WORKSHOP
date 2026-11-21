import os, sys, shutil, asyncio, inspect, hashlib, json, logging
from datetime import datetime

logging.disable(logging.CRITICAL)

BACKEND = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "..", "..", "src", "backend")
BACKEND = os.path.abspath(BACKEND)
side = os.path.basename(os.path.dirname(os.path.dirname(BACKEND)))
WORK = f"/tmp/kt_469/{side}"
shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(WORK)
os.chdir(WORK)  # relative ./data/* runtime files go here
os.environ["LANCEDB_URI_BASE"] = os.path.join(WORK, "mem")
sys.path.insert(0, BACKEND)

settings_file = os.path.join(BACKEND, "data", "automation_settings.json")
data_dir_existed = os.path.exists(os.path.join(BACKEND, "data"))

import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from integrations import atom_communication_ingestion_pipeline as acip
    from integrations import atom_ingestion_pipeline as aip
    from core.automation_settings import get_automation_settings
    try:
        from integrations import atom_telegram_integration as tg
        TG = ("ok", tg.atom_slack_integration is None)
    except Exception as e:
        TG = ("err", type(e).__name__)

# keep knowledge extraction (LLM calls) off; in-memory only
get_automation_settings()._settings["enable_automatic_knowledge_extraction"] = False

if not data_dir_existed:
    shutil.rmtree(os.path.join(BACKEND, "data"), ignore_errors=True)


async def call(fn, *a):
    r = fn(*a)
    if inspect.isawaitable(r):
        r = await r
    return r


N_MSG = 30
N_REC = 30


async def main():
    results = []
    mm = acip.LanceDBMemoryManager(db_path=os.path.join(WORK, "mem1"), workspace_id="ws")
    pipe = acip.CommunicationIngestionPipeline(mm)
    apps = ["whatsapp", "gmail", "slack"]
    for i in range(N_MSG):
        app = apps[i % 3]
        ts = f"2025-01-{1 + i % 28:02d}T10:{i % 60:02d}:00"
        if app == "gmail":
            msg = {"id": f"m{i}", "date": ts, "from": f"u{i%7}@x.com", "to": "me@x.com",
                   "subject": f"Subj {i}", "body": f"Email body number {i} " * 3, "tags": ["mail"]}
        else:
            msg = {"id": f"m{i}", "timestamp": ts, "from": f"u{i%7}", "sender": f"u{i%7}",
                   "to": "me", "content": f"Message {i} about topic {i % 5}", "tags": [app]}
        results.append(bool(await call(pipe.ingest_message, app, msg)))

    gm = acip.LanceDBMemoryManager(db_path=os.path.join(WORK, "mem2"), workspace_id="ws")
    gm.initialize()
    p2 = aip.AtomIngestionPipeline(gm)
    rtypes = [("salesforce", "lead", {"name": "Acme", "status": "open"}),
              ("shopify", "order", {"order_id": 1, "total": 9.5}),
              ("google_ads", "ad_performance", {"spend": 10, "roas": 2.1}),
              ("google_drive", "document", {"content": "rule X", "file_path": "/a"})]
    for i in range(N_REC):
        app, rt, d = rtypes[i % 4]
        d = dict(d, id=f"r{i}", idx=i)
        results.append(bool(await call(p2.ingest_record, app, rt, d)))

    # fallback path (manager without ingest_generic_record)
    p3 = aip.AtomIngestionPipeline(mm)
    for i in range(10):
        results.append(bool(await call(p3.ingest_record, "hubspot", "contact", {"id": f"c{i}", "name": f"N{i}"})))

    t1 = mm.connections_table.to_pandas()
    t2 = gm.connections_table.to_pandas()
    meta1 = mm.metadata_table.to_pandas()
    summary = {
        "results": results,
        "t1": sorted(zip(t1["id"], t1["app_type"], t1["content"])),
        "t2": sorted(zip(t2["id"], t2["app_type"], t2["content"])),
        "tg": list(TG),
        "meta1": sorted(zip(meta1["app_type"], [int(x) for x in meta1["total_messages"]])),
    }
    return summary


s = asyncio.run(main())
print("tg", TG)
print("ok", sum(s["results"]), len(s["results"]), len(s["t1"]), len(s["t2"]), s["meta1"])
shutil.rmtree(WORK, ignore_errors=True)
print(hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest())
