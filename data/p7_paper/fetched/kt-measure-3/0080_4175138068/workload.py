import hashlib
import numpy as np
import torch
from transformers import ParakeetFeatureExtractor

torch.manual_seed(0)
rng = np.random.default_rng(0)
fe = ParakeetFeatureExtractor()
h = hashlib.sha256()

def feed(out):
    f = out["input_features"].detach().cpu().numpy().astype(np.float32)
    m = out["attention_mask"].detach().cpu().numpy()
    h.update(np.round(f, 3).tobytes())
    h.update(m.astype(np.int8).tobytes())

for it in range(30):
    bs = 1 + it % 6
    lens = [int(rng.integers(8000, 48000)) for _ in range(bs)]
    batch = [(rng.standard_normal(L) * 0.1).astype(np.float32) for L in lens]
    feed(fe(batch, sampling_rate=16000, return_tensors="pt"))
    # single array
    feed(fe(batch[0], sampling_rate=16000, return_tensors="pt"))
    # 2D batched ndarray
    arr = (rng.standard_normal((2, 16000)) * 0.1).astype(np.float32)
    feed(fe(arr, sampling_rate=16000, return_tensors="pt"))
print(h.hexdigest())
