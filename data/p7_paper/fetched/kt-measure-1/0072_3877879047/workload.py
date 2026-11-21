import hashlib, tempfile
import torch
from datasets import Dataset
from open_instruct.data_loader import HFDataLoader, to_device

torch.manual_seed(0)
N, L = 2000, 64
g = torch.Generator().manual_seed(0)
ids = torch.randint(0, 32000, (N, L), generator=g).tolist()
ds = Dataset.from_dict({"input_ids": ids, "index": list(range(N))})

def collator(examples):
    return {
        "input_ids": torch.tensor([e["input_ids"] for e in examples], dtype=torch.long),
        "index": torch.tensor([e["index"] for e in examples], dtype=torch.long),
        "prompt_id": [e["prompt_id"] for e in examples],
    }

h = hashlib.sha256()
dev = torch.device("cpu")
with tempfile.TemporaryDirectory() as wd:
    for epoch_seed in range(2):
        dl = HFDataLoader(ds, batch_size=16, seed=epoch_seed, dp_rank=0, dp_world_size=1,
                          work_dir=wd, collator=collator, device=dev)
        for b in dl:
            h.update(b["input_ids"].sum().item().to_bytes(8, "little"))
            h.update(b["index"].numpy().tobytes())
            h.update("".join(b["prompt_id"]).encode())

# Direct to_device calls with mixed tensor / non-tensor values
batch = {f"t{i}": torch.arange(i * 10, dtype=torch.float32).reshape(-1) for i in range(20)}
batch["meta"] = "x"
batch["lst"] = [1, 2, 3]
acc = 0.0
for _ in range(10000):
    out = to_device(batch, dev)
    acc += out["t5"][3].item()
assert to_device(batch, None) is batch
h.update(repr(acc).encode())
h.update(repr(sorted(out.keys())).encode())
print(h.hexdigest())
