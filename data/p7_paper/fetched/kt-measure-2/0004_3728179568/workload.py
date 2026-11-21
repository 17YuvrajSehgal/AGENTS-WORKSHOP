import os, sys, hashlib, json, shutil, logging
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
logging.disable(logging.CRITICAL)

from PySide6.QtCore import QObject, Signal, QCoreApplication, QEventLoop
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from iPhoto.gui.ui.models.asset_list_model import AssetListModel
from iPhoto.gui.ui.models.asset_state_manager import AssetListStateManager
from iPhoto.gui.ui.tasks.asset_loader_worker import AssetLoaderWorker, AssetLoaderSignals, build_asset_entry
from iPhoto.cache.index_store import IndexStore

ROOT = Path("/tmp/kt_445/album")
H = hashlib.sha256()


class Facade(QObject):
    linksUpdated = Signal(Path)
    assetUpdated = Signal(Path)
    scanChunkReady = Signal(Path, list)
    errorRaised = Signal(str)
    library_manager = None
    current_album = None


def make_row(i):
    return {"rel": f"sub{i % 7}/IMG_{i:05d}.jpg", "abs": str(ROOT / f"sub{i % 7}/IMG_{i:05d}.jpg"),
            "w": 4000, "h": 3000, "mime": "image/jpeg", "dt": f"2024-01-{1 + i % 28:02d}T10:00:00Z"}


def model_stream(n_rows, chunk_size, dup_every):
    facade = Facade()
    model = AssetListModel(facade)
    finished = []
    model.loadFinished.connect(lambda r, s: finished.append(s))
    model._album_root = ROOT
    model._pending_loader_root = ROOT
    model._is_first_chunk = True
    rows = [make_row(i) for i in range(n_rows)]
    for start in range(0, n_rows, chunk_size):
        chunk = [dict(r) for r in rows[start:start + chunk_size]]
        # re-send some already-seen rows to exercise dedup
        if start:
            chunk += [dict(rows[j]) for j in range(0, start, dup_every)][:50]
        model._on_loader_chunk_ready(ROOT, chunk)
    model._on_loader_finished(ROOT, True)
    # drain buffer deterministically
    guard = 0
    while model._pending_chunks_buffer and guard < 100000:
        model._flush_pending_chunks()
        guard += 1
    model._flush_timer.stop()
    sm = model._state_manager
    sm.rebuild_lookup()
    # error and ignore paths
    model._pending_chunks_buffer = [make_row(1)]
    model._on_loader_error(ROOT, "boom")
    model._ignore_incoming_chunks = True
    model._on_loader_finished(ROOT, True)
    model._flush_timer.stop()
    rels = [r["rel"] for r in sm.rows]
    return {"count": sm.row_count(), "rels": hashlib.sha256("\n".join(rels).encode()).hexdigest(),
            "lookup": len(sm.row_lookup), "finished": finished}


def state_manager_work(n):
    sm = AssetListStateManager(None, None)
    rows = []
    for i in range(n):
        rel = f"a/b{i % 13}/c_{i}.heic"
        rows.append({"rel": Path(rel) if i % 3 == 0 else rel, "abs": f"/x/{rel}"})
    for start in range(0, n, 250):
        sm.append_chunk(rows[start:start + 250])
    a = sorted(((str(k), v) for k, v in sm.row_lookup.items()))[:5]
    sm.rebuild_lookup()
    sm.rebuild_lookup()
    return [len(sm.row_lookup), a, sorted(((str(k), v) for k, v in sm.row_lookup.items()))[-3:]]


def loader_worker(n):
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    store = IndexStore(ROOT)
    store.write_rows([{"rel": f"p/IMG_{i:05d}.jpg", "w": 100 + i, "h": 80, "mime": "image/jpeg",
                       "dt": f"2023-02-{1 + i % 28:02d}T0{i % 10}:00:00Z", "id": f"id{i}"}
                      for i in range(n)])
    sig = AssetLoaderSignals()
    out = []
    sig.chunkReady.connect(lambda r, c: out.append([e.get("rel") for e in c]))
    done = []
    sig.finished.connect(lambda r, s: done.append(s))
    err = []
    sig.error.connect(lambda r, m: err.append(m))
    w = AssetLoaderWorker(ROOT, ["p/IMG_00003.jpg"], sig)
    w.setAutoDelete(False)
    w.run()
    QCoreApplication.processEvents()
    return {"chunks": [len(c) for c in out], "sum": sum(len(c) for c in out), "done": done, "err": err,
            "h": hashlib.sha256(json.dumps(out).encode()).hexdigest()}


class LibMgr:
    def __init__(self, items):
        self.items = items
    def root(self):
        return None
    def get_live_scan_results(self, relative_to=None):
        return [dict(r) for r in self.items]


def full_flow(n_db, n_live):
    root = Path("/tmp/kt_445/full")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    store = IndexStore(root)
    store.write_rows([{"rel": f"d/IMG_{i:05d}.jpg", "w": 100, "h": 80, "mime": "image/jpeg",
                       "dt": f"2023-03-{1 + i % 28:02d}T00:00:00Z", "id": f"x{i}"} for i in range(n_db)])
    # live items: half overlap with DB, half new
    live = [{"rel": f"d/IMG_{i:05d}.jpg", "w": 100, "h": 80, "mime": "image/jpeg",
             "dt": "2023-03-01T00:00:00Z", "id": f"x{i}"} for i in range(n_db - n_live // 2, n_db + n_live // 2)]
    facade = Facade()
    facade.library_manager = LibMgr(live)
    model = AssetListModel(facade)
    loop = QEventLoop()
    finished = []
    def on_fin(r, s):
        finished.append(s)
    model.loadFinished.connect(on_fin)
    model.prepare_for_album(root)
    from PySide6.QtCore import QThreadPool, QTimer
    for _round in range(2):
        finished.clear()
        model.start_load()
        _wait(loop, model, finished)
    rels = sorted(str(r["rel"]) for r in model._state_manager.rows)
    return {"n": len(rels), "uniq": len(set(rels)), "fin": finished[:1],
            "h": hashlib.sha256("\n".join(sorted(set(rels))).encode()).hexdigest()}


def _wait(loop, model, finished):
    from PySide6.QtCore import QThreadPool, QTimer
    def poll():
        if finished and not model._pending_chunks_buffer and not model._data_loader.is_running() \
                and QThreadPool.globalInstance().activeThreadCount() == 0:
            loop.quit()
    t = QTimer(); t.timeout.connect(poll); t.start(20)
    QTimer.singleShot(25000, loop.quit)
    loop.exec()
    t.stop()
    QThreadPool.globalInstance().waitForDone()
    for _ in range(2):
        QCoreApplication.processEvents()


results = []
results.append(full_flow(2000, 300))
results.append(loader_worker(3000))
for _ in range(2):
    results.append(model_stream(6000, 400, 37))
results.append(state_manager_work(30000))
for r in results:
    s = json.dumps(r, sort_keys=True, default=str)
    print(s[:200])
    H.update(s.encode())
print(H.hexdigest())
