import asyncio, hashlib, json, random
from types import SimpleNamespace
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart, ToolReturnPart, ToolCallPart
from pydantic_ai.usage import RequestUsage
from shotgun.agents.config.models import ModelConfig, ProviderType, KeyProvider
from shotgun.agents.conversation.history.compaction import apply_persistent_compaction
from shotgun.agents.conversation.history.history_processors import token_limit_compactor
from shotgun.agents.context_analyzer.analyzer import ContextAnalyzer

rng = random.Random(461)
WORDS = "the quick brown fox jumps over lazy dog code function class module import return value token context agent".split()

def text(n):
    return " ".join(rng.choice(WORDS) for _ in range(n))

def conversation(turns, with_usage, trailing):
    msgs = [ModelRequest(parts=[UserPromptPart(content=text(200))])]
    total = 0
    for t in range(turns):
        total += 300 + t
        usage = RequestUsage(input_tokens=total, output_tokens=50, cache_read_tokens=t * 10) if with_usage else RequestUsage()
        msgs.append(ModelResponse(parts=[TextPart(content=text(150)), ToolCallPart(tool_name="read_file", args={"p": "x"}, tool_call_id=f"c{t}")], usage=usage))
        msgs.append(ModelRequest(parts=[ToolReturnPart(tool_name="read_file", content=text(250), tool_call_id=f"c{t}"), UserPromptPart(content=text(80))]))
    if not trailing:
        msgs.append(ModelResponse(parts=[TextPart(content=text(50))], usage=RequestUsage(input_tokens=total + 500, output_tokens=10) if with_usage else RequestUsage()))
    return msgs

model = ModelConfig(name="gpt-4o", provider=ProviderType.OPENAI, key_provider=KeyProvider.BYOK,
                    max_input_tokens=10_000_000, max_output_tokens=16000, api_key="dummy")
deps = SimpleNamespace(llm_model=model, agent_mode=None)
ctx = SimpleNamespace(deps=deps, usage=RequestUsage())

convs = [conversation(t, u, tr) for t in (40, 60, 80) for u in (True, False) for tr in (True, False)]

async def main():
    out = []
    analyzer = ContextAnalyzer(model)
    for _ in range(2):
        for c in convs:
            r = await apply_persistent_compaction(c, deps)
            out.append(len(r))
            r = await token_limit_compactor(ctx, c)
            out.append(len(r))
            alloc = await analyzer._allocate_tokens_from_usage(c)
            out.append(alloc.model_dump())
    return out

res = asyncio.run(main())
print(len(res))
print(hashlib.sha256(json.dumps(res, sort_keys=True, default=str).encode()).hexdigest())
