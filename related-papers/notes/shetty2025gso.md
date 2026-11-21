# GSO: Challenging Software Optimization Tasks for Evaluating SWE-Agents
- **Authors:** Manish Shetty, Naman Jain, Jinjian Liu, Vijay Kethanaboyina, Koushik Sen, Ion Stoica (all UC Berkeley)
- **Venue / year / status:** Our copy is arXiv:2505.23671v3 [cs.SE], 24 Oct 2025, and the first page is marked "Preprint." The PDF itself names no venue. (The FormulaCode paper's reference list cites it as NeurIPS 2025, Datasets and Benchmarks Track. Check this before putting a venue in refs.bib.)
- **PDF:** related-papers/shetty2025gso_2505.23671.pdf
- **Cite key:** shetty2025gso
- **BibTeX-style reference:** Manish Shetty, Naman Jain, Jinjian Liu, Vijay Kethanaboyina, Koushik Sen, and Ion Stoica. 2025. GSO: Challenging Software Optimization Tasks for Evaluating SWE-Agents. arXiv:2505.23671v3.

## In short
GSO ("Global Software Optimization") is a benchmark of 102 tasks from 10 open-source codebases. In each task an agent gets a codebase and one performance test, and must write a patch that makes the code faster while keeping the output the same. The patch is not scored by its raw speed-up. It is scored by whether it reaches at least 95% of the speed of the real human commit that optimized the same code, on the same machine. The best model (Claude-4.0 in OpenHands) succeeds on 4.9% of tasks with one attempt. The paper also describes how agents fail: they avoid C/C++ code, make "lazy" changes such as compiler flags or input-specific fast paths, and misdiagnose the bottleneck.

## Problem and motivation
- Existing code benchmarks are either small puzzles (HumanEval, LiveCodeBench) or repository-level bug fixing (SWE-bench). The bug-fixing ones do not measure runtime. The runtime ones (EvalPerf, ECCO, PIE) are not repository-level (Fig. 2 left, p. 2).
- GitHub issues are ambiguous task descriptions. A performance test is a precise one: it fixes both the workload and the expected output.
- Question (p. 2): "Can LLM agents aid in the development of high-performance software?"

## Background / key terms (explain each term simply)
- **SWE-Agent:** an LLM that works in a loop with tools (file editor, shell) on a real repository.
- **Performance test:** a Python script that builds a workload (`setup`), runs the code under test (`experiment`), times it, and compares the result with a stored reference (`check_equivalence`). In GSO these scripts are written by an LLM, not by the project maintainers.
- **Ground-truth / human commit (C_h):** the real commit in the repository history that made the code faster. It is the target.
- **Speedup on test i:** s_i = T(C1, i) / T(C2, i), the runtime in one code state divided by the runtime in the other.
- **Harmonic mean:** n divided by the sum of 1/s_i. One slow test pulls it down strongly; one very fast test barely lifts it.
- **Opt_p:** a task is solved if S(C_h, C_a) >= p and the patch is correct. C_a is the code with the agent's patch. So the agent is compared with the human commit, not with the original code.
- **Opt@K:** fraction of tasks where at least one of K attempts is solved, with p = 0.95.
- **Rollout / trajectory:** one full attempt of the agent on a task.
- **Backtranslated plan:** a text plan that an LLM writes from the human diff, then given to the agent as a hint.
- **Reward hacking:** passing the test without really solving the task (for example caching the answer).

## Method and setup
- **Dataset:** 102 tasks, 10 codebases, 5 languages, 8 domains (Fig. 3 right, p. 3). Per codebase (Table 1, p. 15): numpy 36, pandas 34, pillow-simd 7, pillow 4, pydantic 4, tornado 4, tokenizers 4, transformers 4, datasets 3, llama-cpp 2. So 70 of 102 tasks are numpy or pandas.
- **Tests per task:** average 12.45, maximum 20 (Fig. 3 right).
- **Human commits:** Fig. 3 right gives 250 lines on average, 110 median, 2278 max, 3.9 files on average, 58.8% touch non-Python code. Table 2 (p. 15), which counts only non-test lines, gives min 7, median 108, mean 231.5, max 1,477. The two do not match (see Weaknesses).
- **Pipeline (Section 2.2, p. 3-4):**
  - Stage I: an LLM judge plus code-change heuristics pick performance-related commits and collect context (files, commit message, linked issues, PRs, endpoints).
  - Stage II: an LLM writes performance tests from that context ("execution-based rejection sampling"). Tests are run before and after the commit. "We retain commits showing significant performance improvements across multiple test cases." (p. 4). The paper gives no number for "significant" and no statistical test.
  - Final manual curation: remove weak tests and reproducibility problems, pick for diversity.
  - Yield (Table 3, p. 16): 32.5% of commits retained with plain test generation, 43.3% with commit context.
- **How performance is measured (this is what we compare with):**
  - **Workload:** the LLM-generated performance tests. The example test (Appendix C.3, p. 17-18) downloads Pride and Prejudice from Project Gutenberg, adds 1000 random strings with fixed seed 42, and calls `np.char.replace` three times. The setup is not timed. The timed part is `timeit.timeit(lambda: experiment(data), number=1)`, so one call per measurement.
  - **Number of runs:** the main text does not say. The only evidence is a log line in Example 2 (p. 27): "Running test /pyperf_test_2.py 5 times... Iteration 1/5", with `timeout 300s` per test run. Appendix C.2 says repetition was moved out of the test scripts ("perform runs outside the test scripts instead", p. 17). How the repeated runs are combined (mean, median, minimum) is not stated.
  - **Machine:** "All tasks are run on a single Google Cloud n2-standard-64 VM (64 vCPUs, 256 GB Memory)." (Section 3, p. 5). Each task runs in a Docker container.
  - **Isolation:** the paper does not say anything about CPU pinning, how many tasks run at the same time on the VM, frequency scaling, warm-up, or a noise floor. It only requires that "each task gets sufficent resources" (p. 5, spelling as in the paper).
  - **What counts as a speed-up:** not a raw speed-up. Success = harmonic-mean speedup of the agent's code against the human commit's code is at least 0.95, and all equivalence assertions pass, and the patch applies cleanly (Sections 2.1 and 2.3).
  - **Correctness:** assertions in the test compare the output with a stored reference from the original code.
  - **Statistics:** confidence intervals on Opt@K "following established methods for pass@K metrics" (p. 4). No statistical test on the timings themselves.
- **Agent:** OpenHands CodeActAgent-v0.35.0, file editor and bash. 3-hour limit per task, 20-minute timeout per step (p. 5).
- **Models:** GPT-4o, o3-mini, o4-mini, Claude-3.5-v2 Sonnet (called Claude-3.6), Claude-3.7, Claude-4.0. For Opt@1: 3 rollouts at temperature 0.1. For scaling experiments: o4-mini and Claude-3.5-v2 only, temperature 0.8.
- **Prompt (Appendix G.1, p. 22):** shows the test script, asks to make it faster, to keep the repository "functionally equivalent to the original", and "Do not overoptimize for just the specific inputs". It tells the agent to write its own timing script and rerun it.

## Section-by-section notes

### 1. Introduction (p. 1-3)
- Fig. 1: one task = codebase + generated performance test + human commit as target.
- Fig. 2 right: o4-mini scores 73.3% on LiveCodeBench, 56.8% on SWE-bench Verified, 3.6% on GSO.
- Claim: gold patches have "4-15x" more edited lines than earlier benchmarks.
- Three failure modes named: low-level languages, lazy optimizations, wrong localization.

### 2. GSO (p. 3-5)
- 2.1 Task: input is codebase, build script, one performance test. Output is a patch. Evaluation runs "all associated performance tests". So the agent sees one test in the prompt but is scored on the whole set (average 12.45). The paper does not spell this out in one sentence; it follows from Sections 2.1, 5.2 and the prompt.
- 2.3 Metric. Two problems they want to solve: tasks have different baseline speed, and tests inside one task have very different speed-ups. Geometric mean can be gamed: speedups of [0.1, 1000] give 10. They use the harmonic mean instead.
- They call Opt@K "machine-independent" because both sides (human commit and agent patch) are timed on the same machine.
- 2.4 Features. Speedup is kept as a "secondary metric". They argue a continuous speedup also helps against contamination: a patch much faster than the human one cannot be a memorized copy.

### 3. Evaluation setup (p. 5)
- Covered in Method above.

### 4. Experiments and results (p. 5-7)
- 4.1 Opt@1 (Fig. 4 left): GPT-4o 0.0%, o3-mini 1.3%, o4-mini 3.6%, Claude-3.6 4.6%, Claude-3.7 3.8%, Claude-4 4.9%.
- With p = 0 (only correctness): Claude-4.0 about 70%, o4-mini about 45% (text, p. 6). So many patches are correct but too slow.
- 4.2 Scaling (Fig. 5). More rollouts help more than more steps. At 50 steps and 8 rollouts: o4-mini 8.82, Claude-3.5-v2 11.76. At 400 steps and 1 rollout: 1.96 and 4.95. Opt@10: Claude-3.6 15.7%, o4-mini 12.7%.
- 4.3 With ground-truth plans (Fig. 6, o4-mini): Opt@1 goes from 3.5% to 5.7%, Opt@5 from 9.9% to 18.6%. Knowing the idea is not enough; writing the low-level code is still hard.

### 5. Qualitative analysis (p. 7-9)
- Failures are labelled by an LLM judge (o4-mini) that reads the trajectory, the human diff and the success flag (Appendix I, p. 25).
- 5.1 Low-level code. o4-mini Opt@10: 21.4% on the 42 Python-only tasks, 4.0% on the 60 non-Python tasks. o4-mini leaves out needed C/C++ changes about 40% of the time (Fig. 8: c 22.1%, cpp 19.1% omitted). Claude-3.5-v2 adds C changes (9.2%) when the human commit was Python only.
- 5.2 Lazy optimizations. o4-mini is "lazy" in nearly 30% of trajectories (Fig. 7: 29.0%). In over 60% of incorrect trajectories the agent edited at most 15% of the lines the human edited. Examples: adding `-O3` to a project that already builds optimized; a fast path only for the input shape in the test; overriding a function in `__init__.py`.
- 5.3 Compute. With budgets of 200+ steps, 75% of trajectories end before 100 steps. o4-mini explores too much (25.7% "explore-heavy"), Claude-3.5-v2 edits too early (27.2% "exploit-heavy").
- 5.4 Misdiagnosis. Example: an agent parallelizes NumPy's `char.count`, ignores the GIL and process start-up cost, and makes it slower. Fig. 7: "Misdiagnosed Bottlenecks" is 13.2% of Claude-3.6 trajectories and 6.6% of o4-mini trajectories.
- 5.5 Successes. Some are simpler than the human commit (a fast path in Tornado). Some are better: TIFF frame counting goes from O(n^2) to O(n) by reading only IFD headers (Example 11).

### 6. Related work (p. 9-10)
- On measurement in earlier work: "PIE simulates hardware-level runtime for C++ programs while EvalPerf employs hardware counters for precise performance measurement. While providing reliability, these approaches unfortunatly do not scale to larger codebases considered in our work." (p. 10, spelling as in the paper). They give no evidence for "do not scale".

### 7. Limitations and conclusion (p. 10)
- 102 tasks is small, so results have variance.
- Reward hacking exists; tests currently catch it, they say.
- Only runtime is measured. Memory, maintainability and idiomatic style are not.
- Contamination: argued to be low risk because scores are low.

### Appendix (p. 15-37)
- B: Tables 1 and 2 (dataset composition, line counts).
- C.2 (p. 16-17): reward hacking found during curation. Some human commits could be matched by simply caching outputs (`@lru_cache`). Tests that visibly repeated the same call led models to "simply cached the output of the function calls!". Fix: remove the hints and repeat outside the test script. Tests with narrow inputs were extended or the task was removed.
- D (p. 19): raw speedups differ across three machines (16 cores/128 GB, 32 cores/256 GB, 64 cores/512 GB), "due to differences in CPUs, cache sizes, memory bandwidth, etc." They say Opt@K is "unaffected", but show no Opt@K numbers per machine.
- E (p. 19): Opt@1 under other aggregations (Fig. 11). Arithmetic mean: 8.5, 17.5, 25.0, 15.8, 25.7, 37.3 (GPT-4o to Claude-4). Geometric mean: 0.0, 1.3, 5.9, 5.9, 6.2, 9.8. Risk-adjusted geometric mean: 0.0, 1.0, 2.6, 3.3, 2.6, 3.9. (Read from small bar labels on the page image.)
- F (p. 20-21): test pass rate and "has speedup over base" (Fig. 12), patch size ratio (Fig. 13), speedups of solved tasks (Fig. 14).
- G, H, I: prompts. J (p. 26-37): 12 worked examples.

## Key results (with numbers) and what they mean
- Opt@1 is at most 4.9% -> with one attempt, agents almost never reach the speed of the human commit.
- Opt_0@1 is about 70% (Claude-4.0) and 45% (o4-mini) -> most of the gap is speed, not broken code.
- Fig. 12 (o4-mini, K=1): 43.7% of problems pass the tests and 24.9% show some speedup over the original code; Claude-3.5-v2: 37.2% and 13.8%. -> "less than 5%" does not mean agents cannot speed code up. It means they rarely match the expert.
- Aggregation changes the headline a lot: Claude-4 gets 37.3% with arithmetic mean, 9.8% with geometric mean, 4.9% with harmonic mean -> the choice of mean is a result in itself. A few very large per-test speedups can hide slow-downs.
- 21.4% (Python-only) against 4.0% (non-Python) at Opt@10 for o4-mini -> the hard part is native code.
- Plans raise Opt@5 from 9.9% to 18.6% -> diagnosis explains part of the gap, not all of it.
- Human commit speedups (Fig. 9b, log scale): the box is roughly between 1.5x and 5x, with outliers above 10^4 -> selected tasks have large effects, far above normal timing noise. This is why a weak timing protocol may be good enough for them.

## Tables and figures
- **Fig. 1 (p. 1):** task layout. Table inside shows per-test reference time vs model time.
- **Fig. 2 (p. 2):** feature table; lines-of-code boxplots; o4-mini 73.3 / 56.8 / 3.6.
- **Fig. 3 (p. 3):** optimization concepts; dataset statistics.
- **Fig. 4 (p. 6):** Opt@1 bars with error bars; Opt_p@1 curve from p=0 to 1. Read: curves fall fast between p=0 and p=0.1, so many correct patches bring almost no speed.
- **Fig. 5 (p. 6):** heatmap steps x rollouts; Opt@K up to K=10.
- **Fig. 6 (p. 7):** with and without plans.
- **Fig. 7 (p. 7):** failure categories. Claude-3.6: wrong abstraction level 30.1%, exploit-heavy 27.2%, lazy 16.6%, misdiagnosed 13.2%, less impactful 10.0%, explore-heavy 3.0%. o4-mini: lazy 29.0%, explore-heavy 25.7%, wrong abstraction level 25.1%, exploit-heavy 6.9%, less impactful 6.8%, misdiagnosed 6.6%.
- **Fig. 8 (p. 8):** file extensions added or omitted against the human commit.
- **Table 1, 2 (p. 15), Table 3 (p. 16):** composition, line counts, yield.
- **Fig. 9 (p. 16):** lines edited and speedups of human commits (log scale).
- **Fig. 10 (p. 19):** speedups on three machines. The y axis is labelled "Geometric Mean Speedup", although the paper's metric is the harmonic mean.
- **Fig. 11 (p. 19):** other aggregation metrics.
- **Fig. 12-14 (p. 20-21):** pass rates, patch size, speedups of solved tasks (one Claude-3.5-v2 patch is above 10^3 x).

## Ideas we can use
- **Harmonic mean, or report the worst workload.** If a PR is measured on several workloads, one big win must not hide a slow-down. Their [0.1, 1000] example is a clean way to explain this.
- **Compare both versions on the same machine.** They justify relative comparison by Appendix D. Our before/after design on fixed cores is the same idea, with stronger control.
- **Workload hints can be gamed.** Their caching story (C.2) is a warning for our build agent: a workload that repeats the same call can reward memoization. Our "output changed" verdict and kernel signals can separate "less work" from "cached answer".
- **Failure taxonomy as hypotheses.** "Compiler-flag twiddling", "input-specific fast path", "misdiagnosed bottleneck" are exactly the cases where a claimed mechanism and the measured effect can disagree. We can check whether the AIDev PRs show the same patterns with measured evidence.
- **Equivalence check design:** store reference output from the base version and assert on it after the change.

## Weaknesses and things glossed over
- **Timing protocol is thin.** The number of repetitions is not in the method text (only "5 times" in one log). The combination rule is not given. The example test times one call (`number=1`). No warm-up, no pinning, no noise floor, no A/A run (base against base) is reported.
- **Shared cloud VM.** One n2-standard-64 for all tasks. The paper does not say whether tasks run in parallel on it. Docker gives packaging, not performance isolation.
- **"Significant performance improvements" has no definition.** No threshold, no test, for which commits enter the benchmark.
- **A fixed 0.95 threshold with no noise estimate.** A patch that is truly equal to the human commit can land at 0.94 or 0.96 by chance. The paper does not report how often a human commit matches itself.
- **"Machine-independent" is claimed, not shown.** Appendix D shows speedups differ by machine and says Opt@K does not, but gives no Opt@K per machine. Which patches and how many were used in Fig. 10 is not stated.
- **Workloads are LLM-written.** They are not maintainer benchmarks. Manual curation is described in general words only: no count of removed candidates, no number of reviewers.
- **Only wall time.** No hardware counters, no kernel view, no memory. They say counter-based measurement does "not scale to larger codebases" without evidence.
- **Failure analysis is by an LLM judge** (o4-mini judging also its own trajectories). No human agreement number. "Misdiagnosed bottleneck" is therefore a reading of the transcript, not a measurement.
- **Inconsistent numbers and labels:**
  - Lines per human commit: Fig. 3 says 250 avg / 110 median / 2278 max; Table 2 says 231.5 mean / 108 median / 1,477 max; Section 2.4 says "averaging 108 lines" (108 is the median in Table 2).
  - Section 5.4 says Example F.7 (char.count) is Claude-3.5-v2; the example itself (p. 32) is headed "Model: O4-Mini".
  - The text cites "Example F.1 ... F.12", but the examples are in Appendix J.
  - Section 4.3 says Opt@5 "improves by just 9%"; Fig. 6 shows 9.9% to 18.6%, which is 8.7 points.
  - The text says p = 1 checks whether the patch "is identical to the human commit" (p. 6). By the definition it only means equal or better harmonic-mean speed.
- **Concentration:** 70 of 102 tasks are numpy or pandas. Opt@1 uses 3 rollouts at temperature 0.1; scaling uses temperature 0.8, so the two settings are not directly comparable.
- **Small numbers:** 4.9% of 102 is about 5 tasks.

## Open questions and future work (theirs, and ours)
- Theirs: grow the benchmark; ways to stop reward hacking; metrics beyond runtime (memory, maintainability, idiomatic code); better scaffolds that use the step budget.
- Ours:
  - When an agent "misdiagnoses the bottleneck", can a kernel or hardware signal show it directly, without an LLM judge?
  - How many "successful" fast-path patches would show unchanged work in instruction counts on a second workload?
  - What is the A/A spread of GSO-style tests on a shared 64-vCPU VM, and how many 0.95 decisions fall inside it?

## Link to our paper
- **Introduction / Related work:** cite as a repository-level optimization benchmark that scores agents by runtime against a human commit. It scores "is it as fast as the expert", not "is the stated reason true".
- **Method:** cite for the harmonic-mean argument and for relative, same-machine comparison. Contrast: we measure untraced time plus counters and kernel traces on dedicated cores with an A/A control; GSO uses wall time of LLM-written tests on one cloud VM.
- **Discussion:** their failure modes (compiler flags, input-specific fast paths, misdiagnosis) motivate checking the mechanism, not only the time.
- **Threats:** our build agent writes the workload, like their LLM-written tests. Cite C.2 for the risk of weak or gameable workloads.

## Link to the thesis (tracing, kernel analysis)
- Not a tracing paper. Timing is the only signal.
- Their example successes map to kernel-visible mechanisms: the TIFF case (Example 11) replaces decoding every frame with a few `seek` and small `read` calls, which would show as a change in read syscalls and bytes read. The Tornado case (Example 8) is a direct write to the file descriptor that skips buffering. The pandas IndexEngine case (Example 12) removes repeated `np.resize`, which would show in page faults and memory allocation.
- The misdiagnosis case (parallelizing `char.count`) is a futex / process-creation story: tracing would show process start-up cost and lock waits growing.
- Their statement that hardware counters "do not scale to larger codebases" is a claim our thesis work can test.

## Quotes for inline citation
- "Rather than naively measuring machine-dependent speedups, we assess whether model-generated patches can consistently match or exceed the performance of human expert optimizations." (p. 2)
- "A model achieving speedups of [0.1, 1000] across two tests yields a geometric mean of 10, despite degrading performance on one test." (p. 4)
- "All tasks are run on a single Google Cloud n2-standard-64 VM (64 vCPUs, 256 GB Memory)." (p. 5)
- "Agents misdiagnose performance bottlenecks, implementing ineffective optimizations." (p. 9)
- "Agents frequently implement narrow optimizations targeting only the specific input patterns present in given performance test." (p. 8)
- "This approach is ineffective since the Pillow project already uses optimized builds by default." (p. 8)
- "Our work focuses on improving the runtime performance of the code, but practical software development also requires other metrics such as memory usage, maintainability, and idiomaticity." (p. 10)
- "As shown the speedups achieved can be quite different across machines, due to differences in CPUs, cache sizes, memory bandwidth, etc." (p. 19)

## Suggested citation sentences
- GSO scores an agent's patch by whether it reaches 95% of the speed of the human commit on generated performance tests, and the best model succeeds on fewer than 5% of 102 tasks in one attempt \cite{shetty2025gso}.
- Benchmarks such as GSO measure wall-clock time only and do not check why a patch is faster \cite{shetty2025gso}; we add the kernel and hardware signals that a claimed mechanism must move.
- Agents asked to optimize code often make shallow changes, such as compiler flags or fast paths for the test input, and misdiagnose the bottleneck \cite{shetty2025gso}.
- A geometric mean over workloads can hide a slow-down behind one large win \cite{shetty2025gso}, so we report each workload separately.

## Connection to "Below the Stopwatch"
- **How it relates:**
  - Same topic, different question. GSO asks whether an agent can match an expert's speed on a given test. We ask whether a PR that an agent already opened is faster and whether its stated mechanism happened. GSO has no notion of a claimed mechanism.
  - We build on two of its points: compare both versions on the same machine, and do not let one large speed-up hide a slow-down.
  - What it does not do and we do: hardware counters, kernel traces, dedicated cores, an A/A control, and a verdict about the mechanism. GSO's method text gives no repetition count and no noise estimate.
  - Where it pushes against us: (1) it says counter-based measurement does "not scale to larger codebases" (p. 10), with no evidence; we should be ready to answer this. (2) It found that LLM-written workloads can be weak and can be gamed, and needed manual curation. Our build agent also writes the workload, so the same doubt applies to us. (3) Its tasks have large effects (median human speedup of a few x), where simple timing is enough; a reviewer may ask whether our heavier method is needed for large effects.
- **Safe to cite for:**
  - GSO has 102 tasks from 10 codebases and scores patches against the human commit with a 0.95 threshold. Section 2.3 and Fig. 3: "we denote Opt@K as the Opt0.95@K metric that uses a 95% threshold for evaluating success against the human target" (p. 5).
  - Leading agents reach under 5% Opt@1. Abstract: "leading SWE-Agents struggle significantly, achieving less than 5% success rate".
  - Raw speedups depend on the machine. Appendix D, p. 19: "the speedups achieved can be quite different across machines".
  - Agents make lazy optimizations and misdiagnose bottlenecks. Section 5.2 and 5.4; p. 2: "agents resort to superficial optimizations (“lazy optimizations”) like compiler flag manipulation or input-specific fast-paths insertion".
  - GSO measures runtime only. Section 7, p. 10: "Our work focuses on improving the runtime performance of the code".
  - Workloads that repeat the same call invite caching hacks. Appendix C.2, p. 17: "this led to models generating patches that simply cached the output of the function calls!"
- **Do not cite for:**
  - Any statement about pull requests that agents opened in the wild, or about what agents claim in PR text. GSO has no PRs and no claims; it uses human commits as targets.
  - "Agents cannot make code faster." Fig. 12 shows 24.9% (o4-mini) and 13.8% (Claude-3.5-v2) of problems have some speedup over the base at K=1. The under-5% number is about matching the expert.
  - A rigorous timing protocol. Do not write "GSO runs each test 5 times": this appears only in one log line, not in the method.
  - Use of hardware counters or tracing. GSO uses neither.
  - "Opt@K is proven machine-independent." The paper states it and shows only speedup variation, not Opt@K per machine.
  - Measured misdiagnosis rates as ground truth. The failure labels come from an LLM judge with no reported human check.
