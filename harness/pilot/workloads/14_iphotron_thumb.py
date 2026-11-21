# iPhotron #501 "Bolt: Optimize micro-thumbnail generation" (Pillow draft
# mode for JPEGs). Pilot workload (hand-written, experimenter has read the
# PR): generate micro-thumbnails for 30 large JPEGs (4000x3000).
# Last line = SHA-256 over the thumbnail bytes (draft decoding may change
# pixels, so a difference is possible and is recorded, not hidden).
import hashlib
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PIL import Image  # noqa: E402

from iPhoto.utils.image_loader import generate_micro_thumbnail  # noqa: E402

ROOT = Path("/tmp/kt_iphotron_jpeg")
files = []
for i in range(30):
    p = ROOT / f"photo_{i:02d}.jpg"
    if not p.exists():  # created once, deterministic content
        ROOT.mkdir(parents=True, exist_ok=True)
        img = Image.linear_gradient("L").resize((4000, 3000)).convert("RGB")
        img = Image.merge("RGB", [img.getchannel(0).rotate(i * 12),
                                  img.getchannel(1), img.getchannel(2).transpose(0)])
        img.save(p, "JPEG", quality=90)
    files.append(p)

h = hashlib.sha256()
for p in files:
    thumb = generate_micro_thumbnail(p)
    assert thumb is not None, p
    h.update(thumb)
print(len(files))
print(h.hexdigest())
