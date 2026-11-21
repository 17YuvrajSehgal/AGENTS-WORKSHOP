import os, sys, hashlib, shutil
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QImage, QColor

app = QGuiApplication.instance() or QGuiApplication([])
from iPhoto.config import WORK_DIR_NAME
from iPhoto.gui.ui.qml.qml_providers import ThumbnailImageProvider

ROOT = Path("/tmp/kt_564/lib")
N = 500

def build():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    photos = ROOT / "photos"; photos.mkdir(parents=True)
    thumbs = ROOT / WORK_DIR_NAME / "thumbs"; thumbs.mkdir(parents=True)
    paths = []
    for i in range(N):
        p = photos / f"img_{i:04d}.png"
        img = QImage(64, 48, QImage.Format.Format_RGB32)
        img.fill(QColor((i * 37) % 256, (i * 91) % 256, (i * 13) % 256))
        img.save(str(p))
        paths.append(p)
        digest = hashlib.blake2b(str(p.resolve()).encode("utf-8"), digest_size=20).hexdigest()
        if i % 3 != 0:  # some without cached thumb
            for k in range(2):
                t = thumbs / f"{digest}_{1000 + k}_32x24.png"
                ti = QImage(32, 24, QImage.Format.Format_RGB32)
                ti.fill(QColor((i * 5 + k * 100) % 256, 10, 200))
                ti.save(str(t))
                os.utime(t, (1_700_000_000 + k, 1_700_000_000 + k))
        # noise entries
        (thumbs / f"other_{i:04d}.txt").write_text("x")
    return paths

paths = build()
h = hashlib.sha256()
for rnd in range(6):
    prov = ThumbnailImageProvider()
    setter = getattr(prov, "set_library_root", None)
    if setter is not None:
        setter(ROOT)
    for j, p in enumerate(paths):
        rs = QSize(16, 12) if j % 2 else QSize()
        img = prov.requestImage(str(p), QSize(), rs)
        h.update(f"{img.width()}x{img.height()}:{img.pixel(0, 0)}".encode())
    # cached hits
    for p in paths[:20]:
        img = prov.requestImage(str(p), QSize(), QSize())
        h.update(f"{img.width()}x{img.height()}".encode())
    # missing file -> placeholder
    img = prov.requestImage(str(ROOT / "missing.png"), QSize(), QSize())
    h.update(f"{img.width()}x{img.height()}".encode())
    prov.clear_cache()
print(h.hexdigest())
