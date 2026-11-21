import os, json, shutil, time, hashlib, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import logging
logging.disable(logging.CRITICAL)
from pathlib import Path
from PIL import Image
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication
from iPhoto.gui.facade import AppFacade
from iPhoto.library.manager import LibraryManager
from iPhoto import app as backend

BASE = Path("/tmp/kt_483")
TEMPLATE = BASE / "template_v2" / "Library"
WORK = BASE / "work"
N_SUB, N_IMG = 4, 60


def manifest(d, title):
    (d / ".iphoto.album.json").write_text(
        json.dumps({"schema": "iPhoto/album@1", "title": title, "filters": {}}), encoding="utf-8")


def build_template():
    if (TEMPLATE.parent / "done").exists():
        return
    if TEMPLATE.parent.exists():
        shutil.rmtree(TEMPLATE.parent)
    for i in range(N_SUB):
        d = TEMPLATE / f"Album{i}"
        d.mkdir(parents=True)
        manifest(d, f"Album{i}")
        for j in range(N_IMG):
            Image.new("RGB", (32, 32), (i * 40, (j * 7) % 256, j % 13)).save(d / f"img_{j:03d}.jpg")
    manifest(TEMPLATE, "Library")
    backend.rescan(TEMPLATE)
    for i in range(N_SUB):
        backend.rescan(TEMPLATE / f"Album{i}")
    (TEMPLATE.parent / "done").write_text("ok")


def main():
    build_template()
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(TEMPLATE.parent, WORK)
    root = WORK / "Library"
    subs = [root / f"Album{i}" for i in range(N_SUB)]

    app = QApplication.instance() or QApplication([])
    m = LibraryManager()
    m.bind_path(root)
    f = AppFacade()
    f.bind_library(m)
    done = []
    f.loadFinished.connect(lambda r, s: done.append((Path(r), bool(s))))

    def wait_for(p):
        t = time.monotonic()
        while time.monotonic() - t < 10:
            app.processEvents()
            if any(r == p for r, _ in done):
                break
        done.clear()

    results = []
    seq = [root] + subs + [root]
    for rnd in range(6):
        for p in seq:
            f.open_album(p)
            wait_for(p)
            model = f.asset_list_model
            rels = sorted(str((model.get_internal_row(i) or {}).get("rel")) for i in range(model.rowCount()))
            results.append((p.name, model is f._library_list_model, model.rowCount(),
                            hashlib.sha256("\n".join(rels).encode()).hexdigest()[:16]))
    # drain background work for a clean exit
    for _ in range(50):
        app.processEvents()
    QThreadPool.globalInstance().waitForDone(10000)
    app.processEvents()
    for r in results[:len(seq)]:
        print(r)
    print(hashlib.sha256(repr(results).encode()).hexdigest())
    sys.stdout.flush()
    m.deleteLater(); f.deleteLater()
    app.processEvents()


main()
