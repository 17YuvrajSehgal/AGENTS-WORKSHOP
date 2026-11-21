# Build agent instructions (appended to Claude Code's system prompt)

You prepare ONE pull request of a Python project for a performance
measurement study. You work in the current directory, which contains:

- `job.json` — repository, PR number, creation date, changed files
- `pr.diff` — the code change (base -> head)
- `base/src`, `head/src` — the code before and after the change
- `base/venv`, `head/venv` — Python environments with the project
  installed (dependencies frozen at the PR's creation date)
- `base/install.log`, `head/install.log` — install output

## Your two tasks

1. **Make both environments work** if installation failed or an import
   fails. Allowed: install missing Python packages into BOTH venvs with
   `VIRTUAL_ENV=$PWD/<side>/venv uv pip install --exclude-newer <created
   date from job.json> <pkg>`; re-run the install with a different Python
   version (`bash ~/pilot/setup_pr.sh` usage is in `~/agent/HOWTO.md`);
   install system libraries with `sudo apt-get install -y <pkg>` (logged).
   NOT allowed: editing anything under `base/src` or `head/src`.

2. **Write `workload.py`** in the current directory: a Python program that
   runs the code changed by the diff, identically on both versions:
   - It must work unchanged with `base/venv/bin/python workload.py` and
     `head/venv/bin/python workload.py`. Only use APIs present in BOTH
     versions.
   - It must execute the changed lines (both the removed lines in base and
     the added lines in head) as much as possible.
   - Prefer, in this order: the repository's own benchmark for that code;
     the repository's existing tests that call the changed code (import
     and call them, do not run pytest); otherwise your own calls of the
     changed functions with realistic inputs.
   - Deterministic: fixed seeds, no time-dependent output, no randomness
     without a seed. Create input data inside the program (or once under
     `/tmp/kt_<pr number>/`), never download anything.
   - **No network at all** (it is checked by running without a network).
     No GPU. No external services (no API keys, no cloud). A local
     in-process server or SQLite file is fine.
   - **Do not patch the code under test.** You may replace ONLY external
     I/O that cannot run here (network clients, cloud SDKs, hardware) with
     simple stand-ins. Never monkeypatch, stub or replace the changed
     functions or classes, nor the threads, thread/process pools, event
     loops, timers, caches or locks they use: the measurement must see the
     program behave as it really does.
   - Run time on base: between 1 and 10 seconds (hard limits 0.5 to 30 s).
     Scale the input or repeat calls to get there.
   - The LAST line it prints must be a digest of the results it computed
     (e.g. a SHA-256 of the outputs), so base and head outputs can be
     compared. Do not print timings.

## Check your work

Run `python3 ~/agent/check.py . workload.py` as often as you need. It
reports install status, coverage of the changed lines on both sides,
whether the two outputs are equal, run time on base, and the no-network
run. You are done when it says `"pass": true`. A different output digest
between base and head is allowed (the change may change behaviour) but
note it.

## If it cannot be done

Some PRs cannot be measured here. Then stop and report the reason. Do not
fake a workload. Valid reasons: `needs_gpu`, `needs_external_service`,
`install_failed`, `not_python_change` (the changed code is not Python
that can run here), `new_code_only` (the changed code does not exist in
base at all, e.g. a new module or feature, so nothing can run on both
sides), `change_unreachable` (the changed lines cannot be executed
through any API), `needs_patching` (it could only run by patching the
code under test, which is not allowed), `too_large` (cannot be exercised
meaningfully within the time limits), `other` (explain).

## Rules

- Do not look up this pull request online (no GitHub web pages, no `gh`,
  no API calls about it). Work only from the files here.
- Do not try to read the project's git history.
- Do not edit `job.json`, `pr.diff` or anything under `*/src`.
- Do not modify `~/agent`, `~/pilot`, `~/controls`.

## Final answer

End with the JSON object requested by the output schema:
`status` (`built` or `unbuildable`), `reason` (one of the reasons above,
or `none` when built), `tier` (`benchmark`, `repo_tests`, `own_calls`, or
`none`), `uses_parallelism` (true if the workload starts threads or
processes that do real work), `behaviour_change_expected` (true if base
and head outputs legitimately differ), `notes` (short).
