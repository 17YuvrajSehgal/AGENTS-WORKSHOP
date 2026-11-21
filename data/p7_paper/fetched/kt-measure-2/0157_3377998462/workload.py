import os, sys, shutil, hashlib, inspect, random, io, contextlib

ROOT = "/tmp/kt_41"
HOME = os.path.join(ROOT, "home")
DATA = os.path.join(ROOT, "data")
os.environ["HOME"] = HOME
shutil.rmtree(ROOT, ignore_errors=True)
os.makedirs(HOME)
os.makedirs(DATA)

import numpy as np
from dir_assistant.assistant.index import create_file_index
from dir_assistant.assistant.base_embed import BaseEmbed
from dir_assistant.cli.config import CONFIG_DEFAULTS

# Deterministic input tree
rng = random.Random(41)
WORDS = ["alpha", "beta", "gamma", "delta", "index", "embed", "chunk", "file",
         "def", "return", "class", "import", "value", "token", "vector"]
for d in range(6):
    sub = os.path.join(DATA, f"dir{d}")
    os.makedirs(sub)
    for f in range(25):
        lines = []
        for _ in range(rng.randint(40, 120)):
            lines.append(" ".join(rng.choice(WORDS) for _ in range(rng.randint(2, 14))))
        with open(os.path.join(sub, f"f{f}.txt"), "w") as fh:
            fh.write("\n".join(lines))
        os.utime(os.path.join(sub, f"f{f}.txt"), (1_600_000_000, 1_600_000_000))


class FakeEmbed(BaseEmbed):
    """Local stand-in for the external embedding model."""
    DIM = 64

    def __init__(self):
        pass

    def create_embedding(self, text):
        h = hashlib.sha256(text.encode()).digest()
        seed = int.from_bytes(h[:8], "little")
        return np.random.default_rng(seed).standard_normal(self.DIM).astype("float32")

    def count_tokens(self, text):
        return len(text.split())

    def get_chunk_size(self):
        return 120


def run(verbose):
    embed = FakeEmbed()
    params = inspect.signature(create_file_index).parameters
    config = dict(CONFIG_DEFAULTS)
    if "config_dict" in params:
        return create_file_index(embed, [], 120, config, [], verbose)
    return create_file_index(embed, [], 120, [], verbose)


os.chdir(DATA)
digest = hashlib.sha256()
cache = os.path.join(HOME, ".cache", "dir-assistant")
for rep in range(8):
    shutil.rmtree(cache, ignore_errors=True)
    with contextlib.redirect_stdout(io.StringIO()):
        idx, chunks = run(verbose=(rep == 0))
        # second call hits the embedding cache
        idx2, chunks2 = run(verbose=True)
    for c in sorted(chunks, key=lambda c: (c["filepath"], c["text"])):
        digest.update(c["text"].encode())
        digest.update(str(c["tokens"]).encode())
    digest.update(str(idx.ntotal).encode())
    digest.update(str(len(chunks2)).encode())
    D, I = idx.search(np.asarray(FakeEmbed().create_embedding("alpha beta")).reshape(1, -1), 5)
    digest.update(np.round(D, 3).tobytes())
print(len(chunks))
print(digest.hexdigest())
