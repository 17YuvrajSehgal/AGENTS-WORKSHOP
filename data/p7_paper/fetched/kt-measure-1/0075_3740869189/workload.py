import hashlib, json, os, shutil, unicodedata, logging
from pathlib import Path
from PIL import Image

logging.disable(logging.CRITICAL)
from iPhoto.io import scanner

ROOT = Path("/tmp/kt_466/album")
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)

names = []
for i in range(60):
    if i % 3 == 0:
        base = unicodedata.normalize("NFC", f"café_{i}")
    elif i % 3 == 1:
        base = unicodedata.normalize("NFD", f"Ångström_{i}")
    else:
        base = f"img_{i}"
    sub = ROOT / ("sub" if i % 2 else "")
    sub.mkdir(exist_ok=True)
    p = sub / f"{base}.png" if i % 4 else sub / f"{base}.jpg"
    img = Image.new("RGB", (40 + i, 30 + (i % 7)), ((i * 37) % 256, (i * 11) % 256, (i * 5) % 256))
    img.save(p)
    os.utime(p, (1600000000 + i, 1600000000 + i))
    names.append(p)

paths = sorted(names, key=lambda p: p.as_posix())

def digest_rows(rows):
    out = []
    for r in rows:
        r = dict(r)
        mt = r.get("micro_thumbnail")
        if isinstance(mt, bytes):
            r["micro_thumbnail"] = hashlib.sha256(mt).hexdigest()
        out.append(r)
    return json.dumps(out, sort_keys=True, default=str)

h = hashlib.sha256()
for rep in range(3):
    # 1) with exiftool available
    rows = list(scanner._process_path_stream(ROOT, iter(paths), batch_size=25))
    h.update(digest_rows(rows).encode())

    # 2) without exiftool on PATH (metadata payloads empty -> fallback lookups)
    old = os.environ["PATH"]
    os.environ["PATH"] = "/nonexistent"
    try:
        rows2 = list(scanner._process_path_stream(ROOT, iter(paths), batch_size=25))
    finally:
        os.environ["PATH"] = old
    h.update(digest_rows(rows2).encode())

    # 3) incremental scan with existing index keyed by alternate normalization
    index = {}
    for k, r in enumerate(rows):
        rel = r["rel"]
        if k % 3 == 0:
            key = unicodedata.normalize("NFD", rel)
        elif k % 3 == 1:
            key = unicodedata.normalize("NFC", rel)
        else:
            key = "missing/" + rel
        index[key] = dict(r)
    rows3 = list(scanner._process_path_stream(ROOT, iter(paths), existing_index=index, batch_size=25))
    h.update(digest_rows(rows3).encode())
    print(rep, len(rows), len(rows2), len(rows3))

print(h.hexdigest())
