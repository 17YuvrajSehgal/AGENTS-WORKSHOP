"""Workload: train a tiny VITS model for a few steps (generator + discriminator).

Exercises VitsModel.__init__, train_dataloader and training_step.
On head, training_step uses manual optimization and runs through Trainer.fit.
On base, training_step(batch, batch_idx, optimizer_idx) is not supported by
pytorch-lightning 2.x Trainer.fit (raises), so the same work is driven by
calling training_step per optimizer index with the model's own optimizers.
"""
import hashlib
import json
import logging
import os
import warnings

import torch

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import pytorch_lightning as pl  # noqa: E402
from piper_train.vits.lightning import VitsModel  # noqa: E402

torch.set_num_threads(1)

DATA_DIR = "/tmp/kt_113"
N_UTT = 12
HOP = 256
FILTER = 1024
STEPS = 3


def make_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    g = torch.Generator().manual_seed(0)
    lines = []
    for i in range(N_UTT):
        frames = 20 + (i * 3) % 12
        n_ph = 8 + i % 6
        audio = (torch.rand(1, frames * HOP, generator=g) * 2 - 1) * 0.5
        spec = torch.rand(FILTER // 2 + 1, frames, generator=g)
        a_path = os.path.join(DATA_DIR, f"a{i}.pt")
        s_path = os.path.join(DATA_DIR, f"s{i}.pt")
        torch.save(audio, a_path)
        torch.save(spec, s_path)
        ph = torch.randint(1, 40, (n_ph,), generator=g).tolist()
        lines.append(
            json.dumps(
                {"phoneme_ids": ph, "audio_norm_path": a_path, "audio_spec_path": s_path}
            )
        )
    path = os.path.join(DATA_DIR, "dataset.jsonl")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def make_model(ds_path):
    torch.manual_seed(1234)
    return VitsModel(
        num_symbols=40,
        num_speakers=1,
        dataset=[ds_path],
        batch_size=2,
        num_workers=0,
        num_test_examples=1,
        validation_split=0.0,
        hidden_channels=32,
        inter_channels=32,
        filter_channels=64,
        n_layers=2,
        upsample_initial_channel=32,
        segment_size=2048,
        use_sdp=False,
        learning_rate=2e-4,
    )


def manual_loop(model, steps):
    opts, _scheds = model.configure_optimizers()
    model.train()
    it = iter(model.train_dataloader())
    for i in range(steps):
        batch = next(it)
        for idx, opt in enumerate(opts):
            opt.zero_grad()
            loss = model.training_step(batch, i, idx)
            loss.backward()
            opt.step()


def run_once(ds_path):
    model = make_model(ds_path)
    torch.manual_seed(7)
    trainer = pl.Trainer(
        accelerator="cpu",
        devices=1,
        max_steps=STEPS,
        max_epochs=1,
        logger=False,
        enable_checkpointing=False,
        enable_progress_bar=False,
        enable_model_summary=False,
        num_sanity_val_steps=0,
        limit_val_batches=0,
    )
    mode = "fit"
    try:
        trainer.fit(model)
    except Exception as e:  # base: optimizer_idx-style training_step unsupported
        mode = "manual:" + type(e).__name__
        model = make_model(ds_path)
        torch.manual_seed(7)
        manual_loop(model, STEPS)
    vals = [round(float(p.detach().double().sum()), 3) for p in model.parameters()]
    return mode, vals


def main():
    ds_path = make_dataset()
    h = hashlib.sha256()
    for _ in range(1):
        mode, vals = run_once(ds_path)
        print("mode", mode, "nparams", len(vals))
        h.update(json.dumps(vals).encode())
    print(h.hexdigest())


if __name__ == "__main__":
    main()
