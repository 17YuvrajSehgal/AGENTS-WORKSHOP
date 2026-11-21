import os, sys, hashlib, shutil
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import iPhoto
ROOT = Path(iPhoto.__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor
app = QApplication.instance() or QApplication([])

from src.iPhoto.gui.ui.controllers.export_controller import ExportWorker
from src.iPhoto.io import sidecar
from src.iPhoto.gui.ui.controllers.export_controller import LibraryExportWorker
from src.iPhoto.library.manager import LibraryManager
from src.iPhoto.cache.index_store import get_global_repository
from src.iPhoto.gui.ui.controllers.player_view_controller import PlayerViewController
from src.iPhoto.gui.ui.widgets.gl_image_viewer import GLImageViewer
from src.iPhoto.gui.ui.widgets.video_area import VideoArea
from src.iPhoto.gui.ui.widgets.live_badge import LiveBadge
from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtGui import QWheelEvent, QResizeEvent
from PySide6.QtCore import QSize, QPointF, QPoint, Qt, QThreadPool

BASE = Path("/tmp/kt_678")
LIB = BASE / "lib"
N_EDITED, N_PLAIN = 24, 40

def build_library():
    if LIB.exists():
        shutil.rmtree(LIB)
    paths = []
    for i in range(N_EDITED + N_PLAIN):
        album = LIB / f"album{i % 4}"
        album.mkdir(parents=True, exist_ok=True)
        p = album / f"img_{i:03d}.png"
        img = QImage(640, 480, QImage.Format_RGB32)
        img.fill(QColor((i * 37) % 256, (i * 91) % 256, (i * 13) % 256))
        for y in range(0, 480, 16):
            for x in range(0, 640, 16):
                img.setPixelColor(x, y, QColor((x + i) % 256, (y * 3) % 256, (x ^ y) % 256))
        img.save(str(p), "PNG")
        if i < N_EDITED:
            sidecar.save_adjustments(p, {
                "Light_Master": 0.2 + 0.01 * i, "Light_Enabled": True,
                "Crop_CX": 0.5, "Crop_CY": 0.5, "Crop_W": 0.8, "Crop_H": 0.9,
                "Crop_FlipH": bool(i % 2), "Crop_Rotate90": float(i % 4),
            })
        paths.append(p)
    paths.append(LIB / "album0" / "missing.png")
    return paths

paths = build_library()
results = []
for rep in range(2):
    out = BASE / f"export{rep}"
    if out.exists():
        shutil.rmtree(out)
    w = ExportWorker(paths, out, LIB)
    prog, fin = [], []
    w.signals.progress.connect(lambda c, t: prog.append((c, t)))
    w.signals.finished.connect(lambda s, f: fin.append((s, f)))
    w.run()
    files = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
    dims = []
    for f in files:
        im = QImage(str(out / f))
        dims.append((f, im.width(), im.height()))
    results.append((fin, len(prog), dims))
    print(rep, fin, len(files))

# --- Library-wide export of edited assets ---
lib_mgr = LibraryManager()
lib_mgr.bind_path(LIB)
repo = get_global_repository(lib_mgr.root())
repo.write_rows([{"rel": str(p.relative_to(LIB))} for p in paths])
for rep in range(2):
    out = BASE / f"libexport{rep}"
    if out.exists():
        shutil.rmtree(out)
    w = LibraryExportWorker(lib_mgr, out)
    prog, fin, msgs = [], [], []
    w.signals.progress.connect(lambda c, t: prog.append((c, t)))
    w.signals.finished.connect(lambda s, f: fin.append((s, f)))
    w.signals.message.connect(msgs.append)
    w.run()
    files = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
    results.append((fin, sorted(prog), msgs, files))
    print("lib", rep, fin, len(files))

# --- Detail viewer: repeated display of the same images ---
stack = QStackedWidget()
viewer = GLImageViewer()
va = VideoArea()
ph = QWidget()
for wdg in (ph, viewer, va):
    stack.addWidget(wdg)
pvc = PlayerViewController(stack, viewer, va, ph, LiveBadge(stack))
pool = QThreadPool.globalInstance()
shown = []
for rnd in range(3):
    for p in paths[:6]:
        ok = pvc.display_image(p)
        pool.waitForDone()
        app.processEvents()
        img = viewer._image
        shown.append((ok, None if img is None else (img.width(), img.height(), img.pixel(5, 5))))
for k in range(20):
    viewer.resizeEvent(QResizeEvent(QSize(800 + k, 600), QSize(640, 480)))
    viewer.wheelEvent(QWheelEvent(QPointF(100, 100), QPointF(100, 100), QPoint(0, 0), QPoint(0, 120),
                                  Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False))
shown.append(round(viewer._transform_controller._zoom_factor, 6))
results.append(shown)
print("viewer", shown[-1])

print(hashlib.sha256(repr(results).encode()).hexdigest())
