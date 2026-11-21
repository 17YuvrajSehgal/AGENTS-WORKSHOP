import os, hashlib, json
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ.setdefault("OPENAI_API_KEY", "sk-fake")
import io, contextlib
from typing import List, Dict
from pydantic import BaseModel
from crewai.flow.flow import Flow, start, listen, router, or_, and_
from crewai.agents.parser import CrewAgentParser
from crewai import Agent, Task, Crew, LLM

results = []

class Item(BaseModel):
    name: str
    values: List[int] = []
    meta: Dict[str, str] = {}

class S(BaseModel):
    counter: int = 0
    items: List[Item] = []
    tags: Dict[str, List[int]] = {}

class StructFlow(Flow[S]):
    @start()
    def begin(self):
        for i in range(30):
            self.state.items.append(Item(name=f"i{i}", values=list(range(i % 7)), meta={"k": str(i)}))
        self.state.counter += 1
        return "begun"
    @listen(begin)
    def step_a(self, x):
        self.state.tags["a"] = [len(x)] * 10
        self.state.counter += 1
        return x + "-a"
    @listen(begin)
    def step_b(self, x):
        self.state.counter += 1
        return x + "-b"
    @router(and_(step_a, step_b))
    def route(self):
        return "even" if self.state.counter % 2 == 0 else "odd"
    @listen("odd")
    def odd(self):
        self.state.counter += 10
        return "odd!"
    @listen("even")
    def even(self):
        self.state.counter += 100
        return "even!"

class DictFlow(Flow):
    @start()
    def s(self):
        self.state["data"] = {"x": [1, 2, 3], "y": {"z": (1, 2)}}
        return 1
    @listen(s)
    def t(self, v):
        self.state["data"]["x"].append(v)
        return v + 1
    @listen(or_(t, s))
    def u(self, v):
        return v * 2

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    for r in range(60):
        f = StructFlow()
        out = f.kickoff()
        results.append((out, f.state.counter, len(f.state.items)))
        d = DictFlow()
        results.append((d.kickoff(), json.dumps(d.state.get("data"), default=str)))

parser = CrewAgentParser()
texts = [
    "Thought: I know ```now```\nFinal Answer: ```python\nprint(1)\n```",
    "Thought: thinking\nFinal Answer: result ```",
    "Thought: use tool\nAction: search\nAction Input: {\"q\": \"x\"}",
    "Thought: ``` weird\nFinal Answer: plain answer",
]
for _ in range(3000):
    for t in texts:
        try:
            r = parser.parse(t)
            results.append((type(r).__name__, getattr(r, "output", None), getattr(r, "thought", None), getattr(r, "tool", None)))
        except Exception as e:
            results.append(("err", type(e).__name__))

class FakeLLM(LLM):
    def call(self, messages, *args, **kwargs):
        last = messages[-1]["content"] if messages else ""
        n = len(str(last))
        return f"Thought: I now know the final answer\nFinal Answer: answer of length {n}"
    def supports_function_calling(self):
        return False
    def supports_stop_words(self):
        return True

with contextlib.redirect_stdout(buf):
    for r in range(8):
        llm = FakeLLM(model="gpt-4o-mini")
        agents = [Agent(role=f"Role{i}", goal="Do things", backstory="Bk", llm=llm, verbose=False) for i in range(2)]
        tasks = [Task(description=f"Task {j} on {{topic}}", expected_output="text", agent=agents[j % 2]) for j in range(4)]
        crew = Crew(agents=agents, tasks=tasks, verbose=False)
        out = crew.kickoff(inputs={"topic": f"t{r}"})
        results.append((out.raw, [t.raw for t in out.tasks_output]))

print(len(results))
print(hashlib.sha256(json.dumps(results, default=str).encode()).hexdigest())
