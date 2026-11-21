"""Build one PR on a fleet VM: harness setup -> blind agent -> harness re-check.

  python3 run_agent.py '<job json>'

Writes into ~/prs/<order>_<id>/:
  job.json        what the agent may see (no title/body/commits/claim)
  pr.diff         merge-base -> head code diff
  transcript.jsonl  full agent session (stream-json), for audit
  verdict.json    agent's structured answer + harness check + audit flags
The repository's git history is moved to a root-only directory after
setup, so the agent cannot read the PR's commit messages.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
AGENT_DIR = HOME / "agent"
MODEL, EFFORT, TIMEOUT_S = "claude-opus-5-5", "medium", 45 * 60
TOOLS = "Bash,Read,Write,Edit,Glob,Grep"
SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["built", "unbuildable"]},
        "reason": {"type": "string", "enum": ["none", "needs_gpu", "needs_external_service",
                                              "install_failed", "not_python_change",
                                              "new_code_only", "change_unreachable",
                                              "needs_patching", "too_large", "other"]},
        "tier": {"type": "string", "enum": ["benchmark", "repo_tests", "own_calls", "none"]},
        "uses_parallelism": {"type": "boolean"},
        "behaviour_change_expected": {"type": "boolean"},
        "notes": {"type": "string"},
    },
    "required": ["status", "reason", "tier", "uses_parallelism", "behaviour_change_expected", "notes"],
    "additionalProperties": False,
}
TASK = ("Prepare this pull request for measurement as described in your instructions: make both "
        "environments work, write workload.py, run ~/agent/check.py until it passes, then give "
        "the final JSON answer. If it cannot be done, give the final JSON answer with the reason.")


CODE_EXT = {"py", "pyx", "pxd", "rs", "c", "cc", "cpp", "cxx", "h", "hpp", "cu", "go", "java", "kt",
            "scala", "js", "jsx", "ts", "tsx", "rb", "php", "cs", "swift", "m", "mm", "sh", "sql",
            "vue", "svelte", "zig", "lua", "r", "jl", "dart"}


def code_lines_by_language(diff_path):
    """Added + removed lines per code-file extension in the PR diff."""
    out, ext = {}, None
    for line in diff_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("diff --git "):
            name = line.split(" b/")[-1]
            e = name.rsplit(".", 1)[-1].lower() if "." in name.rsplit("/", 1)[-1] else ""
            ext = e if e in CODE_EXT else None
        elif ext and line[:1] in "+-" and not line.startswith(("+++", "---")):
            out[ext] = out.get(ext, 0) + 1
    return out


def main(job):
    d = HOME / "prs" / f"{job['order']:04d}_{job['id']}"
    d.mkdir(parents=True, exist_ok=True)
    blind = {k: job[k] for k in ("repo", "number", "created", "changed_files", "n_files")}
    (d / "job.json").write_text(json.dumps(blind, indent=1))
    t0 = time.time()
    env = {**os.environ, "PATH": f"{HOME}/.local/bin:{os.environ['PATH']}"}
    setup = subprocess.run(["bash", str(HOME / "pilot" / "setup_pr.sh"), str(d), job["repo"],
                            job["api_base_sha"], job["head_sha"], job["created"], "3.12"],
                           capture_output=True, text=True, env=env)
    (d / "setup.log").write_text(setup.stdout + setup.stderr)
    # hide git history (commit messages state the claim)
    hidden = Path("/srv/kt/repos") / f"{job['id']}"
    if (d / "repo").exists():
        subprocess.run(["sudo", "mkdir", "-p", "/srv/kt/repos"], check=True)
        subprocess.run(["sudo", "rm", "-rf", str(hidden)])
        subprocess.run(["sudo", "mv", str(d / "repo"), str(hidden)], check=True)
        subprocess.run(["sudo", "chmod", "700", str(hidden)], check=True)
    for side in ("base", "head"):
        (d / side / "src" / ".git").unlink(missing_ok=True)
    setup_s = time.time() - t0

    t1 = time.time()
    # --append-system-prompt-file is not a listed option in Claude Code 2.1.329: pass the text
    instructions = (AGENT_DIR / "BUILD_AGENT.md").read_text(encoding="utf-8")
    cmd = ["claude", "-p", TASK, "--append-system-prompt", instructions,
           "--model", MODEL, "--effort", EFFORT, "--tools", TOOLS,
           "--permission-mode", "bypassPermissions", "--setting-sources", "",
           "--settings", json.dumps({"disableAllHooks": True}), "--strict-mcp-config",
           "--no-session-persistence", "--json-schema", json.dumps(SCHEMA),
           "--output-format", "stream-json", "--verbose"]
    result, timed_out = None, False
    with open(d / "transcript.jsonl", "w", encoding="utf-8") as tr:
        try:
            subprocess.run(cmd, stdout=tr, stderr=subprocess.STDOUT, cwd=d, env=env,
                           timeout=TIMEOUT_S, text=True)
        except subprocess.TimeoutExpired:
            timed_out = True
    lines = (d / "transcript.jsonl").read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result = ev
            break
    agent_s = time.time() - t1

    # A usage/rate limit is not an outcome of the PR: write no verdict, so the job stays
    # "not attempted" and the worker retries it after the limit resets (batch 0 lost 64
    # attempts to "You've hit your 5-hour limit" before this check existed).
    if result and (result.get("api_error") in ("usage_limit_reached", "rate_limit_error")
                   or result.get("api_error_status") == 429):
        (d / "verdict_ratelimited.json").write_text(json.dumps(
            {"job": job, "message": result.get("result"), "agent_s": round(agent_s),
             "at": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
        (d / "verdict.json").unlink(missing_ok=True)
        print(json.dumps({"id": job["id"], "status": "rate_limited", "message": result.get("result")}))
        return

    # independent re-check by the harness
    check = None
    if (d / "workload.py").exists():
        subprocess.run(["python3", str(AGENT_DIR / "check.py"), str(d), str(d / "workload.py")],
                       capture_output=True, text=True, env=env)
        if (d / "check.json").exists():
            check = json.loads((d / "check.json").read_text())
    text = "\n".join(lines)
    lang = code_lines_by_language(d / "pr.diff") if (d / "pr.diff").exists() else {}
    audit = {"mentions_github_pull": bool(re.search(r"github\.com/[^\s\"']+/pull/|api\.github\.com",
                                                    text)),
             "used_gh_cli": bool(re.search(r'"command":\s*"gh ', text)),
             "read_git_history": bool(re.search(r'"command":\s*"[^"]*git (log|show|reflog)', text))}
    usage = (result or {}).get("modelUsage") or {}
    verdict = {"job": job, "agent": (result or {}).get("structured_output"),
               "agent_is_error": (result or {}).get("is_error"), "timed_out": timed_out,
               "models": sorted(usage), "list_usd": sum(v.get("costUSD", 0) for v in usage.values()),
               "num_turns": (result or {}).get("num_turns"), "setup_ok": setup.returncode == 0,
               "setup_s": round(setup_s), "agent_s": round(agent_s), "check": check,
               "harness_pass": bool(check and check.get("pass")), "audit": audit,
               # changed code lines per language: a PR whose claim lives in non-Python code
               # but whose measured change is Python must be flagged at analysis time
               "changed_code_lines": lang,
               "python_share_of_code_change": round(lang.get("py", 0) / sum(lang.values()), 3)
               if sum(lang.values()) else None}
    (d / "verdict.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps({"id": job["id"], "status": (verdict["agent"] or {}).get("status"),
                      "reason": (verdict["agent"] or {}).get("reason"),
                      "harness_pass": verdict["harness_pass"], "agent_s": verdict["agent_s"],
                      "usd": round(verdict["list_usd"], 2), "audit": audit}))


if __name__ == "__main__":
    main(json.loads(sys.argv[1]))
