import hashlib, os, random, shutil, subprocess, time, atexit

WD = "/tmp/kt_893"
os.makedirs(WD, exist_ok=True)
SOCK = os.path.join(WD, "redis_%d.sock" % os.getpid())
proc = subprocess.Popen(
    ["redis-server", "--port", "0", "--unixsocket", SOCK, "--save", "",
     "--appendonly", "no", "--dir", WD],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
atexit.register(lambda: (proc.terminate(), proc.wait()))
for _ in range(200):
    if os.path.exists(SOCK):
        break
    time.sleep(0.02)
os.environ["REDIS_SOCKET"] = SOCK
os.environ["ADDOK_CONFIG_MODULE"] = os.path.join(WD, "none.conf")

from addok.config import config
config.load()
from addok.db import DB
from addok.pairs import pair_key
from addok.helpers.text import Token
from addok.helpers.collectors import (_compute_onetomany_relations,
                                      _extract_manytomany_relations)

for _ in range(100):
    try:
        DB.ping(); break
    except Exception:
        time.sleep(0.05)
DB.flushdb()

rng = random.Random(893)
vocab = ["w%03d" % i for i in range(400)]
pipe = DB.pipeline()
for w in vocab:
    others = rng.sample(vocab, 40)
    for o in others:
        if o != w:
            pipe.sadd(pair_key(w), o)
            pipe.sadd(pair_key(o), w)
pipe.execute()

queries = []
for _ in range(300):
    n = rng.randint(3, 12)
    queries.append([Token(s) for s in rng.sample(vocab, n)])

h = hashlib.sha256()
for rep in range(3):
    for q in queries:
        rel = _compute_onetomany_relations(q)
        h.update(repr(sorted((str(k), sorted(map(str, v))) for k, v in rel.items())).encode())
    for q in queries[:100]:
        groups = _extract_manytomany_relations(q)
        h.update(repr(sorted(sorted(map(str, g)) for g in groups)).encode())
DB.flushdb()
print(h.hexdigest())
