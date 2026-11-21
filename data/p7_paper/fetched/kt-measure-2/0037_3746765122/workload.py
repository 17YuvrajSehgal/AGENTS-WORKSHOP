import os, hashlib, shutil, random
ROOT = "/tmp/kt_19520"
DEST = os.path.join(ROOT, "artifacts")
shutil.rmtree(DEST, ignore_errors=True)
os.makedirs(DEST, exist_ok=True)
os.environ["_MLFLOW_SERVER_SERVE_ARTIFACTS"] = "true"
os.environ["_MLFLOW_SERVER_ARTIFACT_DESTINATION"] = DEST
from mlflow.server import app, SERVE_ARTIFACTS_ENV_VAR, ARTIFACTS_DESTINATION_ENV_VAR
os.environ[SERVE_ARTIFACTS_ENV_VAR] = "true"
os.environ[ARTIFACTS_DESTINATION_ENV_VAR] = DEST
from mlflow.server import handlers

rng = random.Random(1234)
# text-like data with many short lines and binary data
payloads = []
for i in range(4):
    lines = [("row %d,%d,%f\n" % (j, rng.randint(0, 10**6), rng.random())).encode() for j in range(200000)]
    payloads.append(b"".join(lines))
for i in range(4):
    payloads.append(bytes(rng.getrandbits(8) for _ in range(1_500_000)))

h = hashlib.sha256()
client = app.test_client()
for rep in range(2):
    for i, data in enumerate(payloads):
        p = f"exp/run{i}/file_{i}.bin"
        r = client.put(f"/api/2.0/mlflow-artifacts/artifacts/{p}", data=data)
        assert r.status_code == 200, r.data
        r = client.get(f"/api/2.0/mlflow-artifacts/artifacts/{p}")
        assert r.status_code == 200
        body = r.get_data()
        assert body == data
        h.update(hashlib.sha256(body).digest())
print("files", len(payloads))
print(h.hexdigest())
