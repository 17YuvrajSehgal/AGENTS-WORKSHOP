import hashlib, json, os, random, re, sys
from pathlib import Path

import polyagent.dashboard as dash

ROOT = Path('/tmp/kt_8')
TASK = 'bench'
rng = random.Random(1234)

# ---- build task dir with deterministic data ----
tdir = ROOT / 'tasks' / TASK
for sub in ('data', 'logs', 'test'):
    (tdir / sub).mkdir(parents=True, exist_ok=True)
(tdir / 'task_config.py').write_text(
    "TASK_NAME = 'bench'\nTASK_INIT_TIME = '2026-03-01T00:00:00Z'\n"
    "POLYMARKET_PRIVATE_KEY = '0x" + '4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318' + "'\n")
words = ['market', 'election', 'bitcoin', 'rate', 'cut', 'fed', 'news', 'breaking', 'poll', 'odds', 'surge']
with open(tdir / 'data' / 'tweets.jsonl', 'w') as fh:
    for i in range(400):
        fh.write(json.dumps({'user': f'user{i}', 'created_at': 1700000000 + i * 37,
                             'url': f'https://x.com/user{i}/status/{10**15 + i}' + 'q' * rng.randint(0, 120),
                             'text': ' '.join(rng.choice(words) for _ in range(rng.randint(5, 60)))}) + '\n')
        if i % 50 == 0:
            fh.write('not json\n')
with open(tdir / 'logs' / 'runtime_events.jsonl', 'w') as fh:
    for i in range(600):
        fh.write(json.dumps({'type': rng.choice(['decision', 'trigger_record', 'other'])}) + '\n')
os.chdir(ROOT)


# ---- stand-in for the remote Polymarket HTTP API (network I/O only) ----
class _Resp:
    def __init__(self, data):
        self._d = data

    def json(self):
        return self._d


def _title():
    return ' '.join(rng.choice(words) for _ in range(rng.randint(3, 30)))


VALUE = [{'user': '0xabc', 'value': 1234.5678, 'cashBalance': '99.1', 'realized_profit': 'n/a', 'count': 7}]
ACTIVITY = [{'timestamp': 1700000000 + i, 'side': 'buy', 'type': 'trade', 'price': 0.5 + i / 100,
             'usdcSize': 10 * i, 'title': _title(), 'outcome': 'Yes'} for i in range(15)]
POSITIONS = [{'title': _title(), 'outcome': 'No', 'size': i * 1.5, 'price': 0.3} for i in range(10)]


def fake_get(url, params=None, timeout=None):
    if 'public-profile' in url:
        return _Resp({'proxyWallet': '0x' + 'ab' * 20 + 'ffff' * 10})
    if url.endswith('/value'):
        return _Resp(VALUE)
    if url.endswith('/activity'):
        return _Resp(ACTIVITY)
    if url.endswith('/positions'):
        return _Resp(POSITIONS)
    return _Resp(None)


dash.requests.get = fake_get

d = dash.PolyMonitorDashboard(TASK)
eoa, proxy = d._wallet_summary()

TIME_RE = re.compile(r'Current time  : \d{4}-\d\d-\d\d \d\d:\d\d:\d\d UTC')
HB_RE = re.compile(r'\x1b\[1;38;5;\d+m●( LIVE)?\x1b\[0m')

h = hashlib.sha256()
out_len = 0
for it in range(700):
    d._portfolio_cache = None
    frame = d.render()
    frame = HB_RE.sub('<HB>', TIME_RE.sub('Current time  : <T>', frame))
    h.update(frame.encode())
    out_len += len(frame)
    # missing-wallet branch
    d._portfolio_cache = None
    h.update('\n'.join(d._portfolio_lines('N/A', 'N/A')).encode())
    # value_data as dict
    VALUE_SAVE = VALUE[:]
    d._portfolio_cache = None
    globals()['VALUE'] = {'portfolio_value': 1.5 * it, 'cash_balance': 'x', 'name': 'n'}
    h.update('\n'.join(d._portfolio_lines(eoa, proxy)).encode())
    globals()['VALUE'] = VALUE_SAVE


class _Stop(Exception):
    pass


class _Term:
    """Stand-in terminal: counts rendered frames, stops loop() after a few."""
    def __init__(self, limit):
        self.frames = 0
        self.limit = limit

    def write(self, s):
        if 'NEWS FEED' in s:
            self.frames += 1
            if self.frames > self.limit:
                raise _Stop()
        return len(s)

    def flush(self):
        pass


for _ in range(20):
    d.refresh_seconds = 0
    term = _Term(3)
    real = sys.stdout
    sys.stdout = term
    try:
        d.loop()
    except _Stop:
        pass
    finally:
        sys.stdout = real
    h.update(str(term.frames).encode())

print('frame chars', out_len)
print(h.hexdigest())
