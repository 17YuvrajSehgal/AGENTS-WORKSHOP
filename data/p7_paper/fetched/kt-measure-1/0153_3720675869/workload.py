import os, hashlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import numpy as np
import cv2
from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication
from iPhoto.gui.ui.tasks.video_frame_grabber import grab_video_frame
from iPhoto.utils.ffmpeg import extract_video_frame

app = QGuiApplication.instance() or QGuiApplication([])

d = Path("/tmp/kt_407"); d.mkdir(parents=True, exist_ok=True)
videos = []
for name, (w, h) in [("a.mp4", (640, 360)), ("b.mp4", (480, 640)), ("c.avi", (320, 240))]:
    p = d / name
    if not p.exists():
        rng = np.random.default_rng(len(name) + w)
        fourcc = cv2.VideoWriter_fourcc(*("mp4v" if name.endswith("mp4") else "MJPG"))
        vw = cv2.VideoWriter(str(p), fourcc, 30.0, (w, h))
        base = rng.integers(0, 255, (h, w, 3), dtype=np.uint8)
        for i in range(90):
            fr = np.roll(base, i * 3, axis=1).copy()
            cv2.putText(fr, str(i), (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            vw.write(fr)
        vw.release()
    videos.append(p)
bad = d / "bad.mp4"
bad.write_bytes(b"not a video at all" * 10)

h = hashlib.sha256()
sizes = [QSize(160, 160), QSize(320, 180), QSize(35, 35), QSize(1000, 1000), QSize(0, 0)]
for rep in range(1):
    for v in videos:
        for sz in sizes:
            for st, dur in [(None, None), (None, 3.0), (1.0, 3.0), (2.9, 3.0), (0.0, None)]:
                img = grab_video_frame(v, sz, still_image_time=st, duration=dur)
                r = None if img is None else (img.width(), img.height())
                h.update(repr((v.name, sz.width(), sz.height(), st, dur, r)).encode())
    r = grab_video_frame(bad, QSize(100, 100), duration=2.0)
    h.update(repr(r is None).encode())

for v in videos:
    for fmt in ("jpeg", "png"):
        for sc in [(160, 90), (35, 35), None]:
            data = extract_video_frame(v, at=1.0, scale=sc, format=fmt)
            h.update(hashlib.sha256(data).digest())
print(h.hexdigest())
