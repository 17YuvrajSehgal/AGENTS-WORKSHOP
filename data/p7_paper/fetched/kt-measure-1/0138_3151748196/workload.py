import os
import sys
import shutil
import hashlib
import asyncio

SIDE_SRC = os.path.join(os.path.dirname(sys.prefix), "src")
WORK = os.path.join("/tmp/kt_1045", os.path.basename(os.path.dirname(sys.prefix)))
os.makedirs(WORK, exist_ok=True)
if not os.path.isdir(os.path.join(WORK, "template")):
    shutil.copytree(os.path.join(SIDE_SRC, "template"), os.path.join(WORK, "template"))
os.makedirs(os.path.join(WORK, "config"), exist_ok=True)
if not os.path.exists(os.path.join(WORK, "config", "bot_config.toml")):
    shutil.copy(os.path.join(WORK, "template", "bot_config_template.toml"),
                os.path.join(WORK, "config", "bot_config.toml"))
os.chdir(WORK)
for _k, _v in {
    "HOST": "127.0.0.1", "PORT": "8000", "SIMPLE_OUTPUT": "true",
    "SILICONFLOW_BASE_URL": "http://127.0.0.1:9/v1/", "SILICONFLOW_KEY": "dummy",
    "DEEP_SEEK_BASE_URL": "http://127.0.0.1:9/v1/", "DEEP_SEEK_KEY": "dummy",
    "CHAT_ANY_WHERE_BASE_URL": "http://127.0.0.1:9/v1/", "CHAT_ANY_WHERE_KEY": "dummy",
}.items():
    os.environ.setdefault(_k, _v)
sys.path.insert(0, SIDE_SRC)

import logging  # noqa: E402

from src.chat.heart_flow.subheartflow_manager import SubHeartflowManager  # noqa: E402
from src.chat.heart_flow.sub_heartflow import SubHeartflow, ChatState  # noqa: E402
from src.chat.focus_chat.working_memory.working_memory import WorkingMemory  # noqa: E402
import src.chat.focus_chat.expressors.default_expressor as de  # noqa: E402
from src.chat.utils.prompt_builder import global_prompt_manager  # noqa: E402

try:
    from loguru import logger as _lg
    _lg.remove()
except Exception:
    pass
logging.disable(logging.CRITICAL)

N_FLOWS = 400
ROUNDS = 6


async def run_transitions(results):
    mgr = SubHeartflowManager()
    flows = []
    for i in range(N_FLOWS):
        sid = f"stream_{i:05d}"
        sf = SubHeartflow(sid)
        sf.is_group_chat = (i % 3 == 0)
        mgr.subheartflows[sid] = sf
        flows.append(sf)
    for r in range(ROUNDS):
        for sf in flows:
            sf.chat_state.chat_status = ChatState.FOCUSED
            sf.interest_dict[f"m{r}"] = (None, 0.5, False)
        for sf in flows:
            await mgr.sbhf_focus_into_normal(sf.subheartflow_id)
        results.append(
            "|".join(f"{sf.subheartflow_id}:{sf.chat_state.chat_status.value}:{len(sf.interest_dict)}"
                     for sf in flows)
        )
        # ABSENT -> NORMAL branch
        for sf in flows[:50]:
            sf.chat_state.chat_status = ChatState.ABSENT
            await mgr.sbhf_focus_into_normal(sf.subheartflow_id)
    await mgr.sbhf_focus_into_normal("missing_id")


async def run_working_memory(results):
    out = []
    for i in range(3000):
        wm = WorkingMemory(f"chat_{i}")
        out.append(len(wm.get_all_memories()))
        try:
            await wm.shutdown()
            out.append("s")
        except Exception as e:
            out.append(type(e).__name__)
    results.append(",".join(map(str, out)))


async def main():
    results = []
    await run_transitions(results)
    await run_working_memory(results)
    p = await global_prompt_manager.get_prompt_async("default_expressor_private_prompt")
    results.append(str(p))
    return results


res = asyncio.run(main())
h = hashlib.sha256()
for r in res:
    h.update(r.encode("utf-8"))
    h.update(b"\n")
print(len(res))
print(h.hexdigest())
