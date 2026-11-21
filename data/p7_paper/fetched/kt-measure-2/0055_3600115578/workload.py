"""Workload: drive the real edit flow (begin_edit -> image load -> sidebar preview).

Runs the GUI under a private Xvfb display (software Mesa OpenGL, no GPU) so
the GL image viewer has a real context.  Measures EditController's image
loaded handler, sidebar preview preparation and EditSidebarPreviewWorker.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/tmp/kt_140")
side_root = Path(sys.prefix).resolve().parent
side = side_root.name

# The project imports itself as ``iPhotos.src.iPhoto`` / ``iPhotos.maps``.
# Build that package layout: ``src`` links to the code under test; the map
# assets are copied so an (empty) tile directory can be provided.
pkg_parent = ROOT / f"x_{side}"
pkg = pkg_parent / "iPhotos"
if not (pkg / "maps" / "tiles").exists():
    shutil.rmtree(pkg_parent, ignore_errors=True)
    pkg.mkdir(parents=True)
    (pkg / "src").symlink_to(side_root / "src" / "src")
    shutil.copytree(side_root / "src" / "maps", pkg / "maps",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (pkg / "maps" / "tiles").mkdir()
sys.path.insert(0, str(pkg_parent))

home = ROOT / f"home_{side}"
shutil.rmtree(home, ignore_errors=True)
home.mkdir(parents=True)
os.environ["HOME"] = str(home)
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

# Private X server (unix socket only).
rfd, wfd = os.pipe()
xvfb = subprocess.Popen(
    ["Xvfb", "-displayfd", str(wfd), "-screen", "0", "1600x1200x24", "-nolisten", "tcp"],
    pass_fds=(wfd,), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
os.close(wfd)
buf = b""
while not buf.endswith(b"\n"):
    chunk = os.read(rfd, 64)
    if not chunk:
        break
    buf += chunk
os.close(rfd)
os.environ["DISPLAY"] = ":" + buf.decode().strip()

from PySide6.QtCore import QPointF, QThreadPool  # noqa: E402
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])

from iPhotos.src.iPhoto.appctx import AppContext  # noqa: E402
from iPhotos.src.iPhoto.gui.ui.main_window import MainWindow  # noqa: E402


def make_image(w, h, seed):
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(QColor((seed * 37) % 256, (seed * 91) % 256, (seed * 53) % 256))
    p = QPainter(img)
    g = QLinearGradient(QPointF(0, 0), QPointF(w, h))
    g.setColorAt(0.0, QColor((seed * 13) % 256, 40, 200))
    g.setColorAt(1.0, QColor(250, (seed * 29) % 256, 30))
    p.fillRect(0, 0, w, h // 2, g)
    p.fillRect(w // 4, h // 4, w // 3, h // 3, QColor(10, 220, (seed * 7) % 256))
    p.fillRect(0, (3 * h) // 4, w, h // 8, QColor(230, 190, 160))
    p.end()
    return img


album = ROOT / f"album_{side}"
shutil.rmtree(album, ignore_errors=True)
album.mkdir(parents=True)
SIZES = [(2400, 1600), (1600, 2400), (1024, 768),
         (640, 480), (400, 300)]
for i, (w, h) in enumerate(SIZES):
    make_image(w, h, i + 1).save(str(album / f"IMG_{i:03d}.PNG"))


def pump(cond, timeout=20.0):
    t = time.monotonic()
    while time.monotonic() - t < timeout:
        app.processEvents()
        if cond():
            return True
        time.sleep(0.002)
    return False


ctx = AppContext()
win = MainWindow(ctx)
win.resize(1400, 900)
win.show()
win.open_album_from_path(album)
mc = [v for v in vars(win).values() if type(v).__name__ == "MainController"][0]
pl = mc._playlist
pump(lambda: pl._model is not None and pl._model.rowCount() >= len(SIZES), 30)
n = pl._model.rowCount()
ec = mc.edit_controller()
sidebar = win.ui.edit_sidebar

results = []
for rnd in range(1):
    for row in range(n):
        pl.set_current(row)
        sidebar.set_light_preview_image(None)
        gen0 = ec._sidebar_preview_generation
        ec.begin_edit()
        ok = pump(lambda: ec._sidebar_preview_generation > gen0
                  and ec._sidebar_preview_worker is None
                  and sidebar._light_preview_image is not None)
        img = sidebar._light_preview_image
        st = sidebar._color_stats
        src = pl.current_source()
        results.append((
            src.name if src else None, ok,
            (img.width(), img.height()) if img is not None else None,
            None if st is None else tuple(
                round(v, 4) if isinstance(v, float) else tuple(round(x, 4) for x in v)
                for v in (st.saturation_mean, st.saturation_median, st.highlight_ratio,
                          st.dark_ratio, st.skin_ratio, st.cast_magnitude,
                          st.white_balance_gain)),
        ))
        ec.leave_edit_mode(animate=False)
        pump(lambda: not mc.is_edit_view_active(), 5)


# Re-prepare the sidebar preview from a full-resolution frame while editing
# (the CPU-scaling path of _start_sidebar_preview_preparation).
pl.set_current(0)
gen0 = ec._sidebar_preview_generation
ec.begin_edit()
pump(lambda: ec._sidebar_preview_generation > gen0 and ec._sidebar_preview_worker is None)
for i, (w, h) in enumerate([(1200, 1800), (2000, 1500)]):
    gen0 = ec._sidebar_preview_generation
    ec._start_sidebar_preview_preparation(make_image(w, h, 60 + i))
    ok = pump(lambda: ec._sidebar_preview_generation > gen0 and ec._sidebar_preview_worker is None)
    pump(lambda: False, 0.05)
    img = sidebar._light_preview_image
    st = sidebar._color_stats
    results.append(("full-res", w, h, ok, img.width(), img.height(),
                    round(st.saturation_mean, 4), round(st.cast_magnitude, 4)))
ec.leave_edit_mode(animate=False)
pump(lambda: not mc.is_edit_view_active(), 5)

# Direct calls of the sidebar preview worker on the main thread (as in the
# repository's test_edit_sidebar_preview_worker), covering both an explicit
# target height and the "already scaled" (-1) request used by the controller.
from iPhotos.src.iPhoto.gui.ui.tasks.edit_sidebar_preview_worker import (  # noqa: E402
    EditSidebarPreviewWorker,
)

for i, (w, h) in enumerate([(640, 480), (504, 336), (336, 336)]):
    src = make_image(w, h, 40 + i)
    for th in (320, -1):
        worker = EditSidebarPreviewWorker(src, generation=i, target_height=th)
        worker.setAutoDelete(False)
        got = []
        worker.signals.ready.connect(lambda res, g, got=got: got.append(res))
        worker.run()
        res = got[0]
        st = res.stats
        results.append(("worker", w, h, th, res.image.width(), res.image.height(),
                        round(st.saturation_mean, 4), round(st.cast_magnitude, 4)))

for r in results:
    print(r)
print(hashlib.sha256(repr(results).encode()).hexdigest())
sys.stdout.flush()
win.close()
pump(lambda: False, 0.3)
QThreadPool.globalInstance().waitForDone(10000)
pump(lambda: False, 0.1)
xvfb.terminate()
try:
    xvfb.wait(5)
except Exception:
    xvfb.kill()
