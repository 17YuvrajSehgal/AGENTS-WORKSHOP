import os, sys, json, random, hashlib, copy
os.environ.setdefault("DD_API_KEY", "0" * 32)
side = os.path.dirname(os.path.abspath(sys.prefix))
sys.path.insert(0, os.path.join(side, "src", "aws", "logs_monitoring"))
from steps.splitting import split

rng = random.Random(1080)

def make_event(i):
    k = i % 8
    if k == 0:
        msg = json.dumps({"m": f"metric.{i%50}", "v": rng.random() * 100, "e": 1700000000 + i, "t": [f"t:{i%7}"]})
    elif k == 1:
        msg = json.dumps({"m": "cnt", "v": i, "e": 1700000000, "t": "bad"})
    elif k == 2:
        msg = json.dumps({"traces": [[{"trace_id": i, "span_id": i + 1, "name": "op", "duration": 123}]], "env": "prod"})
    elif k == 3:
        msg = json.dumps({"traces": ["unrelated"]})
    elif k == 4:
        msg = f"START RequestId: {i:08x} Version: $LATEST plain text log line {rng.random()}"
    elif k == 5:
        msg = json.dumps({"level": "info", "msg": "hello", "n": i, "nested": {"a": [1, 2, 3]}})
    elif k == 6:
        msg = json.dumps({"traces": []})
    else:
        msg = json.dumps({"m": "x", "v": None, "e": 0, "t": []})
    ev = {"message": msg, "ddtags": f"env:prod,service:svc{i%5},version:1"}
    if i % 3 == 0:
        ev["lambda"] = {"arn": f"arn:aws:lambda:us-east-1:123:function:Fn{i%11}"}
    return ev

base_events = [make_event(i) for i in range(4000)]
h = hashlib.sha256()
for r in range(150):
    events = [dict(e) for e in base_events]
    metrics, logs, traces = split(events)
    if r == 0:
        h.update(json.dumps([metrics, [e["message"] for e in logs], traces], sort_keys=True).encode())
    h.update(f"{len(metrics)},{len(logs)},{len(traces)}".encode())
print(len(metrics), len(logs), len(traces))
print(h.hexdigest())
