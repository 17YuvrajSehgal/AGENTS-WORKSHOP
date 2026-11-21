import asyncio, hashlib, json, logging, os, shutil, sys
logging.disable(logging.CRITICAL)
os.environ["NEXUS_DOCKER_NETWORK"] = "kt_net"
for k in ("NEXUS_URL", "NEXUS_DATABASE_URL", "E2B_API_KEY"):
    os.environ.pop(k, None)
import docker.errors  # noqa
import nexus
from nexus.core.sandbox_manager import SandboxManager
from nexus.core.sandbox_docker_provider import DockerSandboxProvider

D = "/tmp/kt_412/data"
shutil.rmtree(D, ignore_errors=True)
os.makedirs(D, exist_ok=True)


# Stand-in for the Docker daemon (external I/O)
class FakeContainer:
    def __init__(self, cid, name):
        self.id = cid
        self.name = name
        self.status = "running"


class FakeContainers:
    def __init__(self):
        self.n = 0
        self.names = []

    def run(self, image, command, detach, name=None, **kw):
        self.n += 1
        self.names.append(name)
        return FakeContainer(hashlib.sha256(str(self.n).encode()).hexdigest(), name)


class FakeImages:
    def get(self, name):
        return object()


class FakeClient:
    def __init__(self):
        self.containers = FakeContainers()
        self.images = FakeImages()


import warnings; warnings.simplefilter("ignore")
nx = nexus.connect(config={"data_dir": D, "mode": "embedded"})
client = FakeClient()
mgr = SandboxManager(db_session=nx.metadata.SessionLocal())
mgr.providers["docker"] = DockerSandboxProvider(docker_client=client, cleanup_interval=3600)
nx._sandbox_manager = mgr

out = []
NAMES = ["my sandbox", "--weird/name!!", "agent_1.test", "___", "ok-name", "été ünïcode"]
N = 250
for i in range(N):
    name = f"{NAMES[i % len(NAMES)]} #{i}" if i % 7 else NAMES[i % len(NAMES)] + f"{i}"
    if i % 11 == 0:
        name = "*" * (i // 11 + 1)  # sanitizes to nothing
    r = nx.sandbox_create(name=name, ttl_minutes=10,
                          context={"user_id": f"user{i % 5}", "tenant_id": "t1"})
    out.append((r["sandbox_id"], r["name"], r["status"]))

for rep in range(20):
    for u in range(5):
        res = nx.sandbox_list(context={"user_id": f"user{u}", "tenant_id": "t1"})
        out.append(sorted(s["sandbox_id"] for s in res["sandboxes"]))
out.append(client.containers.names)

for t in asyncio.all_tasks(nx._get_event_loop()) if hasattr(nx, "_get_event_loop") else []:
    t.cancel()

print(len(out))
print(hashlib.sha256(json.dumps(out, sort_keys=True, default=str).encode()).hexdigest())
