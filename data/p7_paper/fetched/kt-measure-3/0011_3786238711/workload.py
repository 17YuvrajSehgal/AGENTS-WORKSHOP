import hashlib, os, queue
from pathlib import Path
from iPhoto.io.scanner import FileDiscoverer
from iPhoto.utils.pathutils import is_excluded, should_include

ROOT = Path("/tmp/kt_507/album")
EXTS = ["jpg", "JPG", "png", "heic", "mov", "mp4", "txt", "tmp", "json", "ignore"]
if not (ROOT / ".done").exists():
    for d in range(40):
        sub = ROOT / f"d{d:02d}" / ("temp" if d % 7 == 0 else "pics")
        sub.mkdir(parents=True, exist_ok=True)
        for i in range(50):
            (sub / f"f{i:03d}.{EXTS[(i + d) % len(EXTS)]}").touch()
    (ROOT / ".done").touch()

INC = ["**/*.{jpg,JPG,jpeg,png,heic,heif}", "**/*.{mov,mp4,m4v}"]
EXC = ["**/temp/**", "**/*.{ignore,tmp}", "**/.iPhoto/**", "**/f00{1,2,3}.*"]

h = hashlib.sha256()
for rep in range(8):
    q = queue.Queue()
    t = FileDiscoverer(ROOT, INC, EXC, q)
    t.start(); t.join()
    items = []
    while True:
        x = q.get_nowait()
        if x is None:
            break
        items.append(x.relative_to(ROOT).as_posix())
    items.sort()
    h.update(("\n".join(items) + f"|{t.total_found}").encode())

files = sorted(p for p in ROOT.rglob("*") if p.is_file())
res = []
for rep in range(5):
    for p in files:
        res.append((is_excluded(p, EXC, root=ROOT), should_include(p, INC, EXC, root=ROOT)))
h.update(repr(res).encode())
print(len(items), sum(a for a, b in res), sum(b for a, b in res))
print(h.hexdigest())
