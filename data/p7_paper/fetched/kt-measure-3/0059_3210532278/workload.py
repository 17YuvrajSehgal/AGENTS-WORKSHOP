import asyncio, hashlib, json, os
import instructor
from pydantic import BaseModel
from openai.types.chat import ChatCompletion

try:
    from instructor.cache import AutoCache, DiskCache  # present on head only
except ImportError:  # base: minimal equivalent; base's patch ignores the kwarg
    class AutoCache:
        def __init__(self, maxsize=128):
            self._d = {}

        def get(self, key):
            return self._d.get(key)

        def set(self, key, value, ttl=None):
            self._d[key] = value

    class DiskCache(AutoCache):
        def __init__(self, directory=".instructor_cache", **kw):
            self._d = {}


class User(BaseModel):
    name: str
    age: int


def make_completion(i):
    return ChatCompletion.model_validate({
        "id": f"c{i}", "object": "chat.completion", "created": 0, "model": "gpt-4o",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {
            "role": "assistant", "content": None,
            "tool_calls": [{"id": "t", "type": "function", "function": {
                "name": "User", "arguments": json.dumps({"name": f"u{i}", "age": i % 90})}}]}}],
    })


# Local stand-in for the network call (accepts and ignores extra kwargs)
def fake_create(**kwargs):
    i = int(kwargs["messages"][-1]["content"].split()[-1])
    return make_completion(i)


async def fake_create_async(**kwargs):
    return fake_create(**kwargs)


# from_provider with cache= (client construction only; no request is made)
os.environ.setdefault("OPENAI_API_KEY", "sk-dummy")
prov = []
for j in range(20):
    cl = instructor.from_provider("openai/gpt-4o-mini", cache=AutoCache(maxsize=16))
    prov.append(type(cl).__name__ + str("cache" in cl.kwargs))
    acl = instructor.from_provider("openai/gpt-4o-mini", async_client=True, cache=AutoCache(maxsize=16))
    prov.append(type(acl).__name__ + str("cache" in acl.kwargs))

sync_create = instructor.patch(create=fake_create, mode=instructor.Mode.TOOLS)
async_create = instructor.patch(create=fake_create_async, mode=instructor.Mode.TOOLS)

out = []
N = 2500
try:
    AutoCache(maxsize=0)  # head raises ValueError; result not recorded
except ValueError:
    pass
cache = AutoCache(maxsize=500)  # smaller than key space -> evictions
for k in range(N):
    i = k % 700
    u = sync_create(model="gpt-4o", response_model=User, cache=cache, cache_ttl=60,
                    messages=[{"role": "user", "content": f"extract {i}"}])
    out.append(u.model_dump_json())
import shutil
ddir = "/tmp/kt_1674/diskcache"
shutil.rmtree(ddir, ignore_errors=True)
dcache = DiskCache(directory=ddir)
for k in range(400):
    i = k % 150
    u = sync_create(model="gpt-4o", response_model=User, cache=dcache,
                    cache_ttl=(600 if k % 2 else None),
                    messages=[{"role": "user", "content": f"extract {i}"}])
    out.append(u.model_dump_json())
# no-cache path too
for i in range(N // 3):
    u = sync_create(model="gpt-4o", response_model=User,
                    messages=[{"role": "user", "content": f"extract {i}"}])
    out.append(u.model_dump_json())


async def run_async():
    res = []
    acache = AutoCache(maxsize=1000)
    for k in range(N // 2):
        i = k % 400
        u = await async_create(model="gpt-4o", response_model=User, cache=acache, cache_ttl=60,
                               messages=[{"role": "user", "content": f"extract {i}"}])
        res.append(u.model_dump_json())
    return res

out.extend(asyncio.run(run_async()))
out.extend(prov)
print(len(out), prov[:2])
print(hashlib.sha256("\n".join(out).encode()).hexdigest())
