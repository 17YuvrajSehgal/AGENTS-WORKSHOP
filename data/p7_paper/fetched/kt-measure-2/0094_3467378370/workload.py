import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

SRC = os.path.join(os.path.dirname(os.path.abspath(sys.prefix)), "src")
sys.path.insert(0, SRC)
os.chdir(SRC)

import requests  # noqa: E402
from requests.adapters import BaseAdapter  # noqa: E402

logging.disable(logging.CRITICAL)

from intentkit.models import db as dbmod  # noqa: E402
from intentkit.models.agent_data import AgentDataTable  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.services.twitter import oauth2_refresh  # noqa: E402
from app.services.twitter.oauth2 import oauth2_user_handler  # noqa: E402

N_AGENTS = 24
ROUNDS = 2
LATENCY = 0.004


class FakeXTokenAdapter(BaseAdapter):
    """Stand-in for the remote X OAuth2 token endpoint (network I/O)."""

    def __init__(self):
        super().__init__()
        self.counter = 0

    def send(self, request, **kwargs):
        time.sleep(LATENCY)  # simulated network latency
        body = request.body or ""
        if isinstance(body, bytes):
            body = body.decode()
        params = dict(p.split("=", 1) for p in body.split("&") if "=" in p)
        rt = params.get("refresh_token", "")
        resp = requests.Response()
        if rt.startswith("bad"):
            resp.status_code = 400
            payload = {"error": "invalid_grant"}
        else:
            resp.status_code = 200
            h = hashlib.sha256(rt.encode()).hexdigest()[:16]
            payload = {
                "token_type": "bearer",
                "access_token": "acc-" + h,
                "refresh_token": "ref-" + h,
                "expires_in": 7200,
                "expires_at": 1900000000 + int(h[:4], 16),
                "scope": "tweet.read users.read offline.access",
            }
        resp._content = json.dumps(payload).encode()
        resp.headers["Content-Type"] = "application/json"
        resp.url = request.url
        resp.request = request
        resp.encoding = "utf-8"
        return resp

    def close(self):
        pass


async def seed():
    now = datetime.now(timezone.utc)
    async with dbmod.get_session() as s:
        for i in range(N_AGENTS):
            rt = f"bad-{i}" if i % 10 == 7 else f"seed-{i}"
            s.add(
                AgentDataTable(
                    id=f"agent-{i:03d}",
                    twitter_access_token=f"old-{i}",
                    twitter_refresh_token=rt,
                    twitter_access_token_expires_at=now + timedelta(minutes=2),
                )
            )
        await s.commit()


async def reset_expiry():
    now = datetime.now(timezone.utc)
    async with dbmod.get_session() as s:
        rows = (await s.execute(select(AgentDataTable))).scalars().all()
        for r in rows:
            r.twitter_access_token_expires_at = now + timedelta(minutes=2)
            if r.twitter_access_token is None:
                r.twitter_access_token = "x"
        await s.commit()


async def snapshot():
    async with dbmod.get_session() as s:
        rows = (
            await s.execute(select(AgentDataTable).order_by(AgentDataTable.id))
        ).scalars().all()
        return [
            (r.id, r.twitter_access_token, r.twitter_refresh_token)
            for r in rows
        ]


async def main():
    await dbmod.init_db(None, None, None, None, None, True)
    oauth2_user_handler.mount("https://api.x.com", FakeXTokenAdapter())
    await seed()
    results = []
    for _ in range(ROUNDS):
        await oauth2_refresh.refresh_expiring_tokens()
        results.append(await snapshot())
        await reset_expiry()
    # also direct calls
    async with dbmod.get_session() as s:
        rows = (await s.execute(select(AgentDataTable).order_by(AgentDataTable.id))).scalars().all()
    for r in rows[:10]:
        await oauth2_refresh.refresh_token(r)
    results.append(await snapshot())
    # nothing expiring -> early-return path
    async with dbmod.get_session() as s:
        for r in (await s.execute(select(AgentDataTable))).scalars().all():
            r.twitter_access_token_expires_at = datetime(2099, 1, 1, tzinfo=timezone.utc)
        await s.commit()
    await oauth2_refresh.refresh_expiring_tokens()
    results.append(await snapshot())
    return results


res = asyncio.run(main())
print("agents:", len(res[-1]))
print(hashlib.sha256(json.dumps(res, default=str).encode()).hexdigest())
