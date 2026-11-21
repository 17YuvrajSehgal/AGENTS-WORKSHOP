import hashlib
import logging
import warnings

import torch

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import pytorch_lightning as pl
from torch.utils.data import DataLoader

from piper_train.vits.dataset import Batch
from piper_train.vits.lightning import VitsModel
from piper_train.vits.models import SynthesizerTrn

torch.set_num_threads(1)
h = hashlib.sha256()

SMALL = dict(
    inter_channels=64, hidden_channels=64, filter_channels=128,
    n_heads=2, n_layers=6, kernel_size=3, p_dropout=0.1, resblock="2",
    resblock_kernel_sizes=(3, 5, 7),
    resblock_dilation_sizes=((1, 2), (2, 6), (3, 12)),
    upsample_rates=(8, 8, 4), upsample_initial_channel=64,
    upsample_kernel_sizes=(16, 16, 8),
)


# ---------- Part 1: direct SynthesizerTrn forward (MAS / DP paths) ----------
def make(use_sdp, n_speakers, gin):
    torch.manual_seed(1)
    return SynthesizerTrn(
        n_vocab=100, spec_channels=513, segment_size=32,
        n_speakers=n_speakers, gin_channels=gin, use_sdp=use_sdp, prosody_dim=0,
        **SMALL,
    )


B = 4
for use_sdp, ns, gin in [(True, 1, 0), (False, 1, 0), (False, 4, 64), (True, 4, 64)]:
    model = make(use_sdp, ns, gin)
    for step in range(1):
        g = torch.Generator().manual_seed(100 + step)
        x_len = torch.tensor([40, 35, 30, 25])
        y_len = torch.tensor([120, 100, 90, 80])
        x = torch.randint(1, 100, (B, 40), generator=g)
        y = torch.randn(B, 513, 120, generator=g)
        sid = torch.arange(B) % ns if ns > 1 else None
        model.train()
        torch.manual_seed(step)
        out = model(x, x_len, y, y_len, sid=sid)
        h.update(repr(tuple(out[0].shape)).encode())
        model.eval()
        torch.manual_seed(step)
        with torch.no_grad():
            out = model(x, x_len, y, y_len, sid=sid)
        h.update(repr(round(float(out[1].sum()), 2)).encode())
        h.update(repr(float(out[2].sum())).encode())


# ---------- Part 2: Lightning training steps (VitsModel) ----------
def make_batches(n, ns, seed):
    g = torch.Generator().manual_seed(seed)
    batches = []
    for _ in range(n):
        pl_ = torch.tensor([30, 26])
        sl = torch.tensor([40, 34])
        ph = torch.randint(1, 60, (2, 30), generator=g)
        spec = torch.rand(2, 513, 40, generator=g)
        audio = torch.randn(2, 1, 40 * 256, generator=g) * 0.1
        batches.append(Batch(
            phoneme_ids=ph, phoneme_lengths=pl_, spectrograms=spec,
            spectrogram_lengths=sl, audios=audio,
            audio_lengths=sl * 256,
            speaker_ids=(torch.tensor([0, 1]) if ns > 1 else None),
        ))
    return batches


configs = [
    dict(num_speakers=2, gin_channels=32, use_sdp=False,
         use_duration_discriminator=True, dp_lr=1e-3,
         cosine_scheduler=True, warmup_epochs=1, max_epochs=3),
    dict(num_speakers=1, use_sdp=False, use_duration_discriminator=True),
]
for cfg in configs:
    pl.seed_everything(7, verbose=False)
    model = VitsModel(
        num_symbols=60, dataset=None, use_wavlm_discriminator=False,
        segment_size=2048, prosody_dim=0, batch_size=2, **SMALL, **cfg,
    )
    batches = make_batches(1, cfg["num_speakers"], 11)
    dl = DataLoader(batches, batch_size=None, shuffle=False)
    trainer = pl.Trainer(
        accelerator="cpu", devices=1, max_epochs=1, logger=False,
        enable_checkpointing=False, enable_progress_bar=False,
        enable_model_summary=False, limit_val_batches=0, num_sanity_val_steps=0,
    )
    trainer.fit(model, train_dataloaders=dl)
    h.update(repr(int(trainer.global_step)).encode())
    h.update(repr(sorted(trainer.callback_metrics.keys())).encode())
    lrs = [round(o.param_groups[0]["lr"], 10) for o in trainer.optimizers]
    h.update(repr(lrs).encode())

print(h.hexdigest())
