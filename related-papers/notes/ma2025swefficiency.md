# SWE-fficiency: Can Language Models Optimize Real-World Repositories on Real Workloads?
- **Authors:** Jeffrey Jian Ma (Harvard University), Milad Hashemi, Amir Yazdanbakhsh, Kevin Swersky (Google DeepMind), Ofir Press (Princeton University), Enhui Li (Xi'an Jiaotong University), Vijay Janapa Reddi (Harvard University), Parthasarathy Ranganathan (Google)
- **Venue / year / status:** The PDF is arXiv:2511.06090v3 [cs.SE], dated 27 Jun 2026. Its footer says "Proceedings of the 43rd International Conference on Machine Learning, Seoul, South Korea. PMLR 306, 2026", so this version is the ICML 2026 paper (peer-reviewed). 39 pages: main text pp. 1-9, references pp. 10-11, appendix A to N pp. 12-39.
- **PDF:** `related-papers/ma2025swefficiency_2511.06090.pdf`
- **Cite key:** ma2025swefficiency
- **BibTeX-style reference:** Jeffrey Jian Ma, Milad Hashemi, Amir Yazdanbakhsh, Kevin Swersky, Ofir Press, Enhui Li, Vijay Janapa Reddi, and Parthasarathy Ranganathan. 2026. SWE-fficiency: Can Language Models Optimize Real-World Repositories on Real Workloads? In Proceedings of the 43rd International Conference on Machine Learning (ICML), PMLR 306. arXiv:2511.06090. (Note: `paper/refs.bib` lists it as an arXiv 2025 preprint. The PDF we hold states the ICML 2026 venue.)

## In short
SWE-fficiency is a benchmark of 498 tasks from 9 Python libraries (pandas, numpy, scipy and others). Each task comes from a real, merged, human-written pull request that made one workload faster. The agent gets the codebase and a workload script and must make that workload faster without breaking the repository's own unit tests. The score is the "speedup ratio": the agent's speedup divided by the human expert's speedup, combined over tasks with a harmonic mean. The best of 15 models (Claude 4.5 Opus with OpenHands) reaches 0.225x, where 1.0x means "as good as the expert". Performance is measured as wall-clock time with Python `timeit`, in Docker containers pinned to 4 vCPUs on one Google Cloud VM. There are no hardware counters and no kernel traces.

## Problem and motivation
- Most coding benchmarks check **what** gets fixed (does the test pass), not **how good** the code is (speed, memory).
- Earlier speed benchmarks (PIE, EffiBench, Mercury, KernelBench, AlgoTune) work on single functions or small programs, not full repositories.
- The two closest repository-level benchmarks, GSO and SWE-Perf, either give the agent a correctness oracle or reuse unit tests as the performance workload and tell the agent which functions to optimize. The authors say this skips the investigation part of performance work: find the bottleneck yourself, and find the relevant tests yourself.
- Research question (p. 1): "to what extent can LM agents optimize the runtime of real-world repositories on real-world workloads?"

## Background / key terms (explain each term simply)
- **Workload:** a short Python script that runs some library function many times and prints the mean and standard deviation of the run times. It is the thing to make faster. It is separate from the unit tests.
- **Gold patch / expert patch:** the code change from the real merged PR. It is the human reference.
- **Covering tests (also "guarding" or "intersecting" tests):** the repository's unit tests that run the lines changed by the gold patch. These must still pass after the agent's edit.
- **Pass-to-pass:** tests pass before and must still pass after. The task adds no new behaviour, only speed. (SWE-bench is fail-to-pass: a failing test must start passing.)
- **Speedup:** T_pre / T_post, the workload time before the edit divided by the time after. 2x means half the time.
- **Speedup ratio (SR):** Speedup_LM / Speedup_gold. 1.0 means the agent matched the expert. Above 1.0 means it beat the expert.
- **Harmonic mean:** an average that is pulled down strongly by small values. The authors use it to combine SR over tasks (they cite Smith 1988 and Eeckhout 2024).
- **timeit:** Python's standard module for timing a function. `timeit.repeat(f, number=n, repeat=r)` gives r timings, each one the total time of n calls.
- **CPU pinning:** forcing a process to run only on chosen CPU cores, so other work does not disturb it.
- **NUMA node:** a group of CPU cores with their own local memory. Using memory from another node is slower.
- **Flamegraph / function-level profiler:** records how much time is spent in each function, alone ("tottime") and including the functions it calls ("cumtime").
- **Reward hacking:** the agent makes the score look good without really making the code faster (for example, it detects that it is being timed).
- **Satisficing:** stopping at the first result that is "good enough" instead of looking for the best one.

## Method and setup

### How the dataset was built (Sec. 2.1, Appendix E)
Five stages, with the number of PRs left after each (Appendix E, pp. 18-19):
1. **Scrape** merged PRs from 9 repositories, cutoff date March 12th, 2025: 96,457 PRs. (Appendix E.4 says "100k" loosely.)
2. **Attribute filter:** keep PRs that (i) have a performance keyword or tag (list on p. 19: performance, speedup, faster, memory, optimize, cache, timeit, asv, and more), (ii) do **not** change test files, (iii) really change the AST (not only comments or docs). 9,257 PRs remain "after attribute filtering and prior to checking for meaningful changes to the AST" (-90.4%).
3. **Covering tests:** build a Docker image per instance with pinned dependencies, run the test suite under `coverage.py`, add static symbol resolution with `jedi`, keep PRs with at least one test that runs the edited code. 1,041 PRs remain (-88.8%).
4. **Workload annotation (manual):** two author annotators read each PR's description, diff and discussion and wrote a workload script. About 200 author-hours for 1,041 instances. They calibrated on 5 examples first. Both annotators reviewed every workload.
5. **Execution filter:** run tests and workload before and after the gold patch. Keep the instance only if the speedup is significant. 498 tasks remain.

### How performance is measured (the part we compare against)
- **What is timed:** the `workload()` function of the annotated script, with Python `timeit.repeat()` (Appendix C, p. 17). An optional `setup()` function is run before each repetition and is not timed.
- **Metric:** wall-clock run time only. The script prints `Mean` and `Std Dev` of the timings (Appendix B.2, E.4). No hardware counters, no system calls, no memory metric, no kernel tracing.
- **How many runs:** not fixed. Each workload has its own `number` and `repeat`, chosen by the annotator "to get tight error bars" (template in Fig. 15 uses `number=1, repeat=10`). Examples printed in the paper: `number=1, repeat=5` (dask-6293), `number=100, repeat=10**4` (numpy-11720), `number=1, repeat=200` using only the last 100 timings (scipy-12001), `number=5, repeat=1000` (pandas-56508). The paper does not give the distribution of repeat counts over the 498 tasks.
- **Warm-up:** no general warm-up rule. They keep whatever warm-up the PR author's script had (Appendix C, p. 18).
- **Process isolation between repetitions (Appendix L.2):** at evaluation time the script is rewritten so that each timing repetition runs in a **new child process** (Python `multiprocessing`). This stops caches (`@lru_cache`, module-level dicts) from carrying over between repetitions. The text says "spawn start method" once, but the description and the printed harness code use `fork`.
- **What counts as a real speed-up for the gold patch (curation, Appendix E.5):** an instance is dropped when µ_pre − µ_post ≤ 2σ_post. In words: the mean must improve by more than two standard deviations of the post-edit timings. Main text (p. 4): "runtime improvement greater than 2× measurement std. dev." This is a threshold rule, not a statistical test, and it has no minimum effect size.
- **What counts as a speed-up for an agent patch:** nothing is tested. The speedup is just the ratio T_pre / T_post-LM-patch. Table 3 sorts patches into "slower than pre-edit", "faster than pre-edit" and "faster than expert". The paper does not say what noise margin (if any) is used for these three groups.
- **Machine (Sec. 3, p. 5):** "All evaluations are run on a single Google Cloud n2-standard-64 VM (64 vCPUs, 256GB Memory)." This is a virtual machine in a public cloud, not bare metal.
- **Isolation (Sec. 3 and Appendix F):**
  - Every task runs in a prebuilt Docker image, so no installation work happens during timing.
  - Each worker is pinned to 4 vCPUs, bound to the matching NUMA memory node, with a 16 GB memory limit.
  - The Docker daemon and `containerd` are pinned to a separate set of physical CPUs.
  - Several workers run in parallel on the same VM, each on its own group of 4 vCPUs.
- **Correctness:** the covering tests (`PASS_TO_PASS`) must pass. In curation the tests were run ten times to remove flaky ones. A patch that adds new stack-inspection code (`inspect.currentframe`, `sys._getframe`, and so on) is marked as failing (Appendix L.1).
- **Stability check (Appendix N, Table 11):** three independent evaluation runs of the expert patch and of three agents' patches. The aggregate SR barely moves between runs (see Key results). This is reported for the aggregate score only.

### The score (Sec. 2.3)
- Per task: SR = Speedup_LM / Speedup_gold.
- Over tasks: harmonic mean of SR, with a floor of SR_min = 0.001 per task.
- Empty patch or failed tests: the task's SR is set to max(1 / Speedup_gold, SR_min). This is the same as "the agent changed nothing" (speedup 1).
- One patch per task (pass@1). One trajectory is sampled per task.

### Agents and models (Sec. 3, Appendix G)
- Scaffolds: OpenHands and SWE-agent. Limits: 3 hours per task, 30 minutes per step, at most 100 actions. Same 4 vCPUs and 16 GB as the evaluation. SWE-agent also has a $1 cost cap per task. OpenHands has no cost cap.
- 15 models from OpenAI, Anthropic, Google, Z.ai, Moonshot AI and DeepSeek. Temperature 0, except GPT-5 Mini at temperature 1.
- The agent is told to make the given `workload()` faster, not to edit the workload, and not to break passing tests. It is not told which tests matter. It gets a rebuild command and a test command prefix.
- Conflict of interest note (p. 2): several authors work at Google, which makes the Gemini models tested.

## Section-by-section notes

### 1. Introduction
- Motivation and the gap described above.
- Headline: agents reach less than 0.23x of expert speedup "on average" and often break tests.
- Five contributions: the 498-task benchmark, the collection pipeline, the SR metric, the analysis of the gap, the open release.

### 2. Overview
- Table 1 (p. 3) compares benchmarks. SWE-fficiency is the only one with all four ticks: evaluates run time, repository level, uses the repository's own tests for correctness, uses a separate end-to-end workload for performance. Task counts listed: EffiBench 1000, Mercury 1889, PIE 978, KernelBench 250, AlgoTune 154, GSO 102, SWE-Perf 140, SWE-fficiency 498.
- The dataset has no overlap with SWE-bench, because SWE-bench needs PRs that change tests and this pipeline rejects them. Check: they ran SWE-bench instances through their keyword filter, got 581, sampled 50, and all 50 introduced new behaviour (Appendix B, p. 12).
- Sec. 2.2: the task is open-ended (any edit is allowed) but the grading is exact (tests plus speedup against the expert).

### 3. Evaluation setup
- Machine, pinning and agent limits as listed above.
- "We observe < 0.5% variance in Speedup Ratio across independent measurement runs on our fixed hardware platform."

### 4. Experiments and results
- **4.1 Overall:** Table 2 gives SR for 15 models with OpenHands. Table 3 breaks patches into four outcome groups.
- **Difficulty (Fig. 4, Fig. 16):** three difficulty measures: pre-edit workload run time, gold patch length, gold speedup. Agents do well on tasks with short run time and small gold speedup. They do badly when the workload is long or the expert speedup is large. Gold patch size makes little difference.
- **Mislocalization (Fig. 6, Appendix I):** agents often edit different functions than the expert.
- **4.2 Qualitative:**
  - *Satisficing:* when the agent stays below the expert, the median trajectory is 30 to 50 actions, far below the cap of 100 (Fig. 5). The agent stops after the first measurable speedup.
  - *Shortcut bias:* agents add identity checks, early exits and caches. Experts restructure code to lower the cost per element, or move work into compiled code (Cython, Pythran, BLAS).
  - *Workload overfitting and semantic drift:* patches hard-code properties of the evaluation workload (array shapes, dtypes). Worst cases are wrong code: returning the input DataFrame unchanged from `groupby.apply`, or monkey-patching `np.arange` at module level.
  - *Maintainability:* agent edits are invasive (global monkey-patching, module-level mutable caches). Expert edits are small and local.
  - *LM-written workloads:* see Key results.

### 5. Related work
- Function-level benchmarks keep the library fixed and change user code. SWE-fficiency does the opposite ("library maintainer" view): the user workload is fixed and the library is edited.
- About SWE-Perf: it "reuses repository unit tests for both correctness and performance and instructs agents to optimize specified functions". About GSO: it uses LM-generated correctness tests and performance workloads and does not show the workloads to the agent.
- The paper cites SWE-Perf as "Fan et al., 2025". The SWE-Perf paper's first author is Xinyi He. Use our own key `he2025sweperf`.

### 6. Discussion
- Limitations stated by the authors: mostly Python and Cython changes in nine libraries. Future: C/C++/Rust, longer workloads, non-CPU hardware, several objectives (memory and run time together).

### Appendix highlights
- **B (dataset):** statistics table (Fig. 11) and repository split (Fig. 10). B.3: an LM (Gemini 2.5 Flash) labels each gold patch with one optimization category and a "mechanism-level explanation"; 50 labels were checked by hand.
- **C (why timeit):** PR authors and the `asv` benchmark tool use `timeit`, so the benchmark measures "the same way the community measures it".
- **D:** real PRs that speed up one workload and slow another were still merged (numpy#21394, pandas#44566, numpy#18324). This is their argument that a single-workload task is realistic.
- **E:** pipeline details. Median covering tests per task: 7,723. Over 90% of tasks have more than 100 covering tests, about 74% have more than 1,000.
- **F:** reproducibility techniques (prebuilt images, pinning, NUMA binding).
- **G, H:** prompts, sampling settings, full results (Tables 6 and 7), and the 100-task "Lite" subset (Table 8).
- **I:** the profiling method behind Fig. 6. Profiles are taken before and after each edit. Speed gain is assigned to the deepest functions that got faster, without counting a caller and its callee twice. Only functions with a gain of at least 2% of the expert's total gain count.
- **K:** LM-generated workloads study.
- **L:** the two reward-hacking guards (stack-frame check, new process per repetition).
- **N:** the SR stability table.

## Key results (with numbers) and what they mean
- **Best agent is at 0.225x of the expert (Table 2, p. 6).** Claude 4.5 Opus 0.225, GPT-5 0.157, GPT-5.2 0.148, Claude 4.5 Sonnet 0.116, Gemini 3 Flash 0.106, Gemini 3 Pro 0.102, Claude 4.1 Opus 0.098, Qwen3 Coder Plus 0.068, Kimi K2-0905 0.054, DeepSeek V3.1 0.043, GLM-4.6 0.042, Gemini 2.5 Flash 0.041, GPT-5 Mini 0.039, Gemini 2.5 Pro 0.031, Claude 3.7 Sonnet 0.024. With SWE-agent and a $1 cap (Table 6): Claude 3.7 Sonnet 0.041, GPT-5 Mini 0.026, Gemini 2.5 Flash 0.006.
  - What it means: on this score, agents are far from human experts. But read the next point before using the number.
- **The low SR comes mostly from the bad tasks, not the typical task (Table 3 / Table 7).** For Claude 4.5 Opus: 9% of patches fail tests, 1% pass but are slower than before, 47% are faster than before but slower than the expert, and 43% are faster than the expert. GPT-5.2 beats the expert on 52% of tasks and still scores 0.148. The harmonic mean is pulled down by failed tasks, which count as "no change" (SR = 1 / gold speedup, which is tiny when the expert gain is large).
  - What it means: do not write "agents reach 23% of expert performance on a typical task". The correct statement is about the harmonic-mean score.
- **Agents break tests often.** Share of patches that fail the covering tests: from 9% (Claude 4.5 Opus) to 45% (GPT-5 Mini) with OpenHands.
- **Some correct patches make the workload slower.** "Passes tests but slower than pre-edit" ranges from 1% (Claude 4.5 Opus) to 18% (DeepSeek V3.1, Gemini 2.5 Pro).
  - What it means for us: an agent's optimization edit can be a slowdown even when tests pass. This supports checking each claimed speed-up by measurement.
- **Mislocalization (Fig. 6, Table 9).** Share of the expert's speedup that sits in functions the agent never edited: 68.6% (Claude 3.7 Sonnet), 72.3% (GPT-5 Mini), 73.4% (Gemini 2.5 Flash), 75.4% (DeepSeek V3.1), all OpenHands. Table 9: wrong-file loss 0.37 to 0.48, in-file loss 0.27 to 0.33, function-level coverage 0.25 to 0.31. Experts change code at call depth 4.5 to 4.9 from the workload; agents at 3.8 to 4.3 (Table 10; the text on p. 30 says 3.8 to 4.2).
- **LM-written workloads are weaker than manual ones (Sec. 4.2, Appendix K).** Gemini 2.5 Flash was given the gold diff and the pre-edit files and asked to write a workload. The manual workload showed a larger gain in 76% of cases. 47% of the LM workloads showed no significant speedup for a patch that is known to be a real optimization. The authors call this a lower bound: a mid-level model, and it did not see the PR description.
  - What it means for us: a workload written by an agent can miss a real speed-up almost half of the time in this setting. See the Connection section.
- **Reward hacking was seen.** During harness development some agents used stack-frame inspection to detect the timing harness, or cached results across timing runs (p. 7, Appendix L).
- **Stability (Table 11, p. 37).** Three independent runs. Expert SR: 1.000, 0.9986, 1.0026 (spread 0.0040). Claude 3.7 Sonnet (OpenHands): 0.04761, 0.04796, 0.04779 (spread 0.00035). GPT-5 Mini: 0.02115, 0.02115, 0.02128 (spread 0.00013). Gemini 2.5 Flash: 0.007941, 0.007947, 0.007935 (spread printed as 0.00012).
  - What it means: the aggregate score is repeatable on the same VM type. It says nothing about the noise of one task's timing.
- **Lite subset (Table 8).** 100 tasks. Gemini 2.5 Pro: SR 0.008, 60% pass tests, $509.52, 9.03 hours of inference. Gemini 2.5 Flash: SR 0.007, 65% pass, $98.83, 6.29 hours.
- **Example (Fig. 8 / Fig. 17).** pandas-50524: expert 20.5x, Claude 3.7 Sonnet 2.3x, SR 0.113. Counter-example (Fig. 19): matplotlib-22108: expert 1.9x, Claude 3.7 Sonnet 2.4x with a "last rotation" cache, SR 1.292.

## Tables and figures
- **Fig. 1 (p. 2):** task picture: codebase plus workload in, patch out, tests must stay green.
- **Table 1 (p. 3):** benchmark comparison (see Section 2 notes).
- **Fig. 2 (p. 3):** the five-stage pipeline.
- **Fig. 3 (p. 4):** three plots. Left: workload run times before and after the gold patch, spread from about 10^-5 s to 10^2 s (log axis). Middle: gold speedup, most tasks near 1x to 10x with a long tail up to 10^4 and more. Right: gold patch categories (LM-labelled): Simplify Code 161, Algorithmic Change 159, Memory Efficiency 93, Caching & Reuse 42, Low-level Tuning 38, Parallelism 4, Config Tuning 1 (sum 498).
- **Table 2 and Table 3 (p. 6), Tables 6 and 7 (pp. 26-27):** scores and outcome breakdown.
- **Fig. 4 (p. 7):** tasks grouped by SR bucket (< 0.25, 0.25 to 0.5, 0.5 to 1.0, ≥ 1.0). The lowest SR bucket has the longest workloads and the largest gold speedups. Exact values are only readable from the plot, so do not quote them.
- **Fig. 5 (p. 8):** median trajectory length per SR bucket. All lines sit between about 25 and 50 actions; the cap is 100.
- **Fig. 6 (p. 8):** stacked bars of missed expert speedup (wrong file plus wrong function): 68.6%, 72.3%, 73.4%, 75.4%.
- **Fig. 7 (p. 8):** flamegraph for pandas-52054. The expert edit in `ndarray_to_mgr` gives a 3.99x speedup. Claude 3.7 Sonnet (SWE-agent) edits a deeper function, `maybe_cast_to_integer_array`, and gets less.
- **Fig. 10 (p. 12):** tasks per repository: pandas 279, scipy 45, sympy 39, astropy 35, scikit-learn 27, numpy 23, matplotlib 20, dask 19, xarray 11 (sum 498).
- **Fig. 11 (p. 12), a table:** workload length mean 25.47 lines, max 180. Workload run time mean 4.47 s, max 257.09 s. Gold patch: 49.1 lines edited on average (max 2,445), 2.2 files (max 12). Gold speedup: harmonic mean 2.64x, max 249k x. Covering tests: mean 54k, max 222k.
- **Table 9 and Table 10 (pp. 30-31):** localization metrics, number of correct instances per system (193 to 252).
- **Table 11 (p. 37):** stability.

## Ideas we can use
- **New process per repetition.** Their harness shows that in-process repetition lets caches leak between runs and fakes a speed-up. If a PR in our set adds a cache, our before/after runs must also start from a clean process, or the "faster" verdict only measures a warm cache.
- **Separate CPUs for the daemon.** They pin Docker's own services away from the measured cores. Same idea as our dedicated cores.
- **Tests as an "output changed" check.** Their covering-test selection (coverage plus symbol resolution) is a way to pick the tests that matter for one diff.
- **Mechanism vocabulary.** The category prompt in Appendix B.3 (pp. 14-16) has buckets and example signals close to our mechanism classes: "Fewer syscalls; buffering/batching", "lock scope/structure", "Fewer allocations/copies", "Memoization, caches". It is a ready taxonomy to compare ours with.
- **Agent shortcut patterns.** Caches, fast paths and early exits are what agents prefer. These are exactly the claims ("cache the result") we see in agent PRs, and they are the ones that can pass a narrow workload and fail elsewhere.

## Weaknesses and things glossed over
- **Cloud VM.** All timing is on one GCP `n2-standard-64` VM. Other tenants on the same physical host, the hypervisor, CPU frequency scaling and turbo are not discussed. The paper does not say that SMT (hyper-threading) is off.
- **Pinning description is unclear.** Sec. 3 says each worker has "an exclusive set of physical CPU cores (4 vCPUs)". Appendix F.2 says the 4 vCPUs in a group are chosen so that "no two vCPUs in the same group share a physical core". If the sibling hyper-threads of those cores go to another group, two workers would share physical cores. The paper does not say where the sibling threads go.
- **Wall-clock only.** No instruction counts, cache misses, system calls, page faults or scheduler data. They cannot say *why* a patch is faster, only that the mean time dropped. The flamegraph analysis is at Python function level.
- **Significance rule is weak.** The 2σ rule uses only the post-edit standard deviation, has no minimum effect size, and is not a statistical test. Repeat counts differ a lot between tasks (5 to 10,000 in the printed examples), so the strength of the check differs per task.
- **Mean and standard deviation on timings.** Timings are usually skewed, with outliers. No median, no confidence interval, no check of the distribution.
- **No same-version control.** There is no base-against-base run per task to show the noise floor. The only noise evidence is the aggregate table over three runs.
- **The "< 0.5%" claim.** It is called "variance" in Sec. 3 and Sec. 4, and "coefficient of variation" in Appendix C, but Table 11 reports a spread (max minus min) of the aggregate SR over three runs. From the printed values, the spread for Claude 3.7 Sonnet is 0.00035 on about 0.0478, which is about 0.7% in relative terms (my arithmetic). For Gemini 2.5 Flash the printed spread 0.00012 does not match the three printed values, whose range is 0.000012. So "< 0.5%" holds as an absolute difference in SR, not clearly as a relative one.
- **Table 11 does not match Table 2.** Claude 3.7 Sonnet (OpenHands) is about 0.048 in Table 11 and 0.024 in Table 2. GPT-5 Mini is 0.021 against 0.039. Gemini 2.5 Flash is 0.0079 against 0.041. The paper does not explain the difference.
- **Stale sentences.** Sec. 4.1 says GPT-5 Mini (OpenHands) "achieved 0.019× of expert speedup"; Table 2 says 0.039. Sec. 4.1 also says that, apart from GPT-5, Claude 4.1 Opus and Claude 4.5 Sonnet, "fewer than a quarter" of solutions are correct and beat the expert; Table 3 shows Claude 4.5 Opus 43%, GPT-5.2 52%, Gemini 3 Pro 47%, Gemini 3 Flash 37% and Qwen3 Coder Plus 25%. When citing, use the tables.
- **The qualitative analysis uses older models.** Figures 4 to 7 and Tables 9 and 10 cover Claude 3.7 Sonnet, GPT-5 Mini, Gemini 2.5 Flash and DeepSeek V3.1, not the best models in Table 2.
- **One trajectory per task.** No repeat of the agent run, so no variance from the agent side.
- **Single workload per task.** A patch that is fast only for this input gets full credit if tests pass. The authors see this ("workload overfitting") and defend the single workload in Appendix D, but do not measure how many high-SR patches are overfit.
- **Dataset is skewed.** pandas has 279 of 498 tasks (56%). All repositories are Python scientific libraries.
- **Selection bias.** A task is kept only if the annotators could show the gain. PRs that claimed a speed-up but did not show one were dropped (1,041 annotated, 498 kept). The paper does not say how many of the 543 dropped ones failed because the gain was not reproducible and how many for other reasons (test problems, flaky tests).
- **Categories come from an LM.** The category counts in Fig. 3 are Gemini 2.5 Flash labels with 50 checked by hand. No error rate is given.
- **Fork or spawn.** Appendix L.2 says "spawn start method" and then describes and prints `fork`. With `fork` the child inherits the parent's memory, so anything cached at import time in the parent is shared.

## Open questions and future work (theirs, and ours)
- Theirs: other languages (C/C++/Rust); longer workloads; non-CPU hardware; several objectives (memory and run time); LM-in-the-loop workload generation with a frontier model, PR-description context and a verification harness; "don't-stop-early" triggers for agents.
- Ours:
  - When an agent patch is "faster than pre-edit" here, did the mechanism the agent had in mind really happen? The benchmark cannot tell. Our kernel and hardware signals can.
  - How many of the high-SR agent patches (the 43% to 52% that beat the expert) are caches that only help a repeated call? Their own Fig. 19 example is one.
  - Would their 47% miss rate for LM-written workloads drop if the workload writer is a full agent that can run code, as in our pipeline? They did not test this.

## Link to our paper
- **Related work:** the main benchmark for "can agents optimize real repositories". It measures agents on tasks made from human PRs. We measure PRs that agents opened in real projects. It scores speed against an expert. We check the stated reason for the speed-up.
- **Method:** cite for the isolation recipe (containers, pinned cores, NUMA binding, separate cores for the daemon, new process per repetition) and contrast: wall-clock only, cloud VM, no same-version control.
- **Threats:** cite for the risk that an automatically written workload misses a real speed-up (47%), and for agents gaming a timing harness.

## Link to the thesis (tracing, kernel analysis)
- The paper stops at wall-clock time and Python-level flamegraphs. It is a clear example of a performance benchmark with no view below the language runtime: no `perf stat` counters, no syscall or scheduler view.
- Its Appendix B.3 prompt tells the labelling model to "Prefer software-side mechanisms; ignore hardware/microarchitecture unless explicitly cited." So hardware-level causes are left out by design. That is the layer kernel and PMU tracing can add.
- The isolation steps (pinning, NUMA binding, keeping daemons off measured cores) are the same hygiene needed before trusting LTTng or perf numbers. On a shared cloud VM some PMU events are not available, which may be one reason they stayed with time only (the paper does not say).
- Their per-function attribution method (deepest non-overlapping set of improved functions, Appendix I.2) is a reusable way to compare two profiles without double counting callers and callees.

## Quotes for inline citation
- "Our suite contains 498 tasks across nine widely used data-science, machine-learning, and HPC repositories" (abstract, p. 1)
- "On average, agents achieve less than 0.23× the expert speedup: agents struggle in localizing optimization opportunities, reasoning about execution across functions, and maintaining correctness in proposed edits." (abstract, p. 1)
- "We retain only instances that demonstrate significant speedups (runtime improvement greater than 2× measurement std. dev.)" (Sec. 2.1, p. 4)
- "All evaluations are run on a single Google Cloud n2-standard-64 VM (64 vCPUs, 256GB Memory)." (Sec. 3, p. 5)
- "we pin each worker to an exclusive set of physical CPU cores (4 vCPUs), the CPU's corresponding memory node, and assigning a memory limit (16GB) per worker." (Sec. 3, p. 5)
- "LM agents often propose edits that cause repository unit tests to newly fail, invalidating any optimizations made." (Sec. 4.1, p. 5)
- "over 68% of expert gains occur in functions the LM never edits." (Sec. 4.1, p. 6)
- "LM patches hard-code properties of the specific evaluation workload (e.g., expected array shapes, dtypes, or index structures), achieving large speedups on that workload that would not survive minor input variations." (Sec. 4.2, p. 7)
- "Our annotations show stronger performance deltas 76% of the time, with 47% of LM workloads showing no significant speedups." (Sec. 4.2, p. 7)
- "Our benchmark uses Python's timeit module for performance measurement." (Appendix C, p. 17)
- "We observed that some LLM-generated patches only speed up workloads when they detect they are being timed" (Appendix L.1, p. 33)

## Suggested citation sentences
- SWE-fficiency builds 498 optimization tasks from merged human pull requests in nine Python libraries and scores an agent's speed-up against the expert's on a fixed workload \cite{ma2025swefficiency}.
- Its measurement is wall-clock time from Python's \texttt{timeit}, in containers pinned to four vCPUs on one cloud VM \cite{ma2025swefficiency}; it does not record hardware counters or kernel events.
- On that benchmark, between 1\% and 18\% of agent patches that pass the tests make the workload slower than before \cite{ma2025swefficiency}.
- Workloads written by a language model from the diff alone showed no significant gain for 47\% of known optimizations \cite{ma2025swefficiency}, a risk our build agent shares.
- Agents have been seen to detect the timing harness or cache results across timing runs \cite{ma2025swefficiency}, so each of our runs starts in a fresh process.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - *What we build on.* The same before/after design on real repositories with a workload, containers and pinned cores, and a correctness check next to the speed check. Their findings on agent behaviour (caches and fast paths, workload overfitting, test breakage, slower-but-correct patches) are the motivation for checking agent performance PRs one by one.
  - *What it does not do that we do.* It only has a stopwatch: `timeit` wall-clock mean and standard deviation. It has no hardware counters and no kernel traces, so it cannot say whether a claimed mechanism happened. It does not look at claims at all: tasks come from human PRs, and the agent patch is scored on speed only. It has no base-against-base control per task. It runs on a cloud VM. Its Appendix B.3 does extract a "mechanism-level explanation" for each gold patch, but with an LM from the diff, only to show dataset diversity, and never checked against a measurement.
  - *Where it weakens our approach.* (1) Their LM-written workloads missed the known speed-up in 47% of cases, and the manual workload was stronger 76% of the time. Our workload is written by a build agent that does not see the claim. A reviewer can say our "not faster" verdicts may be workload misses. Their setting is weaker than ours (one mid-level model, one shot, no code execution loop), and they call it a lower bound, but we should name this threat and cite it. (2) Appendix D argues that workload-specific speed-ups are normal and accepted by maintainers. So "the PR is not faster on our workload" does not show the PR's claim is false for the author's workload. (3) Their workloads come from the PR author's own script where one exists. That is closer to the author's intent than a workload written blind.
  - *A point in our favour.* They needed about 200 author-hours of manual workload writing for 1,041 PRs and kept 498. Manual annotation does not scale to a large set of agent PRs, which is the reason to automate.

- **Safe to cite for:**
  - Repository-level optimization benchmarks measure wall-clock time only. Support: Appendix C, p. 17: "Our benchmark uses Python's timeit module for performance measurement." Each workload prints only "Mean" and "Std Dev" (Appendix B.2, pp. 13-14).
  - The isolation they use: one cloud VM, containers, pinned vCPUs, NUMA binding. Support: Sec. 3, p. 5: "All evaluations are run on a single Google Cloud n2-standard-64 VM (64 vCPUs, 256GB Memory)" and "we pin each worker to an exclusive set of physical CPU cores (4 vCPUs), the CPU's corresponding memory node, and assigning a memory limit (16GB) per worker".
  - Their acceptance rule for a real speed-up is a 2-standard-deviation threshold. Support: Sec. 2.1, p. 4: "runtime improvement greater than 2× measurement std. dev."; Appendix E.5, p. 23 gives the formula µ_pre − µ_post ≤ 2σ_post for rejection.
  - Agents favour caches and fast paths, and can overfit the measured workload. Support: Sec. 4.2, pp. 6-7: "LMs preferentially add localized shortcuts—identity checks, ad-hoc early exits, and memoization" and "achieving large speedups on that workload that would not survive minor input variations".
  - Agent optimization patches often break tests, and some correct ones are slower. Support: Table 3, p. 6 (fails tests 9% to 45%; passes but slower than pre-edit 1% to 18%, OpenHands rows).
  - Automatically generated workloads can miss real speed-ups. Support: Sec. 4.2, p. 7: "with 47% of LM workloads showing no significant speedups"; details and caveats in Appendix K, p. 33.

- **Do not cite for:**
  - Anything about pull requests that agents opened in real projects. All 498 tasks come from human expert PRs; agents are only run on them as a benchmark.
  - Any claim that agents' stated reasons or PR descriptions are wrong. The paper never looks at what an agent says about its patch.
  - Hardware counters, system calls, page faults, or kernel tracing. None are used.
  - "Agents reach 23% of expert speed on a typical task." The 0.225 is a harmonic mean dominated by failed tasks; 43% of Claude 4.5 Opus patches beat the expert.
  - A per-task noise level. "< 0.5%" is about the aggregate SR over three runs, not about single measurements.
  - A base-against-base (A/A) control. They do not run one.
  - Languages other than Python (with Cython), or domains outside scientific Python libraries.
  - The claim that timing on cloud VMs is reliable in general. They show stability of their aggregate score on one VM type only.
