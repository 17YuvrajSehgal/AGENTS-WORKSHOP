"""Workload for github_agents board CLI / BoardManager (PR 202).

A local in-process HTTP server stands in for the GitHub GraphQL API.
"""

import asyncio
import contextlib
import hashlib
import io
import json
import logging
import os
import random
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORK = "/tmp/kt_202"
os.makedirs(WORK, exist_ok=True)
os.chdir(WORK)
with open("ai-agents-board.yml", "w") as f:
    f.write("project:\n  number: 1\n  owner: octo\nrepository: octo/repo\nexclude_labels:\n  - wontfix\n")
with open(".agents.yaml", "w") as f:
    f.write("security:\n  agent_admins:\n    - admin1\n")
os.environ["GITHUB_TOKEN"] = "dummy"
os.environ.pop("GITHUB_PROJECTS_TOKEN", None)

from github_agents.board import cli  # noqa: E402
from github_agents.board.manager import BoardManager  # noqa: E402

rng = random.Random(1234)
N_ITEMS = 100
STATUSES = ["Todo", "Todo", "Todo", "Blocked", "In Progress", "Done"]
PRIOS = ["Critical", "High", "Medium", "Low", None]
AGENTS = [None, None, "Claude Code", "Gemini CLI", "Codex"]
LABELS = ["bug", "enhancement", "docs", "wontfix", "agent-task", "security"]

ITEMS = []
COMMENTS = {}
APPROVAL = {}
for n in range(1, N_ITEMS + 1):
    fv = []
    st = rng.choice(STATUSES)
    fv.append({"name": st, "field": {"name": "Status"}})
    p = rng.choice(PRIOS)
    if p:
        fv.append({"name": p, "field": {"name": "Priority"}})
    a = rng.choice(AGENTS)
    if a:
        fv.append({"name": a, "field": {"name": "Agent"}})
    if rng.random() < 0.1:
        fv.append({"text": str(rng.randint(1, N_ITEMS)), "field": {"name": "Blocked By"}})
    labels = rng.sample(LABELS, rng.randint(0, 3))
    ITEMS.append(
        {
            "id": f"ITEM_{n}",
            "fieldValues": {"nodes": fv},
            "content": {
                "number": n,
                "title": f"Issue {n}",
                "body": "body",
                "state": "OPEN" if rng.random() < 0.9 else "CLOSED",
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-02T00:00:00Z",
                "url": f"https://example.invalid/{n}",
                "labels": {"nodes": [{"name": x} for x in labels]},
                "repository": {"owner": {"login": "octo"}, "name": "repo"},
            },
        }
    )
    comments = []
    r = rng.random()
    if r < 0.15:
        ag = rng.choice(["claude", "gemini"])
        comments.append(
            {
                "id": f"C{n}",
                "body": f"🤖 **[Agent Claim]**\n\nAgent: `{ag}`\nStarted: `2099-01-01T00:00:00Z`\nSession ID: `s{n}`\n",
                "createdAt": "2099-01-01T00:00:00Z",
                "author": {"login": "bot"},
            }
        )
    COMMENTS[n] = comments
    ar = rng.random()
    if ar < 0.3:
        body = "[Approved][Claude] go ahead"
    elif ar < 0.5:
        body = "Reply with `[Approved]` to create PR"
    elif ar < 0.6:
        body = "[Review][Gemini CLI]"
    else:
        body = "just a comment"
    author = rng.choice(["octo", "admin1", "random_user"])
    APPROVAL[n] = {
        "body": "issue body",
        "author": {"login": "someone"},
        "comments": {"nodes": [{"body": "lgtm", "author": {"login": "x"}}, {"body": body, "author": {"login": author}}]},
    }

STATUS_FIELD = {
    "id": "F_STATUS",
    "options": [{"id": f"O_{s}", "name": s} for s in ["Todo", "In Progress", "Blocked", "Done", "Abandoned"]],
}
BAD = 9999


def answer(query, variables):
    m = re.search(r"(query|mutation)\s+(\w+)", query)
    name = m.group(2) if m else ""
    num = (variables or {}).get("number")
    if name == "GetProject":
        return {"user": {"projectV2": {"id": "PROJ_1", "title": "Board"}}, "organization": None}
    if name in ("GetProjectItems", "GetProjectItem"):
        return {"node": {"items": {"nodes": ITEMS}, "field": STATUS_FIELD}}
    if num == BAD:
        return {"repository": None}
    if name == "GetIssueComments":
        return {"repository": {"issue": {"comments": {"nodes": COMMENTS.get(num, [])}}}}
    if name == "GetIssueForApproval":
        return {"repository": {"issue": APPROVAL.get(num, {"body": "", "author": {"login": ""}, "comments": {"nodes": []}})}}
    if name == "GetIssueId":
        return {"repository": {"issue": {"id": f"ISSUE_{num}"}}}
    if name == "AddComment":
        return {"addComment": {"commentEdge": {"node": {"id": "X", "createdAt": "2025-01-01T00:00:00Z"}}}}
    if name in ("UpdateProjectField", "UpdateField"):
        return {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "ITEM"}}}
    return {"unknown": None}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(ln))
        data = json.dumps({"data": answer(payload["query"], payload.get("variables"))}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
# Point the client at the local stand-in instead of api.github.com
BoardManager.GITHUB_API_URL = f"http://127.0.0.1:{server.server_address[1]}/graphql"

logging.disable(logging.CRITICAL)
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def run_cli(argv):
    sys.argv = ["board-cli"] + argv
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            cli.main()
        except SystemExit as e:
            code = e.code
    logging.disable(logging.CRITICAL)
    return f"{argv}|{code}|" + UUID_RE.sub("<uuid>", buf.getvalue())


results = []
ready_variants = [
    [],
    ["--agent", "claude"],
    ["--agent", "gemini"],
    ["--agent", "codex", "--limit", "5"],
    ["--agent", "claude", "--priority", "high"],
    ["--priority", "medium", "--limit", "50"],
    ["--agent", "Claude Code", "--limit", "100"],
]
for rep in range(2):
    for v in ready_variants:
        results.append(run_cli(["--json", "ready"] + v))
        results.append(run_cli(["ready"] + v))

for n in (3, 7, 12, 21, BAD):
    results.append(run_cli(["--json", "claim", str(n), "--agent", "claude"]))
    results.append(run_cli(["claim", str(n), "--agent", "gemini"]))
for n, reason in ((3, "completed"), (7, "blocked"), (12, "abandoned"), (21, "error"), (BAD, "completed")):
    results.append(run_cli(["--json", "release", str(n), "--agent", "claude", "--reason", reason]))
    results.append(run_cli(["release", str(n), "--agent", "claude", "--reason", reason]))


def run_cmd(coro_fn, **kw):
    import argparse
    ns = argparse.Namespace(**kw)
    buf = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf):
        try:
            asyncio.run(coro_fn(ns))
        except SystemExit as e:
            code = e.code
    return f"{sorted(kw.items())}|{code}|" + UUID_RE.sub("<uuid>", buf.getvalue())


ready_ns = [
    dict(agent="claude", priority=None, limit=10, include_labels=["bug", "enhancement"], exclude_labels=None),
    dict(agent=None, priority=None, limit=20, include_labels=None, exclude_labels=["security", "docs"]),
    dict(agent="gemini", priority="high", limit=5, include_labels=["agent-task"], exclude_labels=["bug"]),
    dict(agent="claude", priority=None, limit=5, include_labels=None, exclude_labels=None, approved_only=True),
    dict(agent=None, priority="low", limit=8, include_labels=["bug"], exclude_labels=None, approved_only=True),
]
for js in (True, False):
    for kw in ready_ns:
        results.append(run_cmd(cli.cmd_ready, json=js, **kw))
    for n in (5, 9, BAD):
        results.append(run_cmd(cli.cmd_claim, json=js, issue=n, agent="claude", session="sess-fixed"))
        results.append(run_cmd(cli.cmd_claim, json=js, issue=n, agent="codex", session=None))
        results.append(run_cmd(cli.cmd_release, json=js, issue=n, agent="claude", reason="blocked"))


async def direct():
    out = []
    async with BoardManager(config=cli.load_config("ai-agents-board.yml"), github_token="dummy") as m:
        for agent in (None, "claude", "gemini", "codex", "crush"):
            issues = await m.get_ready_work(agent_name=agent, limit=100)
            out.append((agent, [(i.number, i.agent, i.priority.value) for i in issues]))
        for n in range(1, N_ITEMS + 1):
            out.append(("approved", n, await m.is_issue_approved(n)))
        texts = [
            "[Approved]",
            "[Approved][Claude]",
            "reply with `[Approved]` to create PR",
            "[review][gemini cli] please",
            "[Close][github-actions]",
            "[Summarize]",
            "[Debug][Codex] x",
            "no trigger here",
        ]
        cnt = 0
        for _ in range(30):
            for t in texts:
                for author in ("octo", "admin1", "nobody"):
                    cnt += m._check_approval_trigger(t, author)
        out.append(("triggers", cnt, [m._check_approval_trigger(t, "octo") for t in texts]))
    return out


results.append(repr(asyncio.run(direct())))
server.shutdown()

blob = "\n".join(results)
print(f"entries={len(results)} bytes={len(blob)}")
print(hashlib.sha256(blob.encode()).hexdigest())
