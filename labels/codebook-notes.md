# Codebook notes: open cases for v1

`codebook-perf-v0.md` is the system prompt of the pilot run and must stay
byte-identical for all 2,000 pilot PRs. Cases found during the pilot are
collected here and settled when v1 is written.

## 1. Slowdown introduced and fixed inside the same PR (2026-11-20, smoke test)

AutoGPT #12347 (https://github.com/Significant-Gravitas/AutoGPT/pull/12347),
a feature PR. A commit "Fixes based on pr comments" says: "Performance
regression — get_or_activate_user() does an uncached User.find_unique on
every API request. The old get_or_create_user was @cache_user_lookup (300 s
LRU)." The regression came from an earlier commit of the same PR. v0
labelled it secondary / runtime. Against the PR's base there may be no
speed-up at all, and the study compares base against head, so v1 needs a
separate value or flag for this.
