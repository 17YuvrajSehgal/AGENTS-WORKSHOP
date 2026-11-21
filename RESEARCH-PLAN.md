# Research plan: kernel-level validation of agent performance PRs

Written 2026-11-19. Background and prior-work check: `paper-ideas.md`
(Idea 2). Dataset paper: `related-papers/2602.09185v1.pdf`.

Working title: **"Below the Stopwatch: Do the Performance Claims of Coding
Agents Hold at the Kernel Level?"**

---

## 1. The one-paragraph pitch

Coding agents open thousands of pull requests that claim to make code
faster. Prior work reads these claims as text, or at most times a few of
them with a stopwatch (53 fixes in "Merged, Not Measured", arXiv
2609.37985). But a performance PR claims a *mechanism*, not only a number:
"cache the file instead of reading it each call", "batch the requests",
"remove the lock". Every such mechanism leaves a footprint in the kernel:
fewer `read` syscalls, fewer context switches, less futex waiting. We build
a harness that rebuilds the before and after commits of agent perf PRs from
AIDev, runs them under `perf` and eBPF, and checks three things: is it
faster, did the claimed mechanism actually happen, and did the cost move
somewhere else. This gives the first mechanism-level check of agent
performance work, and a reusable oracle that maps claims to kernel signals.

## 2. Contributions (what the paper will claim)

1. **A claim-to-signal oracle**: a taxonomy of performance mechanisms that
   agents claim, each mapped to the kernel and hardware signals that must
   move if the claim is true (Section 5).
2. **An executable dataset**: N agent perf PRs and a matched set of human
   perf PRs, each with a container that builds both commits, a workload
   that is proven to reach the changed code, and full traces.
3. **An empirical study** (RQ1 to RQ5): how often claims are checkable, how
   often the speedup holds, how often the mechanism holds, which hidden
   costs appear, and how all of this relates to review outcomes.
4. **(Extension) A trace-in-the-loop agent**: give the agent the kernel
   trace diff and measure whether its PR description becomes accurate.
   This is the part that speaks to agentic engineering directly.
5. **Open artifact**: harness, containers, traces, labels, analysis
   scripts.

## 3. Research questions

- **RQ1. What mechanisms do agent perf PRs claim, and how many can a kernel
  trace check?** Claim taxonomy; share of PRs with a checkable mechanism;
  agent vs human; per agent.
- **RQ2. Do the claimed speedups hold?** Wall-time ratio, head vs base,
  against a measured noise floor. Replicates and scales up "Merged, Not
  Measured".
- **RQ3. Does the claimed mechanism happen?** Does the signal the oracle
  names move in the claimed direction, beyond the noise floor?
  Cross RQ2 x RQ3 gives the main figure, four quadrants:

  |  | mechanism happened | mechanism did not happen |
  |---|---|---|
  | **faster** | claim true | faster for another reason |
  | **not faster** | mechanism is not the bottleneck | claim false |

- **RQ4. Hidden costs.** When wall time improves, which resources got worse
  (system time, syscalls, page faults, peak memory, cache misses, CPU time
  across threads)? When wall time does not change, what does the kernel
  view say about why (for example, a CPU change in an I/O-bound path)?
- **RQ5. Does kernel evidence relate to what reviewers did?** Merged vs
  rejected, verified vs not, controlling for agent, language, PR size and
  repository. Agent vs human on the same repositories.
- **RQ6 (extension). Can kernel feedback make agents honest?** Give an
  agent the trace diff; measure claim accuracy before and after, and how
  often the agent then fixes or withdraws the change.

## 4. Data

### 4.0 Dataset facts register (accuracy rule)

The AIDev authors are on the program committee. Every fact about AIDev in
the paper must be either **V-paper** (stated in arXiv 2602.09185, location
given), **V-data** (checked by a script on the pinned files), or
**attributed** to another paper by citation. Nothing else goes into the
paper. Update this table whenever a fact is checked.

Status codes: **V-paper** = arXiv 2602.09185; **V-readme** = dataset card
README at main commit `b8dc67df93e7c11f6f20c84129db7232eb1ec253`
(saved copy: `data/aidev-readme-b8dc67d.md`);
**V-data** = read from the pinned parquet files by script.

**Pinned version (decision 2026-11-20): AIDev v5, HF tag `v5` = commit
`b37f9fd1613cfec55886105bb76721918d015dc7`.** Load as
`hf://datasets/hao-li/AIDev@b37f9fd1613cfec55886105bb76721918d015dc7/<table>.parquet`.

**The paper (arXiv 2602.09185) describes an older release, not v5.** Its
numbers must never be presented as facts about our data. When we cite the
paper's numbers, we say they describe the release the paper reports.

Facts about the paper's release:

| fact | status | source |
|---|---|---|
| 932,791 agent-authored PRs, 116,211 repositories, 72,189 developers | V-paper | abstract; Sec. 1; Table 1 |
| five agents: OpenAI Codex, Devin, GitHub Copilot, Cursor, Claude Code | V-paper | abstract; Sec. 1 |
| dataset cutoff: 1 August 2025 | V-paper | Sec. 1 |
| curated subset: 33,596 PRs, 2,807 repositories, 1,796 users, repositories with **more than 100** GitHub stars | V-paper | abstract; Sec. 1; Table 1 |
| curated tables: `pr_comments` 39,122; `pr_reviews` 28,875; `pr_review_comments` 19,450; `pr_commits` 88,576; `pr_commit_details` 711,923; `related_issue` 4,923; `issue` 4,614; `pr_timeline` 325,500; `pr_task_type` 33,596 | V-paper | Table 1 |
| `pr_task_type` = automated classification of PR purpose in Conventional Commits categories, GPT-based | V-paper | Sec. 2; Table 1 |
| the paper does not report the accuracy of the `pr_task_type` labels | V-paper (absence) | whole paper read 2026-11-19 |
| the paper never uses the name "AIDev-pop" | V-paper (absence) | whole paper |

Facts about v5 (our pinned data):

| fact | status | source |
|---|---|---|
| v5 = "AIDev-7.6M", cutoff 31 March 2026 | V-readme | README line 109, "Dataset Updates" |
| six agents: OpenAI Codex, GitHub Copilot, Claude Code, Cursor, Google Jules, Devin | V-readme | "Overview" |
| `all_pull_request`: 7,685,281 rows | V-data (= README 7,685,281) | parquet footer |
| `all_repository`: 957,209 rows. README "Overview" says 961,168 repositories | V-data; **does not match README** | ask the authors' definitions or count distinct `repo_id` in `all_pull_request` ourselves before quoting either |
| `all_user`: 399,962 rows. README says 393,349 human developers | V-data; **does not match README** | README counts distinct human PR authors; Copilot and Devin count 0 by definition (README note) |
| "AIDev-pop" = the subset of repositories with more than 100 stars | V-readme | README "AIDev-pop: Filtered (>100 stars)"; spelled "AIDev-pop" |
| AIDev-pop `pull_request`: 361,296 rows; `repository`: 25,402 rows | V-data | parquet footer |
| AIDev-pop tables and rows: `pr_comments` 676,098; `pr_reviews` 541,831; `pr_review_comments` 291,248; `pr_commits` 1,718,829; `pr_commit_details` 12,116,310; `pr_timeline` 6,515,552; `issue` 72,664; `related_issue` 100,050 | V-data | parquet footer |
| v5 has no `user` table for AIDev-pop (dropped) | V-data + commit message `c81e9b18` | file list |
| **`pr_task_type` is not in v5** (removed since v4; only in v3) | V-readme | "Dataset Updates" |
| v3 and v4 truncated comments, reviews, review comments, commits (and in v3 also `pr_timeline`) at 30 items per PR; fixed in v5 | V-readme | top note and "Dataset Updates" |
| v5 re-fetched threads may include items created after the mining date; filter on `created_at` for strict cutoff | V-readme | "Dataset Updates" |
| `pr_commit_details` may miss commits beyond the first 30 of very large PRs; `patch` omits large patches | V-readme | "Dataset Updates"; "AIDev-pop" section |
| AIDev-pop re-validates Claude Code and Copilot PRs with stricter filters (Claude Code footer check, 99.8% recall on a 160k sample; Copilot must be authored by `copilot`) | V-readme | "How Agent PRs Are Identified" |
| agent PRs found by GitHub search queries per agent (table in README) | V-readme | same section |
| **no human-authored PRs** in any table | V-data (file list) + V-readme (tables listed) | human baseline must be mined by us |
| **no base SHA, head SHA or merge SHA column** on `pull_request`; commit SHAs only in `pr_commits` / `pr_commit_details`, with no parent SHA | V-data | schema; the harness must get `base.sha` from the GitHub API |
| language is per repository (`repository.language`), not per PR | V-data | schema |
| v5 schemas, full column list and types | V-data | `data/v5_schema.json` |
| other tags: `v0.1` `5004560a`, `v3` `3ca00457`, `v4` `bc799690` | V-data | HF refs API |

Checked by script on 2026-11-20 (`analysis/p1_download.py`,
`analysis/p1_counts.py`; outputs `data/aidev-v5-manifest.json`,
`data/p1_counts.json`, `data/p1_counts.log`):

| fact | status | source |
|---|---|---|
| all 12 downloaded tables match the SHA-256 Hugging Face publishes for commit `b37f9fd` | V-data | manifest |
| `agent` values are spelled `OpenAI_Codex`, `Copilot`, `Claude_Code`, `Cursor`, `Google_Jules`, `Devin` (underscores) | V-data | p1_counts |
| README "Quick Look": PR counts and % open / closed / merged **match exactly** for all six agents and the total | V-data | p1_counts.log |
| README developer counts **match exactly** for Codex 237,223, Claude Code 114,516, Cursor 62,246, Jules 18 | V-data | p1_counts.log |
| README developers for Copilot (0) and Devin (0): data has 8,463 and 1 distinct `user` values; README says 0 "by definition" for bot-authored agents | V-data; definitional | full set only |
| README total developers 393,349 vs 399,963 distinct `user` in `all_pull_request`; README's exact rule not reproduced | V-data; **unexplained** | do not quote either as ours |
| README repositories are slightly higher than distinct `repo_id` for every agent (total 961,168 vs 957,209); 44,547 full-set PRs have a null `repo_id` | V-data; **unexplained** | possibly counted by `repo_url`; not checked |
| full-set Copilot PRs: top author `Copilot` 1,561,101 of 1,581,924; others include human accounts and `github-actions[bot]` | V-data | p1_counts |
| AIDev-pop: 361,296 PRs, all ids distinct, all in `all_pull_request`; 25,402 repositories, every one with PRs, no PR with a missing repository | V-data | p1_counts |
| AIDev-pop: minimum stars 101; 0 repositories with 100 stars or fewer | V-data | p1_counts |
| AIDev-pop by agent: Claude_Code 172,597; Copilot 98,384; OpenAI_Codex 62,731; Cursor 12,908; Devin 11,219; Google_Jules 3,457 | V-data | p1_counts |
| AIDev-pop Copilot, Devin, Jules PRs each have exactly one author account (`Copilot`, `devin-ai-integration[bot]`, `google-labs-jules[bot]`) | V-data | p1_counts |
| AIDev-pop outcomes: 8.0% open, 23.7% closed unmerged, 68.3% merged | V-data | p1_counts |
| AIDev-pop repository languages, top 5: TypeScript 4,994; Python 4,941; Go 2,180; JavaScript 1,669; Rust 1,568 | V-data | p1_counts |

Rule for the paper: quote only AIDev-pop numbers as our own. Full-set
repository and developer totals are cited as the dataset card's numbers.

Consequences for the plan:

- We cannot use the authors' `perf` labels on v5. We classify perf PRs
  ourselves (Section 4.2), which the plan already does. Numbers like
  "340 `perf` PRs" from other papers refer to v3 and are only cited as
  theirs.
- Do not mix v3 labels into v5 without saying so. If we ever use v3
  `pr_task_type` for comparison, join on PR `id` and report coverage.

### 4.1 Source

- AIDev v5, AIDev-pop subset (repositories with more than 100 stars,
  361,296 PRs): PRs, diffs (`pr_commit_details`), commits, reviews,
  timelines. Spell it "AIDev-pop" as the dataset card does.
- **Pinned**: v5, commit `b37f9fd1613cfec55886105bb76721918d015dc7`
  (Section 4.0).
- **Human baseline**: v5 has no human PRs, so we mine human perf PRs from
  the same AIDev-pop repositories and the same time window with the GitHub
  API, using the same perf classifier.
- **Base commit**: v5 has no base SHA, so the harness fetches `base.sha`
  and `head.sha` for each PR from the GitHub API and records them.

### 4.2 Finding performance PRs

Other papers report that the `perf` label covers only 340 PRs and that
1,100 to 1,300 perf PRs appear when bug-fix and feature PRs are also
searched. These are their numbers on their AIDev versions; we recount on
our pinned version before quoting anything.

1. Keyword filter on title, body and commit messages
   (`analysis/p1_keyword_filter.py`, 14 keyword groups, frozen in the
   file). Template text is removed first: a body line (URLs masked,
   whitespace collapsed) that appears in at least 0.5% of one agent's PR
   bodies is dropped; the dropped lines are listed in
   `data/p1_template_lines.csv`. Without this, Copilot's footer "coding
   agent works faster ... when set up for your repo" (in 27,149 of 98,384
   AIDev-pop Copilot PRs) matched `speed`.
   **Result 2026-11-20:** 108,708 candidates of 361,296 (30.1%); 18,577
   match in the title; 90,131 only in body or commit messages. By agent:
   Claude_Code 56,395; Copilot 29,226; OpenAI_Codex 16,436; Cursor 3,000;
   Devin 2,671; Google_Jules 980. Input for an LLM: about 60M tokens at a
   6,000-character cap per PR (chars / 4, rough); title matches alone
   about 9M.
2. LLM classifier (Claude) with a written codebook: is this PR's main goal,
   or a stated goal, performance?
   **Pilot set up 2026-11-20 (decision: Claude API, pilot of 2,000
   first).** Codebook `labels/codebook-perf-v0.md` (fields `perf_role`:
   primary / secondary / measurement_only / none; `perf_scope`: runtime /
   build_or_ci / test_suite / other / not_applicable; `evidence_quote`
   checked verbatim by code; `confidence`). Script
   `analysis/p1_classify.py` (`sample` / `dryrun` / `submit` / `fetch`).
   Sample: simple random 2,000 of 108,708 candidates, seed 42 (Claude_Code
   1,011; Copilot 584; OpenAI_Codex 284; Cursor 53; Devin 51; Google_Jules
   17); 19 bodies and 82 commit-message sets over 12,000 chars were cut
   and flagged; 53 PRs have no file list. Model `claude-opus-5-5`, effort
   `low`, Message Batches API, strict JSON schema output. Dry run: ~2.3M
   input tokens (chars/4) plus a 2,552-char system prompt per request.
   Environment: `AGENTS-WORKSHOP/.venv`, exact versions in
   `requirements.lock.txt` (anthropic 2.11.0, pandas 3.1.1, pyarrow
   26.0.1, huggingface_hub 2.4.0).
   Whether `build_or_ci` and `test_suite` PRs belong in the study is
   decided after the pilot (the study measures runtime behaviour).
   **Changed 2026-11-20 (user decision): run through headless Claude Code
   on the user's account, not paid API calls** (`analysis/p1_classify_cc.py`,
   same codebook, schema, inputs, quote check). One `claude -p` call per
   PR: our codebook as `--system-prompt-file`, `--tools ""`,
   `--setting-sources ""`, `disableAllHooks`, `--strict-mcp-config`,
   `--no-session-persistence`, `--exclude-dynamic-system-prompt-sections`,
   `--json-schema`, model `claude-opus-5-5`, effort `low`; Claude Code
   2.1.318. Checked: no CLAUDE.md, memory or hook text reaches the call. A
   fixed ~740-token Claude Code environment block (date, OS, model name,
   working directory, user email, file-safety guidance) remains; `--bare`
   would remove it but cannot use an account login. Its size was constant
   in tests (754 tokens with a 15-token prompt; +400 tokens of system
   prompt gave exactly 1,154). The runner stores the system prompt's
   SHA-256 and refuses to continue if it changes. Smoke test 20 PRs: 20 ok,
   0 quotes not found; mean input ~7,900 tokens (long commit histories),
   median call 2.9 s. Full input kept (user decision). Open codebook cases
   go to `labels/codebook-notes.md` until v1.
   **Pilot result 2026-11-20 (`data/p1_classify/pilot_summary_cc.json`):**
   2,000 run, 1,999 labelled, 1 safety stop (Black-Hat-Zig #7, Opus 5.5
   then Opus 4.8 fallback both declined; no label). All 1,999 labels from
   `claude-opus-5-5` alone. Roles: none 1,377; secondary 316; primary 243;
   measurement_only 63. Runtime perf (primary or secondary + runtime): 465
   (23.3%); primary + runtime: 203 (10.2%). Confidence among the 465: high
   143, medium 231, low 91. Quotes not verbatim: 6 (5 differ only in line
   breaks/spaces, 1 dropped markdown `**`); none invented; kept flagged.
   Mean input 8,715 tokens; API list-price equivalent $122.42 (paid from
   the user's plan, not billed). Ran 03:10 to 03:37 EST via scheduled
   task `kt-pilot-classify` (`analysis/run_pilot.cmd`).
   **Decision proposed, not yet taken:** do not classify all 108,708
   (~$6,500 list-equivalent). Use the pilot as the random sample for
   population estimates (RQ1), and classify only candidates in target
   languages for the measurement set. Candidates by repository language:
   TypeScript 27,628; Python 18,696; Go 11,402; Rust 8,986; Scheme 8,488;
   C# 5,716.
   **Scheme explained (2026-11-20):** 8,485 of the 8,488 come from one
   repository, `mochilang/mochi` (325 stars), which has 13,461 AIDev-pop
   PRs (3.7% of AIDev-pop), all OpenAI_Codex. 8,290 match `speed` in the
   body because test commands contain `-tags slow` / `-tags=slow`. The
   pilot handled it (4 of 153 sampled mochi PRs labelled runtime perf).
   Proposed for later stages (user decision): ignore keyword matches
   inside inline code and fenced code blocks. Analysis consequence: use a
   repository-clustered bootstrap for population estimates.
   Python pilot yield 78 of 318 (24.5%).
3. Human check (`analysis/p1_label_sheets.py`, `labels/human/`): 300
   pilot PRs, stratified by the LLM label, seed 42: stratum A = LLM
   runtime perf (150 of 465, weight 3.1), stratum B = everything else
   (150 of 1,534, weight 10.23). Two blind sheets (`sheet_A1.xlsx`,
   `sheet_A2.xlsx`, same items, different order, no machine labels);
   answer key `key.csv`; instructions `INSTRUCTIONS.md`. Report
   inter-annotator kappa, and the LLM's weighted precision and recall
   against the adjudicated human label.
3. Human validation: two annotators label a stratified random sample
   (300 PRs, both positive and negative from step 2). Report precision,
   recall and Cohen's kappa. Re-tune the prompt until precision is at least
   0.9 on a held-out half.
4. Cross-check against the released consensus set of "Merged, Not
   Measured" (1,262 issues) if its artifact is public; report overlap.

### 4.3 Claim extraction

For every perf PR, an LLM fills a fixed schema (structured output, retries,
validation):

```json
{
  "mechanisms": [{"type": "<taxonomy id>", "quote": "<exact text from PR>"}],
  "claimed_metric": "wall | cpu | memory | io | startup | throughput | none",
  "claimed_magnitude": "<number and unit, or null>",
  "evidence_in_pr": "benchmark | profile | test | reasoning | none",
  "target_code": ["<file::function>"]
}
```

- `quote` must be found word for word in the PR text (code checks this, a
  missing quote fails the row). This stops invented claims.
- Two annotators label 200 PRs independently; report kappa per field.
- The taxonomy starts from the oracle in Section 5 and is refined by open
  coding on the first 100 PRs (then frozen before the rest are labelled).

### 4.4 Executability funnel

Report every stage with counts, as a figure:

all perf PRs → language supported → repo still public → base and head
commits fetchable → builds at both commits → tests pass at both commits →
a workload exists that reaches the changed lines → measured.

Language order: Python first (largest share, simple builds), then Go and
Rust (good tooling, native code), then C/C++, Java and JS/TS if time
allows.

**Selection bias check:** compare executed vs not-executed PRs on merge
rate, size, agent, language and claim type (chi-square / Mann-Whitney).
Report it. If the executed set is very different, say so in threats.

### 4.5 Target size

**Sampling design (chosen 2026-11-20, replaces the earlier 300 + 150).**

Population for measurement: AIDev-pop keyword candidates that change at
least one `.py` file: 20,408 PRs (Claude_Code 13,098; Copilot 3,779;
OpenAI_Codex 2,236; Devin 620; Cursor 457; Google_Jules 218).

Measured targets (agent PRs):

| agent | measured | justification |
|---|---|---|
| Claude_Code | 185 | |
| Copilot | 100 | +/- 10 points per agent at 95% (worst case p = 0.5) |
| OpenAI_Codex | 100 | +/- 10 points per agent at 95% |
| **total** | **385** | **+/- 5 points overall at 95%** (n = 1.96^2 x 0.25 / 0.05^2) |
| Devin, Cursor, Google_Jules | all reachable | too few candidates; descriptive only, no per-agent claims |

Human baseline: 200 measured human perf PRs (two-proportion test vs 385
agent PRs detects a difference of about 14 points at alpha 0.05, power
0.8); mined later from the same repositories.

Working back to the classification budget (pilot rates, all candidates,
not Python-specific; re-estimate as data arrives):

- build/measure success >= 40% (Gate 2) -> attempts needed: Claude_Code
  ~463, Copilot ~250, OpenAI_Codex ~250 runtime-perf PRs (~960 total);
- pilot runtime-perf rate per agent among candidates: Claude_Code 28.1%
  (284/1,011), Copilot 21.2% (124/584), OpenAI_Codex 10.6% (30/283) ->
  classify about Claude_Code 1,850, Copilot 1,200, OpenAI_Codex 2,300,
  plus all ~1,300 Devin/Cursor/Jules: **about 6,600 PRs, ~$400
  API-equivalent** (pilot mean $0.061 per PR).

**Stop rule:** within each agent stratum, PRs are classified in a fixed
random order (seed 42); the stratum stops once its runtime-perf count
reaches the attempt target. Random order makes early stopping unbiased.
**Started 2026-11-20 11:11 EST** (`analysis/p2_classify.py`, run dir
`data/p2_classify/`). Population built: 20,408 PRs (Claude_Code 13,098;
Copilot 3,779; OpenAI_Codex 2,236; Devin 620; Cursor 457; Google_Jules
218). 350 pilot PRs fall in the population; their raw results were
reused after checking the system-prompt SHA-256 equals the pilot's.
Order file `order.parquet` (per stratum: pilot PRs first, shuffled, then
the rest, shuffled; seed `42-<agent>`). Targets in `targets.json`
(Claude_Code 463, Copilot 250, OpenAI_Codex 250, others "all").
**To extend the sample later:** raise a target in `targets.json`; the
next run continues down the same order. Runs via the hourly Windows task
`kt-p2-classify` (`analysis/run_p2.cmd`, 7 days, MultipleInstances
IgnoreNew); each run stops itself after 10 failures in a row (usage
limit) and the next hourly run resumes. `p2_classify.py status` prints
progress. Early note: OpenAI_Codex runtime-perf rate among `.py` PRs in
the reused pilot labels is 7/33, higher than its 10.6% over all
candidates; the stop rule adapts.
**Model switch 2026-11-20 11:27 (user decision):** the first 1,131
labels (Opus 5.5) are kept and not relabelled; all later PRs are
labelled by `claude-haiku-5-5` (same codebook, flags, effort `low`),
logged in `data/p2_classify/cc_run.json` (`model_changes`). Each raw
file records its model; analyses must report the labeller per PR.
Haiku vs Opus on the 66 PRs both labelled before the switch
(`analysis/p2_haiku_agree.py`, `data/p2_haiku_agree/agreement.json`):
runtime-perf agreement 0.909, kappa 0.785; Haiku precision vs Opus
0.895, recall 0.810; role kappa 0.781; scope kappa 0.724; 0 quotes not
verbatim; list-price usage $0.0015 vs $0.0621 per PR (n = 66, small).
**Fallback rule (2026-11-20):** if Claude Code answers with any model
other than the requested one (seen after a safety stop: Opus 4.8), the
answer is moved to `fallback_output` and the PR counts as seen with no
valid label (`p1_classify_cc.one`). Applied retroactively: p1 pilot 0
cases; p2 1 case (https://github.com/spellshift/realm/pull/1284, Opus 5.5
0 output tokens, answer by Opus 4.8). Re-run the retroactive scan before
any analysis (the task running at the time used the older code).
**Scheduler fix 2026-11-20 12:10:** the laptop went on battery; the
task's default power settings stopped the wrapper but left the Python
runner alive, so the scheduler showed Ready and would have started a
second copy at the next trigger. Fixed: task allowed on battery
(DisallowStartIfOnBatteries and StopIfGoingOnBatteries set to false), and
`p2_classify.py run` takes an exclusive file lock (`run.lock`, msvcrt) so
a second runner exits at once (tested). The orphaned runner was ended by
PID and restarted under the new code; no failures or duplicates.
**Finished 2026-11-20 13:04 EST; all strata reached their targets**
(`data/p2_classify/labels.parquet`, `summary.json`; scheduled tasks
`kt-p2-classify` and `kt-pilot-classify` deleted). 5,900 classified
(5,899 labels + 1 fallback, 0 failures); labellers: Haiku 5.5 4,769,
Opus 5.5 1,130. Final fallback scan: no new cases. Runtime-perf PRs
found: **1,343**:

| agent | classified / stratum | runtime perf | rate |
|---|---|---|---|
| Claude_Code | 1,850 / 13,098 | 472 | 25.5% |
| Copilot | 1,192 / 3,779 | 254 | 21.3% |
| OpenAI_Codex | 1,563 / 2,236 | 251 | 16.1% |
| Cursor | 457 / 457 | 118 | 25.8% |
| Devin | 620 / 620 | 121 | 19.5% |
| Google_Jules | 217 labelled / 218 | 127 | 58.5% |

Roles: none 4,119; secondary 827; primary 745; measurement_only 208.
Quotes not verbatim: 23 (Haiku 21, Opus 2); 19 differ only in white
space; 4 not found even after normalising (all Haiku; 3 of them runtime
perf) -> check by hand before measuring. Rate by labeller within agent
(Haiku lower each time, consistent with its 0.81 recall vs Opus on 66
PRs): Claude_Code Opus 109/380 vs Haiku 363/1,470; Copilot 52/218 vs
202/974; OpenAI_Codex 27/153 vs 224/1,410. List-price-equivalent usage
for this run's raw files: Opus $70.11 (includes the 350 reused pilot
labels), Haiku $8.07, fallback call $0.18.
**Full-population run (p4), started 2026-11-20 14:28 EST (user
decision: a full Haiku-labelled dataset for a nearby venue; the measured
study stays the main paper).** All 108,708 keyword candidates, fresh
labels by `claude-haiku-5-5` only (no reuse of p1/p2 labels), same
codebook v0, schema, flags and effort `low`; fixed random order (seed
42), so any finished prefix is a simple random sample. Separate directory
`data/p4_full/` (gitignored, large), script `analysis/p4_full.py`,
hourly Windows task `kt-p4-full` (14 days, no execution time limit,
allowed on battery, IgnoreNew, plus the file lock). First check: 109
labels in ~90 s, all Haiku-only; ~73 PRs/min with 4 workers -> ~25 h of
running time plus usage-limit pauses; ~$160 list-equivalent.
Open: the 300-PR human check covers Opus labels only (pilot PRs); to
validate Haiku against humans, Haiku would need to label those 300 too
(~$0.45 list-equivalent), which the user has not asked for.
Pilot PRs that change `.py` files count toward the targets (they were a
random sample of all candidates). Report the stratum sizes, the number
classified per stratum and the weights, so population estimates are
re-weighted correctly.

## 5. The claim-to-signal oracle

The core of the paper. Each row: a claimed mechanism, the signals that
must move, the direction, and the tool. Signals marked (PMU) need hardware
counters.

| claimed mechanism | primary signal | direction | secondary signal | tool |
|---|---|---|---|---|
| avoid repeated file reads / cache file content | `read`, `openat`, `newfstatat` counts; bytes read | down | page cache hits | LTTng syscall events |
| batch network or DB calls | `sendto`/`recvfrom`/`write` on sockets; `connect` | down | context switches down | LTTng syscall events |
| fewer process spawns | `clone`, `execve`, `wait4` | down | task-clock down | LTTng `sched_process_fork/exec` |
| less logging / output | `write` count and bytes to fds 1, 2, log files | down | sys time down | LTTng syscall events |
| fewer allocations / smaller data | minor page faults; `brk`, `mmap` calls; peak RSS | down | malloc calls | perf stat (faults); LTTng syscalls + libc `malloc` userspace probe; `/usr/bin/time -v` |
| algorithmic (lower complexity, remove repeated work) | instructions retired; user CPU time | down | sys time unchanged | perf stat (PMU for instructions) |
| data locality / cache friendliness | L1 and L2 misses (`L1-dcache-load-misses`, `l2_rqsts.miss`, `mem_load_retired.l1_miss/l2_miss`) | down | IPC up | perf stat (PMU `standard`; LLC events not available on our VM, see 7.1) |
| remove a lock / less contention | futex wait time; involuntary context switches | down | off-CPU time down | LTTng `futex` syscall entry/exit + `sched_switch` |
| add parallelism | wall time down, total CPU time up or equal | wall down | threads/CPUs used up | perf stat task-clock vs wall |
| async / non-blocking I/O | off-CPU time in sleep/D states | down | context switches change | LTTng `sched_switch` with prev_state; Trace Compass critical path |
| lazy loading / faster startup | `openat` and bytes read before first useful work; major faults | down | startup wall time | LTTng with a time window |
| fewer system calls in a hot loop (e.g. `stat` per item) | that syscall's count | down | sys time down | LTTng syscall events |

Notes:

- **Python allocations are mostly invisible to the kernel** (pymalloc
  reuses arenas). For Python memory claims also record `tracemalloc` peak,
  and CPython USDT probes if the interpreter is built with
  `--with-dtrace`. Say clearly which claims the kernel cannot see; that is
  itself a result for RQ1.
- **The oracle is written before the measurements** and frozen (git tag),
  so it cannot be tuned to the results.
- Each row needs a positive control: one small synthetic program pair
  where the mechanism is known to change, run through the harness, to show
  the signal moves as expected.

## 6. Execution harness

### 6.1 Per-PR container

- One Docker image per PR, built from the base commit. The head commit is
  applied inside the same image so both sides share the same dependencies.
- **Dependencies frozen at the PR's date**: `uv pip install --exclude-newer
  <PR creation date>` for Python; `go.sum` / `Cargo.lock` as committed; for
  others, the lockfile at the commit.
- Interpreter version chosen from the repo's CI config at that commit
  (`.github/workflows`, `tox.ini`, `pyproject.toml`); record it.
- Network off during measurement (`--network none`), both for noise and
  safety.

### 6.2 Build agent

Setting up old commits is the slow part, so use an agent, with strict
structure (lesson from the C7 work: anything the result depends on must be
enforced by code, not by instruction):

- Agent: Claude Code headless or OpenHands, in the container, with shell.
- Its only job: produce `build.sh`, `test.sh` and `workload.py` (or the
  language equivalent) that pass the checks below. It cannot edit the
  project's source.
- **It never sees the PR title, body or claim.** It sees the base commit,
  the diff, and the list of changed functions. This keeps the workload from
  being written to confirm the claim.
- Hard checks in code, not in the prompt:
  1. `build.sh` succeeds at base and head.
  2. `test.sh` passes at base and head (or the same set of tests fails at
     both, recorded).
  3. **Coverage check:** the workload must execute the changed lines
     (line coverage of the diff hunks at least 80% at head; `coverage.py`,
     `go test -cover`, `llvm-cov`). No coverage, no measurement.
  4. **Same output:** the workload's output is equal at base and head (or
     the PR states an intended change; then recorded and excluded from
     speed claims).
  5. Workload runs between 0.5 s and 30 s at base (long enough to measure,
     short enough to repeat).
- Retries: up to 3 attempts per PR with the error log fed back; timeout
  45 minutes per attempt; every attempt logged with tokens and cost.

### 6.3 Workload tiers

Record which tier each PR used and report results per tier:

- **T1** the PR's own benchmark or reproduction script.
- **T2** the project's existing benchmark suite (asv, pytest-benchmark,
  `go test -bench`, criterion, JMH) filtered to cases that cover the diff.
- **T3** existing tests that cover the diff, run as the workload.
- **T4** a micro-workload written by the build agent, calling the changed
  functions with realistic inputs; a human spot-checks a sample of 50.

T1 and T2 are the most credible; if a finding only holds in T4, say so.

## 7. Measurement

### 7.1 Machines (GCP)

- **Measurement VM (set up 2026-11-20)**: `kt-measure-1`, project
  `project-ba99825a-df02-4405-af4`, zone `us-central1-a`, **c4-standard-8**
  (8 vCPU = 4 cores x 2 threads, 1 socket, Intel Xeon Platinum 8581C),
  `--performance-monitoring-unit=standard`, Ubuntu 24.04.5, 200 GB
  hyperdisk-balanced. Setup is scripted in `harness/vm/setup_lttng.sh`,
  checked by `harness/vm/smoke_lttng.sh`.
  - **C3 does not support the PMU flag**: creation of c3-standard-8 was
    rejected for `enhanced`, `standard` and `architectural` alike. Google's
    docs list PMU support for C4, C4A, M4, A4X.
  - **`standard` = core and L2 events only.** Last-level cache events
    (`cache-references`, `cache-misses`, `LLC-load-misses`) report
    `<not supported>`. `enhanced` (adds LLC) needs a C4 with 144 or 288
    vCPUs per Google's docs, which is over our quota (C3 18 vCPUs in
    us-central1, 24 vCPUs across all regions, 4 already used).
  - Working events checked: `cycles`, `instructions`, `branch-misses`,
    `L1-dcache-load-misses`, `l2_rqsts.miss`, `l2_rqsts.references`,
    `mem_load_retired.l1_miss`, `mem_load_retired.l2_miss`, plus software
    events.
  - **Counter limit**: five programmable events at once were multiplexed
    (each counted about 80% of the time, then scaled). Rule: at most four
    programmable events per `perf stat` run, set `kernel.nmi_watchdog=0`
    so the watchdog does not hold a counter, and split larger sets across
    runs. Reject any counter row where perf reports less than 100% running
    time.
  - Open check: the first test showed about 6 instructions per cycle for
    a short Python loop, which is high. The positive controls must confirm
    counters are trustworthy before any result uses them.
- **Kernel pinned: `7.0.0-1017-gcp`** (`apt-mark hold` on image, headers,
  modules; meta packages `linux-image-gcp` / `linux-headers-gcp` removed so
  no newer kernel is installed; 7.0.0-1018-gcp was pulled in once and
  purged).
- **Build VM**: a separate many-core VM (or several spot VMs) that only
  builds images and runs the build agent. Builds never run on the
  measurement VM during measurement.
- Same image, kernel and settings for every run. Record `uname -r`,
  microcode, CPU model, governor.

### 7.2 Noise control

- **CPU setup (done and checked 2026-11-20).** Topology from `lscpu -e`:
  physical core k = CPUs k and k+4. Measurement cores 2 and 3 (CPUs
  2,3,6,7). Kernel command line `nohz_full=2,3,6,7 rcu_nocbs=2,3,6,7`
  (`/etc/default/grub.d/99-measure-cpus.cfg`); `system.slice` and
  `user.slice` limited to `AllowedCPUs=0,1,4,5` (systemd set-property).
  Each workload runs in its own scope:
  `systemd-run --scope --slice=measure -p AllowedCPUs=<cpus> taskset -c <cpus> <cmd>`;
  single-threaded workloads get CPU 2 only (its SMT sibling 6 stays idle),
  multi-threaded get 2,3. `systemd-run --scope` keeps the workload's pid
  (checked), so trace filtering by process tree works.
  **`isolcpus` must not be used:** it disables load balancing. Measured:
  with `isolcpus=2,3,6,7`, a 2-process pool pinned to CPUs 2,3 ran all
  work on one CPU (CPU3 11.49e9 instructions, CPU2 4.7e3) and was slower
  than serial (b/a wall 1.12). With the scope setup the same pool split
  5.75e9 / 5.82e9 instructions and wall fell 0.48 s -> 0.33 s.
  Persistent sysctls: `/etc/sysctl.d/99-measure.conf`
  (`perf_event_paranoid=-1`, `nmi_watchdog=0`, `kptr_restrict=0`).
  (The `4-11` / `$CPUS` placeholders in commands below mean these CPUs.)
- Set governor to `performance` where the VM allows it; disable ASLR for
  the run (`setarch -R`) as a sensitivity check, not by default.
- **Interleave** base and head runs (ABAB...), 30 timing runs per side
  after 3 warm-up runs.
- **A/A control**: run base against base for every PR. The A/A ratio
  distribution over all PRs defines the noise floor; a change counts only
  if its CI is outside the A/A 99th percentile band.
- **Cross-machine replication**: rerun a random 20% of PRs on a second VM
  of the same type on a different day. Report agreement.
- I/O claims: run both cold cache (`echo 3 > /proc/sys/vm/drop_caches`
  before each run) and warm cache; report both.

### 7.3 Timing runs and tracing runs are separate

Tracers add overhead and could change timing. So:

- **Timing runs** (30 per side): no tracers; wall time, user and sys time
  and peak RSS from `/usr/bin/time -v` or `getrusage`.
- **Counter runs** (10 per side): `perf stat` only.
- **Trace runs** (5 per side): LTTng kernel trace. Syscall counts are close
  to deterministic, so fewer runs are enough; check their variance anyway.
- Measure tracer overhead once per language on the positive-control
  programs and report it.

### 7.4 Tracer choice and commands

**LTTng is the main tracer** (decision 2026-11-20; the user's previous work
all uses it). One trace per run holds every kernel signal; signals are
counted offline, so new signals can be added later without re-running.
`perf stat` stays only for totals of hardware counters (one command, no
trace). Timing runs use neither.

Install: **built from source**, not from apt (`harness/vm/setup_lttng.sh`).
Installed and checked 2026-11-20:

| component | version | why not apt |
|---|---|---|
| lttng-modules | 2.16.0 | Ubuntu's `lttng-modules-dkms` 2.14.0 fails to build on 7.0.0-1017-gcp **and** 6.8.0-1074-gcp (`conflicting types for 'trace_hrtimer_start'`) |
| lttng-ust | 2.16.0 | match modules and tools |
| lttng-tools | 2.16.0 | match |
| userspace-rcu | 0.15.7 | UST 2.16 needs >= 0.15; Ubuntu ships 0.14.0 |
| babeltrace2 + Python `bt2` | 2.1.2 | tools 2.16 needs >= 2.1.0; Ubuntu ships 2.0.x |
| perf | 7.0.14 (`linux-tools-7.0.0-1017-gcp`) | apt is fine |

All tarballs are checked against the `.sha256` files from lttng.org /
efficios.com.

**Page faults are not traced with LTTng on this kernel.** Ubuntu's kernel
headers package leaves out `arch/x86/include/asm/trace/exceptions.h`, so
the lttng-modules build skips `lttng-probe-x86-exceptions` without an
error (the kernel itself has the `exceptions/page_fault_user`
tracepoint). Page faults come from `perf stat` (`minor-faults`,
`major-faults`), which the kernel counts exactly.

**Event guard**: `lttng enable-event` accepts an event name that does not
exist without any error, which would silently produce zeros. Every trace
script first checks each event name against `lttng list --kernel` and
stops if one is missing (see `harness/vm/smoke_lttng.sh`).

Smoke test result (2026-11-20; Python opening and reading `/etc/os-release`
1,000 times): `openat` 1,043, `read` 2,046, `close` 1,037, discarded
events 0; perf: 1,085 minor faults, 0 major. The extra ~40 opens are
interpreter startup; two reads per open (content + end of file).

Counter runs (groups of at most four programmable events, see 7.1):

```bash
sudo sysctl -w kernel.nmi_watchdog=0
# software events, any number
perf stat -x, -o sw.csv -e task-clock,context-switches,cpu-migrations,minor-faults,major-faults -- taskset -c $CPUS ./workload
# hardware group A
perf stat -x, -o hwA.csv -e cycles,instructions,branch-misses,L1-dcache-load-misses -- taskset -c $CPUS ./workload
# hardware group B
perf stat -x, -o hwB.csv -e l2_rqsts.references,l2_rqsts.miss,mem_load_retired.l1_miss,mem_load_retired.l2_miss -- taskset -c $CPUS ./workload
```

Trace runs (`harness/lttng/trace_run.sh`):

```bash
lttng create run-$RUN --output=traces/$PR/$SIDE/$RUN
lttng enable-channel --kernel --subbuf-size=16M --num-subbuf=8 k
lttng enable-event --kernel --channel=k --syscall --all
lttng enable-event --kernel --channel=k \
  sched_switch,sched_wakeup,sched_waking,sched_process_fork,sched_process_exec,sched_process_exit,\
block_rq_issue,block_rq_complete
lttng enable-event --kernel --channel=k \
  --userspace-probe=elf:/lib/x86_64-linux-gnu/libc.so.6:malloc libc_malloc
lttng add-context --kernel --channel=k -t procname -t pid -t tid -t ppid
lttng start
taskset -c 4-11 ./workload
lttng stop
lttng destroy
```

**Full trace profile (2026-11-20, `harness/controls/run_controls.py`;
replaces the event list above).** Per traced run: all syscalls (entry +
exit, with arguments and return values) plus `sched_switch`,
`sched_wakeup`, `sched_waking`, `sched_wakeup_new`, `sched_migrate_task`,
`sched_stat_runtime`, `sched_process_{fork,exec,exit,free}`,
`block_rq_{issue,insert,complete}`, `block_bio_queue`,
`irq_handler_{entry,exit}`, `irq_softirq_{entry,exit}`,
`timer_hrtimer_expire_{entry,exit}`, `net_dev_xmit`,
`net_if_receive_skb`, `power_cpu_frequency`,
`x86_exceptions_page_fault_{user,kernel}`, `kmem_mm_page_{alloc,free}`;
contexts `pid`, `tid`, `ppid`, `procname`; channel 16 x 16 MB per CPU.
Left out on purpose: `kmem_kmalloc`/`kmem_kfree` (fire on nearly every
kernel operation). Derived per run (`counts.json`): syscall counts,
bytes read/written, futex wait time, off-CPU time (main thread / all),
forks/threads/execs, migrations, scheduler runtime, every other event
count for the process tree (`ev:*`), interference on the measurement
CPUs (`irq_on_cpus`, `softirq_on_cpus`, `hrtimer_on_cpus`,
`foreign_switch_in_on_cpus`, `freq_changes_on_cpus`), system-wide block
I/O, and **per-file attribution** (`files.json`: opens, read/write calls
and bytes per path, from `openat`/`close` and each call's fd). Each run
also writes `meta.json` (argv, CPUs, root pid, traced wall time, events,
contexts, buffer sizes, tool versions). Each PR writes `env.json`
(uname, kernel cmdline, lscpu, microcode, PMU, systemd CPU limits,
sysctls, governor, loaded LTTng probes, tool versions, `uv pip freeze`
of base and head). Integrity: a run with any discarded **event or
packet** is rejected; multiplexed perf rows are rejected; tracer overhead
= traced vs untraced wall time, reported per variant.

**Enabling the missing probes on Ubuntu's kernel (2026-11-20,
`harness/vm/enable_full_probes.sh`).** lttng-modules skips probes whose
kernel-internal headers are missing from Ubuntu's trimmed headers package
("Use full kernel source tree to enable it"). We downloaded the exact
running kernel's source (`apt-get source --only-source
linux-gcp-7.0=7.0.0-1017.19~24.04.1`) and copied in only what the probes
need: all `.h` files of `mm/` and `drivers/base/regmap/` (copied
`arch/x86/kvm/*.h` were removed again: they enabled KVM probes that need
more files, and we do not trace VMs). In Linux 7.0 the x86 page-fault
tracepoints moved to `include/trace/events/exceptions.h` with an
identical prototype `(unsigned long address, struct pt_regs *regs,
unsigned long error_code)`; a one-line forwarding header at the old path
`arch/x86/include/asm/trace/exceptions.h` lets lttng-modules' unchanged
x86-exceptions probe build. Result: 33 probes including `kmem`,
`x86-exceptions`, `compaction`, `regmap`; 286 kernel events (was 259).

**Cross-checks (smoke test, 2026-11-20, one run each):** LTTng page-fault
events vs perf minor+major faults: 821,093 vs 821,206 (alloc a), 18,225
vs 18,338 (alloc b), 1,843 vs 1,955 and 1,841 vs 1,958 (file_reads a/b):
a steady gap of ~110 faults (cause not yet checked; possibly faults
before the traced workload process starts). Per-file attribution, file_reads
a: `/tmp/kt_controls_data.txt` 2,000 opens, 4,000 read calls, 40,000,000
bytes, exactly the control's design. No lost events or packets. On the
measurement CPUs per run: 0 hardware interrupts, 2-33 softirqs, 3-7
foreign tasks switched in.

**Fleet (2026-11-20, user decisions: speed first; never more than one
job per VM; old pilot data deleted for uniformity).** Boot-disk image
`kt-measure-disk-v1` (machine images are not supported for hyperdisk) made
from kt-measure-1 after deleting all pilot builds, traces and results.
VMs: kt-measure-1, kt-measure-2 (us-central1-a), kt-measure-3
(us-east1-b; us-central1 hit the 500 GB hyperdisk quota), all
c4-standard-8 + PMU standard. `harness/vm/fleet_check.sh` on each: same
kernel 7.0.0-1017-gcp, CPU Xeon Platinum 8581C, cmdline
`nohz_full=2,3,6,7 rcu_nocbs=2,3,6,7`, slices AllowedCPUs 0-1,4-5,
sysctls, LTTng 33 probes / 286 events incl. page faults, bt2 2.1.2, perf
7.0.14; exact-instruction check 2,000,000,309 / 315 / 264 vs 2e9. Each VM
re-runs the 12 controls (full profile, 5 runs) as its own calibration.
Quota requests filed (pending): CPUS_ALL_REGIONS 24 -> 96, HDB per region
500 -> 2,000 GB (us-central1, us-east1). Plan: separate build VMs from the
same image (environments copied to a measurement VM; builds never run on
a measuring VM); p4 108k classification paused at 3,128 labelled (task
`kt-p4-full` disabled; re-enable to resume).

**Per-VM calibration (2026-11-20, 12 controls, full profile, 5 runs, on
each VM; results in `~/controls/results/controls.json` per VM):**
kt-measure-1 21/22, kt-measure-2 22/22, kt-measure-3 21/22 checks pass;
no multiplexing, no lost events or packets on any VM. The only failure
(VM 1 ratio 0.6, VM 3 ratio 0.8) is `context-switches` of the lock
control: not fully separated across runs; the control's primary signal
(`futex` calls) passes on all VMs. Treat context switches under
contention as an unstable signal. Counter check through the
`systemd-run`/`taskset` launcher: delta 1,999,931,620 / 1,999,936,459 /
1,999,930,429 vs 2e9 (relative error ~3.4e-5, all low by ~65k);
the direct check without the launcher (fleet_check.sh) gave +264 to
+315. Likely cause: launcher instructions are counted and vary
(not verified).

**Claim extraction, all 1,343 runtime-perf PRs (2026-11-20,
`analysis/p5_claims.py`, codebook `labels/codebook-claims-v1.md`, hash
in `labels/codebook-claims-v1.sha256`, Haiku 5.5; open-coding pilot:
v0 put 39% in `other`, v1 6% on the same 100 PRs).** Results
(`data/p5_claims/all_v1/`, summary `data/p5_claims_all_v1_summary.txt`):
1,343 labelled, 0 failures; no mechanism stated 189 (14%); a claimed
effect size stated in 422 (31%). Evidence: reasoning 500, test 347, none
269, benchmark 221, profile 6. Mechanisms (share of PRs, multi-label):
skip_unneeded_work 20.6%, less_memory 16.6%, cache_results 15.3%, other
12.1%, algorithmic 9.5%, parallelize 6.9%, async_io 5.5%, precompute
5.4%, faster_library 4.2%, concurrency_tuning 4.2%, fewer_external_calls
4.2%, lazy_loading 4.1%, reuse_resources 3.9%, faster_db_query 3.7%,
fewer_db_queries 3.6%, vectorize_locality 3.3%, gpu_accelerator 2.8%,
smaller_payload 2.7%, batch_calls 2.7%, avoid_repeated_io 2.6%,
ui_rendering 2.1%, polling_sleep 2.1%, less_locking 1.7%, less_output
1.5%, streaming_output 1.1%, io_granularity 0.9%, fewer_syscalls 0.2%,
fewer_processes 0.2%. Quotes: 101 of 2,087 not verbatim, 46 not found even
after whitespace normalisation (flag; check by hand before use).
`other` is 12.1% on the full set vs 6% in the pilot: review the 192
`other` descriptions for a v2 list. **Measurable by claim** (>= 1
mechanism with a kernel signal): 1,030 (Claude_Code 359, Copilot 205,
OpenAI_Codex 183, Google_Jules 107, Cursor 92, Devin 84); excluded: no
mechanism 189, only GPU/external-API/UI 56, only `other` 68. For the 385
target, Copilot and Codex are tight once build failures are counted:
raise their `targets.json` values after the build agent's success rate
is known.

**Correction of the keyword-scan estimate below:** LLM claim extraction
on 100 PRs (codebook v1) finds DB mechanisms in only 2% of PRs
(`faster_db_query` 1, `fewer_db_queries` 1), not ~34%: the keyword scan
counted every "query"/"index". Top claimed mechanisms in that sample:
cache_results 22%, less_memory 16%, skip_unneeded_work 14%, algorithmic
14%. DB-server tracing stays needed but is not a priority.

**Requirements from the labelled data (2026-11-20, heuristic keyword
scan of the 1,343 runtime-perf PRs, rough):** claimed mechanisms: DB/query
~34%, algorithmic ~15%, file I/O ~13%, memory/copies ~12%, caching ~12%,
network ~12%, concurrency ~11%, GPU/ML ~10%, startup ~6%, locks ~6%,
batching ~5%, no bucket ~20%. Environment needs: GPU ~27%, external
LLM/API ~29%, frontend ~19%, container/k8s ~12%, DB server ~8% (overlap).
62% touch tests, 14% mention a benchmark; changed files median 7, p90
148. Consequences (to build before the study): (a) claim extraction with
a mechanism type per PR (RQ1/RQ3; the ~20% without a bucket); (b) trace
and attribute service processes (DB servers) together with the workload
tree; (c) services on VMs (Postgres, MySQL, Redis, local HTTP mock);
(d) exclusion categories GPU / external API / frontend-only reported in
the funnel; (e) a coverage rule for very large PRs; (f) workload tiers
from the PR's own tests/benchmarks first.

**Collection decisions (user, 2026-11-20):** 3 VMs only for now; each PR
measured once on one VM (no 20% cross-VM re-measurement for now; repeat
runs may be added later); after every 50 PRs per VM the experimenter
checks the batch by hand as in the pilot. Each VM alternates a build
phase (several build agents in parallel; nothing measured) and a measure
phase (one PR at a time, alone). Per PR: 3 + 3 warm-ups, 10 x (base,
head, base again) untraced timing runs, 5 x 3 perf groups x 3 variants,
5 x 3 LTTng traces (full profile); each trace covers one complete
workload execution (workload 0.5-30 s at base). Expected ~10-15 min of
measuring per PR for a 2-3 s workload.

**Build agent (2026-11-20; `harness/agent/`).** Jobs: `analysis/p6_jobs.py`
(1,030 measurable-by-claim PRs, one random order, round-robin over 3 VMs;
19 GitHub errors) then `analysis/p6_refilter.py`: keep only PRs whose
FINAL diff (GitHub `pulls/<n>/files`) touches a `.py` file — AIDev's
per-commit file lists include commits merged in from the base branch
(first test, elodin #525: 207 AIDev files incl. 3 .py; final diff 16
files, 0 .py). Dropped 62 (no .py in final diff); **949 jobs** (312 /
315 / 322). Per job (`run_agent.py`): harness setup (merge base, both
sides always set up, Python project folder = nearest pyproject/setup.py
above the changed .py files, `pkgdir.txt`); git history moved to a
root-only folder; blind agent = Claude Code headless, `claude-opus-5-5`,
effort medium, tools Bash/Read/Write/Edit/Glob/Grep, 45 min limit,
instructions `BUILD_AGENT.md` (sees job.json, pr.diff, src, venvs; no
title/body/commits/claim); structured answer; harness re-runs `check.py`
independently (both sides run, coverage >= 0.8, or >= 0.5 for > 200
changed executable lines, base 0.5-30 s, passes with no network, output
digest); transcript audit (GitHub PR access, gh CLI, git history); changed
code lines per language recorded (`python_share_of_code_change`).
Test round (6 PRs, old rules): 5 built + passed, 1 unbuildable; 44-195 s
and $0.18-0.52 list-equivalent per PR; no audit flags. Manual review found
two problems -> rules added before batch 0: (1) no patching of the code
under test or its threads/pools/loops/timers/caches/locks (iPhotron #445
had made a thread pool synchronous); (2) reasons `new_code_only`
(PostHog #42018) and `needs_patching`. Open analysis rule: dynamo #6470's
only Python change is a benchmark script of a Rust component, so PRs
whose claim targets non-Python code must be flagged, not counted as
"mechanism absent". Batch 0 started 2026-11-20 21:55 on all 3 VMs.

**Storage (open):** one alloc-a trace is 139 MB (page-allocation
events). Full study ~385 PRs x 3 variants x 5 traced runs will exceed the
VM disk (193 GB). Plan: compress CTF traces and archive to a cloud bucket
per PR; decide before the study (cost, retention).

**Trace loss already happened once:** traces were first written to
`/tmp`, which is cleared when the VM stops; the first Phase-0 control
traces were lost that way (their counts survive in `controls.json`).
Traces now go to `/srv/kt/traces` (persistent disk); pilot v1 traces were
moved to `/srv/kt/traces/pilot_v1` before any stop; controls and the 9
measurable pilot PRs are being re-measured with the full profile into
`/srv/kt/traces/{controls,pilot_v2}` (`harness/pilot/remeasure_all.sh`).

Rules:

- **Lost events**: after each run, check the trace for discarded events
  (babeltrace2 reports them). Any loss rejects the run; raise
  `--subbuf-size` for that PR and redo it.
- **Process filter**: PID tracking does not follow children, so trace the
  whole (quiet, isolated) machine and keep only the workload's process
  tree offline, rebuilt from `sched_process_fork` / `sched_process_exec`.
- **Offline counting**: `analysis/count_events.py` reads each trace with
  the babeltrace2 Python bindings (`bt2`) and writes one row per run:
  syscall counts by name, bytes from `read`/`write` return values, futex
  wait time (entry/exit pairs), off-CPU time per state from
  `sched_switch`, page faults, block I/O, forks, malloc calls.
- **Python function level** (case studies only): CPython built with
  `--with-dtrace`, then `--userspace-probe=sdt:<python binary>:python:function__entry`.
- **Per-phase hardware counters** (case studies only):
  `lttng add-context --kernel -t perf:cpu:cycles -t perf:cpu:instructions`.
- Scripts are tested on the positive controls first. Pin the LTTng,
  babeltrace2 and perf versions.

### 7.5 Case studies (deep traces)

For 10 to 15 PRs that end in interesting quadrants, record:

- `perf record -g` at base and head and a **differential flame graph**
  (Brendan Gregg's `difffolded.pl`); Python 3.12+ with `-X perf` so
  Python frames show up.
- The LTTng traces opened in Trace Compass: resource and control-flow
  views for timeline figures, and **critical path analysis** to show what
  the workload was waiting on. This answers RQ4's "why not faster" (for
  example, a CPU-only change on a path blocked on I/O).

## 8. Analysis

### 8.1 Per-PR decisions

- **Speed (RQ2)**: ratio of medians head/base with a 95% bootstrap CI
  (10,000 resamples). Faster / no change / slower by comparison with the
  A/A noise band. Also Cliff's delta.
- **Mechanism (RQ3)**: for each claimed mechanism, the oracle's primary
  signal, same decision rule (counts: ratio with CI; near-deterministic
  counts: a fixed minimum relative change, set from the A/A data).
- **Hidden cost (RQ4)**: for each PR that got faster, every other signal
  that got significantly worse.
- **Claimed magnitude**: when the PR states a number ("3x faster"),
  compare to the measured ratio: within the CI, overstated, understated.

### 8.2 Population level

- Proportions with Wilson 95% intervals.
- Agent vs human, merged vs rejected, per agent: Fisher or chi-square on
  the quadrant table, with Benjamini-Hochberg correction across tests.
- RQ5 model: mixed-effects logistic regression,
  `merged ~ speed_verified + mechanism_verified + agent + language +
  log(lines changed) + evidence_in_pr + (1 | repository)`.
- **Same-population rule** (lesson from earlier work): every comparison is
  on the exact same PRs; human vs agent comparisons are matched by
  repository and time window where possible.
- Robustness: repeat the main results on T1+T2 workloads only, on Python
  only, and with a stricter noise band.

### 8.3 Paper-claim verification

Like `industry-c7/scripts/verify_paper.py`: every number in the paper is a
LaTeX macro generated by a script from the result files, and a checker
traces each one back. Each check pins one exact value.

## 9. Extension: trace-in-the-loop agent (RQ6)

On a held-out set of executed PRs (say 60):

1. Condition A: the agent sees the original PR and the code, and is asked
   to write a performance summary of the change.
2. Condition B: the same, plus the measured kernel-trace diff (a compact
   table: signal, base, head, CI).
3. Judge both summaries against the measured ground truth (claim
   accuracy: correct direction, correct mechanism, magnitude within CI).
   Use an LLM judge validated against two human raters on 50 cases.

Optional second step: give the agent the trace diff and let it revise the
code, then re-measure. Paired comparison, same PRs, same model, fixed
seed. This turns the study into an actionable tool and fits agent venues.

## 10. Threats to validity (plan for them now)

- **Construct**: kernel signals are evidence for a mechanism, not proof.
  Mitigate: the positive controls per oracle row; deep-trace case studies.
- **Workload validity**: a micro-workload may not reflect real use.
  Mitigate: coverage check, tiers, results per tier.
- **Measurement noise in the cloud**: A/A floor, isolation, bare metal,
  cross-machine replication.
- **Tracer overhead**: separate timing and tracing runs; overhead measured.
- **Selection bias**: funnel reporting and the executed vs not-executed
  comparison.
- **LLM labelling**: human agreement reported for every LLM-made label;
  quotes checked word for word.
- **Build agent bias**: the agent never sees the claim.
- **Dependency drift**: dependencies frozen at the PR date.
- **External**: AIDev-pop covers repositories with more than 100 stars and
  the six agents in v5, up to the v5 cutoff (31 March 2026). Agent PRs are
  found by the GitHub search queries listed on the dataset card, so agent
  PRs those queries miss are not in the data.

## 11. Phases and gates

Each phase ends with a gate. If a gate fails, stop and decide together
before going on.

**Phase 0: setup and pilot (laptop + one small GCP VM)**
- [x] Start a GCP Ubuntu VM with PMU access; install LTTng (7.4); confirm
  hardware counters work and `lttng-modules` loads. Done 2026-11-20
  (`kt-measure-1`, see 7.1 and 7.4).
- [x] Measurement cores set up (7.2); `isolcpus` tried and rejected
  (breaks multi-threaded workloads), replaced by systemd CPU limits.
- [x] Counter check (`harness/controls/counters.c`, a dec+jnz loop of
  exactly 2 instructions per iteration): instructions:u difference
  between n=2e9 and n=1e9 was 2,000,000,056 vs 2,000,000,000 expected
  (relative error 2.8e-8), loop IPC 2.0006. Hardware counters on the
  C4 `standard` PMU are exact for retired instructions.
- [x] Positive controls: 12 pairs, one per oracle row
  (`harness/controls/controls.json`, expectations written before any
  measurement; runner `run_controls.py`; results on the VM in
  `~/controls/results/controls.json`). First 1-run pass: 20 of 22 checks
  passed; the two failures were a zero-count bug (fixed) and the
  `isolcpus` problem above. **5-run pass (2026-11-20): 22 of 22 checks
  pass**, every "down" signal fully separated (all b runs below all a
  runs), no counter multiplexing, no lost trace events. b/a medians:
  file_reads openat 0.059, read 0.027, bytes_read 0.019; batch_net sendto
  0.0003; spawn forks 0.0, execve 0.083; logging write 0.0004; alloc
  minor-faults 0.022, mmap 0.755 (weakest pass); algorithmic instructions
  0.051, task-clock 0.177; locality L1 misses 0.0013, L2 misses 0.080;
  lock futex 0.0, context-switches 0.381; parallel wall 0.621 with
  task-clock 1.091 (not down, as expected); async_io wall 0.087,
  main-thread off-CPU 0.057; lazy_import openat 0.459, bytes_read 0.201;
  stat_loop stat calls 0.036.
- Run-to-run spread over the 5 runs (no warm-up runs in this pass):
  instruction and syscall counts mostly < 1% CV; exceptions are the lock
  contention control (instructions 8.8%, syscalls 21.3%: contention is
  not deterministic) and pool startup in parallel b (syscalls 15.7%).
  Wall time: median CV 3.29% over all 24 variant rows; most rows are
  30-50 ms workloads where interpreter startup dominates. Rows of 0.4 s
  or more: 0.17-1.88% CV except lock a (11.9%). Largest CV, lazy_import
  a (31.6%), is one cold first run (0.148 s vs 0.081-0.082 s for the
  other four) while its kernel counts were identical in all 5 runs (354
  `read`, 3,825,420 bytes). **Gate 0 wall-noise target (< 3%) is met for
  workloads >= 0.4 s without contention**; this supports the plan's rule
  that measured workloads run 0.5-30 s, with 3 warm-up runs.
- Write the positive-control program pairs (one per oracle row) and check
  each signal moves in the LTTng counts.
- Hand-pick 10 Python perf PRs, run the full manual pipeline.
  Pool (2026-11-20): the 78 pilot PRs labelled runtime perf in Python
  repositories; base/head SHAs fetched read-only through the logged-in
  `gh` CLI (`analysis/p1_fetch_shas.py` -> `data/p1_pr_meta.jsonl`; no
  separate GitHub token needed, 5,000 requests/hour). 78/78 fetched, 42
  merged, 0 with a deleted head repository, median 5 changed files and
  290.5 added lines; 16 merged with <= 5 files and <= 200 added lines.
  **Finding: repository language is not change language.** E.g.
  https://github.com/PostHog/posthog/pull/43438 "perf: Fix SQL editor
  typing lag by memoizing DatabaseTree" is in a repository whose
  `repository.language` is Python, but its only changed file is
  `frontend/src/layout/panel-layout/DatabaseTree/DatabaseTree.tsx`. The measurement set must
  be selected by changed-file extensions, not `repository.language`.
  **Unmeasurable by design** (report as a funnel category): changes that
  need special hardware or services (TPU kernels, GPU/ONNX models,
  Docker-in-Docker), and empty PRs (one WIP PR with 0 changed files).
  **Pilot builds (started 2026-11-20).** Selection rule and decisions:
  `analysis/p3_pilot_select.py`, `data/p3_pilot/decisions.jsonl` (21
  walked: 10 build, 11 skip with reasons: external API/service 6, GUI 2,
  JAX/TPU 2, per-repository cap 1). Harness: `harness/pilot/`
  (`setup_by_id.sh` reads SHAs only from `manifest.tsv`, built from the
  GitHub API; `cover.py` coverage of changed lines + output digest;
  `measure_pr.py` base / head / base-again A/A, 3 warm-ups, 10 timing runs,
  5 perf and 5 LTTng runs). Workloads are hand-written by the experimenter
  who has read each PR (pilot limitation; the study's build agent will not
  see the claim). Results: `data/p3_pilot/results/`.

  | PR | claim | output | coverage head/base | wall head/base | mechanism signal (head/base, A/A) |
  |---|---|---|---|---|---|
  | PyThaiNLP #1319 | fix exponential BFS | equal | 1.0 / 1.0 | 0.143 | instructions 0.125 (1.000), L1 misses 0.053; syscalls and sys time ~unchanged (CPU-only, as claimed) |
  | mlflow #19520 | fix download perf regression (line iteration -> 1 MB chunks) | equal | 1.0 / 1.0 | 0.826 | `read` syscalls 36,740 -> 4,096 = 0.111 (1.000) |
  | iPhotron #468 | partial hashing to cut scan I/O | differs (intended: ids of files > 2 MB change) | 0.931 / 1.0 | 0.658 | bytes read 836 MB -> 49.8 MB = 0.060 (1.000); sys time 0.278; `lseek` +48 and `newfstat` +48 (new per-file costs) |
  | iPhotron #501 | Pillow draft mode for JPEG micro-thumbnails | differs (thumbnail pixels change) | 1.0 / n.a. | 0.175 | minor faults 379,900 -> 9,832 = 0.026 (1.000); sys time 0.044; `brk` 0.260; instructions 0.243 |
  | maverick-mcp #79 | avoid full DataFrame copies | equal | 0.957 / 1.0 | 0.989 (runs overlap: no speed-up) | `madvise` 33 -> 2 (1.000), L2 misses 0.855: copies gone, but not the bottleneck |
  | static-frame #1140 | weak cache in `StoreXLSX.read_many()` | equal | 0.857 / 0.5 | 0.160 | instructions 0.130; bytes read 0.482, `read` 0.346, `lseek` 0.403 (1.000) |
  | openfisca-core #1367 | fix quadratic `as_of` reconstruction | equal | 0.0 / n.a. | 0.22 s both (2 untimed runs) | **changed code unreachable**: all 18 added lines sit after early returns that already handle `as_of` variables in base (`get_array` line 113-116, `_set` line 425-428); the snapshot fix the title describes (commit `4ecc4a72`) is already an ancestor of the PR's base (merged via #1366). Blocked by the coverage gate; not measured. |

  | smda #84 | cache provider capability lists | equal | 1.0 / 1.0 | 1.007 (overlap: no speed-up) | instructions 0.999 (fully separated but 0.1%): mechanism real, not a hot path |

  **Harness lessons from the pilot (apply to the study's harness):**
  1. **Use the merge base, not the API's `base.sha`.** The API value is the
     base branch tip, which can be later than the commit the PR branched
     from. pandas #64575: API base vs head = 69 files changed; merge base
     vs head = 1 file (the PR). Caught by the coverage check (128 / 103
     changed lines). `setup_pr.sh` now builds base at
     `git merge-base base head`, saves it to `base_commit.txt`, and writes
     `pr.diff` itself. Checked for all 10 pilot PRs: only pandas differed,
     so the other measurements stand.
  2. **Never type commit ids.** One hand-typed base SHA was partly
     invented by the experimenter and rejected by git; all SHAs now come
     from `manifest.tsv` (GitHub API).
  3. **Coverage gate for wide PRs.** prefect #21115 changes the same
     condition in 25 filter classes across many endpoints; a workload for
     the claimed path (deployment pagination) covers 3 of 25 changed lines
     (0.12). Decide before the study: keep "80% of all changed lines", or
     gate on the changed lines in the claimed code path (needs a rule that
     does not depend on judgement).
  4. **One untimed setup run.** prefect's first run on a fresh database
     failed once (exit 1); all later runs succeeded.
  5. **Optional and system dependencies** are the main build failures so
     far: `xlsxwriter` (static-frame), Qt's `libGL`/`libEGL` (iPhotron),
     C builds need a normal (non-editable) install (pandas).
  6. **Attribute syscalls to files/fds** (mlflow head's 4,096 `read`
     calls are not yet explained).

  Prediction check, static-frame: before measuring I predicted the file
  I/O would stay the same because the workbook is still loaded on every
  call. Wrong in part: bytes read fell to 0.482 (openpyxl reads sheets
  lazily, so cache hits skip sheet data), but ~11.6 MB per run remains
  (the workbook is still opened every call). maverick-mcp's first head run
  took 6.01 s vs 1.90 s base; warm repeated runs were 1.82-1.84 s for
  both (first-run effect, not a regression).

  Notes: PyThaiNLP's base time on the PR's own example grows about
  linearly with N (1.45 s, 2.42 s, 4.48 s at N = 1,000 / 2,000 / 4,000),
  not exponentially as the title says; head stays ~0.5 s. mlflow head still
  issues 4,096 `read` calls (source not yet attributed; add per-fd/path
  attribution to the trace counter). All runs: no counter multiplexing, no
  lost events.
  First build candidates (not random; a feasibility pilot): pandas SAS7BDAT
  pre-compute (algorithmic; asv suite exists), openpilot single HTTP
  request (network batching), wetterdienst KML caching (I/O), pythainlp
  BFS fix (algorithmic), trading-strategy lazy import (startup), tinygrad
  cache unbinds (caching).
- **Gate 0**: at least 6 of 10 pilot PRs measurable; A/A noise on wall time
  under 3% for the median PR; all positive controls behave.

**Phase 1: dataset and claims (text only, cheap)**
- Pin AIDev; find perf PRs (4.2); human validation; claim extraction
  (4.3); human agreement; freeze taxonomy and oracle (git tag).
- Result: RQ1 can already be answered at this point, on the full perf set.
- **Gate 1**: classifier precision at least 0.9; kappa at least 0.7 on
  mechanism type.

**Phase 2: harness and build agent**
- Container template, build agent with the hard checks, workload tiers,
  coverage check, logging.
- Run on 50 PRs.
- **Gate 2**: at least 40% of attempted PRs pass every check; human
  spot-check of 20 workloads finds no workload that misses the point of the
  change.

**Phase 3: measurement at scale**
- Build images on the build VMs; measure serially on the measurement VM.
- Cross-machine replication on 20%.
- **Gate 3**: replication agreement on the speed decision at least 90%.

**Phase 4: analysis and case studies**
- RQ2 to RQ5, robustness checks, differential flame graphs, LTTng figures.

**Phase 5: extension (RQ6)**

**Phase 6: paper and artifact**
- Write; generate every number from scripts; verifier; Zenodo release.

## 12. Cost estimate (rough, to be checked against current GCP prices)

- Measurement: per PR about 3 sides (A/A, base, head) x 45 runs x ~10 s
  plus overhead, about 30 to 40 minutes. 450 executed PRs (300 agent + 150
  human) ≈ 250 to 300 machine hours, run serially on one quiet machine.
  On a small PMU-enabled C3 VM this is low hundreds of dollars; on a
  192-core bare-metal machine it is much more per hour, so use bare metal
  only if VM counters turn out to be unreliable. I'm not sure of current
  per-hour prices; check before starting.
- Build agent: about 1,000 attempts x a few dollars of API tokens each.
  Order of 1,000 to 3,000 USD. Log the real cost per attempt from the
  first 50 and re-estimate at Gate 2.
- Claim extraction and classification: a few thousand PRs with a
  mid-size Claude model, tens of dollars.
- Build VMs: spot instances, low hundreds of dollars.

## 13. Paper outline (target: full research paper, 10 to 12 pages)

1. Introduction: stopwatch vs mechanism; four-quadrant teaser figure.
2. Background: agent perf PRs and prior studies; kernel tracing basics.
3. The claim-to-signal oracle (taxonomy + table + positive controls).
4. Study design: data, funnel, harness, measurement, analysis.
5. Results: RQ1 to RQ5 (and RQ6).
6. Case studies: differential flame graphs and timelines.
7. Discussion: what reviewers and agent builders should do; guidance for
   PR templates ("state the mechanism, attach the trace").
8. Threats.
9. Related work.
10. Conclusion and artifact.

Main figures: executability funnel; claim taxonomy bar chart (agent vs
human); four-quadrant chart per agent; hidden-cost heatmap (signal x claim
type); claimed vs measured magnitude scatter; two flame-graph diffs.

## 14. Venue

The AGENT 2027 deadline (20 November 2026) is too early for this plan.
Candidates, deadlines to be checked: MSR 2027 technical track, FSE 2027,
ASE 2027, ICSE 2028, or a journal (EMSE, TOSEM). A short version of
Phase 1 + pilot (RQ1 + Phase 0 results) could go to a workshop or the MSR
mining challenge track if one fits the timing.

## 15. Folder layout (to create when Phase 0 starts)

```
AGENTS-WORKSHOP/
  RESEARCH-PLAN.md        this file
  paper-ideas.md          background and prior work
  data/                   pinned AIDev extracts, labels (gitignored if large)
  labels/                 codebook, human annotation sheets, agreement
  harness/
    docker/               container template
    lttng/                trace session scripts
    controls/             positive-control program pairs
    build_agent/          agent prompt, checks, runner
    measure.py            timing / counter / trace runs
  analysis/               RQ scripts, figures, paper macros, verifier
  paper/                  LaTeX
```
