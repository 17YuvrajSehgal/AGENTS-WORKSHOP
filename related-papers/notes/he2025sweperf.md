# SWE-Perf: Can Language Models Optimize Code Performance on Real-World Repositories?
- **Authors:** Xinyi He (Xi'an Jiaotong University), Qian Liu (TikTok, corresponding author), Mingzhe Du (National University of Singapore), Lin Yan (TikTok), Zhijie Fan (TikTok), Yiming Huang (University of California San Diego), Yin Zheng (TikTok), Zejian Yuan (Xi'an Jiaotong University), Zejun Ma (TikTok)
- **Venue / year / status:** The PDF is arXiv:2507.12415v2 [cs.SE], dated 1 Jul 2026. Its footer says "Proceedings of the 43rd International Conference on Machine Learning, Seoul, South Korea. PMLR 306, 2026", so this version is the ICML 2026 paper (peer-reviewed). 17 pages: main text pp. 1-9, impact statement p. 10, references pp. 11-13 (the reference list is printed twice), appendix A to C pp. 14-17.
- **PDF:** `related-papers/he2025sweperf_2507.12415.pdf`
- **Cite key:** he2025sweperf
- **BibTeX-style reference:** Xinyi He, Qian Liu, Mingzhe Du, Lin Yan, Zhijie Fan, Yiming Huang, Yin Zheng, Zejian Yuan, and Zejun Ma. 2026. SWE-Perf: Can Language Models Optimize Code Performance on Real-World Repositories? In Proceedings of the 43rd International Conference on Machine Learning (ICML), PMLR 306. arXiv:2507.12415. (Note: `paper/refs.bib` lists it as an arXiv 2025 preprint. The PDF we hold states the ICML 2026 venue.)

## In short
SWE-Perf is a benchmark of 140 tasks from 9 Python repositories. Each task comes from a real human pull request whose change made some of the repository's own unit tests run faster. The model gets the codebase and a list of target functions and must write a patch that makes those tests faster while they still pass. Speed is measured as the run time of the unit tests under pytest: 20 repetitions after a warm-up, outliers removed, then a Mann-Whitney U test that gives the largest speed gain that is still statistically significant. The human expert patches score 10.85% on this metric. The best system, OpenHands with Claude 3.7 Sonnet, scores 2.26%. Only wall-clock test time is used. There are no hardware counters and no kernel traces.

## Problem and motivation
- Repository-level benchmarks such as SWE-bench check correctness (does the bug get fixed), not speed.
- Speed benchmarks such as Mercury, EffiBench, EvalPerf, PIE and KernelBench work on single functions or algorithm puzzles. Real speed-ups often need changes across files and modules.
- For speed there is no "right answer" to compare with, so it is unclear how much better the code could be. The authors use the human PR as the reference.
- Research question (p. 1): "Can language models effectively optimize code performance in real-world repositories?"

## Background / key terms (explain each term simply)
- **Pull request (PR):** a proposed code change in a GitHub repository. "Original codebase" is the code before the PR, "modified codebase" is the code after.
- **Expert patch:** the human-written change from the PR. It is the reference for "what a human achieved".
- **Performance-related tests:** unit tests of the repository that pass before and after the PR and that run clearly faster after it. They are the workload in this benchmark.
- **Target functions:** the functions the model is told to make faster. Given so the evaluation can be limited to a small set of tests.
- **Oracle setting (file-level):** the model gets the functions the human actually changed, plus the full files that contain them. One model call writes the patch. Tests whether the model can write a faster version when told where.
- **Realistic setting (repo-level):** the system gets the functions that the performance-related tests call directly, and may change anything in the repository. It must find the slow spot itself.
- **Warm-up:** runs done before measuring, so that one-time start costs (imports, caches) do not count.
- **IQR outlier filter:** IQR is the distance between the first quartile Q1 and the third quartile Q3 of the samples. Points far outside are dropped.
- **Mann-Whitney U test:** a statistical test that asks whether values in one group tend to be larger than in another. It uses ranks, so it does not assume a bell-shaped distribution.
- **Coefficient of variation (CV):** standard deviation divided by the mean. A measure of noise relative to the size of the value.
- **Minimum performance gain (δ):** the paper's own number. The largest percentage x such that, even after shrinking the original run times by x, the patched code is still significantly faster.
- **yappi:** a Python profiler. Used here to list which functions run during a test.
- **Agentless / OpenHands:** two existing systems for repository tasks. Agentless is a fixed pipeline (find location, repair, pick a patch). OpenHands is an agent that takes many steps with tools.

## Method and setup

### How the dataset was built (Sec. 3.2, Fig. 2, Table 3)
Five phases. Counts are from Sec. 3.3 (p. 6) and Table 3 (p. 14):
1. **Collect PRs.** The same 12 repositories as SWE-bench, crawled again. 102,241 PRs. Attribute filter: keep PRs that resolve an issue. Unlike SWE-bench, PRs need not add tests. 19,797 remain.
2. **Measure codebases.** Build a Docker image per codebase (following SWE-Gym), run **all** unit tests with pytest, record each test's run time. 34,397 distinct codebases, tests ran on 19,499. Each codebase is run **three times**, in a container limited to **one CPU core and 16 GB memory**.
3. **Identify performance PRs.** 4,413 PRs have run-time data for both versions. Step 1: keep unit tests that pass in both versions and whose ratio (R_original − R_modified) / R_original, taken as the mean of the three runs, is above **0.3** (30% less time). 3,720 PRs remain (Table 3, "after step1"). Step 2: keep tests that execute the code changed by the PR and that are not themselves changed by the PR. 1,696 remain.
4. **Verify stable improvement.** Warm-up, 20 repetitions, outlier filter, statistical test (details below). Keep unit tests with δ above **0.05**. 140 instances remain.
5. **Extract targets.** Oracle functions from the human patch (AST analysis plus diff matching). Realistic functions from `yappi` profiling of the tests plus AST parsing. The test itself is not given as the target, to stop the model from cutting code down to only what the test uses ("functional pruning").

### How performance is measured (the part we compare against)
- **Workload:** the repository's own unit tests that were found to be faster after the human PR ("performance-related tests"). On average 8.1 tests per instance, at most 68 (Table 1). No separate benchmark script is written.
- **Metric:** run time of each unit test as reported by pytest (p. 3: "We use pytest to collect the execution time (runtime) of each unit test"). Wall-clock only. No hardware counters, no system calls, no memory, no kernel tracing. The paper does not say which pytest option or plugin gives the time, or whether set-up and tear-down time are included.
- **Size of the workload:** mean original run time 0.28 s, max 25.2 s (Table 1). So a typical workload is a short unit test.
- **Runs (Phase 4 and evaluation):**
  1. *Warm-up:* "before each performance measurement, we execute three performance-related unit tests to warm up the environment" (p. 4). It is not clear whether this means three tests or three runs of the tests.
  2. *Repetitions:* "Each unit test is run 20 times".
  3. *Outliers:* IQR filter with multiplier k = 1 (stricter than the usual 1.5). The printed upper rule is "r_i > Q3 − k × IQR" (Eq. 1, p. 4, checked on the page). The minus sign is almost surely a typo for plus; as printed it would remove normal values.
  4. *Statistics:* Algorithm 1 (p. 5), described below.
- **Machine and isolation:**
  - Docker container per codebase.
  - Phase 2: 1 CPU core and 16 GB memory per container. Phase 4 and evaluation: **5 CPU cores** (p. 3: "we constrain each container to a single CPU core and 16 GB memory (5 CPU cores in Phase 4 and evaluation)").
  - Hardware (Appendix B, p. 14): "two Linux machines. Each machine is equipped with 256 logical CPU cores (128 physical cores across 2 sockets, with 2 threads per core) and 2.0 TiB of RAM."
  - The paper does not say: the CPU model, whether containers are pinned to fixed cores or only limited in CPU share, whether several containers run at the same time, whether hyper-threading siblings are kept apart, NUMA binding, frequency scaling or turbo settings, or the order in which original and patched runs are done.
- **What counts as a speed-up (Algorithm 1):**
  - Inputs: A = filtered run times of the modified code, B = filtered run times of the original code.
  - For x = 0.00, 0.01, 0.02, ... up to 1.0: shrink the original times, B_adj = B × (1 − x). Run a one-sided Mann-Whitney U test "B_adj greater than A". If p < 0.1, set δ = x and try the next x. Otherwise stop.
  - δ is the last x that was still significant. In simple words: "we are confident (at the 0.1 level) that the patch saves at least δ of the run time".
  - δ cannot be negative. A patch that makes the test slower gets δ = 0, the same as a patch that changes nothing.
  - Dataset rule: a unit test enters the benchmark only if the human patch gives δ > 0.05.
- **Baseline re-measured at evaluation time (p. 6):** the original codebase is timed again in the same evaluation session, "even when the original codebase runtime from data collection was available", so both sides are measured under the same conditions.
- **Why these thresholds (Appendix B.1, p. 14):** the average CV of their run-time measurements is 10.976%. A 30% screen is "roughly 2.7 times the observed noise level". 20 repetitions are said to give enough samples for the Mann-Whitney test at feasible cost. α = 0.1 is called "suitable for limited-sample non-parametric testing". δ > 0.05 is a minimum practical gain.

### The three scores (Sec. 4)
- **Apply:** share of instances where the patch applies without error.
- **Correctness:** share of instances where **all** performance-related tests pass after the patch. Only these tests are run, not the full test suite.
- **Performance:** for each instance, the mean of δ over its tests; then the mean over all instances (Eq. 2). The denominator is all N_total instances. Sec. 5.3.1 gets a "correct examples only" number by changing the denominator to the number of correct instances, which implies that instances that fail to apply or fail tests count as 0.

### Systems tested (Sec. 5.1, Appendix C)
- **Oracle:** one chain-of-thought call, SEARCH/REPLACE output. 10 models: Claude 3.7 Sonnet, Claude 4 Sonnet, Claude 4 Opus, GPT-4o, o1, o3, DeepSeek-V3, DeepSeek-R1, Gemini 2.5 Pro, Qwen3-235B-A22B. OpenAI models: temperature 0.2, top-p 0.1, max 8192 tokens. Claude: thinking on, 2000-token thinking budget, max 8192 output tokens.
- **Realistic:** Agentless (sample number 1) and OpenHands (maximum 2000 iterations), both with Claude 3.7 Sonnet.

## Section-by-section notes

### 1. Introduction
- States the gap and the benchmark. Says 100K PRs were filtered down to 140 instances from 9 repositories.
- Each instance has: codebase, target functions, performance-related tests, expert patch, Docker image, and run-time numbers.
- Contributions: the dataset, the collection pipeline, the metrics and baseline evaluation.

### 2. Related work
- Code-efficiency datasets are function-level. Repository-level SWE datasets have well-defined goals such as bug fixing.
- GSO is named as concurrent work: it finds performance commits with an LLM judge and code-change heuristics; SWE-Perf uses PRs and measured run times.

### 3. Dataset
- 3.1: why target functions are given. Running a full test suite is too slow (xarray: over 220,000 test cases on average, more than one hour on one core). Without a target there are too many places to optimize. The authors invite future work to drop the target functions.
- 3.2: the five phases above.
- 3.3: counts per phase.

### 4. Evaluation methodology
- The three scores above. Same measurement procedure as Phase 4.

### 5. Experiments
- 5.2 Main results (Table 2, Fig. 4).
- 5.3.1 Performance on correct patches only (Fig. 5, Fig. 6).
- 5.3.2 Run time: the expert's gain grows as the original test run time grows; the models' gain stays flat (Fig. 9).
- 5.3.3 Number of target functions: the expert's gain falls as the number of functions grows. OpenHands is close to the expert for few functions and the gap widens for many (Fig. 8).
- 5.3.4 Word clouds of added lines (Figs. 10 to 13). The authors read them as: OpenHands patches work on low-level data structures and environment-like terms; expert patches work on higher-level, domain-specific parts.

### 6. Conclusion and Appendix
- **A. Limitations (the authors' own):** few repositories; human patches "may not represent the optimal achievable performance".
- **B. Dataset:** hardware, threshold reasons, Table 3 (counts per repository and phase), Table 4 (pytest time per codebase), Table 5 (repository names), B.3 optimization categories.
- **C. Baselines:** model versions and settings, the Oracle prompt (Fig. 14).

## Key results (with numbers) and what they mean
- **Main table (Table 2, p. 6; checked on the page).** Format: Apply / Correctness / Performance.
  - Expert: 100.00% / 100.00% / 10.85%.
  - Oracle setting: Claude 3.7 Sonnet 66.43 / 61.43 / 1.24. Claude 4 Sonnet 73.57 / 70.00 / 1.76. Claude 4 Opus 85.71 / 78.57 / 1.28. GPT-4o 63.57 / 56.43 / 0.60. o1 66.42 / 63.57 / 0.41. o3 78.57 / 76.43 / 1.37. DeepSeek-V3 47.85 / 42.86 / 0.54. DeepSeek-R1 55.71 / 51.43 / 0.90. Gemini 2.5 Pro 95.00 / 83.57 / 1.48. Qwen3-235B-A22B 54.29 / 48.57 / 0.68.
  - Realistic setting: Claude 3.7 Sonnet with Agentless 88.57 / 70.71 / 0.41. With OpenHands 87.86 / 77.86 / 2.26.
  - What it means: "Performance 10.85%" for the expert says that, averaged over the 140 tasks, the human patch gives a statistically safe run-time saving of about 11% on the selected tests. The best system reaches 2.26%. The gap is 8.59 points (10.85 − 2.26), which the paper states on p. 8.
  - Many model patches do not even apply or break the selected tests (Correctness 43% to 84% in the Oracle setting). These count as zero gain, so the Performance column mixes "wrong patch" and "no speed-up".
- **On correct patches only (Fig. 5 and Fig. 6, p. 7).** Model vs expert on the same instances: Oracle (Claude 3.7) 2.0 vs 8.3. Agentless 0.6 vs 8.8. OpenHands 2.9 vs 11.4. In Fig. 5 the model value is between 0.7 (o1) and 2.5 (Claude 4 Sonnet), and the expert value on the same instances is between 6.5 and 12.2.
  - What it means: even when the patch is correct, the gain is a fraction of the human gain. Low scores are not only caused by broken patches.
- **Per repository (Fig. 4, p. 6).** Values as Oracle / Agentless / OpenHands / Expert: xarray 0.4 / 0.2 / 0.7 / 7.4. sklearn 0.5 / 0.4 / 3.6 / 3.2. sympy 0.5 / 0.2 / 2.7 / 31.8. astropy 5.5 / 0.8 / 1.2 / 5.1. others 2.6 / 0.7 / 4.4 / 14.5.
  - What it means: the expert number differs a lot between repositories (3.2 to 31.8). On sklearn OpenHands is 0.4 points above the expert, and on astropy the Oracle setting is above the expert. The authors call the sklearn case an "early-stage breakthrough". With a noise level near 11% CV and differences under half a point, this reading is too strong.
- **Dataset statistics (Table 1, p. 5).** 140 instances, 9 repositories. Codebase: 447.3 non-test files on average (max 1,972), 170k lines (max 502k). Expert patch: 131.1 lines edited (max 1,967), 4.3 files (max 71), 7.6 functions (max 94). Tests: 8.1 related tests (max 68), original run time 0.28 s (max 25.2 s). Target functions: 7.6 oracle (max 94), 30.1 realistic (max 256). Performance ratio: mean 10.9%, max 87.8%.
- **Noise level (Appendix B.1).** Average CV of run-time measurements: 10.976%.
  - What it means: unit-test timing in their containers is noisy. A single before/after pair cannot show a 10% change. This is why they need 20 repetitions and a test.
- **Yield.** 102,241 PRs give 140 tasks. 1,696 instances passed the three-run 30% screen and the coverage check, and only 140 passed the 20-run check.
  - What it means (my reading, the paper does not discuss it): more than 90% of the "30% faster" candidates did not hold up under repeated measurement. A screen based on three runs and the best-looking test out of thousands picks up a lot of noise.
- **Optimization categories (Appendix B.3, p. 16).** Cache & Compatibility 32.9%, Algorithmic Logic 26.4%, Redundancy Elimination 25.7%, Data & Resource Optimization 15.0%. The paper does not say how the labels were made.

## Tables and figures
- **Fig. 1 (p. 2):** the task: codebase plus target functions in, patch out; test run times before, after the model patch, and after the expert patch.
- **Fig. 2 (p. 4):** the five-phase pipeline.
- **Fig. 3 (p. 5):** instances per repository: xarray 54, scikit-learn 32, sympy 20, astropy 12, sphinx 8, seaborn 6, pylint 3, matplotlib 3, requests 2 (sum 140).
- **Table 1 (p. 5):** dataset statistics (above).
- **Algorithm 1 (p. 5):** the δ computation.
- **Table 2 (p. 6):** main results.
- **Fig. 4 (p. 6):** Performance per repository group.
- **Fig. 5, Fig. 6 (p. 7):** Performance on correct patches only, model vs expert.
- **Fig. 7, 8, 9 (p. 8):** Performance against number of oracle functions, number of realistic functions, and original run time. Line plots without value labels. Read: the expert line rises with run time (up to about 0.25 near 0.32 s); model lines stay near zero to 0.05. Do not quote exact values.
- **Figs. 10 to 13 (pp. 9, 16):** word clouds.
- **Table 3 (p. 14):** counts per repository and phase. Sum row: 102,241 PRs; 19,797 tasks; 19,162 tasks with versions; 34,397 unique codebases; 19,499 with pytest report; 4,413 with run times; 3,720 after step 1; 1,696 after step 2; 140 final. django and flask drop out. In the printed table the `requests` row has an empty Phase 4 cell and the `pytest` row shows 0 after step 2 but 2 in Phase 4, while Fig. 3 says requests has 2 instances and pytest is not among the 9 repositories. The two cells look swapped.
- **Table 4 (p. 15):** pytest time per codebase in minutes. Longest: sklearn (avg 83.89, max 119.96) and xarray (avg 58.11, max 119.95).
- **Fig. 14 (p. 17):** the Oracle prompt. It tells the model: "Acceleration of at least one objective function is sufficient for success".

## Ideas we can use
- **Re-measure the base in the same session.** They time the original code again at evaluation time and do not reuse old numbers. Same principle as our interleaved before/after runs.
- **A "safe minimum gain" number.** Algorithm 1 turns two sets of run times into one conservative effect size. It is a simple alternative or cross-check to a bootstrap confidence interval on the ratio of medians.
- **Report the noise level.** They state the CV (10.976%) and derive thresholds from it. We can state our own noise from the base-against-base runs and show how much lower dedicated cores make it.
- **Two-stage screening.** A cheap three-run screen, then a careful 20-run check. Useful if we need to triage many PRs before the expensive traced runs.
- **Tests that execute the patch.** Selecting unit tests that run the changed lines is a quick way to check that a workload really reaches the changed code.

## Weaknesses and things glossed over
- **Unit tests as the workload.** Unit tests are written to check behaviour, with tiny inputs. Mean original run time is 0.28 s. A faster unit test does not have to mean a faster real use case. SWE-fficiency (ma2025swefficiency) criticises this design directly.
- **Selection on the outcome.** Tests are chosen because they got faster with the human patch. The benchmark never checks whether other tests got slower. So "hidden costs" of a patch are invisible, for the expert and for the model.
- **Correctness is checked only on the selected tests.** The Correctness score runs the performance-related tests, not the wider test suite. A patch that breaks other behaviour can pass.
- **No slowdown detection.** δ has a floor of 0. A patch that makes things slower scores the same as no change.
- **Isolation is thin.** A Docker CPU limit on a 256-thread, two-socket machine. No statement on core pinning, NUMA, hyper-threading, frequency scaling, or parallel containers. The reported CV of about 11% fits a setup with noticeable interference.
- **Core count changes between phases.** Screening uses 1 core, verification and evaluation use 5. The paper gives no reason.
- **Loose significance level and many tests.** α = 0.1, one-sided, repeated in a step search, on about 8 tests per instance, with no correction for multiple testing. The δ > 0.05 floor limits the damage for dataset building, but for model scores small false gains can add up.
- **No same-version control.** There is no run of original against original to show what δ comes out from noise alone.
- **Outlier removal with k = 1.** This drops more points than the common k = 1.5 and makes the samples look tighter than the raw data. The printed formula also has a sign error.
- **Run order is not described.** If all 20 original runs come before all 20 patched runs, slow drift (thermal, cache state, other load) can look like a patch effect.
- **The 30% screen is noisy.** With thousands of tests per codebase and three runs, some test will show 30% by chance. 3,720 of 4,413 PRs (84%) passed step 1, which is hard to believe as real speed-ups (my reading).
- **Expert baseline is biased upward and still small.** Instances are selected because the expert patch shows a gain, so the expert score of 10.85% is not a fair sample of what human PRs achieve. The authors admit human patches may not be optimal.
- **Only one model in the realistic setting.** Agentless and OpenHands are run with Claude 3.7 Sonnet only, one run each. No repeated agent runs.
- **Not all "performance" PRs were meant as optimizations.** PRs are found by measured test speed-up, not by intent. Some may be bug fixes or refactors that happened to speed up a test. The paper does not report how many of the 140 PRs state a performance goal.
- **Small and skewed.** 140 instances; xarray and scikit-learn give 86 of them (61%).
- **Inconsistent counts.** Phase 2 text says "a total of 25,264 codebases"; Sec. 3.3 and Table 3 say 34,397 distinct codebases. Fig. 5 has a bar labelled "Claude-3.7-opus", a model that is not in Table 2 (probably Claude 3.7 Sonnet).
- **Word-cloud analysis is weak evidence.** Terms like "miniconda3" and "envs" in model patches look like file paths in the patch text, not optimization strategy.

## Open questions and future work (theirs, and ours)
- Theirs: more repositories; drop the target functions and optimize the whole codebase; better handling of tasks with many target functions and long run times.
- Ours:
  - What does Algorithm 1 give for two identical builds on their setup and on ours? This would turn their method into a comparable noise floor.
  - For the 140 expert patches, does the mechanism (cache, vectorize, remove duplicate calls) show in counters and kernel events? Their four categories (Appendix B.3) could be mapped to our signals.
  - How many of their speed-ups survive on a realistic workload instead of the unit test?

## Link to our paper
- **Related work:** one of the two closest repository-level optimization benchmarks. It scores model patches on human-PR tasks by unit-test run time. We check performance PRs that agents opened themselves, and we check the stated reason.
- **Method:** cite for the measurement recipe we compare to (unit tests as workload, 20 repetitions, warm-up, IQR filter, Mann-Whitney U, δ) and for the reported noise of about 11% CV with container CPU limits.
- **Threats:** cite for the fact that even human-written "performance" PRs give modest, noisy gains on unit tests (expert score 10.85%).

## Link to the thesis (tracing, kernel analysis)
- A clear case where only wall-clock time is used and the noise is high (CV 10.976%). Hardware counters such as instructions retired are usually much more stable than time, and would let a benchmark like this detect small gains with fewer runs.
- The paper gives no view of *why* a test got faster. `perf stat` on the test before and after, or syscall counts from LTTng or bpftrace, would separate "less work" (fewer instructions, fewer syscalls) from "same work, luckier run".
- Isolation is at container-limit level. For kernel-level analysis, the missing details (pinning, NUMA, SMT, frequency) are exactly the ones that decide whether scheduler and cache effects can be trusted.
- The use of `yappi` to map tests to executed functions is the same idea as using a trace to confirm that a workload reaches the changed code path.

## Quotes for inline citation
- "SWE-Perf comprises 140 carefully curated instances, each derived from performance-improving pull requests from popular GitHub repositories." (abstract, p. 1)
- "we reveal a substantial capability gap between existing LLMs and expert-level optimization performance" (abstract, p. 1)
- "we constrain each container to a single CPU core and 16 GB memory (5 CPU cores in Phase 4 and evaluation)." (Sec. 3.2, p. 3)
- "We use pytest to collect the execution time (runtime) of each unit test within the codebase." (Sec. 3.2, p. 3)
- "Each unit test is run 20 times to ensure runtime stability." (Sec. 3.2, p. 4)
- "Unit tests with δ exceeding the threshold (0.05) constitute the final SWE-Perf dataset." (Sec. 3.2, p. 5)
- "we re-evaluated the original codebase runtime during the testing phase, even when the original codebase runtime from data collection was available." (Sec. 4, p. 6)
- "a significant performance gap of 8.59% persists between OpenHands and Expert" (Sec. 5.2, p. 8)
- "the average coefficient of variation (CV) observed in our runtime measurements is 10.976%." (Appendix B.1, p. 14)
- "these may not represent the optimal achievable performance, potentially underestimating the true upper bound of improvement." (Appendix A, p. 14)

## Suggested citation sentences
- SWE-Perf builds 140 optimization tasks from human pull requests in nine Python repositories and uses the repositories' own unit tests as the workload \cite{he2025sweperf}.
- It times each test 20 times after a warm-up, removes outliers, and reports the largest gain that stays significant under a Mann-Whitney U test \cite{he2025sweperf}.
- Its authors report an average coefficient of variation of about 11\% in test run times \cite{he2025sweperf}, which shows how noisy wall-clock timing in containers can be.
- On this benchmark the expert patches reach 10.85\% and the best tested system 2.26\% \cite{he2025sweperf}.
- Like other repository-level benchmarks, it records run time only \cite{he2025sweperf}; it has no hardware counters or kernel events to explain a gain.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - *What we build on.* The before/after comparison of two versions of a real repository in containers, with repeated runs, a rank-based statistical test, and a conservative effect size instead of a single ratio. Also the practice of timing the base version again in the same session as the patched version.
  - *What it does not do that we do.* It measures only pytest run time of unit tests. It has no hardware counters and no kernel traces, so it cannot check a mechanism. It does not look at claims: the tasks come from human PRs chosen by measured test speed-up, and nothing in the pipeline reads what the PR says. It has no base-against-base control. It does not describe dedicated cores. It cannot see slowdowns (δ stops at 0) or costs outside the selected tests. Its correctness check covers only the selected tests.
  - *Where it weakens or challenges our approach.* (1) It uses 20 repetitions and a formal test with a stated α for every comparison. If we use fewer repetitions per PR, a reviewer can point to this paper, so we should state our repetition count and our test clearly. (2) Its workload is fixed and comes from the repository's own tests, so it is reproducible and not chosen by an agent. Ours is written by a build agent, which adds a source of variation they do not have. (3) Its noise figure (CV about 11%) and its drop from 1,696 screened instances to 140 verified ones show how easily a timing-based "faster" verdict is wrong. This supports our use of controls, but it also means our own timing verdicts need the same care.
  - *A point in our favour.* The expert score is only 10.85% and the reported noise is about 11%. Gains of this size are at the edge of what a stopwatch can show, which is the argument for adding signals that are more stable than time.

- **Safe to cite for:**
  - SWE-Perf uses the repository's unit tests as the performance workload and times them with pytest. Support: Sec. 3.2, p. 3: "We use pytest to collect the execution time (runtime) of each unit test within the codebase."
  - Its repetition and filtering procedure: warm-up, 20 runs, IQR filter with k = 1, Mann-Whitney U test at p < 0.1, minimum gain above 0.05. Support: Sec. 3.2, pp. 4-5: "Each unit test is run 20 times to ensure runtime stability." and "Unit tests with δ exceeding the threshold (0.05) constitute the final SWE-Perf dataset."; Algorithm 1 (α default 0.1).
  - Its isolation is a container resource limit. Support: Sec. 3.2, p. 3: "we constrain each container to a single CPU core and 16 GB memory (5 CPU cores in Phase 4 and evaluation)"; hardware in Appendix B, p. 14.
  - Run-time measurements of unit tests in this setup are noisy. Support: Appendix B.1, p. 14: "the average coefficient of variation (CV) observed in our runtime measurements is 10.976%."
  - The base version is re-timed at evaluation. Support: Sec. 4, p. 6: "we re-evaluated the original codebase runtime during the testing phase".
  - Models are far below the human reference on this benchmark. Support: Table 2, p. 6 (Expert 10.85%, OpenHands 2.26%) and Sec. 5.2, p. 8: "a significant performance gap of 8.59% persists between OpenHands and Expert".

- **Do not cite for:**
  - Anything about pull requests opened by agents in real projects. The 140 tasks come from human PRs; models are only evaluated on them.
  - Any claim about PR descriptions, stated reasons, or whether a claimed mechanism is true. The paper does not read or test claims.
  - "Human performance PRs speed code up by about 11%." The 10.85% is a conservative, test-based score on unit tests that were selected because they got faster. It is not an average speed-up of human PRs.
  - Hardware counters, system calls, page faults, or kernel tracing. None are used.
  - CPU pinning, NUMA binding, or dedicated cores. The paper only states a per-container CPU and memory limit.
  - A base-against-base (A/A) control or a measured false-positive rate. They do not report one.
  - Agents making code slower. The metric cannot show slowdowns.
  - Agent systems in general. The realistic setting uses one model (Claude 3.7 Sonnet) with Agentless and OpenHands.
  - Languages other than Python.
