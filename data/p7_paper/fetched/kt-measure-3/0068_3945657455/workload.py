"""Workload for nexus PR: session_factory DI for OAuthCrypto/TokenManager,
PKCE store in OAuthService, AsyncSemanticSearch engine ownership, ReBACManager."""

import asyncio
import hashlib
import logging
import os
import shutil
import warnings
from datetime import UTC, datetime, timedelta

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nexus.search.async_search import AsyncSemanticSearch
from nexus.server.auth.oauth_crypto import OAuthCrypto
from nexus.server.auth.oauth_provider import OAuthCredential
from nexus.server.auth.token_manager import TokenManager
from nexus.services.oauth_service import OAuthService
from nexus.services.permissions.rebac_manager import ReBACManager
from nexus.storage.models import Base

WORK = "/tmp/kt_1622"
shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(WORK, exist_ok=True)
for k in ("NEXUS_OAUTH_ENCRYPTION_KEY",):
    os.environ.pop(k, None)

out = []


# ---- Stand-ins for external OAuth providers (network clients) ----
class FakeProvider:
    def __init__(self, name, redirect_uri):
        self.provider_name = name
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state):
        return f"https://auth.example/{self.provider_name}?redirect={self.redirect_uri}&state={state}"

    def get_authorization_url_with_pkce(self, state):
        verifier = hashlib.sha256(state.encode()).hexdigest()
        return (
            f"https://auth.example/{self.provider_name}/pkce?state={state}",
            {"code_verifier": verifier, "code_challenge": verifier[:16],
             "code_challenge_method": "S256"},
        )

    def _cred(self, code, extra=""):
        return OAuthCredential(
            access_token=f"at-{code}{extra}",
            refresh_token=f"rt-{code}",
            token_type="Bearer",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=["s1"],
            provider=self.provider_name,
        )

    async def exchange_code(self, code):
        return self._cred(code)

    async def exchange_code_pkce(self, code, verifier):
        return self._cred(code, "-" + verifier[:8])


class Cfg:
    def __init__(self, pkce):
        self.requires_pkce = pkce


class FakeFactory:
    def get_provider_config(self, name):
        return Cfg(name == "x")

    def create_provider(self, name, redirect_uri=None, scopes=None):
        return FakeProvider(name, redirect_uri)


db_file = os.path.join(WORK, "nexus.db")
db_url = f"sqlite:///{db_file}"
engine = create_engine(db_url, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
sf = sessionmaker(bind=engine)

# ---- OAuthCrypto via db_url (changed code path in both) ----
crypto0 = OAuthCrypto(db_url=db_url)
tok = crypto0.encrypt_token("seed-token")
for i in range(40):
    c = OAuthCrypto(db_url=db_url)
    out.append(c.decrypt_token(tok))

# ---- TokenManager with session_factory (+db_url for base compatibility) ----
tms = []
for i in range(30):
    tm = TokenManager(session_factory=sf, db_url=db_url)
    out.append(tm.crypto.decrypt_token(tok))
    tms.append(tm)
tm = tms[0]


# ---- OAuthService PKCE + exchange flow ----
async def oauth_flow():
    svc = OAuthService(oauth_factory=FakeFactory(), token_manager=tm)
    for i in range(60):
        prov = "x" if i % 2 == 0 else "google"
        auth = await svc.oauth_get_auth_url(prov, redirect_uri="http://localhost/cb")
        out.append(("pkce_data" in auth, auth["url"].split("?")[0]))
        res = await svc.oauth_exchange_code(
            provider=prov, code=f"code{i}", user_email=f"user{i % 7}@ex.com",
            state=auth["state"],
        )
        out.append((res["success"], res["user_email"]))
        if prov == "x":
            try:
                await svc.oauth_exchange_code(
                    provider=prov, code="again", user_email="u@ex.com", state=auth["state"])
                out.append("reuse-ok")
            except ValueError as e:
                out.append("reuse-err:" + str(e)[:20])
    for i in range(20):
        try:
            await svc.oauth_exchange_code(provider="x", code="c", user_email="u@ex.com",
                                          state=f"missing-{i}")
        except ValueError as e:
            out.append(str(e)[:30])
    for i in range(7):
        t = await tm.get_valid_token("x", f"user{i}@ex.com")
        out.append(t.split("-")[0])


asyncio.run(oauth_flow())


# ---- AsyncSemanticSearch engine creation / close ----
async def search_flow():
    for i in range(40):
        s = AsyncSemanticSearch(database_url=f"sqlite:///{WORK}/search{i % 3}.db")
        out.append(s.engine is not None)
        await s.close()


asyncio.run(search_flow())

# ---- SearchDaemon DB pool + FTS / semantic queries (sqlite) ----
from nexus.search.daemon import DaemonConfig, SearchDaemon


class FakeEmbedder:  # stand-in for remote embedding API
    async def embed_text(self, text):
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h[:8]]


async def daemon_flow():
    dbu = f"sqlite:///{WORK}/daemon.db"
    for i in range(15):
        d = SearchDaemon(DaemonConfig(database_url=dbu, db_pool_min_size=2, db_pool_max_size=4))
        d._embedding_provider = FakeEmbedder()
        await d._init_database_pool()
        out.append(d.stats.db_pool_size)
        for q in ("auth token", "search index"):
            out.append(len(await d._search_fts(q, 5, None)))
            out.append(len(await d._search_fts(q, 5, "/src")))
            out.append(len(await d._semantic_search(q, 5, None)))
        await d.shutdown()
        out.append(len(await d._search_fts("after", 5, None)))


asyncio.run(daemon_flow())

# ---- ReBACManager construction ----
for i in range(10):
    m = ReBACManager(engine)
    out.append(type(m).__name__)

print(len(out))
print(hashlib.sha256(repr(out).encode()).hexdigest())
