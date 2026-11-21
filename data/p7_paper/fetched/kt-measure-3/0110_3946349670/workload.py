"""Workload: run ParallelOrchestratorReviewer.review() end-to-end with
stand-ins for the Claude SDK client (network) and the GitHub CLI client.

Exercises specialist parsing, dedup, cross-validation, line verification,
_validate_findings (incl. dismissed/cross-validated handling), verdict and
_generate_summary.
"""
import asyncio
import contextlib
import hashlib
import io
import json
import logging
import os
import random
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SIDE = "head" if "/head/venv" in sys.executable else "base"
GH_DIR = os.path.join(HERE, SIDE, "src", "apps", "backend", "runners", "github")
BACKEND = os.path.join(HERE, SIDE, "src", "apps", "backend")
sys.path[:0] = [GH_DIR, BACKEND]

logging.disable(logging.CRITICAL)

import claude_agent_sdk  # noqa: E402
import services.parallel_orchestrator_reviewer as por  # noqa: E402
from context_gatherer import ChangedFile, PRContext  # noqa: E402
from models import GitHubRunnerConfig  # noqa: E402

WORK = Path("/tmp/kt_1852/repo")

FILES = [f"src/pkg/module_{i}.py" for i in range(12)]
CATS = ["security", "quality", "logic", "performance", "pattern"]
SEVS = ["critical", "high", "medium", "low"]
SPECIALISTS = {c.name: c.description for c in por.SPECIALIST_CONFIGS}


def setup_repo():
    WORK.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(FILES):
        p = WORK / f
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text("".join(f"x_{i}_{j} = {j}\n" for j in range(200)))


# ---------------------------------------------------------------------------
# Stand-ins for external I/O (Claude SDK client, gh CLI)
# ---------------------------------------------------------------------------
class Scenario:
    seed = 0


def specialist_output(name: str, seed: int):
    rng = random.Random(f"{seed}:{name}")
    findings = []
    # Shared findings (same file/line/category across specialists) -> cross-validated
    shared_rng = random.Random(f"{seed}:shared")
    for k in range(6):
        f = FILES[shared_rng.randrange(len(FILES))]
        line = shared_rng.randrange(1, 190)
        cat = CATS[shared_rng.randrange(len(CATS))]
        if rng.random() < 0.6:
            findings.append({
                "severity": SEVS[rng.randrange(4)],
                "category": cat,
                "title": f"Shared issue {k} seen by {name}",
                "description": f"Problem {k} at {f}:{line} ({name})",
                "file": f,
                "line": line,
                "end_line": line + rng.randrange(0, 3),
                "suggested_fix": "Refactor",
                "evidence": f"x_{k} = {line}",
                "is_impact_finding": False,
            })
    for k in range(rng.randrange(18, 30)):
        f = FILES[rng.randrange(len(FILES))] if rng.random() < 0.9 else "other/out_of_scope.py"
        line = rng.randrange(1, 230)  # some beyond file length
        findings.append({
            "severity": SEVS[rng.randrange(4)],
            "category": CATS[rng.randrange(len(CATS))],
            "title": f"{name} issue {k}",
            "description": f"{name} found something odd #{k} in {f}",
            "file": f,
            "line": line,
            "end_line": None if rng.random() < 0.5 else line + 2,
            "suggested_fix": None if rng.random() < 0.3 else "Fix it",
            "evidence": f"code snippet {k}",
            "is_impact_finding": rng.random() < 0.1,
        })
    return {
        "specialist_name": name,
        "analysis_summary": f"{name} analysis",
        "files_examined": FILES,
        "findings": findings,
    }


def validator_output(prompt: str, seed: int):
    m = re.search(r"```json\n(.*?)\n```", prompt, re.S)
    items = json.loads(m.group(1))
    vals = []
    for it in items:
        h = int(hashlib.md5(f"{seed}:{it['id']}".encode()).hexdigest(), 16) % 10
        if h == 9:
            continue  # no validation result
        status = (
            "dismissed_false_positive" if h < 5
            else "needs_human_review" if h < 7
            else "confirmed_valid"
        )
        vals.append({
            "finding_id": it["id"],
            "validation_status": status,
            "code_evidence": f"evidence for {it['id']}",
            "explanation": f"Explanation {h} for {it['title']} " * 3,
        })
    return {"validations": vals, "summary": f"{len(vals)} validated"}


class FakeSDKClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.prompt = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def query(self, prompt):
        self.prompt = prompt

    async def receive_response(self):
        await asyncio.sleep(0)
        if self.kwargs.get("agent_type") == "pr_finding_validator":
            out = validator_output(self.prompt, Scenario.seed)
        else:
            name = next(n for n, d in SPECIALISTS.items() if d in self.prompt)
            out = specialist_output(name, Scenario.seed)
        yield claude_agent_sdk.ResultMessage(
            subtype="success", duration_ms=1, duration_api_ms=1, is_error=False,
            num_turns=1, session_id="s", total_cost_usd=0.0, usage=None,
            result="done", structured_output=out,
        )


def fake_create_client(**kwargs):
    return FakeSDKClient(**kwargs)


class FakeGHClient:
    def __init__(self, *a, **k):
        pass

    async def get_pr_checks_comprehensive(self, pr_number):
        return {
            "passing": 5, "failing": pr_number % 3 == 0 and 1 or 0, "pending": 0,
            "failed_checks": ["lint"] if pr_number % 3 == 0 else [],
            "awaiting_approval": 0,
        }

    async def get_pr_files(self, pr_number):
        return [{"filename": f, "sha": hashlib.sha1(f.encode()).hexdigest()} for f in FILES]


por.create_client = fake_create_client
por.GHClient = FakeGHClient


def make_context(n):
    cfs = [ChangedFile(path=f, status="modified", additions=10, deletions=2,
                       content="", base_content="", patch=f"@@ -1 +1 @@\n-a\n+b {n}")
           for f in FILES]
    return PRContext(
        pr_number=n, title=f"PR {n}", description="desc", author="dev",
        base_branch="main", head_branch="", state="open", changed_files=cfs,
        diff="diff", repo_structure="mono", related_files=[],
        commits=[{"oid": f"{n:040x}"}],
        has_merge_conflicts=(n % 7 == 0), merge_state_status="CLEAN",
    )


def main():
    setup_repo()
    cfg = GitHubRunnerConfig(token="x", repo="o/r")
    reviewer = por.ParallelOrchestratorReviewer(WORK, WORK / ".auto-claude" / "github", cfg)
    digest = hashlib.sha256()
    results = []
    sink = io.StringIO()
    for n in range(1, 151):
        Scenario.seed = n
        with contextlib.redirect_stdout(sink):
            res = asyncio.run(reviewer.review(make_context(n)))
        sink.seek(0)
        sink.truncate()
        rec = {
            "n": n, "ok": res.success, "err": res.error,
            "verdict": str(res.verdict), "status": res.overall_status,
            "blockers": res.blockers,
            "findings": [(f.id, f.title, f.severity.value, f.validation_status,
                          f.cross_validated) for f in res.findings],
            "summary": res.summary,
        }
        digest.update(json.dumps(rec, sort_keys=True, default=str).encode())
        results.append((n, res.success, len(res.findings), str(res.verdict)))
    for r in results[:5]:
        print(*r)
    print(digest.hexdigest())


if __name__ == "__main__":
    main()
