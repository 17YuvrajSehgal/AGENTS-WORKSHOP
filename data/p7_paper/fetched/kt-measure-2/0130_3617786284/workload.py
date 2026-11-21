import os, shutil, asyncio, hashlib, random
D = "/tmp/kt_19427"
shutil.rmtree(D, ignore_errors=True)
os.makedirs(D)
os.environ["PREFECT_HOME"] = D
os.environ["PREFECT_API_DATABASE_CONNECTION_URL"] = f"sqlite+aiosqlite:///{D}/db.sqlite"
os.environ["PREFECT_SERVER_ANALYTICS_ENABLED"] = "false"

from prefect.server.database import provide_database_interface
from prefect.server import models, schemas
from prefect.server.schemas.core import ConcurrencyLimitV2
from prefect.server.api.concurrency_limits_v2 import _generate_concurrency_locked_response


async def main():
    random.seed(12345)
    db = provide_database_interface()
    await db.create_db()
    specs = [
        ("tag:long-running", 10, 10800.0, 0.0),
        ("tag:quick-tasks", 10, 2.0, 0.0),
        ("queue-long", 5, 500.0, 0.0),
        ("queue-short", 5, 3.0, 0.0),
        ("rate-limit", 10, 0.0, 1.0),
        ("rate-slow", 4, 0.0, 0.25),
    ]
    limits = {}
    async with db.session_context(begin_transaction=True) as session:
        for name, lim, avg, decay in specs:
            obj = await models.concurrency_limits_v2.create_concurrency_limit(
                session=session,
                concurrency_limit=ConcurrencyLimitV2(
                    name=name, limit=lim, active_slots=lim,
                    avg_slot_occupancy_seconds=avg, slot_decay_per_second=decay,
                ),
            )
            limits[name] = schemas.core.ConcurrencyLimitV2.model_validate(obj, from_attributes=True)
    combos = [[n] for n in limits] + [
        ["tag:long-running", "queue-short"],
        ["tag:quick-tasks", "queue-long"],
        ["rate-limit", "tag:quick-tasks"],
    ]
    out = []
    for i in range(300):
        names = combos[i % len(combos)]
        slots = 1 + (i % 3)
        async with db.session_context(begin_transaction=True) as session:
            ls = [limits[n] for n in names]
            exc = await _generate_concurrency_locked_response(session=session, limits=ls, slots=slots)
        ra = float(exc.headers["Retry-After"])
        out.append(f"{i}:{exc.status_code}:{ra:.6g}")
    for l in out[:: 25]:
        print(l)
    print(hashlib.sha256("\n".join(out).encode()).hexdigest())

asyncio.run(main())
