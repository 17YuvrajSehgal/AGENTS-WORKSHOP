import hashlib, io, json, os, shutil, urllib.request
from pathlib import Path
from rich.console import Console

import nao_core.version as v
from nao_core.ui import UI

base_dir = Path("/tmp/kt_488")
shutil.rmtree(base_dir, ignore_errors=True)
base_dir.mkdir(parents=True)
v.CACHE_FILE = base_dir / ".nao" / "version_check.json"

buf = io.StringIO()
UI._console = Console(file=buf, width=200, color_system=None)

# Stand-in for the network (PyPI) -- external I/O only.
STATE = {"version": "0.0.1", "fail": False}

class _Resp:
    def __init__(self, body): self._b = body
    def read(self): return self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False

def fake_urlopen(url, timeout=None):
    if STATE["fail"]:
        raise OSError("offline")
    return _Resp(json.dumps({"info": {"version": STATE["version"]}}).encode())

urllib.request.urlopen = fake_urlopen

def wait_bg():
    t = getattr(v, "_background_thread", None)
    if t is not None:
        t.join()

results = []
N = 4000
for i in range(N):
    STATE["version"] = f"0.{i % 3}.{i % 50}"
    STATE["fail"] = (i % 7 == 0)
    v.clear_version_cache()
    v.check_for_updates()          # cache miss -> fetch
    wait_bg()
    exists = v.CACHE_FILE.exists()
    cached = json.loads(v.CACHE_FILE.read_text())["latest"] if exists else None
    v.check_for_updates()          # cache hit (maybe warn)
    wait_bg()
    try:
        latest = v.get_latest_version()
    except Exception as e:
        latest = "ERR"
    results.append((exists, cached, latest, v.parse_version(STATE["version"])))

out = buf.getvalue()
print(len(out.splitlines()), "warn lines")
h = hashlib.sha256(json.dumps(results).encode() + out.encode()).hexdigest()
print(h)
