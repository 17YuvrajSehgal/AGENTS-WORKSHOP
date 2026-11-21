"""Workload for Shannon PR 125 (llm-service web tools + agent helpers).

Runs WebCrawlTool / WebSubpageFetchTool / FirecrawlFetchProvider end to end
with a local in-process stand-in for the Firecrawl HTTP API (aiohttp client
replaced by a fake that never touches the network), then feeds the tool
outputs into agent.aggregate_tool_results / generate_tool_digest.
"""
import asyncio
import hashlib
import json
import logging
import os
import random
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(sys.executable))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), "src", "python", "llm-service")
sys.path.insert(0, SRC)
os.environ["FIRECRAWL_API_KEY"] = "fc-0123456789abcdef"
logging.disable(logging.CRITICAL)

import aiohttp  # noqa: E402

from llm_service.api import agent as agent_mod  # noqa: E402
from llm_service.roles import presets  # noqa: E402
from llm_service.tools.builtin import web_crawl, web_fetch, web_subpage_fetch  # noqa: E402

WORDS = ("company platform revenue growth team leadership product launch customers "
         "funding investors series announcement market data analytics engineering "
         "research model latency pricing enterprise partner global office report").split()


def make_markdown(url: str, n_paras: int = 30) -> str:
    rng = random.Random(zlib.crc32(url.encode()))
    out = [f"# Page for {url}", ""]
    for i in range(n_paras):
        sent = " ".join(rng.choice(WORDS) for _ in range(rng.randint(20, 60)))
        k = i % 9
        if k == 0:
            sent += f" ![Logo of the company {i}](https://cdn.example.org/img/{i}.png \"logo\")"
        elif k == 1:
            sent += f" [![Banner image alt text](https://cdn.example.org/b{i}.jpg)](https://example.org/x{i})"
        elif k == 2:
            sent += " ![x](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==)"
        elif k == 3:
            sent += f" Contact [sales](mailto:sales{i}@example.org) or [call](tel:+1555000{i}) see [top](#top) <https://example.org/p{i}>"
        elif k == 4:
            sent += f" <img src=\"/a{i}.png\" alt=\"Team photo at headquarters\"> <img src=\"/b.png\" alt=\"x\"> [ ](https://e.org/empty)"
        elif k == 5:
            sent += f"\n\n```python\nprint('![keep](me)')  # code {i}\n```\n\nInline `![also](kept)` code."
        elif k == 6:
            sent += f"\n\n[ref{i}]: https://example.org/ref{i}\n![alt ref][ref{i}]"
        elif k == 7:
            sent += f" Read [the full article](https://example.org/article/{i}) for more."
        out.append(sent)
        out.append("\n\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Stand-in for the Firecrawl HTTP API (network client replacement only)
# ---------------------------------------------------------------------------
SITES = {}  # host -> list of page urls
ERROR_HOSTS = set()


def site_pages(base: str, n: int, seed: int):
    rng = random.Random(seed)
    sections = ["about", "team", "blog", "news", "press", "careers", "contact", "pricing",
                "products", "docs", "legal", "ir", "investors", "leadership", "company",
                "features", "solutions", "random", "misc", "help", "sitemap.xml", "tag",
                "login", "cart", "category", "funding", "api", "developer"]
    pages = [base + "/"]
    for i in range(n):
        depth = rng.randint(1, 4)
        segs = [rng.choice(sections) for _ in range(depth)]
        segs[-1] = segs[-1] + (f"-{i}" if rng.random() < 0.7 else "")
        pages.append(base + "/" + "/".join(segs))
    return pages


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload

    async def text(self):
        return json.dumps(self._payload)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def page_markdown(u: str) -> str:
    host = u.split("/")[2]
    if host in ERROR_HOSTS and u.rstrip("/").count("/") == 2:
        return "404 Not Found\n\nThe page you requested was not found."
    return make_markdown(u, 18)


class FakeSession:
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def close(self):
        pass

    def post(self, url, json=None, headers=None, **kw):
        if url.endswith("/v1/map"):
            host = json["url"].split("/")[2]
            return FakeResponse(200, {"success": True, "links": list(SITES.get(host, []))})
        if url.endswith("/v1/scrape"):
            u = json["url"]
            return FakeResponse(200, {"success": True, "data": {
                "markdown": page_markdown(u),
                "metadata": {"url": u, "title": "Title " + u.split("/")[-1]}}})
        if url.endswith("/v1/crawl"):
            host = json["url"].split("/")[2]
            return FakeResponse(200, {"id": "crawl::" + host + "::" + str(json.get("limit"))})
        return FakeResponse(404, {"error": "unknown"})

    def get(self, url, headers=None, **kw):
        if "/v1/crawl/" in url:
            _, host, limit = url.rsplit("/", 1)[1].split("::")
            pages = SITES.get(host, [])
            # Firecrawl may return more than limit + duplicates
            data = []
            for u in pages + pages[:3]:
                data.append({"markdown": page_markdown(u),
                             "metadata": {"url": u, "title": "Crawl " + u.split("/")[-1]}})
            return FakeResponse(200, {"status": "completed", "data": data})
        return FakeResponse(404, {"error": "unknown"})


aiohttp.ClientSession = FakeSession


def setup_sites():
    hosts = ["93.184.216.%d" % i for i in range(10, 16)]
    for i, h in enumerate(hosts):
        SITES[h] = site_pages("https://" + h, 60 + 10 * i, i)
    ERROR_HOSTS.add(hosts[-1])
    return hosts


async def run_tools(hosts):
    crawl = web_crawl.WebCrawlTool()
    sub = web_subpage_fetch.WebSubpageFetchTool()
    prov = web_fetch.FirecrawlFetchProvider(os.environ["FIRECRAWL_API_KEY"])
    records = []
    outs = []
    for i, h in enumerate(hosts):
        base = "https://" + h
        r = await crawl._execute_impl(url=base, limit=8 + i, max_length=6000)
        outs.append(r.output)
        records.append({"tool": "web_crawl", "success": r.success, "output": r.output,
                        "error": r.error, "tool_input": {"url": base}})
        r1 = await crawl._execute_impl(url=base + "/about", limit=1, max_length=4000)
        outs.append(r1.output)
        for kw in ("about team funding news products", "investor api"):
            r = await sub._execute_impl(url=base, limit=10, target_keywords=kw, max_length=5000)
            outs.append(r.output)
            records.append({"tool": "web_subpage_fetch", "success": r.success, "output": r.output,
                            "error": r.error, "tool_input": {"url": base}})
        f = await prov.fetch(base + "/blog/post-%d" % i, max_length=8000)
        outs.append(f)
        records.append({"tool": "web_fetch", "success": True, "output": f,
                        "tool_input": {"url": base + "/blog"}})
        records.append({"tool": "web_fetch", "success": False, "output": None,
                        "error": "timeout after 30s", "tool_input": {"url": base + "/slow"}})
        records.append({"tool": "web_search", "success": False, "output": None,
                        "error": "", "tool_input": {"query": "company %d funding" % i}})
    return outs, records


def main():
    hosts = setup_sites()
    h = hashlib.sha256()
    sub = web_subpage_fetch.WebSubpageFetchTool()
    for host, pages in SITES.items():
        for u in pages:
            h.update(("%.6f" % sub._calculate_relevance_score(u, "", len(pages))).encode())

    for rep in range(3):
        outs, records = asyncio.run(run_tools(hosts))
        for o in outs:
            h.update(json.dumps(o, sort_keys=True, default=str).encode())
        agg = agent_mod.aggregate_tool_results(records, max_chars=400000)
        h.update(agg.encode())
        dig = agent_mod.generate_tool_digest(json.dumps(records[:3], default=str), records, max_chars=20000)
        h.update(dig.encode())
        dig2 = agent_mod.generate_tool_digest("raw\\nresult\\t{x: [1,2]}", [], max_chars=500)
        h.update(dig2.encode())
        msgs = agent_mod.build_interpretation_messages("sys", "query", agg[:2000])
        h.update(json.dumps(msgs).encode())
    for role in ("research", "deep_research_agent"):
        try:
            h.update(json.dumps(presets.get_role_preset(role), sort_keys=True, default=str).encode())
        except Exception as e:
            h.update(repr(e).encode())
    print("aggregate_len", len(agg), "digest_len", len(dig))
    print(h.hexdigest())


if __name__ == "__main__":
    main()
