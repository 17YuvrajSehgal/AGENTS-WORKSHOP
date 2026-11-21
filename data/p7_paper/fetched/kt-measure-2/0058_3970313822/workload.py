import hashlib
import gzip
import json
import logging
import os
import random
import shutil
import tempfile

ROOT = "/tmp/kt_2934"
# Keep zephyr scratch storage on local disk: make the GCP metadata-server region
# lookup fail fast (no network use) and point MARIN_PREFIX at a local directory.
os.environ["http_proxy"] = "http://127.0.0.1:9"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:9"
os.environ.pop("no_proxy", None)
os.environ.pop("NO_PROXY", None)
os.environ["MARIN_PREFIX"] = ROOT + "/prefix"

logging.basicConfig(level=logging.WARNING)

from tokenizers import Tokenizer, models, pre_tokenizers, trainers
from transformers import PreTrainedTokenizerFast

from marin.processing.tokenize.tokenize import TokenizeConfig, tokenize
from levanter.store.cache import CacheLedger, TreeCache
import numpy as np

rng = random.Random(1234)
WORDS = [
    "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(2, 9)))
    for _ in range(3000)
]


def make_doc(r):
    n = r.randint(30, 400)
    return " ".join(r.choice(WORDS) for _ in range(n)) + "."


def build_tokenizer(path):
    if os.path.exists(os.path.join(path, "tokenizer.json")):
        return
    os.makedirs(path, exist_ok=True)
    r = random.Random(7)
    corpus = [make_doc(r) for _ in range(500)]
    tok = Tokenizer(models.BPE(unk_token="<unk>"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    trainer = trainers.BpeTrainer(vocab_size=2000, special_tokens=["<unk>", "<s>", "</s>"])
    tok.train_from_iterator(corpus, trainer)
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, unk_token="<unk>", bos_token="<s>", eos_token="</s>")
    fast.save_pretrained(path)


def write_data(d, prefix, nfiles, ndocs, seed):
    os.makedirs(d, exist_ok=True)
    r = random.Random(seed)
    for i in range(nfiles):
        with gzip.open(os.path.join(d, f"{prefix}_{i:03d}.jsonl.gz"), "wt") as f:
            for _ in range(ndocs):
                f.write(json.dumps({"text": make_doc(r)}) + "\n")


def main():
    tok_path = os.path.join(ROOT, "tokenizer")
    build_tokenizer(tok_path)
    data_dir = os.path.join(ROOT, "data")
    tr = os.path.join(data_dir, "trn")
    va = os.path.join(data_dir, "dev_validation")
    if not os.path.exists(os.path.join(data_dir, "done")):
        shutil.rmtree(data_dir, ignore_errors=True)
        write_data(tr, "part", 6, 150, 1)
        write_data(va, "val", 2, 100, 2)
        open(os.path.join(data_dir, "done"), "w").close()

    h = hashlib.sha256()
    work = tempfile.mkdtemp(prefix="run_", dir=ROOT)
    try:
        cache = os.path.join(work, "cache")
        cfg = TokenizeConfig(
            train_paths=[tr + "/"],
            validation_paths=[va + "/"],
            cache_path=cache,
            tokenizer=tok_path,
            window_size_bytes=300_000,
        )
        tokenize(cfg)
        exemplar = {"input_ids": np.array([0], dtype=np.int32)}
        for split in ("train", "validation"):
            d = os.path.join(cache, split)
            ledger = CacheLedger.load(d)
            c = TreeCache.load(d, exemplar=exemplar)
            n = len(c)
            rows = []
            for i in range(n):
                ids = np.asarray(c[i]["input_ids"], dtype=np.int64)
                rows.append(hashlib.sha256(ids.tobytes()).hexdigest())
            rows.sort()  # order-insensitive across sharding
            for x in rows:
                h.update(x.encode())
            with open(os.path.join(d, ".stats.json")) as f:
                stats = json.load(f)
            print(split, ledger.total_num_rows, n, stats["total_tokens"], stats["total_elements"])
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(h.hexdigest())


if __name__ == "__main__":
    main()
