import hashlib, json, os, sys
side_root = os.path.dirname(os.path.abspath(sys.prefix))
sys.path.insert(0, os.path.join(side_root, "src", "server", "broadlistening", "pipeline"))
import numpy as np
import pandas as pd
import steps.hierarchical_merge_labelling as m


def fake_llm(messages, model, json_schema, provider, local_llm_address=None):
    # stand-in for the external LLM API: deterministic label from prompt
    h = hashlib.sha256(messages[1]["content"].encode()).hexdigest()
    return json.dumps({"label": "L" + h[:8], "description": "D" + h[8:16]}), 10, 5, 15


m.request_to_chat_ai = fake_llm

import contextlib, io

rng = np.random.default_rng(0)
N = 6000
n_top, n_bottom = 8, 64
bottom = rng.integers(0, n_bottom, N)
top = bottom // (n_bottom // n_top)
df = pd.DataFrame({
    "arg-id": [f"A{i}" for i in range(N)],
    "argument": [f"opinion {i} about topic {bottom[i]}" for i in range(N)],
    "x": rng.normal(size=N) + bottom * 0.3,
    "y": rng.normal(size=N) - top * 0.5,
    "cluster-level-1-id": [f"1_{t}" for t in top],
    "cluster-level-2-id": [f"2_{b}" for b in bottom],
    "cluster-level-2-label": [f"bot{b}" for b in bottom],
    "cluster-level-2-description": [f"desc bot{b}" for b in bottom],
})
config = {"hierarchical_merge_labelling": {"sampling_num": 30, "prompt": "p", "model": "m", "workers": 1}, "provider": "openai"}

np.random.seed(0)
out = []
buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    res = m.merge_labelling(df, ["cluster-level-2-id", "cluster-level-1-id"], config)
    out.append(res[["cluster-level-1-id", "cluster-level-1-label"]].drop_duplicates().to_csv(index=False))
    cur = m.ClusterColumns.from_id_column("cluster-level-1-id")
    prev = m.ClusterColumns.from_id_column("cluster-level-2-id")
    for rep in range(40):
        for sn in (20, 50, 100, 2000):
            config["hierarchical_merge_labelling"]["sampling_num"] = sn
            for t in range(n_top):
                r = m.process_merge_labelling(f"1_{t}", df, cur, prev, config)
                out.append(json.dumps(r, sort_keys=True))
    df_noxy = df.drop(columns=["x", "y"])
    df_bad = df.copy()
    df_bad["x"] = df_bad["x"].map(lambda v: f"x={v:.3f}")
    for rep in range(5):
        config["hierarchical_merge_labelling"]["sampling_num"] = 30
        for t in range(n_top):
            out.append(json.dumps(m.process_merge_labelling(f"1_{t}", df_noxy, cur, prev, config), sort_keys=True))
            out.append(json.dumps(m.process_merge_labelling(f"1_{t}", df_bad, cur, prev, config), sort_keys=True))
print(out[0][:200])
print(hashlib.sha256("\n".join(out).encode()).hexdigest())
