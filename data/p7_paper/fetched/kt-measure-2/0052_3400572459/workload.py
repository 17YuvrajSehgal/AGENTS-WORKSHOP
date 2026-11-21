import asyncio
import hashlib
from typing import Optional
import os
os.makedirs('/tmp/kt_3490/data', exist_ok=True)
os.environ['XDG_DATA_HOME'] = '/tmp/kt_3490/data'

from crewai.tools.structured_tool import CrewStructuredTool

results = []
calls = {"n": 0}


def compute(text: str, rounds: int = 200) -> str:
    """Hash text repeatedly."""
    calls["n"] += 1
    h = text.encode()
    for _ in range(rounds):
        h = hashlib.sha256(h).digest()
    return h.hex()[:16]


async def acompute(text: str, rounds: int = 50) -> str:
    """Async hash."""
    h = text.encode()
    for _ in range(rounds):
        h = hashlib.sha256(h).digest()
    return h.hex()[:16]


def complex_func(nested: dict, items: list, note: Optional[str] = None) -> str:
    """Complex."""
    calls["n"] += 1
    return f"{len(items)}:{len(nested)}:{note}:{sum(items)}"


# Builds schemas via from_function (create_model line)
for i in range(200):
    t = CrewStructuredTool.from_function(func=compute, name=f"tool_{i}", description="d")
    results.append(t.args_schema.__name__)

tool = CrewStructuredTool.from_function(func=compute, name="compute", description="d")
ctool = CrewStructuredTool.from_function(func=complex_func, name="cx", description="d")
for i in range(6000):
    results.append(tool.invoke({"text": f"in{i}", "rounds": 100 + (i % 50)}))
    results.append(tool.invoke(f'{{"text": "s{i}"}}'))
    results.append(ctool.invoke({"nested": {"a": i, "b": 2}, "items": list(range(i % 20))}))

atool = CrewStructuredTool.from_function(func=acompute, name="acompute", description="d")
for i in range(300):
    results.append(atool.invoke({"text": f"a{i}"}))

async def run_async():
    out = []
    for i in range(300):
        out.append(await atool.ainvoke({"text": f"b{i}"}))
        out.append(await tool.ainvoke({"text": f"c{i}", "rounds": 10}))
    return out

results.extend(asyncio.run(run_async()))

# Error paths
for i in range(300):
    try:
        tool._parse_args("{not json")
    except ValueError as e:
        results.append(type(e).__name__ + str(type(e.__cause__).__name__ if e.__cause__ else None))
    try:
        tool._parse_args({"rounds": "x"})
    except ValueError as e:
        results.append(type(e).__name__ + str(type(e.__cause__).__name__ if e.__cause__ else None))

limited = CrewStructuredTool.from_function(func=compute, name="lim", description="d")
limited.max_usage_count = 3
for i in range(5):
    try:
        results.append(limited.invoke({"text": "x"}))
    except Exception as e:
        results.append("limit:" + str(e))

async def alimit():
    try:
        await limited.ainvoke({"text": "y"})
    except Exception as e:
        return "alimit:" + str(e)
results.append(asyncio.run(alimit()))

print("results", len(results))
print("func_calls", calls["n"])
print(hashlib.sha256("\n".join(map(str, results)).encode()).hexdigest())
