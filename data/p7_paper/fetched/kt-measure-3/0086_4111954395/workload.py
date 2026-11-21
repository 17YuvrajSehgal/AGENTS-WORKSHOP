import hashlib, os, sys, tempfile, warnings, logging
from pathlib import Path
_SRC = Path(sys.executable).absolute().parent.parent.parent / "src"
sys.path.insert(0, str(_SRC))
os.chdir(_SRC)
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)
import numpy as np, pandas as pd, torch
torch.set_num_threads(1)
from binanceneural.config import TrainingConfig
from binanceneural.data import (BinanceHourlyDataModule, BinanceHourlyDataset, FeatureNormalizer,
                                MultiSymbolDataModule, MultiSymbolDataset)
from binanceneural.trainer import BinanceHourlyTrainer

SEQ = 32
NF = 13


def make_frame(rng, n):
    close = 100 + np.cumsum(rng.standard_normal(n) * 0.5)
    close = np.maximum(close, 5.0)
    df = pd.DataFrame({
        "open": close * (1 + 0.002 * rng.standard_normal(n)),
        "high": close * 1.01, "low": close * 0.99, "close": close,
        "reference_close": close,
    })
    for h in (1, 4):
        df[f"predicted_high_p50_h{h}"] = close * 1.012
        df[f"predicted_low_p50_h{h}"] = close * 0.988
        df[f"predicted_close_p50_h{h}"] = close * (1 + 0.001 * rng.standard_normal(n))
    feats = rng.standard_normal((n, NF)).astype(np.float32)
    return df, feats


def make_single(rng, n_train, n_val):
    dm = BinanceHourlyDataModule.__new__(BinanceHourlyDataModule)
    tf, tx = make_frame(rng, n_train)
    vf, vx = make_frame(rng, n_val)
    dm.normalizer = FeatureNormalizer.fit(tx)
    dm.feature_columns = tuple(f"f{i}" for i in range(NF))
    dm.train_dataset = BinanceHourlyDataset(tf, dm.normalizer.transform(tx), SEQ, primary_horizon=1)
    dm.val_dataset = BinanceHourlyDataset(vf, dm.normalizer.transform(vx), SEQ, primary_horizon=1)
    return dm


def make_multi(rng):
    subs = [make_single(rng, 100, 60) for _ in range(3)]
    mm = MultiSymbolDataModule.__new__(MultiSymbolDataModule)
    mm.train_dataset = MultiSymbolDataset([s.train_dataset for s in subs])
    mm.val_dataset = subs[0].val_dataset
    mm.normalizer = subs[0].normalizer
    mm.feature_columns = subs[0].feature_columns
    return mm


def run(dm, tmp, name):
    cfg = TrainingConfig(epochs=2, batch_size=8, sequence_length=SEQ, transformer_dim=32,
                         transformer_layers=1, transformer_heads=4, learning_rate=1e-3,
                         use_compile=False, use_amp=False, use_tf32=False, use_flash_attention=False,
                         checkpoint_root=Path(tmp) / "ckpts", run_name=name, seed=42,
                         device="cpu", wandb_project=None)
    art = BinanceHourlyTrainer(cfg, dm).train()
    out = []
    for h in art.history:
        out.append((h.epoch, round(h.train_loss, 5), round(h.val_loss, 5), round(h.val_score, 5)))
    return out


def main():
    torch.manual_seed(0)
    rng = np.random.default_rng(0)
    h = hashlib.sha256()
    with tempfile.TemporaryDirectory(dir="/tmp/kt_46") as tmp:
        single = make_single(rng, 220, 80)
        multi = make_multi(rng)
        # loader-construction + iteration over plain loaders
        for dm in (single, multi):
            for bs in (4, 16):
                for _ in range(3):
                    tl = dm.train_dataloader(bs, 0)
                    vl = dm.val_dataloader(bs, 0)
                    h.update(str((len(tl), len(vl))).encode())
                    for b in vl:
                        h.update(np.round(b["close"].numpy().astype(np.float64), 4).tobytes())
        r1 = run(single, tmp, "single")
        r2 = run(multi, tmp, "multi")
        print(r1)
        print(r2)
        h.update(repr((r1, r2)).encode())
    print(h.hexdigest())


if __name__ == "__main__":
    main()
