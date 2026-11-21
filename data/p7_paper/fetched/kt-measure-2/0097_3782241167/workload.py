import hashlib, os, shutil
from pathlib import Path
from iPhoto.config import DEFAULT_EXCLUDE, DEFAULT_INCLUDE, EXPORT_DIR_NAME, WORK_DIR_NAME
from iPhoto.io.scanner import gather_media_paths

ROOT = Path("/tmp/kt_494/library")
MARK = ROOT.parent / "built_v1"
EXTS = [".jpg", ".JPEG", ".png", ".heic", ".mov", ".mp4", ".txt", ".json"]

def build():
    if MARK.exists():
        return
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for a in range(12):
        for b in range(6):
            d = ROOT / f"album{a:02d}" / f"sub{b}"
            d.mkdir(parents=True)
            for i in range(25):
                (d / f"img{i:03d}{EXTS[(a + b + i) % len(EXTS)]}").touch()
            if b % 2 == 0:
                for special in (WORK_DIR_NAME, EXPORT_DIR_NAME):
                    sd = d / special / "cache"
                    sd.mkdir(parents=True)
                    for i in range(40):
                        (sd / f"thumb{i:03d}.jpg").touch()
        (ROOT / f"album{a:02d}" / "dangling.jpg").symlink_to(ROOT / "nope.jpg")
    w = ROOT / WORK_DIR_NAME
    w.mkdir()
    for i in range(300):
        (w / f"c{i}.png").touch()
    MARK.touch()

build()
h = hashlib.sha256()
for rep in range(6):
    imgs, vids = gather_media_paths(ROOT, DEFAULT_INCLUDE, DEFAULT_EXCLUDE)
    for p in sorted(str(x.relative_to(ROOT)) for x in imgs):
        h.update(b"I" + p.encode())
    for p in sorted(str(x.relative_to(ROOT)) for x in vids):
        h.update(b"V" + p.encode())
    if rep == 0:
        print(len(imgs), len(vids))
# root inside excluded dir
imgs, vids = gather_media_paths(ROOT / WORK_DIR_NAME, DEFAULT_INCLUDE, DEFAULT_EXCLUDE)
print("inside work dir:", len(imgs), len(vids))
h.update(str((len(imgs), len(vids))).encode())
print(h.hexdigest())
