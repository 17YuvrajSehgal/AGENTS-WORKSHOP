# Are Performance-Optimization Benchmarks Reliably Measuring Coding Agents?
- **Authors:** Zhi Chen, Zhensu Sun (corresponding author), David Lo, Lingxiao Jiang (Singapore Management University), Yuling Shi (Shanghai Jiao Tong University)
- **Venue / year / status:** arXiv:2607.01211v2 [cs.SE], 16 Jul 2026. 12 pages in IEEE conference style. The paper does not name a venue and does not say whether it is peer-reviewed. Treat it as a preprint.
- **PDF:** related-papers/chen2026benchmarks_2607.01211.pdf
- **Cite key:** chen2026benchmarks
- **BibTeX-style reference:** Zhi Chen, Zhensu Sun, Yuling Shi, David Lo, and Lingxiao Jiang. 2026. Are Performance-Optimization Benchmarks Reliably Measuring Coding Agents? arXiv:2607.01211v2.

## In short
The paper audits three repository-level benchmarks that score coding agents on making code faster: GSO, SWE-Perf and SWE-fficiency. It does three checks. First, it re-runs the official "reference" patch (the human optimization each task is built on) for all 740 tasks on four Google Cloud machine types, three rounds each. The reference patch still meets the benchmark's own validity rule in every one of the 12 replays for only 39/102 GSO tasks, 11/140 SWE-Perf tasks and 411/498 SWE-fficiency tasks. SWE-Perf fails because its reference patches change runtime by almost nothing (median -0.03%). Second, it shows the leaderboard order depends on the scoring formula: the same eight submissions disagree on 9 of 28 pairwise orders between GSO and SWE-fficiency, and in SWE-fficiency the ten worst tasks carry 58.5% to 82.8% of a submission's score. Third, looking across 10 public submissions, at least one already matches or beats the reference patch on 384 of 450 valid tasks.

## Problem and motivation
- Functional benchmarks (SWE-bench) ask a yes/no question: do the tests pass. That answer is "usually reproducible".
- Performance benchmarks compare runtimes, and runtimes are noisy. They "fluctuate across runs because of CPU scheduling, cache state, memory bandwidth contention, and machine-level microarchitectural effects" (Sec. I, citing Georges et al., Mytkowicz et al., Kalibera and Jones).
- The benchmarks already use repeated trials, outlier filtering and statistical tests. The question is whether that is enough to trust their scores.
- Leaderboard scores are being used "as evidence of coding-agent progress". If the tasks or the scoring are unstable, that evidence is weak.

## Background / key terms (explain each term simply)
- **Repository-level benchmark:** the agent edits a real project, not a single function.
- **Base program / base commit:** the code before the optimization.
- **Reference patch:** the official human (expert) optimization for the task. Agents are compared against it.
- **Workload:** the test or script that is timed to see whether the code got faster.
- **Replay:** running the base and the reference patch again on another machine and recomputing the result.
- **Faster-than-base:** the reference patch has lower runtime than the base in every round on every machine (T_ref < T_base).
- **Original-rule valid / replay-valid:** the replay still meets the rule the benchmark authors used to accept the task. In this paper a task is replay-valid only if this holds in all 12 machine-round replays.
- **Runtime change (%):** 1/s - 1 for a speedup s. Negative means faster. A 1.20x speedup is a -16.7% runtime change.
- **Std./signal:** the spread of the 12 replays of a task divided by the size of the runtime change. Above 1 means the noise is bigger than the effect.
- **Submission:** one agent configuration on a leaderboard. All public ones here are the OpenHands scaffold with one model.
- **OPT@1 (GSO):** percent of tasks where the submitted patch is correct and at least as fast as the reference. All or nothing per task.
- **SpeedUp Ratio, SR (SWE-fficiency):** speedup of the submitted patch divided by speedup of the reference patch. 1 means equal to the reference.
- **Harmonic mean (HM):** N divided by the sum of 1/SR. It is pulled down hard by very small values.
- **Floor:** the smallest SR the formula allows. Officially 0.001, so one failed task adds 1000 to the denominator.
- **Pair flip:** two submissions whose order is different under two rankings. Eight submissions give 28 pairs.

## Method and setup
- **Benchmarks (Table I):** GSO (102 tasks, 10 repos, NeurIPS 2025, generated performance tests); SWE-Perf (140 tasks, 9 repos, ICML 2026, repository unit tests used as efficiency tests); SWE-fficiency (498 tasks, 9 repos, ICML 2026, annotated workload scripts). Total 740 tasks. Venues are as this paper prints them.
- **Selection criteria:** repository-level edits; runtime optimization with executable workloads; recent peer-reviewed benchmark papers.
- **Machines (Table II):** four Google Compute Engine types, all 64 vCPUs and 256 GB memory: n2-standard-64 (Intel Cascade Lake, 2019), n2d-standard-64 (AMD Milan, 2021), n4-standard-64 (Intel Emerald Rapids, 2024), n4d-standard-64 (AMD Turin, 2025). n2-standard-64 is the setup GSO and SWE-fficiency reported in their own papers.
- **Rounds:** three rounds per machine, so 12 machine-round replays per task.
- **What is reused:** official tasks, reference patches, selected tests and workload definitions. Latest public repository version before the data cutoff of April 30, 2026.
- **Original validity rules (Table III):**
  - GSO: each selected generated test passes correctness checks and keeps a speedup of at least 1.2x over base (above 1.1x for "low-test" fallback tasks).
  - SWE-Perf: each efficiency unit test passes on both commits; after 20 timing repetitions and IQR outlier filtering, the Mann-Whitney minimum-gain value must stay above delta_i > 0.05.
  - SWE-fficiency: workload and correctness guards run; base mean runtime minus patched mean runtime must be larger than twice the post-edit runtime standard deviation.
- **RQ2 data:** released per-task outputs of the eight public submissions that are on both the GSO and SWE-fficiency leaderboards. SWE-Perf is left out because it had no comparable public agent outputs.
- **RQ3 data:** 10 public submissions per task on the 450 replay-valid tasks (39 GSO + 411 SWE-fficiency). The paper does not list the 10 in the text.
- **RQ3.3 labelling:** the optimization categories of Peng et al. [34], [35], assigned by their script with GPT-5.5, one category per patch, with a manual sanity check.
- **Not stated:** whether cores were pinned, whether other jobs shared the VM, how many timing repetitions per replay for GSO and SWE-fficiency, kernel or OS version. Only wall-clock runtime is used. No hardware counters, no tracing.
- **Data:** https://github.com/chenzhi-cz/performance-optimization-benchmark-reliability

## Section-by-section notes

### I. Introduction
- States the three findings and the three contributions (replay of 740 reference patches; audit of leaderboard rankings; task-level look across public submissions).
- "Readers need to know which tasks have stable reference signals, how much the scoring rule amplifies extreme cases, and how the remaining unsolved tasks affect the submissions' scores."

### II. Study design
- RQ1: do official reference patches remain valid under cross-machine replay? Motivation: the benchmarks are "machine-agnostic", so the reference signal should survive "reasonable machine variation".
- RQ2: how do leaderboard scoring rules shape submission rankings?
- RQ3: do benchmark tasks remain hard for top submissions?

### III. RQ1: Cross-machine reference-patch validity
- "The goal is not to invent a stricter benchmark, but to test whether the original reference signal survives reasonable cross-machine variation."
- **RQ1.1 Evaluability (Table IV):** tasks that complete all three rounds, per machine (n2 / n2d / n4 / n4d): GSO 99 / 98 / 99 / 99 of 102, 4 not evaluable; SWE-Perf 138 on every machine of 140, 2 not evaluable; SWE-fficiency 498 on every machine, 0 not evaluable. GSO failures: one functional-equivalence failure, one missing external data, one image-decoding failure, one x86_64 CPU-instruction portability failure. SWE-Perf failures: missing dependencies in the evaluation image. All reported to maintainers.
- **RQ1.2 Validity (Fig. 1):** with the official task count as denominator:
  - GSO: 91/102 (89%) faster than base in all 12 replays; 39/102 (38%) original-rule valid.
  - SWE-Perf: 48/140 (34%) faster than base; 11/140 (8%) original-rule valid.
  - SWE-fficiency: 470/498 (94%) faster than base; 411/498 (83%) original-rule valid.
  - So in every benchmark some reference patches run slower than the base in at least one replay.
- **RQ1.3 Signal against variation (Table V):**
  - GSO (98 tasks): median runtime change -54.20%, median within-task std 3.81 pp, std./signal 0.07x.
  - SWE-Perf (138 tasks): median runtime change -0.03%, median std 1.41 pp, std./signal 43.23x.
  - SWE-fficiency (498 tasks): median runtime change -56.04%, median std 2.41 pp, std./signal 0.04x.
  - SWE-Perf has the smallest spread of the three. Its problem is that the effect is tiny. 101 of 138 SWE-Perf tasks have median changes within five percentage points of zero.
- **RQ1 summary:** likely cause is how the benchmark was built. SWE-Perf takes existing unit tests as efficiency checks and accepts gains above a 5% threshold. GSO and SWE-fficiency use workloads written to stress performance. Advice: check that workloads "stress the optimized path strongly enough" and that reference patches "have clear margins over runtime noise; otherwise, machine-level noise can be mistaken for a patch-level performance difference."

### IV. RQ2: Scoring rules and rankings
- **GSO rule:** OPT@1 = 100 x (reference-level successes) / N. One task is worth 0.98 points. No partial credit for a correct but slower-than-reference patch.
- **SWE-fficiency rule:** HM = N / sum of 1/max(SR, 0.001). A task with SR = 2 saves 0.5 denominator units; SR = 10 saves 0.9; the reward is capped below 1. A task with SR = 0.5 adds 1 unit; SR = 0.01 adds 99; the floor adds 999. Failed or incorrect patches are treated as no effective edit, which can put them far below the reference.
- **RQ2.1 (Tables VI, VII):** official ranks of the eight shared submissions differ. GSO order: Claude Opus 4.6 (41.18), GPT-5.2 (27.45), Claude Opus 4.5 (26.47), Gemini 3 Pro (18.63), Claude Sonnet 4.5 (14.71), Gemini 3 Flash (9.80), GPT-5 (6.86), Gemini 2.5 Pro (3.92). SWE-fficiency order: Claude Opus 4.5 (0.2250), GPT-5 (0.1571), Claude Opus 4.6 (0.1553), GPT-5.2 (0.1482), Claude Sonnet 4.5 (0.1162), Gemini 3 Flash (0.1056), Gemini 3 Pro (0.1024), Gemini 2.5 Pro (0.0313). GPT-5 moves five places (7th to 2nd).
  - Official GSO against official SWE-fficiency: Spearman 0.452, 9/28 pair flips, max rank move 5.
  - Both scored with the GSO rule: Spearman 0.762, 6/28 flips, max move 3.
  - Both scored with the SWE-fficiency rule: Spearman 0.238, 11/28 flips, max move 5.
  - So the scoring rule explains part of the disagreement, not all. The task sets differ too.
- **RQ2.2 (Fig. 3):** share of the SWE-fficiency score denominator carried by the worst tasks, across the eight submissions: worst 1 task 6.3% to 33.6%; worst 5 tasks 31.4% to 73.1%; worst 10 tasks 58.5% to 82.8%. Example: one task of Claude Opus 4.5 has raw SR 0.00134 and carries 33.6% of that submission's score weight. This is in a 498-task benchmark.
- **RQ2.3 (Table VIII):** raise the floor from 0.001 to 0.5, so one bad task costs at most one extra unit. Then 6 of 8 ranks move and 8/28 pairs flip. New order: Claude Opus 4.6 (HM 0.952), GPT-5.2 (0.944), Claude Opus 4.5 (0.904), Gemini 3 Pro (0.888), GPT-5 (0.867), Gemini 3 Flash (0.818), Claude Sonnet 4.5 (0.767), Gemini 2.5 Pro (0.613). Median SR for the top two is 1.006 and 1.004, with 258 and 259 of 498 tasks above the reference. The authors say: "The point is not that f = 0.5 is the right constant."
- The authors do not say severe slowdowns should be ignored: "Penalizing them is a reasonable benchmark choice. The issue is interpretability".

### V. RQ3: Do tasks remain hard?
- **RQ3.1 (Fig. 4):** over 10 public submissions on 450 replay-valid tasks: all 450 have a passing patch; 449 have a passing patch that beats the base; 384 (85.3%) have one that matches or beats the reference (GSO 30/39 = 76.9%, SWE-fficiency 354/411 = 86.1%). 66 tasks stay below reference: 9 GSO, 57 SWE-fficiency.
- **RQ3.2 (Fig. 5):** for the 66, the best public patch is correct on all, faster than base on 65. Median best patch reaches 85.3% of the reference speedup on GSO (needs 1.17x more) and 87.9% on SWE-fficiency (needs 1.14x more). SWE-fficiency bands: 27 tasks at 90-100%, 21 at 50-90%, 8 at 10-50%, 1 below 10%. GSO bands from the figure: 2 at 10-50%, 6 at 50-90%, and a thin 90-100% segment that is not labelled (it would be 1 to make 9). Behind these 66 tasks are 660 attempts: 160 fail functionality or validation, 3 do not complete, 46 pass correctness without improving runtime.
- **RQ3.3 (Table IX, Figs. 6-7):** does the best public patch use the same kind of optimization as the reference? Reference categories: Algorithm 31, Structure 16, Memory 12, Build 3, Control 3, Data struct. 1. Same category in 32/66 (Algorithm 21/31, Structure 7/16, Memory 3/12). Different or no visible production optimization in 34/66. Leaving out the two "no visible optimization" cases: same-category median 89.8% of reference speedup (1.12x remaining) against different-category 81.1% (1.23x remaining). But 16/32 same-category cases are still under 90%, and 11/32 different-category cases reach 90-100%. Authors' reading: agents "often find a useful optimization idea but do not apply it broadly or carefully enough to match the reference patch."

### VI. Discussion
- Benchmark users: do not read scores as direct labels of agent capability. "a reported optimization can be hard to distinguish from runtime noise." Reports should separate cross-machine verified tasks from unstable ones and show per-task score weight.
- Agent builders: little room is left if progress is counted only as "more tasks reach the reference".
- Benchmark designers: real performance work "usually starts earlier: engineers inspect profiles, flame graphs, traces, latency breakdowns, or dashboards, then choose which hot operation in a large codebase is worth changing". Future benchmarks should add "hotspot localization from profiles or traces", validation on workloads not fully visible during patch search, "and resource metrics beyond one runtime number". "CPU time, latency, allocation behavior, memory footprint, and regression risk all matter, and optimizing one can hurt another".

### VII. Threats to validity
- Internal: replays may be affected by implementation choices, hardware variation and artifact quality. The all-12 rule is conservative and "may undercount usable tasks".
- External: three benchmarks and specific leaderboard snapshots. The 10-submission analysis "is also a task-coverage proxy, not a newly engineered multi-agent workflow".
- Data: depends on released artifacts. SWE-Perf is excluded from RQ2 and RQ3.

### VIII. Related work and IX. Conclusion
- Lists function-level efficiency benchmarks (PIE, EffiBench, Mercury, ENAMEL, ECCO, EvalPerf, ACECode, COFFE and others) and repository-level ones (GSO, SWE-Perf, SWE-fficiency, PerfBench, PEACE, ISO-Bench, FormulaCode, CppPerf).
- Conclusion: next benchmarks should ask agents "to reason from performance symptoms or profiles, choose optimization targets, and validate runtime improvements together with memory, latency, and other resource costs."

## Key results (with numbers) and what they mean
- 39/102, 11/140, 411/498 tasks stay valid in all 12 replays -> even the human-written, hand-checked "gold" optimization often stops being a provable speedup when the machine changes. Timing alone on one machine is weak evidence that a patch is faster.
- 91/102, 48/140, 470/498 reference patches are faster than base in every replay -> the rest are slower than the unoptimized code at least once. For SWE-Perf that is 92 of 140 tasks.
- SWE-Perf median change -0.03% with 1.41 pp spread (std./signal 43.23x) -> the effect is far inside the noise. A benchmark built on such tasks mostly measures noise. The cause is not a noisy machine; it is an effect too small to measure with a stopwatch.
- GSO and SWE-fficiency median change about -54% and -56% with std./signal 0.07x and 0.04x -> large effects survive machine changes easily. The reliability problem is about small effects.
- 9/28 pairwise orders differ between two leaderboards for the same submissions -> "agent A is better at optimization than agent B" depends on which benchmark you read.
- Worst 10 of 498 tasks carry 58.5% to 82.8% of the score -> a SWE-fficiency score is mostly a count of catastrophic failures, not an average speedup.
- 384/450 tasks already solved to reference level by some submission; the rest reach a median 85-88% of the reference speedup -> finding some speedup is no longer hard for agents on these tasks. The open problem is how deep the speedup goes.
- 32/66 same category but still slower -> picking the right kind of optimization is not enough to get the full gain.

## Tables and figures
- **Table I (p. 2):** the three benchmarks, their scale, venue and what kind of test compares the commits.
- **Table II (p. 3):** the four machine profiles with CPU model and Google Cloud release year.
- **Table III (p. 3):** each benchmark's original validity rule. Read this before quoting "valid": the three rules are different, so the three fractions are not on one scale.
- **Fig. 1 (p. 3):** bars of official tasks, faster-than-base tasks and original-rule-valid tasks per benchmark, with percentages (GSO 100 / 89 / 38; SWE-Perf 100 / 34 / 8; SWE-fficiency 100 / 94 / 83).
- **Fig. 2 (p. 4):** distributions of reference-patch runtime change per machine and round. Read: SWE-Perf piles up at the 0% line; the other two are spread far to the left (large reductions). The paper does not discuss differences between the four machines in the text.
- **Table IV (p. 4):** evaluability counts per machine.
- **Table V (p. 5):** median runtime change, median std and their ratio. The 43.23x for SWE-Perf is presumably computed from unrounded values (1.41 / 0.03 would give 47).
- **Table VI (p. 6):** official ranks and scores of the eight shared submissions on both leaderboards.
- **Table VII (p. 6):** Spearman correlation, pair flips and max rank move for three scoring comparisons.
- **Fig. 3 (p. 7):** stacked bars of score weight of the worst 1, 5 and 10 tasks for each of the eight submissions.
- **Table VIII (p. 7):** ranks with floor 0.5, with official HM, new HM, median SR and number of tasks with SR > 1 (from 258 and 259 for the top two down to 38 for Gemini 2.5 Pro).
- **Fig. 4 (p. 8):** percent of replay-valid tasks where any of 10 runs is correct / beats base / matches reference.
- **Fig. 5 (p. 8):** the 66 below-reference tasks by how close the best public patch gets.
- **Table IX (p. 9):** reference optimization category against whether the best public patch has the same category.
- **Fig. 6 (p. 9):** speedup bands by category alignment. Same category (n=32): 4 at 10-50%, 12 at 50-90%, 16 at 90-100%. Different category (n=32): 6 at 10-50%, 14 at 50-90%, 11 at 90-100%, plus a thin unlabelled below-10% segment (it would be 1).
- **Fig. 7 (p. 9):** box plots of the same data with 90% and 50% lines.

## Ideas we can use
- This is direct evidence for our title. Stopwatch results for the same patch change with the machine, and small effects cannot be told from noise. A mechanism signal (fewer `read` syscalls, fewer instructions) is a count, not a time, so it should be far more stable across machines than a runtime ratio. We should state this as our motivation and, if we can, show it in our data.
- Our A/A control (base against base) answers the question this paper raises: what does "no change" look like on this machine for this workload? SWE-Perf's -0.03% median is what an A/A run would look like.
- Report a signal-to-noise number per PR, like their std./signal column. A PR whose claimed speedup is smaller than the A/A spread should be reported as "not measurable", not as "not faster".
- Their validity rules (Table III) are ready-made decision rules we can compare ours against: a fixed speedup threshold (GSO), a rank test with a minimum gain (SWE-Perf), a difference larger than two standard deviations (SWE-fficiency).
- Their discussion asks for exactly what we do: profiles and traces, and "resource metrics beyond one runtime number". Our "hidden costs" verdict fits "optimizing one can hurt another".
- For aggregation: do not let one failed PR dominate a summary number. Report per-PR verdicts and medians.

## Weaknesses and things glossed over
- Only wall-clock time on shared cloud VMs. The paper does not say whether cores were pinned, whether hyperthreads or other tenants interfered, or how the VM noise was controlled. Part of the "cross-machine" variation may be cloud noise, not hardware difference.
- Machine type and run noise are not separated. A task fails if any of 12 replays fails. The paper does not report how many tasks fail on only one machine type, or how many would fail in 12 replays on the same machine. So "does not survive cross-machine replay" could partly be "does not survive 12 repeats".
- The all-12 rule gets stricter with every added replay. With a rule that already has some false-negative rate per replay, 12 chances to fail will remove many true speedups. The authors call it conservative but do not estimate this effect.
- Fig. 2 shows per-machine distributions, but there is no per-machine analysis. We do not learn whether Intel against AMD, or old against new CPUs, matters.
- No explanation of why a given reference patch is slower on some machine. No counters or traces were collected, so the paper cannot say what moved.
- The three validity rules differ, so 38%, 8% and 83% are not comparable as "benchmark quality" on one scale. GSO's low 38% comes from a strict 1.2x per-test threshold even though 89% are faster than base.
- For SWE-Perf the runtime change is taken from the benchmark's own "significance-aware runtime-reduction score" with the sign flipped, not from raw times. A value near zero may partly reflect how that score is defined. The paper does not show raw time ratios for SWE-Perf.
- The claim that SWE-Perf's weakness comes from using unit tests as workloads is called "one likely reason". It is not tested.
- RQ2 and RQ3 use released leaderboard outputs. RQ3 says the best patch has "the largest replayed speedup", but the paper does not say on which machine or how many times submission patches were replayed.
- The 10 public submissions are not named in the text. Eight are shared between the two leaderboards.
- Category labels in RQ3.3 come from GPT-5.5 with a "manual sanity-check". No agreement number, one category per patch.
- RQ3's "any of 10 submissions" is an upper bound that no single agent reaches. The authors say so.
- Model names such as GPT-5.5 and Claude Opus 4.6 are as printed in the paper.

## Open questions and future work (theirs, and ours)
- Theirs: benchmarks with stronger reference targets; tasks that start from profiles, flame graphs or traces; hidden validation workloads; metrics for memory, latency, allocations and regression risk next to runtime.
- Ours: are kernel and hardware event counts more stable across machines than runtime for the same patch? When a reference patch is slower on one machine, which counter explains it (cache misses, instructions, context switches)? Would their "invalid" SWE-Perf tasks show a clear mechanism signal even though time does not move?

## Link to our paper
- **Introduction:** main citation for "timing alone is fragile". Even curated reference optimizations fail to reproduce as speedups across machines.
- **Method (A/A control, dedicated cores):** cite for why a noise floor is needed before calling a PR faster.
- **Related work:** the benchmark audit. It says what is wrong with stopwatch-only evaluation and asks for traces and more metrics; we provide a method that does this for real agent PRs.
- **Threats:** we measure on one machine type (kt-measure-1). This paper shows that results can change across machine types. We must say this plainly, and say that counts of syscalls or instructions are expected to transfer better than time, if we have evidence.

## Link to the thesis (tracing, kernel analysis)
- The paper names the noise sources a tracer can observe directly: CPU scheduling (sched_switch events), cache state (LLC misses), memory bandwidth contention.
- It measures only time and so cannot explain its own failures. A replay with `perf stat` counters and an LTTng kernel trace would turn "slower on AMD Milan" into "more cache misses" or "more context switches". This is a concrete use case for trace-based analysis.
- Its call for benchmarks with "hotspot localization from profiles or traces" supports thesis work that gives agents trace data.

## Quotes for inline citation
- "These measurements are not fixed quantities: they fluctuate across runs because of CPU scheduling, cache state, memory bandwidth contention, and machine-level microarchitectural effects" (Sec. I, p. 1)
- "The same patch can therefore behave faster, slower, or statistically unsupported depending on where and how it is replayed" (Sec. I, p. 1)
- "their reference patches satisfy the original benchmark validity rules in every cross-machine replay for only 39/102 GSO tasks, 11/140 SWE-Perf tasks, and 411/498 SWE-fficiency tasks" (Abstract, p. 1)
- "All three benchmarks have reference patches that run slower than the base program in at least one cross-machine replay" (Finding RQ1.2, p. 5)
- "the median SWE-Perf runtime change is only -0.03%, so even small timing shifts can cross zero or lose statistical support" (Sec. III-D, p. 5)
- "otherwise, machine-level noise can be mistaken for a patch-level performance difference" (Sec. III-E, p. 5)
- "a reported optimization can be hard to distinguish from runtime noise" (Sec. VI, p. 9)
- "Production performance work usually starts earlier: engineers inspect profiles, flame graphs, traces, latency breakdowns, or dashboards" (Sec. VI, p. 10)
- "CPU time, latency, allocation behavior, memory footprint, and regression risk all matter, and optimizing one can hurt another" (Sec. VI, p. 10)

## Suggested citation sentences
- Timing is a fragile witness: when Chen et al. replayed the official reference patches of three performance benchmarks on four cloud machine types, the patches kept their original validity in every replay for only 39 of 102, 11 of 140 and 411 of 498 tasks \cite{chen2026benchmarks}.
- When the true effect is small, a stopwatch cannot separate it from noise; the median runtime change of SWE-Perf reference patches under replay was $-0.03\%$ with a spread of 1.41 percentage points \cite{chen2026benchmarks}. We therefore run a base-against-base control and look at the claimed mechanism directly.
- Chen et al. call for evaluations that use profiles or traces and ``resource metrics beyond one runtime number'' \cite{chen2026benchmarks}; our method measures kernel events and hardware counters next to time.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It gives the strongest outside support for our premise. Runtime-only evaluation of performance patches is unreliable across machines, even for curated human optimizations, and small gains are lost in noise. We build on this by adding mechanism signals (syscall counts, page faults, futex wait, instructions) and an A/A control.
  - It audits benchmarks and reference patches. It does not look at agent PRs in the wild, does not read any claim, and collects no counters or traces. It cannot say why a patch is slower somewhere. We do those things.
  - It cuts against us in one place: we measure on one machine. This paper shows that a verdict on one machine may not hold on another. Our timing verdicts ("faster or not") carry that risk. Our mechanism verdicts should be more robust, but we have to argue or show that, not assume it.
  - It also warns that a strict "must pass every repeat" rule removes many real effects. Our decision rule for "faster" should be stated and should not silently get stricter with more repeats.
- **Safe to cite for:**
  - Runtime measurements vary with scheduling, cache state and hardware, so the same patch can look faster or slower depending on where it runs. "The same patch can therefore behave faster, slower, or statistically unsupported depending on where and how it is replayed" (Sec. I, p. 1).
  - Official reference patches often fail to stay valid across machines: "only 39/102 GSO tasks, 11/140 SWE-Perf tasks, and 411/498 SWE-fficiency tasks" (Abstract; Sec. III-C, Fig. 1).
  - Some reference optimizations are slower than the base code in at least one replay, in all three benchmarks (Finding RQ1.2, p. 5; 91/102, 48/140, 470/498 are faster in all replays).
  - Small effects are the problem, not unusually noisy machines: SWE-Perf "median runtime change is only -0.03%" while its spread (1.41 pp) is lower than the other two (Sec. III-D, Table V).
  - Leaderboard order depends on the scoring rule: "the official rankings disagree on 9 of 28 pairwise submission comparisons" and the worst ten tasks carry "58.5%-82.8%" of SWE-fficiency score weight (Abstract; Sec. IV).
  - Performance evaluation should go beyond one runtime number and use profiles or traces: "hotspot localization from profiles or traces ... and resource metrics beyond one runtime number" (Sec. VI, p. 10).
- **Do not cite for:**
  - Anything about real-world agent PRs, PR descriptions or claims. The paper studies benchmark tasks and leaderboard submissions.
  - That agents fail at performance optimization. It finds the opposite on valid tasks: some submission matches the reference on 384/450.
  - That kernel tracing or hardware counters give more reliable verdicts. The paper recommends profiles and traces for future benchmarks but uses none and tests no such claim.
  - That Intel and AMD, or old and new CPUs, give different results. No per-machine comparison is reported.
  - That SWE-Perf's reference patches are "wrong" or "not optimizations". The paper says their measured gains are near zero under replay and lose statistical support.
  - That GSO is a poor benchmark because only 38% of tasks are valid. 89% of its reference patches are faster than base in every replay; the 38% comes from its strict 1.2x rule applied 12 times.
  - A peer-reviewed venue. None is stated.
