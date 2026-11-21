import hashlib, json, os, shutil, sys
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCoreApplication, QObject, Signal, QThreadPool, Qt, QModelIndex
from PySide6.QtWidgets import QApplication
from iPhoto.cache.index_store import IndexStore
from iPhoto.gui.ui.tasks.asset_loader_worker import AssetLoaderWorker, AssetLoaderSignals
from iPhoto.gui.ui.models.asset_list_model import AssetListModel

app = QApplication.instance() or QApplication(sys.argv)
BASE = Path("/tmp/kt_453")
LIB = BASE / "lib"
ALBUMS = ["A", "B", "C"]
N = 1200


def make_rows(prefix, n, seed):
    rows = []
    for i in range(n):
        k = i * 3 + seed
        sub = f"d{i % 5}"
        rel = f"{sub}/img_{seed}_{i:05d}.jpg"
        dt = None if k % 13 == 0 else f"2024-{1 + k % 12:02d}-{1 + (k // 3) % 28:02d}T10:{k % 60:02d}:00Z"
        rows.append({
            "rel": rel, "id": f"id{seed}_{i:06d}", "dt": dt, "ts": 1700000000 + k * 37 % 100000,
            "bytes": 1000 + i, "mime": "image/jpeg", "w": 4000 + (i % 3) * 4000, "h": 3000,
            "aspect_ratio": 1.333, "year": 2024, "month": 1 + k % 12, "media_type": 0,
            "is_favorite": i % 5 == 0, "location": "Somewhere",
            "live_role": 1 if i % 17 == 0 else 0,
        })
    return rows


def setup():
    if BASE.exists():
        shutil.rmtree(BASE)
    LIB.mkdir(parents=True)
    all_rows = []
    for s, name in enumerate(ALBUMS):
        root = LIB / name
        rows = make_rows(name, N, s)
        for r in rows:
            p = root / r["rel"]
            p.parent.mkdir(parents=True, exist_ok=True)
            if int(r["id"].split("_")[1]) % 11 != 0:
                p.write_bytes(b"x")
            rr = dict(r); rr["rel"] = f"{name}/{r['rel']}"
            all_rows.append(rr)
        IndexStore(root).write_rows(rows)
    IndexStore(LIB).write_rows(all_rows)


class Facade(QObject):
    assetUpdated = Signal(Path)
    linksUpdated = Signal(Path)
    scanChunkReady = Signal(Path, list)

    def __init__(self):
        super().__init__()
        self.current_album = SimpleNamespace(manifest={"featured": ["d0/img_0_00000.jpg"]})
        nodes = [SimpleNamespace(path=LIB / n, level=1, title=n, has_manifest=True) for n in ALBUMS]
        self.library_manager = SimpleNamespace(
            root=lambda: LIB, list_albums=lambda: list(nodes),
            get_live_scan_results=lambda relative_to=None: [],
        )


def model_load(model, root, mode):
    done = []
    model.loadFinished.connect(lambda r, ok: done.append(ok))
    model.prepare_for_album(root)
    model._active_filter = mode
    model.start_load()
    spins = 0
    while True:
        app.processEvents()
        if model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
        if done and not model.canFetchMore(QModelIndex()) and QThreadPool.globalInstance().activeThreadCount() == 0:
            app.processEvents()
            break
        QThreadPool.globalInstance().waitForDone(5)
        spins += 1
        if spins > 20000:
            break
    model.loadFinished.disconnect()
    out = []
    for i in range(model.rowCount()):
        row = model.get_internal_row(i) if hasattr(model, "get_internal_row") else None
        if row:
            out.append(str(row.get("rel")))
    return out


setup()
h = hashlib.sha256()
# 1. Worker chunk generation
for fp in (None, {"filter_mode": "favorites"}):
    progress = []
    sig = AssetLoaderSignals()
    sig.progressUpdated.connect(lambda r, a, b: progress.append((a, b)))
    w = AssetLoaderWorker(LIB / "A", ["d0/img_0_00000.jpg"], sig, filter_params=fp)
    for chunk in w._build_payload_chunks():
        for e in chunk:
            h.update(json.dumps([e.get("rel"), e.get("featured")], default=str).encode())
    h.update(json.dumps(progress[-1]).encode())
    print("progress", progress[-1])

# 2. Model loading
facade = Facade()
for root, mode in ((LIB / "B", None), (LIB / "C", "favorites"), (LIB, None)):
    model = AssetListModel(facade)
    rels = model_load(model, root, mode)
    print(root.name, mode, len(rels))
    h.update(json.dumps(sorted(rels)).encode())

geo = list(IndexStore(LIB / "A").read_geometry_only(sort_by_date=True))
h.update(json.dumps(sorted(r["rel"] for r in geo)).encode())
QThreadPool.globalInstance().waitForDone()
print(h.hexdigest())
