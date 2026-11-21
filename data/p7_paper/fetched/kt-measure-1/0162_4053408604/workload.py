import os, json, hashlib, threading, asyncio
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n))
        msgs = body.get("messages", [])
        content = "echo:" + hashlib.md5(json.dumps(msgs, sort_keys=True).encode()).hexdigest()
        if body.get("stream"):
            parts = []
            for j in range(0, len(content), 8):
                parts.append("data: " + json.dumps({
                    "id": "chatcmpl-1", "object": "chat.completion.chunk", "created": 1700000000,
                    "model": body.get("model", "m"),
                    "choices": [{"index": 0, "delta": {"role": "assistant", "content": content[j:j+8]}, "finish_reason": None}]}) + "\n\n")
            parts.append("data: " + json.dumps({
                "id": "chatcmpl-1", "object": "chat.completion.chunk", "created": 1700000000,
                "model": body.get("model", "m"),
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}) + "\n\n")
            parts.append("data: [DONE]\n\n")
            out = "".join(parts).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
        out = json.dumps({
            "id": "chatcmpl-1", "object": "chat.completion", "created": 1700000000,
            "model": body.get("model", "m"),
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"

import litellm
litellm.telemetry = False

def msgs(i):
    return [{"role": "system", "content": "You are helpful." * 20},
            {"role": "user", "content": f"Question {i}: " + "lorem ipsum " * 50}]

results = []
N = 45
for i in range(N):
    for model in ("maritalk/sabia-3", "hosted_vllm/llama3-8b"):
        r = litellm.completion(model=model, messages=msgs(i), api_base=base, api_key="k", max_tokens=10)
        results.append(r.choices[0].message.content)

async def amain():
    out = []
    for i in range(N):
        for model in ("maritalk/sabia-3", "hosted_vllm/llama3-8b"):
            r = await litellm.acompletion(model=model, messages=msgs(i), api_base=base, api_key="k", max_tokens=10)
            out.append(r.choices[0].message.content)
    return out
results += asyncio.run(amain())

def stream_text(r):
    return "".join((c.choices[0].delta.content or "") for c in r)

for i in range(N // 3):
    r = litellm.completion(model="maritalk/sabia-3", messages=msgs(i), api_base=base, api_key="k", stream=True)
    results.append(stream_text(r))

from litellm.llms.openai_like.chat.handler import OpenAILikeChatHandler
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLogging
from litellm.types.utils import ModelResponse
import datetime

def mklog(i, stream):
    return LiteLLMLogging(model="sabia-3", messages=msgs(i), stream=stream, call_type="acompletion",
                          start_time=datetime.datetime(2024, 1, 1), litellm_call_id=f"id-{i}", function_id="f")

async def astream():
    h = OpenAILikeChatHandler()
    out = []
    for i in range(N // 3):
        for stream in (False, True):
            lo = mklog(i, stream)
            lo.update_environment_variables(model="sabia-3", user=None, optional_params={}, litellm_params={"litellm_call_id": f"id-{i}"})
            r = await h.completion(model="sabia-3", messages=msgs(i), api_base=base, custom_llm_provider="maritalk",
                                   custom_prompt_dict={}, model_response=ModelResponse(), print_verbose=lambda *a, **k: None,
                                   encoding=None, api_key="k", logging_obj=lo,
                                   optional_params={"stream": stream, "max_tokens": 10}, acompletion=True,
                                   litellm_params={}, timeout=30)
            if stream:
                t = ""
                async for c in r:
                    t += c.choices[0].delta.content or ""
                out.append(t)
            else:
                out.append(r.choices[0].message.content)
    return out
results += asyncio.run(astream())

# Final small phase: re-execute the changed modules in an environment where orjson
# is unavailable (the scenario the optional-orjson fallback targets), then make a
# few calls. On base the re-import raises ImportError and the modules keep orjson.
import sys, importlib
import litellm.llms.custom_httpx.llm_http_handler as m1
import litellm.llms.openai_like.chat.handler as m2
import litellm.llms.openai_like.chat.transformation as m3
_saved = sys.modules.get("orjson")
sys.modules["orjson"] = None
status = []
for m in (m3, m2, m1):
    try:
        importlib.reload(m)
        status.append("ok")
    except ImportError:
        status.append("importerror")
sys.modules["orjson"] = _saved
print("reload without orjson:", status)
results.append(",".join(status))
for i in range(5):
    for model in ("maritalk/sabia-3", "hosted_vllm/llama3-8b"):
        r = litellm.completion(model=model, messages=msgs(i), api_base=base, api_key="k", max_tokens=10)
        results.append(r.choices[0].message.content)
srv.shutdown()
print(len(results))
print(hashlib.sha256("\n".join(results).encode()).hexdigest())
