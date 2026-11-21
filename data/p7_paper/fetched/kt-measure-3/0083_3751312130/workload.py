import hashlib, os, queue, random, shutil
from pathlib import Path
from iPhoto.io.scanner import gather_media_paths, FileDiscoverer

ROOT = Path("/tmp/kt_475/album")
EXTS = [".jpg", ".JPEG", ".png", ".heic", ".mov", ".mp4", ".txt", ".json", ".m4v", ".xmp"]

def build():
    marker = ROOT / ".built_v1"
    if marker.exists():
        return
    if ROOT.exists():
        shutil.rmtree(ROOT)
    rng = random.Random(475)
    for i in range(40):
        for j in range(5):
            d = ROOT / f"year{i:02d}" / f"evt{j}"
            d.mkdir(parents=True, exist_ok=True)
            for k in range(12):
                (d / f"IMG_{i}_{j}_{k}{rng.choice(EXTS)}").touch()
        for sub in (".iPhoto/cache", "exported", ".iPhoto"):
            d = ROOT / f"year{i:02d}" / sub
            d.mkdir(parents=True, exist_ok=True)
            for k in range(15):
                (d / f"skip{k}.jpg").touch()
        sk = ROOT / f"year{i:02d}" / "skipme"
        sk.mkdir(exist_ok=True)
        for k in range(5):
            (sk / f"x{k}.jpg").touch()
    marker.touch()

build()
inc = ["**/*"]
exc = ["**/skipme/**", "**/*.xmp"]
h = hashlib.sha256()
for rep in range(4):
    imgs, vids = gather_media_paths(ROOT, inc, exc)
    for p in sorted(imgs) + sorted(vids):
        h.update(str(p.relative_to(ROOT)).encode())
    q = queue.Queue(maxsize=64)
    d = FileDiscoverer(ROOT, inc, exc, q)
    d.start()
    found = []
    while True:
        item = q.get()
        if item is None:
            break
        found.append(item.relative_to(ROOT).as_posix())
    d.join()
    for p in sorted(found):
        h.update(p.encode())
    h.update(str(d.total_found).encode())
    if rep == 0:
        print(len(imgs), len(vids), d.total_found)
print(h.hexdigest())
