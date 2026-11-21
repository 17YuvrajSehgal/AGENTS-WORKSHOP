# EffiBench: Benchmarking the Efficiency of Automatically Generated Code
- **Authors:** Dong Huang, Yuhao Qing (equal contribution; The University of Hong Kong), Weiyi Shang (University of Waterloo), Heming Cui (The University of Hong Kong; Shanghai AI Laboratory), Jie M. Zhang (King's College London, corresponding author)
- **Venue / year / status:** NeurIPS 2024, Track on Datasets and Benchmarks (footer of p. 1), peer-reviewed. The PDF is arXiv:2402.02037v6, dated 10 May 2025. 42 pages: main text pp. 1-10, references pp. 11-17, appendix pp. 18-40, checklist pp. 41-42.
- **PDF:** `related-papers/huang2024effibench_2402.02037.pdf`
- **Cite key:** huang2024effibench
- **BibTeX-style reference:** Dong Huang, Yuhao Qing, Weiyi Shang, Heming Cui, and Jie M. Zhang. 2024. EffiBench: Benchmarking the Efficiency of Automatically Generated Code. In 38th Conference on Neural Information Processing Systems (NeurIPS 2024), Track on Datasets and Benchmarks. arXiv:2402.02037.

## In short
EffiBench is a benchmark of 1,000 Python LeetCode problems for measuring how efficient LLM-generated code is, not only whether it is correct. Each problem has a human-written "canonical" solution and 100 generated tests. The authors run the correct outputs of 42 LLMs and compare execution time and memory with the canonical solution. Every model is slower on average. GPT-4's code takes 3.12 times the execution time of the canonical solutions on average, and 13.89 times in the worst case. Efficiency is measured by wall time and memory on one real server; the paper gives few details on how.

## Problem and motivation
- Code-generation benchmarks (HumanEval, MBPP, APPS, DS-1000) check correctness only (Section 1, p. 1).
- Two correct programs for the same task can differ a lot in cost. Figure 1 (p. 2): for "merge two sorted arrays", Copilot produced concatenation plus bubble sort, O((n+m)^2); GPT-4 produced a linear merge, O(n+m).
- Existing benchmarks are bad for efficiency: tasks are small, most are not efficiency-critical, and they have few and small tests (p. 2-3).
- Stated motivation: speed, memory, and "green computing and sustainability".

## Background / key terms (explain each term simply)
- **Canonical solution:** the reference answer for a problem. Here it is a top-starred human solution from the LeetCode discussion forum.
- **pass@1:** share of problems where the model's first answer passes all tests.
- **ET (Execution Time):** average time in seconds for a model's correct programs to run all tests of a problem.
- **NET (Normalized Execution Time):** time of the generated code divided by time of the canonical solution, computed per problem and then averaged. Above 1 means slower than the canonical solution.
- **MU (Max Memory Usage):** average peak memory in MB.
- **NMU (Normalized Max Memory Usage):** peak memory divided by the canonical solution's peak memory, averaged over problems.
- **TMU (Total Memory Usage):** area under the memory-over-time curve, in MB*s. It grows if the program uses more memory or runs longer.
- **NTMU (Normalized Total Memory Usage):** TMU divided by the canonical solution's TMU, averaged over problems.
- **"NET>5" columns:** percent of correct programs whose normalized value is above 5.
- **"max NET" columns:** the single worst normalized value among a model's correct programs.
- **Test case generator:** a Python script, written by GPT-3.5-turbo for each problem, that creates random inputs and uses the canonical solution to compute the expected outputs.
- **Efficiency-critical problem:** the authors' term for a problem where the choice of algorithm matters. They select by LeetCode topic tag.

## Method and setup
- **Problem collection (Section 3.1, p. 4):** all problems tagged "LeetCode" on HuggingFace; remove duplicates; remove problems with interview frequency below 40%. This gives 2,605 candidates. Keep those with one of 11 algorithm topic tags. This gives 1,146.
- **Canonical solutions (Section 3.2):** top-starred solutions from the LeetCode Discussion Forum, manually fixed to run outside LeetCode. Problems needing LeetCode-only packages were dropped. Final set: 1,000 problems.
- **Tests (Section 3.3):** GPT-3.5-turbo writes a generator per problem. 100 tests per problem are shipped and used in the paper. Direct LLM-written test cases were rejected because their accuracy was under 15% (Table 31).
- **Dataset statistics (Table 1, p. 4):** 171 easy, 589 medium, 240 hard. Average description 212.0 words. Average canonical solution 14.6 lines. Problems per topic: greedy 243, DP 277, backtracking 48, divide and conquer 21, DFS 108, BFS 86, binary search 148, two pointers 105, sliding window 70, bit manipulation 102, sorting 238 (a problem can have two topics).
- **Machine (Section 5, p. 6):** "an edge server with an Intel Xeon Platinum 8336C CPU with 128 cores, 8 * NVIDIA A100-SXM GPUs, and a total memory capacity of 2.0TiB". Timeout 10 s per code execution. Default Python is 3.11.2 (Table 26).
- **Models (p. 7):** 42 in total, 35 open-source (CodeLlama, DeepSeek-Coder, OpenCodeInterpreter, Phind, StarCoder, WizardCoder, XwinCoder, Yi and others) and 7 closed-source (gpt-3.5-turbo-0301, -0613, -1106, gpt-4, gpt-4-turbo-preview, claude-3-haiku, claude-3-sonnet).
- **Prompt:** MBPP style: task description, examples with explanations, and assertions that fix the function signature.
- **What is measured:** for each model, only the code that passes all tests is executed for efficiency. So each model is measured on a different set of problems (the ones it solved).
- **Repetitions and statistics:** each measurement appears to be taken once. One model (gpt-3.5-turbo-0301) was re-run five times (Table 25). One Kruskal-Wallis test is mentioned for environment stability (p. 6). No confidence intervals and no tests on model differences.
- **How time and memory are measured:** the paper does not say. No tool, no timer, no sampling interval for the memory profile, no CPU pinning, no statement about other load on the 128-core server, no statement on whether programs run one at a time.

## Section-by-section notes

### 1. Introduction (pp. 1-3)
- Claims EffiBench is "the first benchmark specifically designed to assess the efficiency of code generated by LLMs" (p. 3). Footnote 5 notes Mercury as parallel work.
- Headline: GPT-4 code has on average 3.12 times the execution time of canonical solutions; worst cases 13.89× (time) and 43.92× (total memory usage).
- Second headline: higher pass@1 does not mean more efficient code. GPT-4-turbo-preview has higher pass@1 than GPT-4 but lower efficiency.
- Also releases an "efficiency testing framework" usable with other benchmarks.

### 2. Related work (pp. 3-4)
- Lists code LLMs and code-generation benchmarks. Cites PIE (Shypula et al.) among studies showing LLM code is less efficient than canonical solutions.
- Footnote 4 separates it from Liu et al. (EvalPerf): they focus on reliable performance-exercising tasks; EffiBench on the dataset pipeline and benchmarking.

### 3. Benchmark construction (pp. 4-6)
- As in "Method and setup".
- Footnote 6: normalized metrics are computed per task and then averaged ("task level"), not as total generated time over total canonical time. The second variant is in the appendix (NET*).

### 4. Benchmark statistics (p. 6)
- Table 2 compares with HumanEval (164 problems, 7.7 tests on average), MBPP (974; 3.0), APPS (10,000; 13.2), DSP (1,119; 2.1), DS-1000 (1,000; 1.6). EffiBench: 1,000 problems, 100 tests by default, solutions of 14.6 lines on average.

### 5. Evaluation (pp. 6-10)
- The authors expect absolute values to differ across environments and claim the ranking of models is "rather stable (p-value >> 0.05 based on Kruskal-Wallis H tests)" (p. 6). See Weaknesses: Table 26 does not support this well.
- **5.1 Open-source models (Table 3):** all are slower than canonical on average. "Most efficient" is StarCoder2-15B: NET 2.59, NMU 1.71, NTMU 4.83. But its pass@1 is 0.7%, so this is based on about 7 problems out of 1,000.
- The authors say open-source models with lower pass@1 tend to look more efficient because they only solve easy problems (p. 7).
- 23 of 35 open-source models have pass@1 below 10% (p. 9).
- **5.1 Closed-source models (Table 3):** NET from 3.12 (gpt-4) to 3.40 (gpt-3.5-turbo-1106). NMU 1.91 to 1.94. NTMU 6.36 to 7.24. pass@1 from 42.3% to 65.4% (gpt-4-turbo-preview).
- GPT-3.5 versions: pass@1 rises 42.3% → 49.3% from 0301 to 1106, while NET rises 3.18 → 3.40. The paper reads this as "more correct, not more efficient". Part of this is that the newer model solves more and harder problems.
- **5.2 Identical problems (Table 4):** 210 problems solved by all seven closed-source models. NET: 3.10, 3.05, 3.07 (GPT-3.5 0301, 0613, 1106), 3.06 (gpt-4), 3.10 (gpt-4-turbo-preview), 3.27 (haiku), 3.20 (sonnet). NMU is 1.90 for all seven. The paper concludes GPT models beat Claude models and GPT-4 is best on most metrics. On mean NET, gpt-3.5-turbo-0613 (3.05) is slightly lower than gpt-4 (3.06). The gaps are in the second decimal.
- Open-source models are left out of 5.2 because there is no problem that all of them solved.
- **5.3 By algorithm (Table 5; the text calls it "Table 7"):** GPT-3.5-turbo-0301 is worst on DP (NTMU 7.73) and best on DFS (5.68) and binary search (5.83). Claude-3-sonnet on backtracking: NET 4.92, NTMU 11.28, 13.3% of solutions above 5× time.
- **5.4 Worst cases (Table 6):** the 10 worst GPT-3.5-turbo-0301 programs for each metric, labelled by algorithm by hand. NET: bit manipulation 3, backtracking 2, sliding window 2, DP 1, BFS 1, two pointers 1. NTMU: DP 4, greedy 3, backtracking 1, BFS 1, bit manipulation 1.
- Figure 2 case: for "k inverse pairs", the model fills a full (n+1)×(k+1) table; the canonical solution keeps one array and a prefix sum, O(n×k) → O(k) space. Reported ratio: 70.62× total memory usage.

### 6. Conclusion and future work (p. 10)
- Future: other languages (C++, Java, JS, Go). A HuggingFace server lets others evaluate on the same hardware.

### A.1 to A.3 Limitations, improvements, broader impact (pp. 18-19)
- **Language:** Python only.
- **Dataset scope:** "EffiBench focuses solely on LeetCode problems, which primarily involve algorithmic challenges. This excludes real-world applications and other coding scenarios that might necessitate different efficiency considerations."
- **Environment dependency:** "The efficiency results obtained using EffiBench may vary across different hardware and software environments." Their fix is to offer one shared server, not to control noise.

### A.6 / A.9 Other benchmarks (Tables 8 and 10, pp. 21, 26)
- The same framework on HumanEvalPlus and MBPPPlus. On HumanEvalPlus the generated code is about as fast as the canonical solution: NET between 0.71 and 1.08 for the 17 models listed.
- Footnote 12: original HumanEval and MBPP have fewer than 10 tests per task, "which can lead to highly random efficiency testing results due to the rapid execution of the code." So the authors know that short runs give noisy timings.
- MBPPPlus has outliers: deepseek-coder-1.3b-instruct NMU 6.05 and NTMU 89.12; starcoder2-7b NET 8.63.

### A.7 / A.10 Distribution of normalized metrics (Tables 9 and 11, pp. 22, 28)
- For four models (the three GPT-3.5 versions and gpt-4) no correct program is faster than the canonical solution: "NET<1" is 0.00% and the minimum NET is 1.09 to 1.11. For gpt-4-turbo-preview it is 0.15%, for the two Claude models 0.23%.
- Memory: 1.38% to 2.13% of programs have NMU below 1.
- The authors' explanation: training data from GitHub is correct but not optimized (p. 22).

### A.8 Worst-case illustrations (pp. 23-25)
- BFS (Figure 4): model uses a list as a queue with `pop(0)`; canonical uses two-way BFS with deques. 50.1 MB*s against 7.5 MB*s.
- Backtracking (Figure 5): model enumerates all splits and validates late; canonical prunes early. 34.36× total memory usage.

### A.12 / A.19 Dataset-level normalization (Tables 12 and 23, pp. 28, 33)
- NET* = sum of generated times / sum of canonical times. All values go down: gpt-3.5-turbo-0301 NET 3.18 → NET* 2.92; NMU 1.91 → 1.61; NTMU 6.50 → 2.52.
- Meaning: the metric definition changes the headline. NTMU more than halves, so the per-task average is driven by tasks with small canonical values or by a few extreme ratios.

### A.14 / A.21 Number of tests (Tables 13 and 24, pp. 29, 33)
- gpt-3.5-turbo-0301 with 10, 100, 1,000 tests: NET 2.36, 3.18, 3.95. NTMU 4.75, 6.50, 10.08. max NET 4.13, 27.70, 66.68. Share with NTMU above 5: 41.9%, 89.1%, 66.6%.
- Meaning: the measured "inefficiency" depends strongly on the workload size. With 10 tests the model looks 2.4× slower, with 1,000 tests almost 4× slower.
- The text says TMU rises "from 8.84 MB*s to 340.51 MB*s" when going "from 100 to 1,000" tests. In the table 8.84 is the value for 10 tests; for 100 tests it is 19.06.

### A.15 / A.23 Randomness (Tables 14, 15, 25, 26, pp. 29-30, 33-34)
- **Seed (five runs of gpt-3.5-turbo-0301, same environment):** mean NET 3.18 (std 0.00), ET 0.39 s (std 0.00), NMU 1.91 (std 0.00), NTMU 6.52 (std 0.10), max NET 27.67 (std 0.13, range 27.42 to 27.78). The mean values are stable. Note these are averages over all solved problems; the paper gives no per-problem run-to-run variation.
- **Environment (Table 26):** same code, canonical and generated both re-run, on Xeon 8336C with Python 3.11.2, 3.10.14, 3.9.19, 3.8.19, and on "4216 CPU" and "4116 CPU" with Python 3.11.2.
  - gpt-3.5-turbo-0301: NET 3.18, 2.77, 2.40, 2.36, 2.32, 2.27. Share with NTMU above 5: 89.1%, 73.7%, 29.6%, 24.6%, 16.1%, 11.8%.
  - gpt-4: NET 3.12, 2.71, 2.67, 2.69, 2.70, 2.70.
  - NMU stays at 1.91 to 1.94 everywhere.
  - The model with the lowest NET changes: gpt-4 (3.12) on the default; claude-3-sonnet (2.70) on Python 3.10.14; gpt-3.5-turbo-0301 (2.40) on Python 3.9.19; gpt-3.5-turbo-0613 (2.29) on Python 3.8.19; gpt-3.5-turbo-0301 on the two other CPUs (2.32 and 2.27).
  - The authors describe this as "the efficiency changed slightly".
  - Meaning: the *ratio* to the canonical solution moves by up to about 0.9 (3.18 to 2.27) only from a different Python version or CPU. This is larger than every difference between closed-source models in Table 3 (3.12 to 3.40).

### A.16 / A.24 Overhead (Tables 16 and 30)
- Efficiency testing of one closed-source model takes 17 s to 37 s.

### A.17 / A.25 Why not complexity classes (pp. 30-31, 34-36)
- Same big-O does not mean same speed; manual labelling is subjective; complexity predictors are inaccurate. So they measure time and memory directly.

### A.22 Difficulty (Tables 27-29, pp. 35-36)
- Results split by easy, medium, hard. Many open-source cells for hard problems rest on one problem (pass@1 0.1%), and some rows are empty.

### A.26 / A.27 Tests (Table 31, Figure 9, pp. 37, 40)
- Accuracy of test cases written directly by LLMs: 5.9% (gpt-3.5-turbo-0301), 8.2% (0613), 14.3% (gpt-4-turbo), 13.7% (gpt-4).
- Figure 9 shows a generator: random strings of length 0 to 10 for "longest substring without repeating characters". Inputs this small cannot separate a slow algorithm from a fast one.

## Key results (with numbers) and what they mean
- **GPT-4: NET 3.12, max NET 13.89, NTMU 6.36, max NTMU 43.92 (Table 3)** -> on the problems it solves, GPT-4 code needs on average about 3 times the time of the reference in this setup. One program needs about 14 times.
- **All 42 models have mean NET between 2.59 and 3.44 and mean NMU between 1.71 and 2.08 (Table 3)** -> the benchmark barely separates models. Weak and strong models land on almost the same value.
- **StarCoder2-15B is "most efficient" (NET 2.59) with pass@1 0.7%** -> this is about 7 problems. It is not evidence that the model writes efficient code.
- **pass@1 and efficiency do not move together (GPT-4-turbo-preview: 65.4% and NET 3.19; GPT-4: 50.8% and NET 3.12)** -> correctness benchmarks do not tell you about speed. But the problem sets differ, so the comparison is not clean.
- **On 210 common problems NET is 3.05 to 3.27 and NMU is 1.90 for all (Table 4)** -> when the problem set is fixed, the models are nearly identical.
- **Almost no correct program beats the canonical solution (NET<1: 0.00% to 0.23%, Table 11), and the minimum NET is about 1.09** -> either canonical solutions are always better, or the measurement adds a constant offset to generated code. See Weaknesses.
- **On HumanEvalPlus NET is 0.71 to 1.08 (Table 8)** -> with other canonical solutions the same framework shows no gap. The gap is specific to this dataset.
- **Python version or CPU alone moves NET from 3.18 to 2.27 for the same code (Table 26)** -> a ratio between two programs is not stable across environments.
- **10 → 1,000 tests moves NET from 2.36 to 3.95 (Table 24)** -> the workload decides the size of the measured gap.
- **Per-task mean against dataset-level ratio: NTMU 6.50 against 2.52 (Table 23)** -> the aggregation rule decides the headline number.

## Tables and figures
- **Figure 1 (p. 2):** Copilot (bubble sort) against GPT-4 (linear merge) for merging sorted arrays. Code accessed January 15, 2024.
- **Table 1 (p. 4):** problems per algorithm and difficulty, description length, solution length.
- **Table 2 (p. 7):** comparison with other benchmarks.
- **Table 3 (p. 8):** main results, 42 models × 12 efficiency columns plus pass@1. Read NET, NMU, NTMU first; "max" columns are single worst cases.
- **Table 4 (p. 8):** seven closed-source models on the 210 common problems.
- **Table 5 (p. 9):** GPT-3.5-turbo-0301, GPT-4, Claude-3-sonnet by algorithm.
- **Table 6 (p. 10):** algorithm labels of the 10 worst programs per metric.
- **Figure 2 (p. 22):** DP case, 2-D table against rolling array.
- **Figures 4-5 (pp. 24-25):** BFS and backtracking cases.
- **Tables 8/10:** HumanEvalPlus and MBPPPlus.
- **Tables 9/11:** min, share below 1, share above 1, max for each normalized metric.
- **Tables 12/23:** task-level against dataset-level normalization.
- **Tables 13/24:** 10, 100, 1,000 tests.
- **Tables 14/25:** five repeated executions.
- **Tables 15/26:** six environments.
- **Tables 17-22:** per-algorithm results for the other closed-source models.
- **Tables 27-29:** by difficulty.
- **Table 31:** accuracy of LLM-written tests.
- **Figures 7 and 8 (pp. 38-39):** histograms of NET, NMU, NTMU for GPT-3.5-turbo-0301. The two figures are identical. NET: almost all programs sit in the lowest buckets starting at 1.09, with one at 27.43-27.70. NMU: most programs sit at the top of the range, near 2.04-2.05, with a few near 1.0 and one near 0.5. Exact bar heights are unclear in the text extraction.
- **Figure 9 (p. 40):** a test case generator.
- **Numbering:** the appendix content is printed twice (A.4 to A.17 and again A.18 to A.27) with different table numbers. The text refers to the second numbering (Tables 23-31) and sometimes to the wrong table.

## Ideas we can use
- **Contrast for our motivation.** EffiBench reports "X times slower" from wall time and memory alone, on puzzle code, with no explanation of what the machine did. We add the "why" (counters, kernel events) and work on real PRs.
- **Their Table 26 is evidence for controlled measurement.** The same code gives NET 3.18 or 2.27 depending on Python version and CPU. This supports our choice to measure before and after in one fixed environment and never compare across machines.
- **Their footnote 12** supports sizing workloads so that runs are long enough: very short runs give "highly random" results.
- **Workload sensitivity (Table 24)** supports our care with the workload: the measured gap depends on input size. This is a reason to have the workload written by an agent that does not see the claim.
- **TMU (memory × time)** is a simple way to report a memory cost that also reflects duration. We could report something similar from our traces when a PR trades memory for speed (a hidden cost).
- **Case studies (Figures 2, 4, 5)** are mechanism explanations in words ("full matrix against rolling array", "list.pop(0) against deque"). They are argued from reading the code, not measured. This is exactly the gap we fill.

## Weaknesses and things glossed over
- **The measurement procedure is not described.** No timing tool, no memory sampler or sampling interval, no number of repetitions, no warm-up, no CPU pinning, no isolation on a shared 128-core server with 8 GPUs.
- **A near-constant ratio suggests a systematic offset (my reading; the paper does not discuss it).** Mean NET is about 3 and mean NMU about 1.9 for every model, every algorithm and every difficulty. No GPT program is faster than the canonical one, and the minimum NET is about 1.09. Most NMU values sit near 2.0. If the gaps came from algorithm choice, weak and strong models, and easy and hard problems, would not all give the same ratio. On HumanEvalPlus the same framework gives NET near 1. One possible explanation is that generated code and canonical code are not run under the same harness or overhead. I could not confirm this from the paper.
- **Runs are short.** ET is 0.27 s to 0.56 s for all tests of a problem (Tables 3 and 24) and peak memory is about 50 to 60 MB for most models. At this scale, interpreter start-up and imports can be a large share of both numbers. The paper does not separate them.
- **Different problems per model.** Efficiency is computed on the problems each model solved. Models with pass@1 of 0.4% to 2% are scored on a handful of problems. The "most efficient open-source model" claim rests on about 7 problems.
- **No statistics.** Differences of 0.01 to 0.3 in NET are read as rankings without any interval or test.
- **The environment-stability claim is weak.** The text says rankings are "rather stable" with a Kruskal-Wallis p-value far above 0.05 (p. 6). The paper does not show the test. Table 26 shows the best model changing across environments, and a large p-value from such a test does not show that rankings are the same.
- **"GPT-4 is the most efficient" does not hold across environments** (Table 26) and is a tie on common problems (Table 4).
- **Canonical solutions are assumed optimal.** They are top-starred forum posts. The abstract says they obtain "the SOTA efficiency on the LeetCode solution leaderboard", but Section 3.2 only says "top-starred". Stars measure popularity. No check that they are the fastest.
- **Tests come from a GPT-3.5-written generator** and expected outputs come from the canonical solution. The paper says generators were fixed by hand but gives no validation numbers. The example generator (Figure 9) makes inputs of length 0 to 10, which do not stress efficiency.
- **"Efficiency-critical" is only a topic-tag filter.** No check that the problems or the tests actually separate efficient from inefficient solutions.
- **Section 5.4 over-reads Table 6.** The text says most of the worst programs are DP and backtracking. For NET the largest group is bit manipulation (3 of 10); DP plus backtracking is 3 of 10 for NET and 2 of 10 for NMU. Only for NTMU do they reach 5 of 10.
- **Inconsistent numbers.** Table 11 gives max NTMU 47.0 for gpt-3.5-turbo-0301 and 15.3 for gpt-4, while Table 3 gives 70.62 and 43.92. Table 11's max NET values equal the full-set values in Table 3 although the text says it follows the 210-problem setup of Table 4. Section A.12 says "9 open- and closed-source models" but Table 23 has 7. Section 5.3 and A.8 point to "Table 7" for other tables.
- **Explanations are not tested.** "Models learn non-optimal solutions because they are more frequent in training data" (p. 7, p. 9, p. 22) is a guess. No experiment.
- **No threats-to-validity section.** Limitations are three short paragraphs in A.1.
- **TMU depends on time,** so NTMU is close to NET × NMU in most rows (for example gpt-4: 3.12 × 1.92 ≈ 6.0 against 6.36; my arithmetic). It adds little independent information.

## Open questions and future work (theirs, and ours)
- Theirs: more languages (C++, Java, JS, Go); more diverse datasets beyond LeetCode; a standard server for all evaluations.
- Ours: Would their gaps survive a controlled setup (pinned cores, repeated runs, A/A control with the canonical solution against itself)? What is the A/A ratio in their harness? They never run it. For real PRs, is "N times slower" explained by an algorithm change, as their case studies argue, or by system effects (I/O, allocation, page faults)?

## Link to our paper
- **Introduction / Related work:** cite as a main example of efficiency benchmarks for LLM-generated code. It establishes that correct LLM code is often slower than a good human solution, on algorithm puzzles, in Python.
- **Gap statement:** it measures outcome only (time, memory). It does not ask why the code is slower, and it has no notion of a claim to check. It says itself that it "excludes real-world applications".
- **Method / Threats:** its Table 26 and Limitations paragraph are citations for "efficiency numbers change with hardware and software environment", which is why we fix the machine and add an A/A control.
- **Hidden costs:** its memory metrics show that time alone is not the full cost. Our "hidden costs" verdict follows the same idea with kernel-level signals.

## Link to the thesis (tracing, kernel analysis)
- Not a tracing paper. It uses no hardware counters, no system-call data, and no kernel information.
- Its three case studies explain slowness by reading code. A trace or counter profile could confirm them: `pop(0)` on a list should show as more instructions and memory copies; a full DP table should show as more page faults and a higher resident set.
- Its memory-over-time profile (TMU) is a coarse user-space version of what kernel memory events (`mm_page_alloc`, page-fault tracepoints, RSS statistics) give exactly.
- The environment table (Python version changes the ratio) is a reminder that the runtime is part of the measured system. A trace would show whether the change is in the interpreter or in the code under test.

## Quotes for inline citation
- "the efficiency of the code generated by LLMs is generally worse than the efficiency of human-written canonical solutions." (p. 1, abstract)
- "GPT-4 generated code has an average 3.12 times execution time that of the human-written canonical solutions." (p. 1, abstract)
- "a high pass@1 score (indicating the LLM's ability to generate correct code on the first attempt) does not necessarily translate to more efficient code." (p. 3)
- "we do expect that with different environments, the absolute values of the efficiency metrics would be different." (p. 6)
- "This excludes real-world applications and other coding scenarios that might necessitate different efficiency considerations." (p. 18, A.1)
- "The efficiency results obtained using EffiBench may vary across different hardware and software environments." (p. 18, A.1)
- "HumanEval and MBPP datasets have a limited number of test cases (fewer than 10) for each task, which can lead to highly random efficiency testing results due to the rapid execution of the code." (p. 21, footnote 12)
- "identical time and space complexity annotations do not guarantee equivalent performance across different implementations." (p. 30, A.17)

## Suggested citation sentences
- Benchmarks such as EffiBench show that correct LLM-generated code is often slower than a good human solution: GPT-4's solutions took on average 3.12 times the execution time of the reference solutions on 1,000 LeetCode problems \cite{huang2024effibench}.
- These benchmarks report execution time and memory only, on self-contained algorithm problems; EffiBench itself notes that this "excludes real-world applications" \cite{huang2024effibench}.
- Efficiency numbers depend on the environment: in EffiBench the same code gave a normalized execution time of 3.18 or 2.27 depending on the Python version and CPU \cite{huang2024effibench}. We therefore compare the two versions of each PR on one fixed machine.
- A model that is more often correct is not more efficient \cite{huang2024effibench}, so performance has to be measured, not assumed.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It shows the problem we start from: LLM-written code can be correct and still slow, and correctness scores do not reveal it. We build on this as motivation.
  - It stops at the stopwatch (and a memory meter). It measures time and memory of a whole run and compares with a reference. It does not look at what the machine did, and it has no claims to verify. We go below this level with hardware counters and kernel traces, and we check the reason the agent gave.
  - It studies generated *solutions* to LeetCode problems in Python. We study *pull requests* by coding agents in real repositories, with a before and an after version of the same code.
  - **Where it pushes against us:** not much. One point: its five-run check (Table 25) shows very stable *average* numbers on an uncontrolled server (std 0.00 for mean NET). A reader could use this to say that noise control is not needed. This is weak, because the averages are over hundreds of problems, per-problem noise is never shown, and Table 26 shows large shifts from the environment. A second point: its results suggest that algorithm-level gaps are large (about 3×), while kernel-level effects may be small in comparison. That is true for puzzle code; it does not tell us about real PRs, where claimed mechanisms are often I/O, caching or locking.

- **Safe to cite for:**
  - LLM-generated code that passes tests is often less efficient than a human reference solution. Abstract, p. 1: "the efficiency of the code generated by LLMs is generally worse than the efficiency of human-written canonical solutions." Table 3: mean NET above 2.5 for all 42 models.
  - The size of the gap for a strong model in their setup. Abstract and Table 3: GPT-4 average 3.12× execution time, worst case 13.89×, worst total memory usage 43.92×.
  - Correctness and efficiency are different things. Section 1, p. 3: "a high pass@1 score ... does not necessarily translate to more efficient code." Table 3: gpt-4-turbo-preview 65.4% pass@1 and NET 3.19; gpt-4 50.8% and NET 3.12.
  - Existing efficiency benchmarks use self-contained algorithm tasks and not real software. A.1, p. 18: "EffiBench focuses solely on LeetCode problems ... This excludes real-world applications and other coding scenarios that might necessitate different efficiency considerations."
  - Efficiency measurements depend on hardware and software environment. A.1, p. 18: "The efficiency results obtained using EffiBench may vary across different hardware and software environments." Table 26: NET of the same gpt-3.5-turbo-0301 code is 3.18 on Python 3.11.2 and 2.36 on Python 3.8.19 on the same CPU.
  - Very short runs give unreliable timings. Footnote 12, p. 21: "can lead to highly random efficiency testing results due to the rapid execution of the code."

- **Do not cite for:**
  - Anything about coding agents, pull requests, or performance claims. The paper tests single-shot code generation.
  - Why LLM code is slow. The training-data explanation is the authors' guess ("We suspect that...").
  - Rankings of models by efficiency ("GPT-4 writes the most efficient code"). The differences are tiny, untested, and change across environments in their own Table 26.
  - "LLM code is 3 times slower than human code" as a general fact. It holds for this dataset and harness; on HumanEvalPlus their own framework shows about 1×.
  - Measurement noise being negligible. The five-run table reports only averages for one model.
  - Rigorous measurement practice. The paper does not describe repetitions, pinning, timers or statistical tests.
  - Hardware counters, system calls, energy, or kernel behaviour. None are measured. "Green computing" is motivation only; no energy is measured.
  - "Canonical solutions are optimal." They are top-starred forum solutions; optimality is not verified.
