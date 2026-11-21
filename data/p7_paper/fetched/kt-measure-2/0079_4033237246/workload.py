import hashlib, json, os, random, sys
from pathlib import Path

ROOT = Path("/tmp/kt_5798/root")
(ROOT / "data" / "plugins").mkdir(parents=True, exist_ok=True)
(ROOT / ".astrbot").touch()
os.chdir(ROOT)
os.environ["ASTRBOT_ROOT"] = str(ROOT)

rng = random.Random(5798)
WORDS = ["weather", "music", "image", "chat", "game", "rss", "translate", "news",
         "todo", "memo", "bili", "github", "dice", "quiz", "remind", "search"]

ONLINE = {}
for i in range(3000):
    w1, w2 = rng.sample(WORDS, 2)
    ONLINE[f"astrbot_plugin_{w1}_{i}"] = {
        "desc": f"A {w2} helper that does {w1} things #{i}",
        "version": f"1.{i % 10}.{i % 7}",
        "author": rng.choice(["Soulter", "alice", "bob", "carol", "MusicFan"]),
        "repo": f"https://example.invalid/{w1}/{i}",
    }

# local installed plugins
import yaml
for i in range(30):
    d = ROOT / "data" / "plugins" / f"local_{i}"
    d.mkdir(exist_ok=True)
    (d / "metadata.yaml").write_text(yaml.safe_dump({
        "name": f"astrbot_plugin_{WORDS[i % len(WORDS)]}_{i}", "desc": f"local {WORDS[(i*3) % len(WORDS)]}",
        "version": "1.0.0", "author": "local", "repo": f"https://example.invalid/l/{i}"}))

import httpx
import astrbot.cli.utils.plugin as plugutil


class _Resp:
    def raise_for_status(self):
        pass

    def json(self):
        return dict(list(ONLINE.items())[:200])


class _FakeClient:  # stand-in for the network registry fetch
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, **kw):
        return _Resp()


plugutil.httpx = type("httpx_stub", (), {"Client": _FakeClient})

from click.testing import CliRunner
from astrbot.cli.commands.cmd_plug import plug
from astrbot.core.config.i18n_utils import ConfigMetadataI18n
from astrbot.core.config.default import CONFIG_METADATA_2

h = hashlib.sha256()
runner = CliRunner()
queries = ["weather", "music", "Soulter", "game", "nomatch_xyz", "bili", "helper", "alice", "local", "rss"]
for rep in range(1):
    for q in queries:
        r = runner.invoke(plug, ["search", q])
        h.update(r.output.encode())
        h.update(str(r.exit_code).encode())

# i18n conversion including "templates"
def make_meta(n):
    meta = {}
    for g in range(n):
        md = {}
        for s in range(5):
            items = {}
            for f in range(8):
                items[f"f{f}"] = {
                    "description": "d", "hint": "h", "type": "object",
                    "items": {"x": {"description": "dx", "type": "string"}},
                    "templates": {f"t{t}": {"name": "tn", "hint": "th",
                                            "items": {"y": {"description": "dy", "labels": ["a"]}}}
                                  for t in range(4)},
                    "template_schema": {"z": {"description": "dz"}},
                }
            md[f"s{s}"] = {"description": "sd", "items": items}
        meta[f"g{g}"] = {"name": "G", "metadata": md}
    return meta

meta = make_meta(6)
for rep in range(10):
    out = ConfigMetadataI18n.convert_to_i18n_keys(meta)
h.update(json.dumps(out, sort_keys=True, default=str).encode())
out2 = ConfigMetadataI18n.convert_to_i18n_keys(CONFIG_METADATA_2)
h.update(json.dumps(out2, sort_keys=True, default=str).encode())

# dashboard market list with query filtering, served by a local in-process registry
import asyncio, types
from aiohttp import web
from quart import Quart
from astrbot.dashboard.routes.plugin import PluginRoute
from astrbot.dashboard.routes.route import RouteContext

MARKET = {k: dict(v, display_name=k.replace("astrbot_plugin_", "").title()) for k, v in ONLINE.items()}
MD5 = hashlib.md5(json.dumps(MARKET, sort_keys=True).encode()).hexdigest()


async def run_market():
    app = web.Application()

    async def plugins(req):
        return web.json_response(MARKET)

    async def md5(req):
        return web.json_response({"md5": MD5})

    app.router.add_get("/plugins.json", plugins)
    app.router.add_get("/plugins-md5.json", md5)
    runner_ = web.AppRunner(app)
    await runner_.setup()
    site = web.TCPSite(runner_, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    url = f"http://127.0.0.1:{port}/plugins.json"

    qapp = Quart("kt")
    lifecycle = types.SimpleNamespace(astrbot_config={"provider_settings": {"extension_install": {"search_result_limit": 6}}})
    route = PluginRoute(RouteContext(config={}, app=qapp), lifecycle, None)
    results = []
    qs = ["weather", "music", "soulter", "game", "nomatch_xyz", "bili", "helper", "alice", "rss", ""]
    for rep in range(2):
        for i, q in enumerate(qs):
            qstr = f"/api/plugin/market_list?custom_registry={url}&query={q}"
            if i % 3 == 0:
                qstr += "&limit=20"
            if rep == 0 and i == 0:
                qstr += "&force_refresh=true"
            async with qapp.test_request_context(qstr):
                res = await route.get_online_plugins()
            results.append(res)
    await runner_.cleanup()
    return results

res = asyncio.run(run_market())
h.update(json.dumps(res, sort_keys=True, default=str).encode())
print(len(res), [r.get("status") for r in res])
print(h.hexdigest())
