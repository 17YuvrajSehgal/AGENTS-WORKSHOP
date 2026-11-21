import hashlib, json, shutil, sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication
app = QCoreApplication.instance() or QCoreApplication(sys.argv)

from iPhoto.cache.index_store import IndexStore
from iPhoto.gui.ui.tasks.asset_loader_worker import AssetLoaderWorker, AssetLoaderSignals

BASE = Path("/tmp/kt_489")
LIB = BASE / "Library"
N_ALBUMS = 4
PER_ALBUM = 900


def setup():
    if BASE.exists():
        shutil.rmtree(BASE)
    LIB.mkdir(parents=True)
    rows = []
    idx = 0
    for a in range(N_ALBUMS):
        d = LIB / f"album{a}"
        (d / "sub").mkdir(parents=True)
        for i in range(PER_ALBUM):
            sub = "sub/" if i % 3 == 0 else ""
            ext = "mov" if i % 7 == 0 else "jpg"
            rel = f"album{a}/{sub}IMG_{i:05d}.{ext}"
            (LIB / rel).write_bytes(b"\x00")
            # some duplicate timestamps to exercise keyset tie-break
            day = (idx // 3) % 28 + 1
            month = (idx // 84) % 12 + 1
            rows.append({
                "rel": rel,
                "id": f"as{idx:06d}",
                "dt": f"2023-{month:02d}-{day:02d}T10:00:00Z",
                "ts": 1_600_000_000 + (idx // 3),
                "bytes": 1000 + idx,
                "mime": "video/quicktime" if ext == "mov" else "image/jpeg",
                "w": 4000, "h": 3000,
                "media_type": 1 if ext == "mov" else 0,
                "is_favorite": 1 if i % 11 == 0 else 0,
                "live_role": 1 if i % 13 == 5 else 0,
                "dur": 3.5 if ext == "mov" else None,
            })
            idx += 1
    store = IndexStore(LIB)
    store.write_rows(rows)
    if hasattr(store, "close"):
        store.close()


def run(root, filter_params):
    signals = AssetLoaderSignals()
    progress = []
    signals.progressUpdated.connect(lambda r, a, b: progress.append((a, b)))
    w = AssetLoaderWorker(root, featured=["album0/IMG_00001.jpg"], signals=signals,
                          filter_params=filter_params, library_root=LIB)
    out = []
    for chunk in w._build_payload_chunks():
        out.append([(str(e.get("rel")), str(e.get("id")), str(e.get("dt")),
                     bool(e.get("featured")), bool(e.get("is_video"))) for e in chunk])
    return {"chunks": out, "progress": progress}


def main():
    setup()
    results = []
    results.append(run(LIB, None))
    results.append(run(LIB / "album1", None))
    results.append(run(LIB, {"filter_mode": "videos"}))
    results.append(run(LIB / "album2", {"filter_mode": "favorites"}))
    for r in results:
        print(len(r["chunks"]), sum(len(c) for c in r["chunks"]), r["progress"][-1])
    print(hashlib.sha256(json.dumps(results, sort_keys=True, default=str).encode()).hexdigest())


main()
