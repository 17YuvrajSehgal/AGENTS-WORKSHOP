# mlflow #19520 "Fix artifact download performance regression".
# Pilot workload (hand-written, experimenter has read the PR): download one
# 128 MB binary artifact through the real route
# GET /api/2.0/mlflow-artifacts/artifacts/<path> with artifact serving
# enabled the way `mlflow server --serve-artifacts` enables it, and stream
# the response. Last line = SHA-256 of the downloaded bytes.
import hashlib
import os
import random
from pathlib import Path

from mlflow.server.constants import ARTIFACTS_DESTINATION_ENV_VAR, SERVE_ARTIFACTS_ENV_VAR

ROOT = Path("/tmp/kt_mlflow_artifacts")
FILE = ROOT / "model" / "weights.bin"
SIZE = 128 * 1024 * 1024
if not FILE.exists():  # created once, deterministic content (seeded random bytes)
    FILE.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    with open(FILE, "wb") as f:
        for _ in range(SIZE // (1 << 20)):
            f.write(rng.randbytes(1 << 20))

os.environ[ARTIFACTS_DESTINATION_ENV_VAR] = str(ROOT)
os.environ[SERVE_ARTIFACTS_ENV_VAR] = "true"

from mlflow.server import app  # noqa: E402

h = hashlib.sha256()
n_chunks = 0
with app.test_client() as client:
    r = client.get("/api/2.0/mlflow-artifacts/artifacts/model/weights.bin", buffered=False)
    assert r.status_code == 200, (r.status_code, r.get_data()[:300])
    for chunk in r.response:
        h.update(chunk)
        n_chunks += 1
    r.close()
    # the PR also refactored the upload handler: exercise it with 16 MB
    up = random.Random(7).randbytes(16 * 1024 * 1024)
    r = client.put("/api/2.0/mlflow-artifacts/artifacts/upload/blob.bin", data=up)
    assert r.status_code == 200, (r.status_code, r.get_data()[:300])
    h.update(hashlib.sha256((ROOT / "upload" / "blob.bin").read_bytes()).digest())
print("chunks", n_chunks)
print(h.hexdigest())
