import asyncio, hashlib, json, os, sys, threading, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ["PREFECT_HOME"] = tempfile.mkdtemp(prefix="kt_20973_")
import prefect

HITS = {"n": 0}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        HITS["n"] += 1
        body = json.dumps(prefect.__version__).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/api"

from prefect.settings import PREFECT_API_URL, temporary_settings
from prefect.context import SyncClientContext, AsyncClientContext

N = 150
results = []

async def run_async():
    out = []
    for i in range(N):
        async with AsyncClientContext() as ctx:
            async with ctx:  # reentrant
                out.append(type(ctx.client).__name__)
    return out

with temporary_settings(updates={PREFECT_API_URL: url}):
    for i in range(N):
        with SyncClientContext() as ctx:
            with ctx:
                results.append(type(ctx.client).__name__)
    results.extend(asyncio.run(run_async()))

srv.shutdown()
results.append(f"hits={HITS['n']}")
print(len(results), results[-1])
print(hashlib.sha256("\n".join(results).encode()).hexdigest())
