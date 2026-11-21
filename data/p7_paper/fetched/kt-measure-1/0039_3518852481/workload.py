import hashlib, random
import warnings
warnings.simplefilter("ignore")
from Bio.Seq import Seq
from Bio.SeqUtils import MeltingTemp as mt

rng = random.Random(5085)
seqs = ["".join(rng.choice("ACGT") for _ in range(rng.randint(15, 60))) for _ in range(4000)]
saltcorrs = [0, 1, 2, 3, 4, 5, 6, 7]
out = []
for rep in range(12):
    for i, s in enumerate(seqs):
        sc = saltcorrs[i % 8]
        if i % 10 == 3:
            sc = float(sc)  # float saltcorr: C path rejects it, falls back to Python
        kw = dict(saltcorr=sc, Na=50, K=(i % 3) * 10, Tris=(i % 2) * 5, Mg=(i % 4) * 1.5, dNTPs=(i % 2) * 0.8)
        if i % 5 == 0:
            tm = mt.Tm_NN(Seq(s), **kw)
        else:
            tm = mt.Tm_NN(s.lower() if i % 7 == 0 else s, **kw)
        out.append(round(tm, 6))
print(len(out), sum(out))
print(hashlib.sha256(repr(out).encode()).hexdigest())
