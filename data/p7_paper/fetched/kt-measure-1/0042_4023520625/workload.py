import hashlib, json, os, random, sys
os.environ["PREFECT_HOME"] = "/tmp/kt_20965/prefect_home"
os.environ.setdefault("PREFECT_PROFILES_PATH", "/tmp/kt_20965/prefect_home/profiles.toml")
os.environ.setdefault("PREFECT_LOGGING_SETTINGS_PATH", "/tmp/kt_20965/prefect_home/logging.yml")
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import MagicMock

from prefect_dbt.core._executor import DbtExecutor, ExecutionResult
from prefect_dbt.core._orchestrator import ExecutionMode, PrefectDbtOrchestrator, TestStrategy

D = Path("/tmp/kt_20965"); D.mkdir(parents=True, exist_ok=True)
rng = random.Random(1234)
LAYERS, WIDTH = 12, 60
nodes = {}
prev = []
for l in range(LAYERS):
    cur = []
    for w in range(WIDTH):
        uid = f"model.proj.m_{l}_{w}"
        deps = sorted(rng.sample(prev, min(len(prev), rng.randint(1, 3)))) if prev else []
        nodes[uid] = {"name": f"m_{l}_{w}", "resource_type": "model",
                      "depends_on": {"nodes": deps},
                      "config": {"materialized": rng.choice(["table", "view", "incremental"])}}
        cur.append(uid)
        if rng.random() < 0.5:
            tdeps = [uid]
            nodes[f"test.proj.t_{l}_{w}"] = {"name": f"t_{l}_{w}", "resource_type": "test",
                                             "depends_on": {"nodes": tdeps}, "config": {"materialized": "test"}}
    prev = cur
mpath = D / "manifest.json"
mpath.write_text(json.dumps({"nodes": nodes, "sources": {}}))

def make_executor():
    ex = MagicMock(spec=DbtExecutor)
    def _execute_wave(nodes, full_refresh=False, indirect_selection=None, target=None, extra_cli_args=None):
        return ExecutionResult(success=True, node_ids=[n.unique_id for n in nodes])
    ex.execute_wave = MagicMock(side_effect=_execute_wave)
    return ex

def make_settings():
    s = MagicMock()
    s.project_dir = D; s.profiles_dir = D; s.target_path = Path("target")
    s.model_copy.return_value = s
    @contextmanager
    def _r():
        yield str(D)
    s.resolve_profiles_yml = _r
    return s

h = hashlib.sha256()
for rep in range(6):
    for strat in (TestStrategy.IMMEDIATE, TestStrategy.DEFERRED, TestStrategy.SKIP):
        ex = make_executor()
        orch = PrefectDbtOrchestrator(settings=make_settings(), manifest_path=mpath, executor=ex,
                                      execution_mode=ExecutionMode.PER_WAVE, test_strategy=strat)
        res = orch.run_build(full_refresh=(rep % 2 == 1), target="dev",
                             extra_cli_args=["--vars", "{x: 1}"] if rep % 3 == 0 else None)
        summary = sorted((k, v.get("status")) for k, v in res.items())
        waves = [[n.unique_id for n in c.args[0]] for c in ex.execute_wave.call_args_list]
        h.update(json.dumps([strat.value, summary, waves]).encode())
    try:
        orch.run_build(extra_cli_args=["--select", "x"])
    except ValueError as e:
        h.update(str(e).encode())
print(len(nodes))
print(h.hexdigest())
