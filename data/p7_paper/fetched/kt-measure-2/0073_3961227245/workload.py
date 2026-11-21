import gzip, hashlib, io, logging, random, sys
from pathlib import Path

side = Path(sys.executable).parents[2]
sys.path.insert(0, str(side / "src/airbyte-integrations/connectors/source-bing-ads"))
logging.disable(logging.CRITICAL)
import requests
import components

rng = random.Random(1234)
def make_csv(nrows):
    lines = ["AccountId,CampaignId,AdGroupId,TimePeriod,Impressions,Clicks,Spend,Name"]
    for i in range(nrows):
        lines.append(f"{rng.randint(1,10**9)},{rng.randint(1,10**6)},{rng.randint(1,10**6)},2024-01-{i%28+1:02d},"
                     f"{rng.randint(0,100000)},{rng.randint(0,1000)},{rng.random()*100:.4f},\"name, {i}\"")
    return ("\n".join(lines) + "\n").encode("utf-8-sig")

def gz(b):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as f:
        f.write(b)
    return buf.getvalue()

payloads = []
for n in (20000, 50, 0, 5000):
    raw = make_csv(n)
    payloads.append(gz(raw))
    payloads.append(raw)
payloads.append(b"")
payloads.append(b"\x1f\x8b not valid gzip at all")

def make_response(data):
    r = requests.Response()
    s = io.BytesIO(data)
    s.auto_close = True
    r.raw = s
    r.status_code = 200
    return r

h = hashlib.sha256()
dec = components.BingAdsGzipCsvDecoder()
total = 0
for rep in range(4):
    for p in payloads:
        rows = list(dec.decode(make_response(p)))
        total += len(rows)
        for row in rows:
            h.update(repr(sorted(row.items())).encode())
        h.update(b"|")
print("rows", total)
print(h.hexdigest())
