import os, sys, io, hashlib, random, runpy, contextlib

SRC = os.path.abspath(os.path.join(sys.prefix, "..", "src"))
os.chdir(SRC)
sys.path.insert(0, SRC)
SCRIPT = os.path.join(SRC, "seedrecover_batch.py")

WORK = "/tmp/kt_633"
os.makedirs(WORK + "/home", exist_ok=True)
os.environ["HOME"] = WORK + "/home"
os.makedirs(WORK, exist_ok=True)

with open(os.path.join(SRC, "btcrecover", "wordlists", "bip39-en.txt"), encoding="utf-8") as f:
    WORDS = [w.strip() for w in f if w.strip()]
assert len(WORDS) == 2048

def make_mnemonic(rng):
    ent = bytes(rng.getrandbits(8) for _ in range(16))
    cs = hashlib.sha256(ent).digest()[0] >> 4
    bits = (int.from_bytes(ent, "big") << 4) | cs
    return " ".join(WORDS[(bits >> (11 * (11 - i))) & 0x7FF] for i in range(12))

MATCH_SEED = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
MATCH_ADDR = "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA"
COMMON = ["--wallet-type", "bip39", "--language", "en", "--addrs", MATCH_ADDR,
          "--addr-limit", "1", "--typos", "0", "--no-eta", "--dsw", "--threads", "1"]

def run_batch(name, seeds, pre_progress=None, extra=()):
    batch = os.path.join(WORK, name + ".txt")
    prog = os.path.join(WORK, name + ".progress")
    with open(batch, "w", encoding="utf-8") as f:
        f.write("\n".join(seeds) + "\n")
    if os.path.exists(prog):
        os.remove(prog)
    if pre_progress:
        with open(prog, "w", encoding="utf-8") as f:
            f.write(pre_progress)
    old_argv = sys.argv
    sys.argv = [SCRIPT, "--batch-file", batch, "--batch-progress-file", prog] + list(extra) + COMMON
    code = None
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            runpy.run_path(SCRIPT, run_name="__main__")
    except SystemExit as e:
        code = e.code
    finally:
        sys.argv = old_argv
    with open(prog, encoding="utf-8") as f:
        content = f.read()
    return code, content

rng = random.Random(633)
results = []
# Run 1: many non-matching seeds, then the matching seed, then more
seeds = [make_mnemonic(rng) for _ in range(12)] + [MATCH_SEED] + [make_mnemonic(rng) for _ in range(3)]
results.append(run_batch("run1", seeds))
# Run 2: progress file already has a MATCHED entry from an earlier run
seeds2 = [make_mnemonic(rng) for _ in range(5)]
pre = "CHECKED\t%s\nMATCHED\t%s\n" % (seeds2[0], MATCH_SEED)
results.append(run_batch("run2", seeds2, pre_progress=pre, extra=["--batch-skip-completed"]))
# Run 3: progress file with only CHECKED entries, skip-completed
seeds3 = [make_mnemonic(rng) for _ in range(10)]
pre3 = "".join("CHECKED\t%s\n" % s for s in seeds3[:5])
results.append(run_batch("run3", seeds3, pre_progress=pre3, extra=["--batch-skip-completed"]))

h = hashlib.sha256()
for code, content in results:
    print("exit", code, "lines", content.count("\n"))
    h.update(repr((code, content)).encode())
print(h.hexdigest())
