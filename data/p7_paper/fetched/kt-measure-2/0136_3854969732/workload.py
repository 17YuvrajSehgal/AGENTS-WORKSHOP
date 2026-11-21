"""Workload: exercise NotebookLMClient against a local fake NotebookLM HTTP server.

Works on both base (sync client) and head (async client): any coroutine
returned by a client method is awaited on one persistent event loop.
"""
import asyncio
import hashlib
import inspect
import json
import os
import random
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("HOME", "/tmp/kt_16")
os.makedirs("/tmp/kt_16", exist_ok=True)

from notebooklm_mcp.api_client import NotebookLMClient as C  # noqa: E402

rng = random.Random(1234)


def make_notebooks(n):
    out = []
    for i in range(n):
        sources = [[[f"src-{i}-{j}"], f"Source {i}.{j}", [None, None, None, None, 5]] for j in range(5)]
        meta = [1 if i % 3 else 2, bool(i % 2), True, None, None, [1700000000 + i, 0], None, None, [1690000000 + i, 0]]
        out.append([f"Notebook {i}", sources, f"nb-{i:04d}", None, None, meta])
    return out


NOTEBOOKS = make_notebooks(200)
NB_DETAIL = [["Notebook 0", [[[f"src-0-{j}"], f"Source 0.{j}", [None] * 8] for j in range(10)], "nb-0000"]]
SUMMARY = [["This is a summary of the notebook " * 5], [[[f"Q{k}?", f"Prompt {k}"] for k in range(10)]]]
GUIDE = [[[None, ["Guide summary text"], [["kw1", "kw2", "kw3"]]]]]
FULLTEXT = [[["src-x"], "Full text title", [None, None, None, None, 5, None, None, ["https://example.com/a"]]],
            None, None, [[[0, 10, [["para " + str(k) * 20, [["nested text " + str(k)]]]]] for k in range(50)]]]


def rpc_result(rpc_id):
    if rpc_id == C.RPC_LIST_NOTEBOOKS:
        return [NOTEBOOKS]
    if rpc_id == C.RPC_GET_NOTEBOOK:
        return NB_DETAIL
    if rpc_id == C.RPC_GET_SUMMARY:
        return SUMMARY
    if rpc_id == C.RPC_GET_SOURCE_GUIDE:
        return GUIDE
    if rpc_id == C.RPC_GET_SOURCE:
        return FULLTEXT
    if rpc_id == C.RPC_CREATE_NOTEBOOK:
        return ["New", None, "nb-new-0001"]
    return [[]]


def batch_body(rpc_id):
    payload = json.dumps([["wrb.fr", rpc_id, json.dumps(rpc_result(rpc_id)), None, None, None, "generic"]])
    return f")]}}'\n\n{len(payload)}\n{payload}\n25\n[[\"e\",4,null,null,123]]\n"


def query_body():
    lines = [")]}'", ""]
    for k in range(30):
        typ = 1 if k % 3 else 2
        text = ("Answer chunk %d " % k) * (k + 3)
        inner = json.dumps([[text, None, [], None, [[], None, None, None, typ]]])
        payload = json.dumps([["wrb.fr", None, inner]])
        lines.append(str(len(payload)))
        lines.append(payload)
    return "\n".join(lines) + "\n"


QUERY_BODY = query_body().encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        u = urllib.parse.urlparse(self.path)
        if u.path.endswith("GenerateFreeFormStreamed"):
            body = QUERY_BODY
        else:
            q = urllib.parse.parse_qs(u.query)
            body = batch_body(q.get("rpcids", [""])[0]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{port}"

loop = asyncio.new_event_loop()


def run(x):
    if inspect.isawaitable(x):
        return loop.run_until_complete(x)
    return x


client = C(cookies={"SID": "abc", "HSID": "def"}, csrf_token="tok", session_id="sess")
# Redirect external endpoints to the local stand-in server.
client.BASE_URL = BASE
client.BATCHEXECUTE_URL = f"{BASE}/_/LabsTailwindUi/data/batchexecute"

results = []
for it in range(250):
    nbs = run(client.list_notebooks())
    results.append([(n.id, n.title, n.source_count, n.is_owned) for n in nbs][:: 17])
    results.append(run(client.get_notebook_summary(f"nb-{it:04d}")))
    results.append(run(client.get_source_guide(f"src-{it}")))
    ft = run(client.get_source_fulltext(f"src-{it}"))
    results.append((ft["title"], ft["char_count"], ft["url"]))
    nb = run(client.create_notebook(f"Created {it}"))
    results.append(nb.id if nb else None)
    results.append(run(client.rename_notebook("nb-0001", f"Renamed {it}")))
    r = run(client.query("nb-0000", f"Question {it}?"))
    cid = r["conversation_id"]
    r2 = run(client.query("nb-0000", f"Follow up {it}?", conversation_id=cid))
    results.append((r["answer"][:50], r["turn_number"], r2["turn_number"], r2["is_follow_up"]))
    h = run(client.get_conversation_history(cid))
    results.append([t["turn"] for t in h])
    results.append(run(client.clear_conversation(cid)))
    results.append(run(client.clear_conversation(cid)))
    results.append(run(client.get_notebook("nb-0000")) is not None)

# Exercise the MCP server tool handlers through the same client.
import notebooklm_mcp.server as server  # noqa: E402

server._client = client
TOOL_CALLS = [
    ("notebook_list", dict(max_results=50)),
    ("notebook_create", dict(title="T")),
    ("notebook_get", dict(notebook_id="nb-0000")),
    ("notebook_describe", dict(notebook_id="nb-0000")),
    ("source_describe", dict(source_id="src-1")),
    ("source_get_content", dict(source_id="src-1")),
    ("notebook_add_url", dict(notebook_id="nb-0000", url="https://example.com/x")),
    ("notebook_add_text", dict(notebook_id="nb-0000", text="hello world", title="t")),
    ("notebook_add_drive", dict(notebook_id="nb-0000", document_id="doc1", title="d")),
    ("notebook_query", dict(notebook_id="nb-0000", query="What?")),
    ("notebook_query", dict(notebook_id="nb-0000", query="What?", source_ids='["src-0-0","src-0-1"]')),
    ("notebook_delete", dict(notebook_id="nb-0001", confirm=True)),
    ("notebook_delete", dict(notebook_id="nb-0001", confirm=False)),
    ("notebook_rename", dict(notebook_id="nb-0001", new_title="R")),
    ("chat_configure", dict(notebook_id="nb-0000", goal="custom", custom_prompt="be brief", response_length="longer")),
    ("chat_configure", dict(notebook_id="nb-0000")),
    ("source_list_drive", dict(notebook_id="nb-0000")),
    ("source_sync_drive", dict(source_ids=["src-0-0", "src-0-1"], confirm=True)),
    ("source_delete", dict(source_id="src-0-0", confirm=True)),
    ("research_start", dict(query="topic", notebook_id="nb-0000")),
    ("research_start", dict(query="topic", mode="deep")),
    ("research_status", dict(notebook_id="nb-0000", max_wait=0)),
    ("research_import", dict(notebook_id="nb-0000", task_id="task1")),
    ("audio_overview_create", dict(notebook_id="nb-0000", confirm=True)),
    ("video_overview_create", dict(notebook_id="nb-0000", confirm=True)),
    ("studio_status", dict(notebook_id="nb-0000")),
    ("studio_delete", dict(notebook_id="nb-0000", artifact_id="a1", confirm=True)),
    ("infographic_create", dict(notebook_id="nb-0000", confirm=True)),
    ("slide_deck_create", dict(notebook_id="nb-0000", confirm=True)),
    ("report_create", dict(notebook_id="nb-0000", confirm=True)),
    ("report_create", dict(notebook_id="nb-0000", report_format="Create Your Own", custom_prompt="x", confirm=True)),
    ("flashcards_create", dict(notebook_id="nb-0000", confirm=True)),
    ("quiz_create", dict(notebook_id="nb-0000", confirm=True)),
    ("data_table_create", dict(notebook_id="nb-0000", description="table", confirm=True)),
    ("mind_map_create", dict(notebook_id="nb-0000", confirm=True)),
]


def scrub(o):
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items() if "time" not in k and k != "conversation_id"}
    if isinstance(o, list):
        return [scrub(v) for v in o]
    return o


for it in range(20):
    for name, kw in TOOL_CALLS:
        res = run(getattr(server, name).fn(**kw))
        results.append((name, scrub(res)))

close = getattr(client, "close", None)
if close is not None:
    run(close())
elif client._client is not None:
    client._client.close()
srv.shutdown()

print(len(results))
print(hashlib.sha256(json.dumps(results, sort_keys=True, default=str).encode()).hexdigest())
