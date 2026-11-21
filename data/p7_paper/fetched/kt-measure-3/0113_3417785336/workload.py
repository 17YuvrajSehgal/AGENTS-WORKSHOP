import os
os.makedirs("/tmp/kt_22086/cfg", exist_ok=True)
os.environ["YOLO_CONFIG_DIR"] = "/tmp/kt_22086/cfg"
os.environ.setdefault("YOLO_OFFLINE", "1")
import hashlib, torch
from ultralytics import YOLO
from ultralytics.engine.model import Model

torch.manual_seed(0)
torch.set_num_threads(1)
cfgs = ["yolo11n.yaml", "yolo11n-seg.yaml", "yolo11n-cls.yaml", "yolo11n-pose.yaml", "yolo11n-obb.yaml", "yolov8n.yaml"]
out = []
x = torch.zeros(1, 3, 64, 64)
for rep in range(5):
    for c in cfgs:
        m = YOLO(c)
        for _ in range(50):
            w = YOLO(m)
            w2 = Model(w)
            w3 = YOLO(w2)
        out.append((c, w3.task, sum(p.numel() for p in w3.model.parameters()), w3.ckpt_path, w3.cfg is not None))
h = hashlib.sha256(repr(out).encode()).hexdigest()
print(out[:len(cfgs)])
print(h)
