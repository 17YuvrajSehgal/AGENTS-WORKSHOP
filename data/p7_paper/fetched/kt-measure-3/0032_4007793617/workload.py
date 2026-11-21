import asyncio, hashlib, json, os, shutil, logging
from pathlib import Path

ROOT = Path("/tmp/kt_249/work")
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)
os.environ["COPAW_WORKING_DIR"] = str(ROOT)
os.environ["HOME"] = "/tmp/kt_249/home"
os.makedirs("/tmp/kt_249/home", exist_ok=True)
logging.disable(logging.CRITICAL)

from copaw.app.routers import skills as R  # noqa: E402

CUST = ROOT / "customized_skills"
ACT = ROOT / "active_skills"


def make_skill(base: Path, i: int):
    d = base / f"skill_{i:03d}"
    (d / "references" / "sub").mkdir(parents=True, exist_ok=True)
    (d / "scripts").mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\nname: skill_{i:03d}\ndescription: test skill {i}\n---\n" + ("body line\n" * 20)
    )
    for j in range(4):
        (d / "references" / f"ref{j}.md").write_text(f"ref {i} {j}")
        (d / "references" / "sub" / f"deep{j}.txt").write_text(f"deep {i} {j}")
        (d / "scripts" / f"s{j}.py").write_text(f"print({i}+{j})")


CUST.mkdir(parents=True, exist_ok=True)
for i in range(40):
    make_skill(CUST, i)

h = hashlib.sha256()


def dump(specs):
    return json.dumps([s.model_dump() for s in specs], sort_keys=True, default=str)


async def main():
    # Phase A: no active skills
    for k in range(60):
        res = await R.list_skills()
        if k == 0:
            h.update(dump(res).encode())
            print("list_skills(empty active):", len(res), sum(s.enabled for s in res))
    # Phase B: active skills present
    ACT.mkdir(parents=True, exist_ok=True)
    for i in range(0, 40, 2):
        shutil.copytree(CUST / f"skill_{i:03d}", ACT / f"skill_{i:03d}")
    for k in range(60):
        res = await R.get_available_skills()
        if k == 0:
            h.update(dump(res).encode())
            print("get_available_skills:", len(res))
    try:
        res = await R.list_skills()
        out = dump(res)
        print("list_skills(active):", len(res), sum(s.enabled for s in res))
    except Exception as e:
        out = "ERR:" + type(e).__name__
        print("list_skills(active) error:", type(e).__name__)
    h.update(out.encode())


asyncio.run(main())
print(h.hexdigest())
