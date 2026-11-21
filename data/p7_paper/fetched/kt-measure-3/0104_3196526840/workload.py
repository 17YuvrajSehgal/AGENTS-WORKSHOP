import asyncio, hashlib, json, os
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
import instructor
from pydantic import BaseModel
from openai.types.chat import ChatCompletion

class User(BaseModel):
    name: str
    age: int

def make_completion(i):
    return ChatCompletion.model_validate({
        "id": f"c{i}", "object": "chat.completion", "created": 0, "model": "gpt-4o",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {
            "role": "assistant", "content": None,
            "tool_calls": [{"id": "t", "type": "function", "function": {
                "name": "User", "arguments": json.dumps({"name": f"user{i}", "age": i % 90})}}]}}],
    })

N = 300
COMPLETIONS = [make_completion(i) for i in range(N)]

def fake_create(*args, **kwargs):
    i = int(kwargs["messages"][-1]["content"].split()[-1])
    return COMPLETIONS[i]

async def afake_create(*args, **kwargs):
    return fake_create(*args, **kwargs)

class DictCache:
    """Simple user-provided cache backend (get/set) passed via cache=."""
    def __init__(self):
        self.d = {}
    def get(self, key):
        return self.d.get(key)
    def set(self, key, value, ttl=None):
        self.d[key] = value

out = []
sync_create = instructor.patch(create=fake_create, mode=instructor.Mode.TOOLS)
async_create = instructor.patch(create=afake_create, mode=instructor.Mode.TOOLS)
for rep in range(2):
    for i in range(N):
        u = sync_create(model="gpt-4o", response_model=User,
                        messages=[{"role": "user", "content": f"extract {i}"}])
        out.append(u.model_dump_json())
    cache = DictCache()
    for i in range(N):
        for _ in range(2):
            u = sync_create(model="gpt-4o", response_model=User, cache=cache, cache_ttl=60,
                            messages=[{"role": "user", "content": f"extract {i}"}])
            out.append(u.model_dump_json())

async def run_async():
    res = []
    for rep in range(2):
        for i in range(N):
            u = await async_create(model="gpt-4o", response_model=User,
                                   messages=[{"role": "user", "content": f"extract {i}"}])
            res.append(u.model_dump_json())
        cache = DictCache()
        for i in range(N):
            for _ in range(2):
                u = await async_create(model="gpt-4o", response_model=User, cache=cache,
                                       messages=[{"role": "user", "content": f"extract {i}"}])
                res.append(u.model_dump_json())
    return res
out += asyncio.run(run_async())

# from_provider (client construction only, no network)
for i in range(10):
    c = instructor.from_provider("openai/gpt-4o")
    out.append(type(c).__name__)
    c = instructor.from_provider("openai/gpt-4o", async_client=True)
    out.append(type(c).__name__)

    c = instructor.from_provider("azure_openai/gpt-4o", api_key="k",
                                 azure_endpoint="https://example.invalid")
    out.append(type(c).__name__)
for prov in ["azure_openai", "google", "mistral", "anthropic", "generative-ai", "bogus"]:
    for kw in ({}, {"api_key": "k"}):
        try:
            instructor.from_provider(f"{prov}/m", **kw)
            out.append(prov + " ok")
        except Exception as e:
            out.append(prov + " " + type(e).__name__)
try:
    instructor.from_provider("noslash")
except Exception as e:
    out.append(type(e).__name__)

print(len(out))
print(hashlib.sha256("\n".join(out).encode()).hexdigest())
