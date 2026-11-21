# prefect #21115 "fix: skip no-op SQL filters for empty values to speed up
# deployment pagination". Pilot workload (hand-written, experimenter has read
# the PR): an in-process Prefect server (create_app(ephemeral=True), as in
# Prefect's own tests) on a SQLite file with 2,000 deployments (created once
# per environment), then POST /deployments/paginate 40 times with the empty
# filters the PR changes (like_="" on flow-or-deployment name and on name,
# tags all_=[]). Last line = SHA-256 over the returned deployment names
# (ids are random per database, so they cannot be compared across versions).
import hashlib
import os
import sys
from pathlib import Path

env_tag = hashlib.sha256(sys.prefix.encode()).hexdigest()[:8]  # one DB per venv
home = Path(f"/tmp/kt_prefect_{env_tag}")
home.mkdir(exist_ok=True)
os.environ["PREFECT_HOME"] = str(home)
os.environ["PREFECT_API_DATABASE_CONNECTION_URL"] = f"sqlite+aiosqlite:///{home}/prefect.db"
os.environ["PREFECT_SERVER_ANALYTICS_ENABLED"] = "false"
os.environ["PREFECT_LOGGING_LEVEL"] = "ERROR"

from fastapi.testclient import TestClient  # noqa: E402

from prefect.server.api.server import create_app  # noqa: E402

app = create_app(ephemeral=True)
FILTERS = [
    {"deployments": {"flow_or_deployment_name": {"like_": ""}}},
    {"deployments": {"name": {"like_": ""}}},
    {"deployments": {"tags": {"all_": []}}},
]
with TestClient(app, base_url="https://test/api") as c:
    marker = home / "seeded"
    if not marker.exists():
        for i in range(200):
            flow_id = c.post("/flows/", json={"name": f"flow-{i}"}).json()["id"]
            for j in range(10):
                r = c.post("/deployments/", json={"name": f"dep-{i}-{j}", "flow_id": flow_id,
                                                   "tags": [f"t{j}"]})
                assert r.status_code in (200, 201), r.text[:300]
        marker.touch()
    h = hashlib.sha256()
    total = 0
    for _ in range(40):
        for f in FILTERS:
            r = c.post("/deployments/paginate", json={**f, "limit": 200, "page": 1})
            assert r.status_code == 200, r.text[:300]
            body = r.json()
            total += body["count"]
            h.update(",".join(sorted(d["name"] for d in body["results"])).encode())
print(total)
print(h.hexdigest())
