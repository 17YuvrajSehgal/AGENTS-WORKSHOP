"""Workload: multi-turn prompt caching through mlx_lm.server.LRUPromptCache
with hybrid (KVCache + ArraysCache) prompt caches, as the server does it."""
import hashlib
import random

import mlx.core as mx

from mlx_lm.models.cache import ArraysCache, KVCache
from mlx_lm.server import LRUPromptCache

rng = random.Random(1234)
mx.random.seed(0)
mx.disable_compile()  # CPU JIT cannot build with this g++ (_Float128 error)

H, D = 2, 32


def make_cache():
    a = ArraysCache(2)
    a[0] = mx.zeros((1, 3, 64))
    a[1] = mx.zeros((1, 4, 16, 16))
    return [KVCache(), a, KVCache()]


def process(cache, n):
    """Simulate a model step over n tokens on the hybrid cache."""
    if n <= 0:
        return
    kv = mx.ones((1, H, n, D), dtype=mx.float16)
    cache[0].update_and_fetch(kv, kv)
    cache[2].update_and_fetch(kv, kv)
    a = cache[1]
    a[0] = a[0] + n
    a[1] = a[1] * 0.5 + 1.0
    mx.eval(cache[0].keys, cache[2].keys, a[0], a[1])


out = []
model = ("test-model", None, None)
pc = LRUPromptCache(max_size=12, max_bytes=1 << 26)

# Several independent conversations, each with several turns, interleaved.
n_conv = 6
convs = []
for c in range(n_conv):
    system = [1000 + c] + [rng.randrange(1, 900) for _ in range(rng.randrange(40, 120))]
    convs.append(system)

for rnd in range(30):
    for c in range(n_conv):
        # The new prompt extends the conversation with a user message
        user = [rng.randrange(1, 900) for _ in range(rng.randrange(5, 60))]
        prompt = convs[c] + user
        # Occasionally branch: drop the tail of the conversation
        if rng.random() < 0.15 and len(convs[c]) > 50:
            cut = rng.randrange(20, len(convs[c]))
            prompt = convs[c][:cut] + user
        res = pc.fetch_nearest_cache(model, prompt)
        cache, rest = res[0], res[1]
        if cache is None:
            cache = make_cache()
        process(cache, len(rest))
        gen = [rng.randrange(1, 900) for _ in range(rng.randrange(3, 30))]
        process(cache, len(gen))
        key = prompt + gen
        pc.insert_cache(model, key, cache)
        # Re-insert duplicates sometimes (count > 1 path)
        if rng.random() < 0.2:
            pc.insert_cache(model, key, cache)
        convs[c] = key
        nb = sum(x.nbytes for x in cache)
        out.append((rnd, c, len(prompt), len(rest), cache[0].offset, nb,
                    len(pc), pc.nbytes))
        if len(convs[c]) > 1500:
            convs[c] = convs[c][:100]
    # exact-match fetches
    for c in range(n_conv):
        res = pc.fetch_nearest_cache(model, convs[c])
        cache = res[0]
        out.append(("exact", rnd, c, None if cache is None else cache[0].offset,
                    len(res[1]), len(pc)))
        if cache is not None:
            pc.insert_cache(model, convs[c], cache)
    # ArraysCache nbytes on its own
    a = make_cache()[1]
    out.append(("arr", a.nbytes))



# ---------------------------------------------------------------------------
# Part 2: the server's ResponseGenerator with a tiny local model / tokenizer
# ---------------------------------------------------------------------------
import os, json
from mlx_lm.utils import load
from mlx_lm.server import (ResponseGenerator, CompletionRequest, GenerationArguments,
                           ModelDescription, SamplingArguments, LogitsProcessorArguments)

def build_model():
    import json, os
    import mlx.core as mx
    from mlx.utils import tree_flatten
    from tokenizers import Tokenizer, models, pre_tokenizers, decoders
    d="/tmp/kt_929/model"
    os.makedirs(d, exist_ok=True)
    words=[f"w{i}" for i in range(400)]
    specials=["<unk>","<|im_start|>","<|im_end|>","system","user","assistant","\n"]
    vocab={t:i for i,t in enumerate(specials+words)}
    tok=Tokenizer(models.WordLevel(vocab=vocab, unk_token="<unk>"))
    tok.pre_tokenizer=pre_tokenizers.WhitespaceSplit()
    tok.add_special_tokens(["<|im_start|>","<|im_end|>"])
    tok.save(f"{d}/tokenizer.json")
    tmpl="{% for m in messages %}<|im_start|> {{ m['role'] }} {{ m['content'] }} <|im_end|> {% endfor %}{% if add_generation_prompt %}<|im_start|> assistant {% endif %}"
    json.dump({"tokenizer_class":"PreTrainedTokenizerFast","eos_token":"<|im_end|>","unk_token":"<unk>","chat_template":tmpl,"model_max_length":100000},open(f"{d}/tokenizer_config.json","w"))
    cfg=dict(model_type="llama",hidden_size=64,num_hidden_layers=2,intermediate_size=128,num_attention_heads=4,num_key_value_heads=2,rms_norm_eps=1e-5,vocab_size=len(vocab),tie_word_embeddings=True)
    json.dump(cfg,open(f"{d}/config.json","w"))
    from mlx_lm.models import llama
    mx.random.seed(0)
    m=llama.Model(llama.ModelArgs(**cfg))
    mx.save_safetensors(f"{d}/model.safetensors", dict(tree_flatten(m.parameters())))
    return d

if not os.path.exists("/tmp/kt_929/model/model.safetensors"):
    build_model()
MODEL_DIR = "/tmp/kt_929/model"
NT_DIR = "/tmp/kt_929/model_nt"  # same model, tokenizer without a chat template
if not os.path.exists(NT_DIR + "/tokenizer_config.json"):
    import shutil
    os.makedirs(NT_DIR, exist_ok=True)
    for f in ("config.json", "model.safetensors", "tokenizer.json"):
        shutil.copy(os.path.join(MODEL_DIR, f), NT_DIR)
    tc = json.load(open(MODEL_DIR + "/tokenizer_config.json"))
    tc.pop("chat_template")
    json.dump(tc, open(NT_DIR + "/tmp_tc.json", "w"))
    os.replace(NT_DIR + "/tmp_tc.json", NT_DIR + "/tokenizer_config.json")


class Provider:
    def __init__(self, batchable, model_dir=MODEL_DIR):
        self.model, self.tokenizer = load(model_dir)
        self.model_key = (model_dir, None, None)
        self.is_batchable = batchable
        self.draft_model = None
        self.draft_model_key = None
        self.cli_args = type("obj", (object,), {
            "adapter_path": None, "chat_template": None,
            "use_default_chat_template": False, "trust_remote_code": False,
            "draft_model": None, "num_draft_tokens": 3, "temp": 0.0,
            "top_p": 1.0, "top_k": 0, "min_p": 0.0, "max_tokens": 16,
            "chat_template_args": {}, "model": None,
            "decode_concurrency": 32, "prompt_concurrency": 8,
            "prompt_cache_size": 10, "prompt_cache_bytes": 1 << 63,
            "prompt_cache_total_bytes": None,
        })

    def load(self, model, adapter=None, draft_model=None):
        return self.model, self.tokenizer


def gen_args(seed, max_tokens, kwargs=None):
    return GenerationArguments(
        model=ModelDescription("default_model", None, None),
        sampling=SamplingArguments(0.0, 1.0, 0, 0.0, 0.0, 0.0),
        logits=LogitsProcessorArguments(None, 1.0, 20),
        stop_words=[], max_tokens=max_tokens, num_draft_tokens=3,
        logprobs=False, top_logprobs=-1, seed=seed, chat_template_kwargs=kwargs,
    )


def words(r, n):
    return " ".join(f"w{r.randrange(400)}" for _ in range(n))


def run_server(batchable, seed, n_conv, n_turns, long_ctx=False,
               model_dir=MODEL_DIR, max_bytes=1 << 63):
    r = random.Random(77 + int(batchable))
    lru = LRUPromptCache(max_size=20, max_bytes=max_bytes)
    # head exposes checkpoint_interval as a constructor option (default 8192);
    # use a smaller interval so moderately long chats get periodic checkpoints.
    lru.checkpoint_interval = 256
    rg = ResponseGenerator(Provider(batchable, model_dir), lru)
    res = []
    try:
        convs = [[{"role": "system", "content": words(r, 60)}] for _ in range(n_conv)]
        if long_ctx:
            # one long conversation (> 8192 tokens) with many messages
            long_msgs = []
            for i in range(24):
                long_msgs.append({"role": "user" if i % 2 == 0 else "assistant",
                                  "content": words(r, 40)})
            convs.append(long_msgs)
        for turn in range(n_turns):
            for c in range(len(convs)):
                msgs = convs[c]
                msgs.append({"role": "user", "content": words(r, r.randrange(10, 60))})
                req = CompletionRequest("chat", "", [dict(m) for m in msgs], None, None)
                kw = {"enable_thinking": False} if turn % 3 == 1 else None
                ctx, it = rg.generate(req, gen_args(seed, 8, kw))
                if c == 1 and turn % 4 == 2:
                    # client goes away after the first token
                    first = next(it)
                    ctx.stop()
                    for _ in it:
                        pass
                    toks = [first.token]
                else:
                    toks = [g.token for g in it]
                res.append((batchable, turn, c, len(ctx.prompt), toks))
                msgs.append({"role": "assistant", "content": words(r, 6)})
                # occasionally branch the conversation back to an earlier point
                if r.random() < 0.2 and len(msgs) > 3 and c < n_conv:
                    convs[c] = msgs[:3]
            # a fresh single-message chat
            req = CompletionRequest("chat", "", [{"role": "user", "content": words(r, 20)}], None, None)
            ctx, it = rg.generate(req, gen_args(seed, 4))
            res.append(("single", turn, len(ctx.prompt), [g.token for g in it]))
            # plain text completion requests
            req = CompletionRequest("text", words(r, 40), [], None, None)
            ctx, it = rg.generate(req, gen_args(seed, 4))
            res.append(("text", turn, len(ctx.prompt), [g.token for g in it]))
            res.append(("cache", len(rg.prompt_cache)))
    finally:
        rg.stop_and_join()
    return res

out.append(run_server(False, 0, 3, 6))
out.append(run_server(False, 0, 0, 4, long_ctx=True))
out.append(run_server(False, 0, 2, 3, model_dir=NT_DIR))
out.append(run_server(True, None, 3, 4, max_bytes=1 << 20))
out.append(run_server(True, None, 4, 8, long_ctx=True))

pc.trim_to(n_sequences=3)
out.append(("final", len(pc), pc.nbytes))

for line in out[-1:]:
    print(line)
print(hashlib.sha256(repr(out).encode()).hexdigest())
