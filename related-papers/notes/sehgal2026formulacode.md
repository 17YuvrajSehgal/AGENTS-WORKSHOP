# FormulaCode: Evaluating Agentic Optimization on Large Codebases
- **Authors:** Atharva Sehgal* (UT Austin), James Hou* (Caltech), Akanksha Sarkar (Cornell), Ishaan Mantripragada (Caltech), Swarat Chaudhuri (UT Austin), Jennifer J. Sun (Cornell), Yisong Yue (Caltech). * equal contribution.
- **Venue / year / status:** Proceedings of the 43rd International Conference on Machine Learning (ICML), Seoul, South Korea, PMLR 306, 2026 (as printed on page 1). Our copy is arXiv:2603.16011v3 [cs.SE], 17 Jul 2026. 56 pages (9 main, the rest references and appendix).
- **PDF:** related-papers/sehgal2026formulacode_2603.16011.pdf
- **Cite key:** sehgal2026formulacode
- **BibTeX-style reference:** Atharva Sehgal, James Hou, Akanksha Sarkar, Ishaan Mantripragada, Swarat Chaudhuri, Jennifer J. Sun, and Yisong Yue. 2026. FormulaCode: Evaluating Agentic Optimization on Large Codebases. In Proceedings of the 43rd International Conference on Machine Learning (ICML 2026), PMLR 306. arXiv:2603.16011.

## In short
FormulaCode is a benchmark of 957 performance tasks taken from merged performance pull requests in 70 scientific Python repositories. Each task comes with the benchmarks that the project maintainers wrote themselves for the airspeed velocity (ASV) tool, on average 264.58 per task. An agent edits the repository; its change is timed on all these workloads and compared with the human expert's patch on the same cloud machine. Agents were run on a 108-task subset (FormulaCode-V). All seven agent setups make the code a little faster than the baseline (speedup 1.03 to 1.10), but all are worse than the expert (speedup 1.1040), and about half of the agent patches are thrown away because they break tests.

## Problem and motivation
- Coding benchmarks mostly give a pass/fail signal, or use synthetic (LLM-written) tasks. Optimization needs a continuous signal.
- Real optimization touches many workloads: a change that speeds up one path can slow another.
- Four wishes for a benchmark (p. 1): fine-grained metrics, real-world measurements "derived from established execution environments (e.g., standard profiling suites) rather than synthetic proxies", a human baseline, and repository scale.

## Background / key terms (explain each term simply)
- **airspeed velocity (ASV):** a Python benchmarking tool. Maintainers write functions named `time_*` (runtime) or `mem_*` (memory) plus a `setup`. ASV runs them with warm-up and repeated samples and can compare two commits.
- **Workload:** one ASV benchmark function with one parameter set. It measures one thing (time or memory).
- **Code_0 / Code_expert / Code_agent:** the repository before the PR, after the human PR, after the agent's edit.
- **Speedup (per workload):** workload(Code_0) / workload(Code_agent). Above 1 is better. Per task and overall, they take the geometric mean (Eq. 1, p. 3).
- **Advantage (Adv):** speedup of the agent minus speedup of the expert. Zero means equal to the expert; negative means worse.
- **Stratified advantage:** advantage computed after grouping workloads by module, class or function (levels 1, 2, 3).
- **Normalized advantage:** Adv divided by sqrt(variance of agent speedups + variance of expert speedups). A signal-to-noise form.
- **Mann-Whitney U test:** a rank test that asks whether two sets of samples come from the same distribution. It needs no normal-distribution assumption.
- **Holm-Bonferroni correction:** makes the p-value rule stricter when many tests are done at once.
- **Snapshot test:** stores what a workload returns (or its local variables) on the baseline and checks the edited code gives the same.
- **Ranked Pairs:** a voting method used to turn pairwise comparisons into one ranking.
- **FormulaCode-V:** the 108-task subset with manually validated unit tests, used for all agent runs.

## Method and setup
- **Pipeline (Section 3, Appendix A, Fig. 2):**
  1. Scrape: BigQuery GitHub dataset for repositories with an `asv.conf.json`, not forks, active in the last three years, Python 3.8+. Result: 766 repositories.
  2. Filter: 105,074 merged PRs. Rule-based filters (at least 100 stars, merged, ASV config present at that commit, touches real code, regex on messages, at most 500 files / 80,000 lines / 64,000 tokens, builds with `uv`) leave 26,717 PRs. An LLM classifier for "primary intent is performance" plus problem-statement extraction leaves 3,181 candidates from 101 repositories. The classifier is tuned for recall.
  3. Environment: an LLM agent writes a Docker build script per task (reusing scripts from nearby commits). 1,232 tasks from 75 repositories build. They stopped early "due to limited resources".
  4. Validation: keep tasks where the expert patch gives a statistically significant speedup on at least one workload. Result: 957 tasks from 70 repositories.
- **How performance is measured (this is what we compare with):**
  - **Workload:** the maintainers' own ASV benchmarks at that commit. Mean 264.58 per task, max 1,364; "% Coverage" mean 41.24%, max 97.86% (Table 1, p. 5; the paper does not define how coverage is computed).
  - **Number of runs:** ASV defaults are kept. "ASV defaults to collecting between 2 and 40 measurements per workload through adaptive stopping" (A.6, p. 17), after a warm-up, "with interleaved rounds when enabled". Repositories can override this per workload. So the sample count is not fixed and can be as low as 2.
  - **Machine:** AWS EC2 `c5ad.large`: 2 vCPUs, 4 GiB RAM, 75 GiB SSD, $0.086 per hour (B.5, p. 42; Table 12, p. 43).
  - **Isolation:** one EC2 instance per task. On it, in this order: baseline, expert patch, then each agent's patch, each in a fresh Docker container, with container state reset between them (B.5, p. 42). ASV adds its own safeguards ("CPU affinity, warm-ups, repeated trials", B.1, p. 39). No dedicated physical cores, no statement on hyper-threading or frequency control.
  - **What counts as a speed-up when building the dataset:** per workload, two-sided Mann-Whitney U between baseline samples and expert samples, significant only if p < 0.002 (ASV default). If there are too few samples for the test to ever reach 0.002, ASV instead requires that the two 99% confidence intervals do not overlap (A.6, p. 18). A task is kept if at least one workload is significantly faster.
  - **Multiple testing:** re-running with Holm-Bonferroni inside each task removed 35 of 957 tasks and none of the 108 in FormulaCode-V (p. 18).
  - **What counts as a speed-up for an agent:** the ratio of measured values, per workload, then the geometric mean. The paper does not say that non-significant workload changes are set to 1, and it does not say which statistic of the samples (median, mean, minimum) is the workload value.
  - **Correctness gate:** the patch must pass the repository's pytest suite and the snapshot tests. If not, the patch is rolled back and its speedup counts as 1 (p. 3; B.7, p. 44-45).
  - **Not reported:** a base-against-base (A/A) run, a noise floor in percent, or how much the same code varies between containers.
- **Agents and models (Section 4, B.2, Tables 12-13):** Terminus 2 (at commit d71d8fc, temperature 0.7) with GPT-5, Claude 4.0 Sonnet, Gemini 2.5 Pro, Qwen 3 Coder. OpenHands (CodeActAgent v0.51.0, temperature 0.0, max 500 steps) with GPT-5, Claude 4.0 Sonnet, Qwen 3 Coder. Seven setups. Six-hour cap per task, never reached; average 38 minutes per task.
- **What the agent is told (Fig. 16-18):** the issue text, "initial observations" extracted from the PR, and instructions to run `asv run --python=same --bench="<regex>"` and `asv profile`. The agent can run the same benchmarks it is scored on.
- **Dataset build machine:** Ubuntu 22.04, dual Xeon Platinum 8352Y (128 threads), 503 GiB RAM, 4 A40 GPUs. About 32 hours, about 2 TB of Docker cache. Claude 3.5 Sonnet fallback cost $446.

## Section-by-section notes

### 1. Introduction (p. 1-2)
- Lists the main findings: agents speed code up but lose to experts; better at function level than repository level; good at some strategies (parallelizing, batching), bad at others (vectorized or lower-level code); results vary with repository popularity; frontier models are more cost-effective; little sign of data leakage.

### 2. Benchmark design and metrics (p. 2-4)
- A change is valid only if the edited code passes all tests the baseline passes.
- Fig. 1 example: an Astropy task with 59 workloads.
- Speedup, advantage, stratified advantage, normalized advantage, cost-weighted advantage are defined here.
- Text says a workload "may exhibit natural variability due to execution noise" (p. 3), but the metrics themselves use point values.

### 3. Dataset construction (p. 4-5)
- Covered in Method. Tasks span 2017-10-21 to 2025-11-21. The benchmark is "live": new tasks each month (updated on the 25th, Fig. 19).
- Table 1: gold patch edits 38.088 lines on average (max 526), 3.93 files (max 34), 6.06 functions (max 54). Issue text 2,718.03 tokens on average.

### 4. Experiments (p. 5-8)
- **4.1 Leaderboard (Table 2).** Every setup has speedup above 1 and Adv below 0. Best Adv: OpenHands + Claude 4.0 Sonnet, -0.0112 (speedup 1.0539). Best raw speedup among agents: Terminus 2 + Claude 4.0 Sonnet, 1.0987, but its Adv is -0.0410. Expert speedup: 1.1040. So ranking by speedup and ranking by Adv disagree.
- **4.2 Scale (Fig. 3).** Most setups have higher advantage at function level than at module level. Exception: OpenHands + Claude 4.0 Sonnet is best at module level.
- **4.3 Optimization type (Table 3).** Expert patches are labelled by an LLM into 13 classes. All agents are positive on "Parallel" (0.007 to 0.015) and "Batch" (0.028 to 0.051). All are strongly negative on "Lower" (use a lower-level system): -0.180 to -0.720.
- **4.4 Popularity (Table 4).** Quintiles by GitHub stars. Worst is Q4 (6,371 to 10,343 stars): Adv from -0.0378 to -0.3529. Expert speedup is lowest there too (1.0822). In Q1 (133 to 202 stars) expert speedup is 1.1104. Q2 is the only quintile where most setups are positive.
- **4.5.1 Cost (Table 14, Fig. 4).** Cost per task from $0.7814 (OpenHands + GPT-5) to $3.7722 (Terminus 2 + Claude 4.0 Sonnet).
- **4.5.2 Trade-offs (Fig. 5).** For each task take the worst workload speedup, then average over tasks. The expert has the highest global speedup and also a low worst-workload value (about 0.89 on the plot; read from the figure, not printed as a number). So experts accept slow-downs on some workloads to win overall.
- **4.5.3 Leakage (Table 5).** Mean speedup in 3-month bins around each model's knowledge cutoff. No steady drop after the cutoff. Example, Claude 4.0 Sonnet: 1.0892, 1.0564, 0.9966 before; 1.0915, 1.0951, 1.0519 after.

### 5. Related work (p. 8-9)
- Table 6 compares benchmarks: GSO-Bench 102 tasks, SWEfficiency 400, SWE-Perf 140, each listed with a "Single" workload per task; FormulaCode 957 tasks with 264.58. (These are the numbers as printed in Table 6. Check each against its own paper before citing.)
- Claim: GSO-Bench and SWEfficiency "only optimize for a single target function at a time" (p. 9).

### 6. Conclusion and limitations (p. 9)
- Only scientific Python with ASV. Signal is limited to what the workloads exercise. Agents were run on 108 tasks, not 957. One AWS instance type; "cross-platform behavior remains untested".

### Impact statement (p. 10)
- Workloads are an attack surface: someone could add easy workloads upstream. Usernames are anonymized.

### Appendix A: dataset construction (p. 14-19)
- A.3: the intent classifier leans to YES when unsure, because later timing removes false positives.
- A.4: the task text is built only from material that existed before or at PR creation. An LLM extracts near-verbatim sentences from the PR into four fields: initial observations, triage attempts, solution overview, solution observations (Fig. 13). Fig. 16-18 show only "initial observations" and issues in the agent's prompt.
- A.6: measurement and statistics (see Method).
- A.7: FormulaCode-V picks tasks with a large, low-variance expert speedup and a working pytest suite.
- A.8 (Tables 7, 8): share of optimization types. In the full set: micro-optimizations 20.2469%, remove or reduce work 20.0823%, better algorithm 20.0823%, lower-level system 11.0288%, better data structure 9.7119%, cache and reuse 8.3128%. LLM-inferred difficulty: easy 54.8971%, medium 44.4444%, hard 0.6584%.
- A.9: limitations (same four as Section 6).

### Appendix B: experiment details (p. 39-56)
- B.1: why ASV. First released 1 May 2015.
- B.5: the Terminal-Bench changes: fixed cloud machines, sequential evaluation, continuous metrics, cost accounting. "remote execution is a reproducibility convenience rather than a methodological prerequisite" (p. 42).
- B.6: Adv and speedup disagree because big speedups sit on tasks where the expert also got big speedups. Log-space advantage gives the same ranking for OpenHands setups (Table 15).
- B.7 (Tables 16-20):
  - Rejected for correctness, out of 108: 47 to 56 per setup. On average about 48.5%. Most are pytest failures (42 to 54), fewer are snapshot failures (29 to 36).
  - Trajectory length: mean from 68.60 steps (OpenHands + GPT-5) to 633.10 (OpenHands + Qwen 3 Coder).
  - Tool use: on average 14.90% of calls are benchmarking or profiling, 2.68% are tests.
  - Memorization: mean normalized edit distance between agent and expert patch is 0.94 to 0.98, so patches are almost never copies.
- B.9 (Fig. 20-25): six side-by-side examples. In the Modin case the agent fixed a real caching bug that was "not on the performance-critical path" and got Adv -0.1265. In the Optuna hypervolume case both found the same O(N^2) algorithm, but the human used vectorized numpy and the agent a Python loop: Adv -0.03964. In three cases (NetworkX, PyBaMM, Shapely) the agent beat the human by small margins (+0.0132, +0.0167, +0.0131).
- Fig. 26-27: scatter of agent speedup against expert speedup per workload.

## Key results (with numbers) and what they mean
- Agent speedups 1.0346 to 1.0987, expert 1.1040 (Table 2) -> averaged over hundreds of workloads, the effect of a whole PR is only 3% to 10%. Most workloads do not touch the changed code, so the geometric mean stays near 1. Effects this small are in the range where measurement noise matters.
- Adv from -0.0112 to -0.0504 -> every setup is behind the expert, but the gap is a few percent of speedup.
- About 48.5% of agent patches rejected for correctness -> half of the "optimizations" change behaviour or break tests. This supports checking output, not only time.
- 14.90% of tool calls for benchmarks, 2.68% for tests -> agents measure speed far more than they check correctness.
- "Lower" class Adv down to -0.720 -> the big losses are where the expert moved work into C, Rust or vectorized numpy.
- Parallel and Batch are positive for all agents -> but see Weaknesses: each of these classes is 0.9259% of FormulaCode-V, which is 1 task out of 108.
- Holm-Bonferroni removes 35 of 957 tasks -> about 3.7% of tasks pass only because many workloads were tested without correction.
- Edit distance at least 0.94 -> agents do not reproduce the expert patch text.

## Tables and figures
- **Fig. 1 (p. 2):** one task: issue, codebase, crowdsourced metrics, radar of workloads.
- **Fig. 2 (p. 4):** pipeline counts: 766 repositories; 26,717 PRs / 101 repositories; 1,232 candidates / 75 repositories; 957 tasks / 70 repositories.
- **Table 1 (p. 5):** task statistics.
- **Table 2 (p. 6):** leaderboard. Rows (Adv / normalized Adv / speedup): Terminus 2 GPT-5 -0.0504 / -0.1387 / 1.0585; Claude -0.0410 / -0.1065 / 1.0987; Gemini -0.0433 / -0.1138 / 1.0963; Qwen -0.0454 / -0.1257 / 1.0677. OpenHands GPT-5 -0.0209 / -0.0702 / 1.0825; Claude -0.0112 / -0.0483 / 1.0539; Qwen -0.0301 / -0.1529 / 1.0346. Expert 0 / 0 / 1.1040.
- **Fig. 3 (p. 6):** stratified advantage at module, class, function level.
- **Table 3 (p. 7):** advantage per optimization class. Columns Approx, Scale, DB, I/O, Uncat are empty.
- **Table 4 (p. 7):** advantage per popularity quintile.
- **Fig. 4 (p. 7):** mean advantage against mean cost.
- **Fig. 5 (p. 7):** worst-workload speedup against global speedup.
- **Table 5 (p. 8):** speedup around knowledge cutoff (GPT-5, Claude 4.0 Sonnet, Gemini 2.5 Pro; no Qwen row).
- **Table 6 (p. 9):** comparison with other benchmarks.
- **Fig. 6 (p. 15), Fig. 19 (p. 41), Tables 9-10 (p. 27-35):** dataset composition by repository and month.
- **Tables 7-8 (p. 19):** optimization type and difficulty shares.
- **Tables 12-13 (p. 43):** full evaluation configuration and model API details.
- **Tables 14-20 (p. 44-47):** cost, log-advantage, correctness violations, trajectory length, tool categories, tool use, edit distance.
- **Fig. 20-25 (p. 49-54):** expert vs agent patches.
- **Fig. 26-27 (p. 55-56):** how to read advantage; per-workload scatter for Terminus 2 agents.

## Ideas we can use
- **Rank test with a strict threshold.** Mann-Whitney U at p < 0.002, with a fallback of non-overlapping 99% confidence intervals when samples are few, is a ready-made, citable decision rule for "faster or not".
- **Multiple-testing check.** If we test several workloads or several signals per PR, report how many verdicts survive Holm-Bonferroni, as they did (35 of 957 dropped).
- **Same machine, fixed order, fresh container.** Base, then reference, then candidate on one instance. We do this with dedicated cores and add the A/A control they do not report.
- **Worst-workload view (Fig. 5).** A direct way to show "hidden costs": report the worst regression next to the headline gain.
- **Roll back on wrong output.** Their rule "speedup = 1 if tests fail" matches our "output changed" verdict.
- **Their PR fields.** "initial observations / triage attempts / solution overview / solution observations" is close to our claim extraction. It shows that PR text can be split into symptom, diagnosis and mechanism by an LLM with a verbatim check (longest common subsequence ratio).
- **Optimization taxonomy (Table 11).** A possible starting list for mechanism classes, though it is taken from blog posts and forum threads.

## Weaknesses and things glossed over
- **Small, shared cloud VM.** `c5ad.large` has 2 vCPUs. The harness, Docker and ASV share them with the benchmark. The paper says this "ensures hardware isolation" and cites an AWS security page; that page is about tenant isolation, not about timing noise. No pinning to dedicated physical cores beyond what ASV does.
- **No A/A control and no noise number.** They never show how much the baseline differs from itself across containers. With whole-task effects of 3% to 10%, this matters.
- **Agent speedups are not significance-filtered (as far as the paper says).** The Mann-Whitney rule is described for dataset inclusion. For agent scores the paper describes plain ratios. Table 12 lists the test under "Measurement" for all runs, but the text does not say how it enters the agent metrics.
- **As few as 2 samples per workload.** ASV's adaptive 2 to 40 samples is kept. With 2 against 2 samples a rank test cannot reach p < 0.002, so the confidence-interval fallback decides.
- **Statistic not stated.** Median, mean or minimum of the samples: the paper does not say.
- **"Section 2 includes additional safeguards to further minimize system variance" (B.1, B.5).** Section 2 defines metrics only. I found no such safeguards there.
- **Two different machines described.** Appendix B opens with "All experiments ran on a single Ubuntu 22.04 LTS machine" (Xeon, 128 threads). B.5 and A.9 say all performance measurements are on EC2 `c5ad.large`. The paper does not explain how the two fit (probably the Xeon machine drives the runs, but this is my guess).
- **Advantage is not clearly defined in aggregate.** The text says Adv_agent "is the geometric mean over n workloads" of differences that can be negative, which is not well defined. Table 2 values are not "agent speedup minus expert speedup" either: 1.0539 - 1.1040 = -0.0501, but the table gives -0.0112. The exact aggregation is not given.
- **Level numbering differs:** Section 2 starts levels at 0 (modules); Section 4.2 and Fig. 15 use 1, 2, 3.
- **Dataset counts do not add up in the composition tables.** Table 10 has 69 numbered repositories, not 70, and its "#Tasks" column sums to 1,215 (my sum), not 957. The month boxes in Fig. 19 also sum to 1,215 (my sum). Fig. 6 uses the same per-repository numbers (pandas 222, scikit-learn 143, qiskit 142). So these composition displays seem to describe a larger set than the 957 final tasks. The paper does not explain this.
- **Repository count after rule filters:** text says 26,717 PRs "from 127 repositories" (p. 4, p. 15); Fig. 2 prints "26,717 PRs, 101 repositories".
- **Holm-Bonferroni status unclear:** it removes 35 of 957, and "Our codebase incorporates this correction", but the paper keeps reporting 957.
- **Strategy claims rest on tiny groups.** In FormulaCode-V, "Use Parallelization" and "Do It Earlier Batch Throttle" are 0.9259% each, which is 1 of 108 tasks. "All agents beat experts on parallelization and batching" is a statement about one task each. "Hard" difficulty is 2.7778%, 3 tasks.
- **Evaluation on a selected subset.** FormulaCode-V was chosen for large, low-variance expert speedups (A.7; Table 7 caption says "sampled from the best performing tasks"). Results may not hold on the other 849 tasks. One run per setup per task; no repeated agent runs or confidence intervals on Table 2.
- **Agents can run the scoring workloads.** They are told to use `asv run` on the same benchmarks. Overfitting to the workloads is possible; the paper does not discuss it for agents.
- **LLM labels without validation.** Optimization class, difficulty and tool category come from gpt-oss-120b with no human agreement number.
- **Leakage test is weak.** Bins are small and noisy (values jump from 0.9871 to 1.1708); "no consistent drop" is not evidence of no leakage. The authors say "limited evidence", which is fair.
- **Small label mismatches:** Table 20 caption says patches share "only ~4%" of content, the text says "at most ~6%". Example IDs in the B.9 list differ from the figure captions (for example `modin_modin_2` vs `modin_project-modin_7637`; Shapely +0.0132 vs +0.0131).
- **Only wall time and memory benchmarks.** No hardware counters, no syscall or kernel view, no check of why a patch is faster.

## Open questions and future work (theirs, and ours)
- Theirs: other domains and languages; evaluation on the full 957 tasks; cross-platform behaviour; evolutionary and tree-search agents; ensembles that route by optimization scope.
- Ours:
  - What is the A/A spread of ASV workloads on a 2-vCPU cloud instance, and how many per-workload "speedups" in their scatter plots fall inside it?
  - In their Modin example, the agent's stated fix was real but off the hot path. How often does this happen in AIDev PRs, and can a kernel or counter signal show it without an expert patch to compare with?
  - Would ASV's own rule (Mann-Whitney, p < 0.002) agree with our verdicts when both are run on the same PR?

## Link to our paper
- **Introduction / Related work:** cite as the largest repository-level optimization benchmark, with maintainer-written workloads and a statistical inclusion test. It scores speed against an expert; it does not check the reason given for a change.
- **Method:** cite for the Mann-Whitney U decision rule and the 2 to 40 adaptive samples of ASV, and contrast our setup: dedicated cores, counters and LTTng traces, and an A/A control.
- **Results / Discussion:** cite the 48.5% correctness rejections next to our "output changed" verdict, and the worst-workload analysis next to our "hidden costs".
- **Threats:** cite their admission that measured gain reflects only the code paths the workloads exercise. The same limit holds for the workload our build agent writes.

## Link to the thesis (tracing, kernel analysis)
- Not a tracing paper. ASV gives time and memory per benchmark; nothing below that.
- The measurement noise sources they name, "OS scheduling, background load, and CPU power management" (p. 17), are exactly what kernel tracing can observe (sched_switch, cpu_frequency events). A traced A/A run on their instance type would put a number on the noise they treat only with statistics.
- Their optimization classes map to low-level signals: "cache and reuse" and "remove or reduce work" should lower instruction counts; "I/O and latency hiding" should change syscall counts and wait time; "parallelization" should change futex and scheduling activity. They classify by reading the patch; a trace could check it.

## Quotes for inline citation
- "Because timing measurements are inherently noisy (e.g., due to OS scheduling, background load, and CPU power management), we adopt the statistical significance validation procedure used by ASV to verify that the observed differences between two code states are significant under repeated measurement on commodity hardware." (p. 17)
- "In practice, ASV defaults to collecting between 2 and 40 measurements per workload through adaptive stopping, where additional samples are drawn until the estimate converges or the maximum is reached." (p. 17)
- "When sufficient raw samples are available, it applies the Mann–Whitney U test and declares a difference only if the resulting p-value is below a stringent threshold (default p < 0.002)." (p. 18)
- "We use the c5ad.large instance with 2 vCPUs, 4GiB RAM, and a dedicated 75 GiB SSD for storage." (p. 42)
- "we measure the baseline implementation (Code0), then the expert-written optimized solution (Codeexpert), and then each agent-produced candidate in turn, resetting the container state between configurations." (p. 42)
- "For all agents, the overall advantage, Adv, is negative, indicating a fundamental performance gap." (p. 5)
- "On average, ∼48.5% of trajectories are rejected due to correctness violations" (p. 45)
- "a patch's measured gain reflects only the code paths that the workloads exercise, so speedups on uncovered paths go unmeasured." (p. 9)
- "A correctness fix, but not on the performance-critical path." (Fig. 20, p. 49)

## Suggested citation sentences
- FormulaCode evaluates agents on 957 tasks mined from performance pull requests, each with on average 264.58 maintainer-written ASV workloads, and finds that agents speed code up but stay behind the human patch \cite{sehgal2026formulacode}.
- FormulaCode decides whether a patch changes performance with a Mann-Whitney U test at p < 0.002 on ASV samples taken on a 2-vCPU cloud instance \cite{sehgal2026formulacode}; we use dedicated cores, a base-against-base control and kernel-level signals.
- About half of agent-written optimization patches in FormulaCode-V are rejected because they break tests \cite{sehgal2026formulacode}, which is why we report output changes next to speed.
- Existing optimization benchmarks score the size of a speed-up \cite{shetty2025gso,sehgal2026formulacode}; none of them checks whether the mechanism named by the author took place.

## Connection to "Below the Stopwatch"
- **How it relates:**
  - Closest prior work on the measurement side: real performance PRs, before/after builds in Docker, repeated timing, a statistical test. We build on its decision rule (rank test, strict threshold) and its same-machine, sequential design.
  - What it does not do and we do: it never looks at the reason for a speed-up. No hardware counters, no kernel traces, no claimed-mechanism check, no reported A/A control, and no dedicated cores (2 shared vCPUs). It studies agents solving benchmark tasks, not PRs that agents opened in the wild.
  - Where it pushes against us: (1) it argues that metrics should come from "established execution environments (e.g., standard profiling suites) rather than synthetic proxies" (p. 1). Our workload is written by a build agent, which a reviewer from this group can call a synthetic proxy. (2) It has up to 1,364 workloads per task and shows that experts trade slow-downs on some for gains on others; one agent-written workload per PR can miss this. (3) Its filter keeps only repositories with ASV; we cannot assume AIDev PRs have maintainer benchmarks, so our coverage argument must be made separately.
  - Where it supports us: the Modin example (agent fixed a real issue that was not on the hot path, Adv -0.1265) is a concrete case of "plausible mechanism, no effect"; and the 48.5% correctness rejections support reporting "output changed".
- **Safe to cite for:**
  - Size and source of the benchmark. Abstract: "957 performance bottlenecks mined from scientific Python repositories on GitHub, each paired with expert-authored patches and, on average, 264.6 community-maintained performance workloads per task".
  - Timing is noisy and needs a statistical rule; they use Mann-Whitney U at p < 0.002. Appendix A.6, p. 17-18 (quotes above).
  - Their measurement machine and order. Appendix B.5, p. 42: "c5ad.large instance with 2 vCPUs, 4GiB RAM"; baseline, expert, agents measured in turn in fresh containers.
  - Agents improve runtime but less than experts. Section 4.1 and Table 2, p. 5-6: "All evaluated configurations attain speedup > 1 on FormulaCode-V relative to the baseline codebase"; "For all agents, the overall advantage, Adv, is negative".
  - Many agent optimization patches break correctness. Appendix B.7, p. 45: "∼48.5% of trajectories are rejected due to correctness violations".
  - Workload coverage limits what a measurement can show. Section 6, p. 9: "speedups on uncovered paths go unmeasured".
- **Do not cite for:**
  - Any claim about the reasons agents give in PRs, or about agent-opened PRs in the wild. The PRs in FormulaCode are human expert PRs; agents only solve the tasks.
  - "Measured on isolated hardware" in the sense of dedicated cores. It is a 2-vCPU EC2 instance with Docker; the "hardware isolation" wording is the paper's own and is not backed by a noise measurement.
  - Results on all 957 tasks. Agent results are on the 108-task FormulaCode-V subset.
  - "No data leakage." The paper says "Limited evidence of a cutoff-aligned leakage effect" (p. 8).
  - "Agents beat experts at parallelization and batching" as a general finding. In FormulaCode-V each class is 0.9259% of tasks (1 task).
  - A fixed number of repetitions. It is 2 to 40, adaptive, and repositories can override it.
  - Hardware counters, tracing, or any kernel-level signal. None are used.
  - Per-repository or per-month task counts from Table 10, Fig. 6 or Fig. 19 as a breakdown of the 957 tasks: they sum to 1,215.
