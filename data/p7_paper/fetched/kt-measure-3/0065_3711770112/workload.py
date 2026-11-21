import hashlib, json, os, shutil, logging
from pathlib import Path
from PIL import Image

logging.disable(logging.CRITICAL)
from iPhoto.io.scanner import scan_album, process_media_paths, gather_media_paths
from iPhoto import app

ROOT = Path("/tmp/kt_381/album")
N = 300
FIXED = 1_700_000_000

def make_album():
    marker = ROOT / ".done"
    if marker.exists():
        return
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for i in range(N):
        sub = ROOT / f"d{i % 5}"
        sub.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (32 + i % 7, 24 + i % 5), ((i * 37) % 256, (i * 11) % 256, (i * 3) % 256))
        p = sub / f"img_{i:04d}.jpg"
        img.save(p, "JPEG")
        os.utime(p, (FIXED + i, FIXED + i))
    marker.write_text("ok")

def norm(rows):
    out = []
    for r in rows:
        out.append({k: (str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                    for k, v in sorted(r.items())})
    return sorted(out, key=lambda r: str(r.get("rel")))

make_album()
h = hashlib.sha256()
for _ in range(2):
    rows = list(scan_album(ROOT, ["**/*"], []))
    h.update(json.dumps(norm(rows), sort_keys=True).encode())
    print("scan_album", len(rows))
# early-closed generator (cancellation path)
gen = scan_album(ROOT, ["**/*"], [])
first = [next(gen) for _ in range(5)]
gen.close()
h.update(str(len(first)).encode())
print("early_close", len(first))
# album with corrupt files and a video
BAD = Path("/tmp/kt_381/bad")
if BAD.exists():
    shutil.rmtree(BAD)
BAD.mkdir(parents=True)
for i in range(60):
    (BAD / f"bad_{i:03d}.jpg").write_bytes(b"\xff\xd8garbage" * (i + 1))
    os.utime(BAD / f"bad_{i:03d}.jpg", (FIXED, FIXED))
(BAD / "clip.mov").write_bytes(b"\x00" * 64)
os.utime(BAD / "clip.mov", (FIXED, FIXED))
rows = list(scan_album(BAD, ["**/*"], []))
h.update(json.dumps(norm(rows), sort_keys=True).encode())
print("bad_album", len(rows))
imgs, vids = gather_media_paths(ROOT, ["**/*"], [])
rows = list(process_media_paths(ROOT, sorted(imgs), sorted(vids)))
h.update(json.dumps(norm(rows), sort_keys=True).encode())
print("process_media_paths", len(rows))
rows = app.rescan(ROOT)
h.update(json.dumps(norm(rows), sort_keys=True).encode())
print("rescan", len(rows))

from PySide6.QtCore import QCoreApplication
qapp = QCoreApplication.instance() or QCoreApplication([])
from iPhoto.gui.ui.tasks.scanner_worker import ScannerWorker, ScannerSignals
from iPhoto.gui.ui.tasks.rescan_worker import RescanWorker, RescanSignals

sig = ScannerSignals()
got = {"chunks": 0, "final": None, "err": None, "prog_last": None}
sig.chunkReady.connect(lambda r, rows: got.__setitem__("chunks", got["chunks"] + len(rows)))
sig.finished.connect(lambda r, rows: got.__setitem__("final", rows))
sig.error.connect(lambda r, m: got.__setitem__("err", m))
sig.progressUpdated.connect(lambda r, a, b: got.__setitem__("prog_last", (a, b)))
w = ScannerWorker(ROOT, ["**/*"], [], sig)
w.run()
print("scanner_worker", got["chunks"], len(got["final"] or []), got["err"], got["prog_last"])
h.update(json.dumps(norm(got["final"] or []), sort_keys=True).encode())
h.update(str((got["chunks"], got["err"], got["prog_last"])).encode())

rs = RescanSignals()
res = {}
rs.finished.connect(lambda r, ok: res.__setitem__("ok", ok))
rs.error.connect(lambda r, m: res.__setitem__("err", m))
rw = RescanWorker(ROOT, rs)
rw.run()
print("rescan_worker", res)
h.update(str(sorted(res.items())).encode())
print(h.hexdigest())
