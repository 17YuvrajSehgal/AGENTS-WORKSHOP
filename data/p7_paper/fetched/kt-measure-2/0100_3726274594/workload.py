import hashlib, json, os, shutil, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from PySide6.QtCore import QThreadPool, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from iPhoto.app import open_album
from iPhoto.cache.index_store import IndexStore
from iPhoto.gui.ui.tasks.asset_loader_worker import AssetLoaderWorker, AssetLoaderSignals

app = QApplication.instance() or QApplication(sys.argv)
BASE = Path("/tmp/kt_428")
if BASE.exists():
    shutil.rmtree(BASE)

def make_album(name, n):
    root = BASE / name
    root.mkdir(parents=True)
    rows = []
    for i in range(n):
        is_vid = i % 7 == 0
        rel = f"IMG_{i:06d}." + ("mov" if is_vid else "heic")
        rows.append({
            "rel": rel, "id": f"as_{i}", "dt": f"20{10 + i % 14:02d}-{1 + i % 12:02d}-{1 + i % 28:02d}T10:{i % 60:02d}:00Z",
            "ts": 1_300_000_000_000_000 + i * 1_000_000, "bytes": 1000 + i,
            "mime": "video/quicktime" if is_vid else "image/heic",
            "w": 4032, "h": 3024, "aspect_ratio": 4032 / 3024,
            "content_id": f"cid_{i // 2}" if i % 5 < 2 else None,
            "dur": 2.5 if is_vid else None, "still_image_time": 1.0 if is_vid else None,
            "year": 2010 + i % 14, "month": 1 + i % 12, "media_type": 1 if is_vid else 0,
            "gps": {"lat": 10 + (i % 50) * 0.1, "lon": 20 + (i % 30) * 0.1} if i % 3 == 0 else None,
        })
    IndexStore(root).write_rows(rows)
    return root

h = hashlib.sha256()
out = []

# open_album on existing indices (base pairs synchronously, head defers)
for k in range(1):
    root = make_album(f"open{k}", 400)
    album = open_album(root, autoscan=False)
    out.append(("open", k, IndexStore(root).count()))

for k in range(3):
    eroot = BASE / f"empty{k}"
    eroot.mkdir(parents=True)
    open_album(eroot, autoscan=True)
    out.append(("autoscan", k, IndexStore(eroot).count()))

# Loader worker streaming in various sizes / filters
sizes = [50, 100, 150, 3000, 10000]
for n in sizes:
    root = make_album(f"load{n}", n)
    for params in (None, {"filter_mode": "videos"}, {"filter_mode": "favorites"}):
        sig = AssetLoaderSignals()
        prog = []
        sig.progressUpdated.connect(lambda r, a, b: prog.append((a, b)))
        w = AssetLoaderWorker(root, ["IMG_000003.heic"], sig, params)
        total = 0
        for chunk in w._build_payload_chunks():
            for e in chunk:
                total += 1
                h.update(f"{e['rel']}|{e['dt']}|{e['is_video']}|{e['featured']}|{e['live_group_id']}".encode())
        out.append(("load", n, json.dumps(params), total, prog[-1]))

    # cancellation mid-stream
    sig = AssetLoaderSignals()
    w = AssetLoaderWorker(root, [], sig, None)
    got = 0
    for i, chunk in enumerate(w._build_payload_chunks()):
        got += len(chunk)
        if i == 1:
            w.cancel()
    out.append(("cancel", n, got))

    st = IndexStore(root)
    for lim, off in ((None, None), (10, None), (None, 10)):
        try:
            kw = {}
            if lim is not None: kw["limit"] = lim
            if off is not None: kw["offset"] = off
            rows = list(st.read_geometry_only(sort_by_date=True, **kw))
            out.append(("geom", n, lim, off, len(rows), rows[0]["rel"] if rows else None))
        except TypeError:
            out.append(("geom", n, lim, off, "unsupported"))

# Full GUI facade path: open album, stream into list model, wrap in spacer proxy
from iPhoto.gui.facade import AppFacade
from iPhoto.gui.ui.models.spacer_proxy_model import SpacerProxyModel
from iPhoto.gui.ui.models.roles import Roles
facade = AppFacade()

def settle():
    pool = QThreadPool.globalInstance()
    idle = 0
    for _ in range(5000):
        app.processEvents(QEventLoop.AllEvents, 5)
        busy = pool.activeThreadCount() > 0 or facade.asset_list_model._pending_chunks_buffer
        if busy:
            pool.waitForDone(5)
            idle = 0
        else:
            idle += 1
            if idle >= 20:
                break

for n in (80, 500):
    root = make_album(f"gui{n}", n)
    facade.open_album(root)
    settle()
    model = facade.asset_list_model
    proxy = SpacerProxyModel()
    proxy.setSourceModel(model)
    rels = []
    for r in range(proxy.rowCount()):
        idx = proxy.index(r, 0)
        rels.append((proxy.data(idx, Roles.IS_SPACER), proxy.data(idx, Roles.REL)))
    out.append(("gui", n, model.rowCount(), hashlib.sha256(repr(sorted(rels, key=repr)).encode()).hexdigest()))

# Album whose links.json is current but whose backup folder is blocked by a stray file:
# rewriting links.json fails, reading/pairing does not.
from iPhoto import app as backend
from iPhoto.utils.jsonio import write_json
errors = []
facade.errorRaised.connect(lambda m: errors.append(m.split(":")[0]))
broot = make_album("blocked", 120)
_, payload = backend._compute_links_payload(list(IndexStore(broot).read_all()))
write_json(broot / ".iPhoto" / "links.json", payload)
(broot / ".iPhoto" / "manifest.bak").write_text("not a directory")
facade.open_album(broot)
settle()
out.append(("blocked", facade.asset_list_model.rowCount(), errors))

proxy = SpacerProxyModel()
out.append(("nosrc", proxy.data(proxy.index(0, 0), Roles.REL)))
QThreadPool.globalInstance().waitForDone()
app.processEvents()

for o in out:
    print(o)
h.update(repr(out).encode())
print(h.hexdigest())
