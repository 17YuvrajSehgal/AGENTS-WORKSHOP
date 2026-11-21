"""Workload: exercise baml_py.stream.BamlSyncStream / BamlStream iteration
(the changed Python code) against a real baml_py native runtime (PyPI wheel
0.207.1) streaming from a local in-process OpenAI-compatible SSE server."""
import os as _os
_os.environ.setdefault("BAML_LOG", "off")
import asyncio
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SIDE = os.path.basename(os.path.dirname(os.path.abspath(sys.prefix)))
SRC_PKG = os.path.join(HERE, SIDE, "src", "engine", "language_client_python", "python_src")

# Locate the native extension from the installed wheel.
_spec = importlib.util.find_spec("baml_py")
_SO_DIR = list(_spec.submodule_search_locations)[0]
_SO = [f for f in os.listdir(_SO_DIR) if f.startswith("baml_py.") and f.endswith(".so")][0]
_SO = os.path.join(_SO_DIR, _SO)


class _NativeFinder:
    """Load baml_py.baml_py (compiled) from the wheel while the pure-Python
    part of baml_py comes from the source tree under test."""

    @staticmethod
    def find_spec(name, path=None, target=None):
        if name == "baml_py.baml_py":
            loader = importlib.machinery.ExtensionFileLoader(name, _SO)
            return importlib.util.spec_from_file_location(name, _SO, loader=loader)
        return None


sys.meta_path.insert(0, _NativeFinder)
sys.path.insert(0, SRC_PKG)

import baml_py  # noqa: E402
from baml_py import BamlRuntime  # noqa: E402
from baml_py.stream import BamlStream, BamlSyncStream  # noqa: E402

assert os.path.abspath(baml_py.stream.__file__).startswith(SRC_PKG), baml_py.stream.__file__

N_CHUNKS = 200


def make_tokens(i):
    words = []
    x = (i * 7919 + 13) % 1000003
    for k in range(N_CHUNKS):
        x = (x * 1103515245 + 12345) % (2 ** 31)
        words.append("w%d_%d " % (k, x % 997))
    return words


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n))
        msg = body["messages"][-1]["content"]
        if isinstance(msg, list):
            msg = "".join(p.get("text", "") for p in msg)
        idx = int(msg.split("REQ")[1].split()[0])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        for tok in make_tokens(idx):
            chunk = {
                "id": "c", "object": "chat.completion.chunk", "created": 0, "model": "m",
                "choices": [{"index": 0, "delta": {"content": tok}, "finish_reason": None}],
            }
            self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
            self.wfile.flush()
        chunk = {
            "id": "c", "object": "chat.completion.chunk", "created": 0, "model": "m",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
        self.close_connection = True


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--serve":
    # Mock LLM server runs in its own process: the native sync stream holds
    # the GIL while waiting on HTTP, so an in-process Python server would block.
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    sys.stdout.write("%d\n" % server.server_address[1])
    sys.stdout.flush()
    server.serve_forever()
    sys.exit(0)

import subprocess  # noqa: E402

srv_proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--serve"],
                            stdout=subprocess.PIPE, text=True)
port = int(srv_proc.stdout.readline())

BAML = """
client<llm> Local {
  provider openai-generic
  options {
    base_url "http://127.0.0.1:%d"
    model "m"
    api_key "sk-test"
  }
}

function Echo(input: string) -> string {
  client Local
  prompt #"
    {{ _.role("user") }}
    {{ input }}
  "#
}
""" % port

runtime = BamlRuntime.from_files("baml_src", {"baml_src/main.baml": BAML}, {})


import types as _types  # noqa: E402

_Mod = _types.ModuleType("kt_types")


def partial(x):
    return x.cast_to(_Mod, _Mod, _Mod, True, runtime)


def final(x):
    return x.cast_to(_Mod, _Mod, _Mod, False, runtime)


def sync_call(i):
    ctx = runtime.create_context_manager()
    ffi = runtime.stream_function_sync(
        "Echo", {"input": "REQ%d please" % i}, None, ctx, None, None, [], {}, None
    )
    s = BamlSyncStream(ffi, partial, final, ctx)
    last = None
    count = 0
    for p in s:
        last = p
        count += 1
    res = s.get_final_response()
    return res, last, count


async def async_call(i):
    ctx = runtime.create_context_manager()
    ffi = runtime.stream_function(
        "Echo", {"input": "REQ%d please" % i}, None, ctx, None, None, [], {}, None
    )
    s = BamlStream(ffi, partial, final, ctx)
    last = None
    count = 0
    async for p in s:
        last = p
        count += 1
    res = await s.get_final_response()
    return res, last, count


def main():
    h = hashlib.sha256()
    for i in range(60):
        res, last, count = sync_call(i)
        assert count >= 1
        h.update(("S%d:%s|%s\n" % (i, res, last)).encode())

    async def run_async():
        out = []
        for i in range(60, 120):
            out.append(await async_call(i))
        return out

    for j, (res, last, count) in enumerate(asyncio.run(run_async())):
        assert count >= 1
        h.update(("A%d:%s|%s\n" % (j, res, last)).encode())
    print("streams completed: 120")
    print(h.hexdigest())


try:
    main()
finally:
    srv_proc.terminate()
    srv_proc.wait()
