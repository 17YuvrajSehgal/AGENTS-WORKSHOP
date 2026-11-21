# Codebook v0: is this pull request about performance?

Draft 2026-11-20, used by the LLM classifier (`analysis/p1_classify.py`)
and by the human annotators. Freeze (git tag) before the full run.

Read the PR title, description, commit messages and the list of changed
files. Judge only what the PR itself says and changes. Do not guess what
the code might do.

## Field 1: `perf_role`

- **primary**: making the software use less time or fewer resources is the
  main stated goal of the PR. Includes fixing a performance regression,
  a slow path, a memory leak, or excess I/O.
- **secondary**: the PR has another main goal (feature, bug fix, refactor)
  but explicitly states a performance improvement as one of its effects.
- **measurement_only**: the PR adds or changes benchmarks, profiling or
  performance tests, without claiming to change performance itself.
- **none**: performance words appear (e.g. "performance" as a section
  heading, "faster" in an unrelated sense, "cache" in a CI config, a
  feature called "batch"), but the PR does not claim to improve
  performance.

## Field 2: `perf_scope` (only when role is primary or secondary)

- **runtime**: the software's own execution: latency, throughput, CPU,
  memory, I/O, startup time, rendering, query time.
- **build_or_ci**: build time, CI pipeline time, Docker build, dependency
  install.
- **test_suite**: making the test suite run faster.
- **other**: anything else (developer tooling speed, docs site build).
- **not_applicable**: role is measurement_only or none.

## Field 3: `evidence_quote`

The shortest exact text, copied character for character from the PR
title, description or commit messages, that supports the role. Empty
string only when role is none. Code rejects any quote that is not found
word for word.

## Field 4: `confidence`

`high`, `medium` or `low`: how sure the judgement is from the text alone.

## Examples of the boundary

- "## Performance\nNo performance impact." -> none.
- "Copilot coding agent works faster ... when set up" footer -> none
  (template text; removed before classification anyway).
- "Use a dict lookup instead of scanning the list; this makes import 4x
  faster" in a refactor PR -> secondary, runtime.
- "Cache node_modules in GitHub Actions" -> primary, build_or_ci.
- "Add pytest-benchmark suite for the parser" -> measurement_only.
- "feat: batch export of reports" (a feature named batch) -> none.
