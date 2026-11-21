import os, sys, json, hashlib, random
WD = "/tmp/kt_46/run"
import shutil
SRC = os.path.join(os.path.dirname(sys.prefix), "src")
sys.path.insert(0, SRC)
shutil.rmtree(WD, ignore_errors=True)
os.makedirs(WD, exist_ok=True)
os.chdir(WD)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import main
    main.init_database()
    main.run_schema_migrations()

rng = random.Random(46)
db = main.get_db()
cur = db.cursor()
NOW = "2025-12-01T00:00:00+00:00"
N_T, N_S = 400, 25
cur.execute("BEGIN")
for i in range(N_T):
    d = f"target{i:04d}.example.com"
    flags = {"amass_done": bool(i % 2), "httpx_done": bool(i % 3 == 0)}
    cur.execute("INSERT INTO targets (domain,data,flags,options,comments,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (d, "{}", json.dumps(flags), json.dumps({"x": i}), json.dumps([{"c": i}] if i % 5 == 0 else []), NOW, NOW))
    n = 0 if i % 17 == 0 else N_S
    for j in range(n):
        s = f"s{j:03d}.{d}"
        data = {"sources": ["amass", "subfinder"][: 1 + j % 2]}
        if j % 2 == 0:
            data["httpx"] = {"status_code": 200 + j % 5, "title": f"t{j}", "webserver": "nginx", "tech": ["a"] * (j % 4)}
        if j % 3 == 0:
            data["nuclei"] = [{"id": f"n{k}", "severity": "low"} for k in range(rng.randint(0, 4))]
        if j % 4 == 0:
            data["screenshot"] = {"path": f"/s/{s}.png", "meta": "x" * 50}
        cur.execute("INSERT INTO subdomains (domain,subdomain,data,interesting,comments,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                    (d, s, json.dumps(data), (j % 3) if j % 7 else None, json.dumps([{"note": j}]) if j % 6 == 0 else None, NOW, NOW))
cur.execute("COMMIT")

h = hashlib.sha256()
def canon(o):
    return json.dumps(o, sort_keys=True, default=str).encode()
for it in range(15):
    st = main.load_state()
    h.update(canon(st))
    with contextlib.redirect_stdout(io.StringIO()):
        summ = main.build_state_payload_summary()
    h.update(canon(summ["targets"]))
    h.update(canon(summ["last_updated"]))
import threading, urllib.request
from http.server import ThreadingHTTPServer
srv = ThreadingHTTPServer(("127.0.0.1", 0), main.CommandCenterHandler)
th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
port = srv.server_address[1]
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for full in ("false", "true"):
    for page in range(1, 9):
        with opener.open(f"http://127.0.0.1:{port}/api/state?full={full}&page={page}&per_page=50") as r:
            body = json.loads(r.read())
        h.update(canon(sorted(body.get("targets", {}).keys())))
        h.update(canon(sorted(body.get("targets", {}).items())))
srv.shutdown(); srv.server_close()
print(len(st["targets"]), sum(len(t["subdomains"]) for t in st["targets"].values()))
print(h.hexdigest())
