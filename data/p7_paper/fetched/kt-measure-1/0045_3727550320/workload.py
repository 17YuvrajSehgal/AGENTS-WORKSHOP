import hashlib, os, shutil, sys, logging
from pathlib import Path
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
logging.disable(logging.CRITICAL)
from PIL import Image
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])

import iPhoto
sys.path.append(str(Path(iPhoto.__file__).resolve().parents[2]))
from iPhoto.io import scanner
from iPhoto.cache.index_store import IndexStore
from iPhoto.gui.ui.tasks.asset_loader_worker import build_asset_entry
from iPhoto.gui.ui.models.asset_row_adapter import AssetRowAdapter

ROOT = Path("/tmp/kt_435/album")
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)
import random
rng = random.Random(1234)
paths = []
for i in range(120):
    w, h = rng.choice([(640, 480), (480, 640), (800, 400), (500, 500)])
    img = Image.new("RGB", (w, h), (rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    for _ in range(20):
        x, y = rng.randrange(w - 20), rng.randrange(h - 20)
        img.paste((rng.randrange(256), rng.randrange(256), rng.randrange(256)), (x, y, x + 20, y + 20))
    if i % 4 == 0:
        p = ROOT / f"img_{i:03d}.png"
        img.convert("RGBA").save(p, format="PNG")
    else:
        p = ROOT / f"img_{i:03d}.jpg"
        img.save(p, format="JPEG", quality=90)
    paths.append(p)
bad = ROOT / "broken.jpg"
bad.write_text("not an image")
paths.append(bad)
for p in paths:
    os.utime(p, (1_600_000_000, 1_600_000_000))

hasher = hashlib.sha256()

def digest_row(r):
    keys = sorted(k for k in r if k not in ("abs",))
    for k in keys:
        v = r[k]
        if isinstance(v, bytes):
            v = hashlib.sha256(v).hexdigest()
        elif hasattr(v, "isNull"):
            v = (v.width(), v.height())
        hasher.update(f"{k}={v!r};".encode())

for rep in range(3):
    rows = list(scanner.process_media_paths(ROOT, paths, []))
    rows.sort(key=lambda r: r["rel"])
    store = IndexStore(ROOT)
    store.write_rows(rows)
    read = list(store.read_all())
    geo = list(store.read_geometry_only())
    # cache-hit path with records lacking micro thumbnail
    existing = {}
    for r in read:
        r2 = dict(r)
        r2.pop("micro_thumbnail", None)
        existing[r2["rel"]] = r2
    cached = list(scanner._process_path_stream(ROOT, iter(paths), existing_index=existing))
    entries = [build_asset_entry(ROOT, r, set()) for r in geo]
    entries += [build_asset_entry(ROOT, r, set()) for r in cached]
    for r in rows + cached:
        digest_row(r)
    for e in entries:
        if e is not None:
            digest_row(e)

from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QImage, QPainter, QStandardItemModel, QStandardItem, QPalette
from PySide6.QtWidgets import QStyleOptionViewItem
from iPhoto.gui.ui.models.asset_cache_manager import AssetCacheManager
from iPhoto.gui.ui.widgets.asset_delegate import AssetGridDelegate
MICRO_ROLE = int(Qt.UserRole) + 20
cm = AssetCacheManager(QSize(192, 192))
cm.reset_for_album(ROOT)
adapter = AssetRowAdapter(QSize(192, 192), cm)
model = QStandardItemModel()
micro_entries = [e for e in entries if e is not None and e.get("micro_thumbnail_image") is not None]
for e in entries:
    if e is None:
        continue
    row = dict(e)
    row["is_image"] = False
    row["is_video"] = False
    pm = cm.resolve_thumbnail(row, cm.thumbnail_loader().Priority.NORMAL) if hasattr(cm.thumbnail_loader(), "Priority") else None
    if pm is not None:
        hasher.update(f"pm{pm.width()}x{pm.height()};".encode())
    v = adapter.data(row, MICRO_ROLE)
    hasher.update(repr(None if v is None else (v.width(), v.height())).encode())
    it = QStandardItem()
    if v is not None:
        it.setData(v, MICRO_ROLE)
    model.appendRow(it)
delegate = AssetGridDelegate()
canvas = QImage(192, 192, QImage.Format_ARGB32)
for r in range(model.rowCount()):
    canvas.fill(0)
    p = QPainter(canvas)
    opt = QStyleOptionViewItem()
    opt.rect = QRect(0, 0, 192, 192)
    delegate.paint(p, opt, model.index(r, 0))
    p.end()
    hasher.update(hashlib.sha256(bytes(canvas.constBits())).digest())
print(len(rows), len(read), len(geo), len(entries))
print(hasher.hexdigest())
