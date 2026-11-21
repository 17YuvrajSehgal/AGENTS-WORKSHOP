# An Exploratory Study of Performance Regression Introducing Code Changes
- **Authors:** Jinfu Chen, Weiyi Shang (Department of Computer Science and Software Engineering, Concordia University, Montreal, QC, Canada)
- **Venue / year / status:** ICSME 2017 (IEEE International Conference on Software Maintenance and Evolution). Peer-reviewed. Pages 341-352. DOI 10.1109/ICSME.2017.13.
- **PDF:** `related-papers/chen2017regression.pdf`
- **Cite key:** chen2017regression
- **BibTeX-style reference:** Jinfu Chen and Weiyi Shang. 2017. An Exploratory Study of Performance Regression Introducing Code Changes. In 2017 IEEE International Conference on Software Maintenance and Evolution (ICSME). IEEE, 341-352.

## In short
The authors check out commits of Hadoop (1,126 commits, ten releases) and RxJava (135 commits, five releases), run the tests or micro-benchmarks touched by each commit 30 times, and record response time, CPU, memory, I/O read and I/O write. A test "regresses" if a metric gets worse with p < 0.05 (t-test) and a medium or large effect size (Cohen's d above 0.5). They find regressions in 243 Hadoop commits and 91 RxJava commits, usually with improvements in other tests of the same commit. Response time and the resource metrics are almost uncorrelated. Most regressing commits are bug fixes. A manual study of 680 regressing tests gives six code-level root causes; 85 (12.5%) are judged avoidable or reducible. The experiment has no same-version control run and no correction for the very large number of statistical tests.

## Problem and motivation
- Performance regressions are normally found late, after the system is built and deployed or in dedicated performance tests. Finding them at that stage is costly.
- Earlier empirical studies of performance problems (Jin et al., Zaman et al., Huang et al.) use issue reports. Regressions that nobody reports are invisible to them.
- So the authors measure performance at the level of each commit and ask: RQ1, how common are commits that introduce a regression? RQ2, what are the root causes?

## Background / key terms (explain each term simply)
- **Performance regression:** the system, or one feature, performs worse than before. The authors stress that a regression "may not be performance bugs, since the performance may still meet the requirement".
- **Domain level metric:** what the user sees. Here: response time of a test.
- **Physical level metrics:** resource use. Here: CPU usage, memory usage, I/O read, I/O write, collected with `psutil` (a Python library that reads process statistics from the operating system).
- **Impacted test:** a test that exercises a file changed by the commit. For Hadoop it is found by name: `TestFSNamesystem.java` tests `FSNamesystem.java`.
- **Micro-benchmark (JMH):** a small benchmark of one unit of code. RxJava ships 76 of them.
- **Student's t-test:** a test for whether two means differ. p < 0.05 is taken as "the difference is likely not by chance".
- **Cohen's d:** effect size = difference of the two means divided by the pooled standard deviation. Their scale: trivial up to 0.2, small up to 0.5, medium up to 0.8, large above 0.8.
- **Pearson correlation:** a number from -1 to 1 for how strongly two series move together in a straight-line way.
- **Syndrome (their word):** the set of metrics that regress together in one test.

## Method and setup
- **Subjects (Table I, p. 342):** Hadoop 2.6.0 to 2.6.5 and 2.7.0 to 2.7.3 (about 1,496K to 1,568K lines, 1,664 to 1,786 tests). RxJava 2.0.0 to 2.0.4 (164K to 244K lines, 76 tests listed for every version).
- **Commit filtering (Section II.B.1):** only commits that change `.java` files. If several commits belong to one issue ID, only the code after the last one is measured.
- **Tests (Section II.B.2):** Hadoop: impacted tests by the naming rule. RxJava: all 76 micro-benchmarks. When a commit changes a test, the old test is used. If the old test fails or does not compile, the new one is used. If both fail, the test is dropped. Counts: 132 tests in 106 commits used the new test; 21 tests in 19 commits were dropped; 6 commits were dropped completely.
- **Machine (Section II.B.3):** Azure "Standard F8s (8 cores, 16 GB memory)" virtual machine. Hadoop tests run on the local machine, no cluster. The paper does not say whether all runs used the same VM, whether cores were pinned, or what else ran on the VM.
- **Repetitions:** "each test or performance micro-benchmark is executed 30 times independently". Total run time "over 2,000 hours". The paper does not say in which order the runs were done (old and new interleaved or one after the other).
- **Statistics (Section II.B.4):** t-test at p < 0.05, plus Cohen's d. A regression is counted only for medium or large d. Normality is justified by the central limit theorem. There is no correction for multiple tests.
- **Controls:** none of the same version against itself. The paper does not say exactly which earlier snapshot each commit is compared with; the text speaks of "two commits" and of evaluating commits "chronologically".
- **RQ2 manual study:** all 338 regressing Hadoop tests, and a random sample of 342 of the 3,100 regressing RxJava tests (95% confidence, 5% interval). Root causes were found iteratively until no new one appeared. The paper does not say how many people did the labelling.

## Section-by-section notes

### I. Introduction
- Claim of novelty: "To the best of our knowledge, our work is the first that extensively evaluates and studies performance at the commit level" (p. 342). The conclusion words it more weakly: "one of the first".
- Preview of findings: regressions are common, involve several metrics, come together with improvements, are mostly introduced during bug fixing, and 12.5% of the examined ones are avoidable or reducible.

### II. Case study setup
- See Method above. Fig. 1 (p. 343) shows the pipeline: filter commits, prepare impacted tests, evaluate performance, statistical analysis.
- Reasons given for not running Hadoop on a cluster: not every commit builds into a deployable version; cluster jobs may not cover the changed code; locating the cause is harder on a cluster.

### III. RQ1: How prevalent are performance regression introducing changes?
- Each impacted test is judged alone, not the commit as a whole. Reason: a worse feature hurts users even if another feature got better.
- **Commits with at least one regressing test (Table II):** Hadoop 243 in any metric; 93 in response time, 175 CPU, 138 memory, 90 I/O read, 82 I/O write. RxJava 91 in any metric; 91 for response time, CPU, memory and I/O read, 90 for I/O write.
- **Tests:** Hadoop 1,270 executed tests, 338 regress in at least one metric; 129 regress in response time (87 large, 42 medium). RxJava 7,600 executed tests, 3,100 regress in at least one metric; 1,410 in response time (745 large, 665 medium).
- More regressions have a large effect than a medium one, in every metric (Table II).
- **Resource metrics add information.** More commits and tests regress in CPU and memory than in response time. The correlation between effect sizes for response time and for each resource metric is close to zero (Table III). Resource metrics correlate with each other at a medium level (for example CPU with memory 0.60 in Hadoop).
- **Complex syndromes.** 154 commits and 203 tests in Hadoop, and 91 commits and 777 tests in RxJava, regress in more than one physical metric.
- **"Performance regression and performance improvement co-exist."** Measured by response time: in Hadoop, 70 commits have both; in these commits 82 tests regress and 117 improve. In RxJava all 91 regressing commits also have improvements; 1,410 tests regress and 1,545 improve. The authors read this as a possible trade-off or side effect. They show this only for response time "due to limited space".

### III. RQ2: What are the root-causes of performance regressions?
- **Context from issue types (Fig. 3):** 176 of 243 Hadoop commits (72%) and 48 of 91 RxJava commits (53%) are linked to an issue of type "bug". The authors checked these by hand and say all are functional bug fixes. Only three commits are linked to new features; the authors think this is a side effect of their method (they prefer the old test, which does not exercise a new feature).
- **Low-impact tasks:** 12 commits are typed "cleanup" and 6 "documentation". In Fig. 3 these two types appear only in the RxJava part. On inspection these commits also contained small code changes (RxJava issues #4987 and #4706).
- **Six code-level root causes (Table IV, counts of regressing tests; avoidable or reducible in brackets):**
  - *Changing function calls:* 334 (36). Sub-patterns: new functionality, external impact, changing algorithm, skippable function. Example: Hadoop commit #c927f938 adds `Collections.shuffle` inside a loop in `Mover.java`.
  - *Changing parameters:* 100 (18). Sub-patterns: more expensive parameter, condition parameter, configuration parameter. Example: Hadoop commit #81a445ed passes a large `conf` object into `doPreUpgrade`, called in a loop.
  - *Changing conditions:* 85 (13). Example: Hadoop commit #3c1b25b5 turns an `else` into an `else if`, so `isEmpty` runs each time.
  - *Having extra loops:* 14 (0). Example: Hadoop commit #94a9a5 adds a loop that adds items to a queue one by one.
  - *Using more expensive variables:* 48 (9). Example given: `static` variables live longer and cost more memory.
  - *Introducing locks and synchronization:* 6 (0), all in Hadoop. Example: Hadoop commit #2946621a adds a `synchronized` block in `MetricsSourceAdapter.java`.
  - *Others:* 93 (9). The paper does not describe what is in "Others".
- **Avoidable:** "Among the total 680 manually examined performance regressions, we find 85 of them are avoidable or their impact may be reduced" (p. 348). 85 / 680 = 12.5%.
- Two explanations offered for "bug fixes cause regressions": no performance regression test is enforced after a bug fix, and developers may accept slower code to make the fix easier.

### IV. Threats to validity
- **External:** two Java systems, fifteen releases.
- **Internal:** root-cause labels are subjective. Causality: "the performance regression may be not caused by the particular code change but due to unknown factors"; they suggest mutation-based causal analysis as future work. Choice of metrics.
- **Construct:** accuracy of `psutil`. Noise: "There always exists noise when monitoring performance", handled by 30 repetitions. Issue types may be wrong. Tests may not cover all performance impact; the aim is a sample of regressions, not all of them. The in-house environment differs from users' machines, so some regressions "may not be noticeable in the field".

### V. Related work
- Regression detection after deployment: ad hoc analysis, pair-wise analysis (control charts), model-based, multi-model based.
- Empirical studies: Jin et al., Zaman et al., Huang et al. Table V compares them with this work. Luo et al. (PerfImpact) searches inputs that expose regressions between releases and compares execution traces.

### VI. Conclusion
- Contributions: commit-level study, a "statistically rigorous approach", regressions are widespread and often follow bug fixes, six root causes, 12.5% avoidable or reducible.
- Future work: user studies and automated change impact analysis for performance.

## Key results (with numbers) and what they mean
- 243 Hadoop commits and 91 RxJava commits have at least one regressing test -> by this method, regressions are common in normal development. How many commits were measured after filtering and grouping is not stated, so a clean rate "X% of commits" cannot be computed from the paper. (7,600 RxJava tests = 76 benchmarks x 100, which suggests 100 measured RxJava snapshots, but the paper does not say this.)
- Hadoop: 93 commits regress in response time, 175 in CPU, 138 in memory -> a stopwatch alone would miss many of the commits this method flags.
- Correlation of response-time effect size with any resource metric is between -0.02 and 0.06 in both systems (Table III) -> knowing that a test got slower tells almost nothing about whether it uses more CPU, memory or I/O, and the other way round. The two kinds of metric are separate evidence.
- CPU with memory 0.60 (Hadoop) and memory with I/O read 0.57 (RxJava) -> resource metrics partly move together.
- 70 Hadoop commits and all 91 RxJava commits have both regressing and improving tests -> one commit rarely has one direction of effect; the verdict depends on which test you look at.
- RxJava: 1,410 tests regress and 1,545 improve out of 7,600 -> about 39% of all test runs show a "significant" medium or large change in response time, almost evenly split between slower and faster. The paper reads this as real trade-offs. A reader should also consider that noise between runs on a cloud VM, with thousands of tests and no A/A control, would give a similar even split. This second reading is mine, not the paper's.
- 72% (Hadoop) and 53% (RxJava) of regressing commits are bug fixes -> regressions enter while people work on something else. There is no base rate (what share of all commits are bug fixes), so this does not show that bug fixes are riskier than other commits.
- 85 of 680 (12.5%) avoidable or reducible -> by the authors' judgment, most detected regressions are a price for needed functionality.

## Tables and figures
- **Table I (p. 342):** versions, lines of code, files, tests.
- **Fig. 1 (p. 343):** the pipeline.
- **Table II (p. 346), checked on the page image.** Commits: Hadoop 243 / 93 / 175 / 138 / 90 / 82 (any, response time, CPU, memory, I/O read, I/O write); RxJava 91 / 91 / 91 / 91 / 91 / 90. Tests (large, medium): Hadoop response time 87, 42; CPU 202, 97; memory 167, 74; I/O read 75, 28; I/O write 75, 17. RxJava response time 745, 665; CPU 659, 487; memory 919, 489; I/O read 657, 449; I/O write 38, 0. Read: "any metric" (338 and 3,100) is smaller than the sum because one test can regress in several metrics.
- **Fig. 2 (p. 346):** per commit, bars upward = number of tests with a response-time regression, downward = with an improvement, split into large and medium. RxJava bars reach about 25 in both directions for most commits. Hadoop bars are 1 to 4 up and 1 to 6 down over about 70 commits. Read: the RxJava plot looks roughly symmetric around zero for almost every commit.
- **Table III (p. 347):** Pearson correlations between effect sizes. Hadoop: response time with CPU -0.02, memory 0.04, I/O read 0.01, I/O write 0.06; CPU with memory 0.60, I/O read 0.32, I/O write -0.02; memory with I/O read 0.27, I/O write 0.04; I/O read with I/O write 0.06. RxJava: response time with CPU -0.01, memory 0.01, I/O read 0.01, I/O write -0.01; CPU with memory 0.39, I/O read 0.46, I/O write 0.06; memory with I/O read 0.57, I/O write -0.26; I/O read with I/O write 0.06.
- **Fig. 3 (p. 347):** regressing commits by issue type. RxJava: test, enhancement, documentation, cleanup, bug. Hadoop: new feature, sub-task, test, improvement, bug. Only the bug counts (176, 48), new feature (three), cleanup (12) and documentation (6) are given in the text; the other bars must be read from the chart.
- **Table IV (p. 349):** root causes. Hadoop / RxJava with avoidable in brackets: new functionality 125 (11) / 119 (6); external impact 32 (6) / 18 (3); changing algorithm 15 (2) / 19 (2); skippable function 6 (6) / 0; expensive parameter 12 (4) / 22 (3); condition parameter 15 (2) / 21 (3); configuration parameter 22 (5) / 8 (1); more expensive variables 22 (5) / 26 (4); extra loops 6 (0) / 8 (0); changing condition 37 (8) / 48 (5); locks and synchronization 6 (0) / 0; others 40 (5) / 53 (4). I re-added the rows: Hadoop 338, RxJava 342, total 680, avoidable 85. They match the text.
- **Table V (p. 350):** comparison with Jin et al., Huang et al., Zaman et al. Read with care: it describes Jin et al.'s approach as a "Dynamic rule-based checker" (their checkers are static) and gives 100 instances for Zaman et al. (that study samples 400 reports, 200 of them performance bugs).

## Ideas we can use
- **Timing and resource signals are separate evidence.** Table III is the best published support we have for looking below the stopwatch: effect sizes for response time and for CPU, memory and I/O are almost uncorrelated.
- **Per-test verdicts.** They judge each test alone because one commit helps some tests and hurts others. Our per-PR verdict with one workload should say that it holds for that workload only.
- **Effect size next to significance.** They require a medium or large Cohen's d. We should also report an effect size and a minimum size, set from the A/A control.
- **Old test on both versions.** They run the test from before the change on both versions, so the workload is the same. Our build agent's workload must also be identical on base and PR.
- **Regression classes.** "Introducing locks", "extra loops", "more expensive parameter" are the mirror image of what agents claim to remove.

## Weaknesses and things glossed over
- **No A/A control.** The same version is never measured against itself. So we do not know how many "medium or large" effects appear from the environment alone.
- **Multiple testing.** 1,270 and 7,600 tests times five metrics, each at p < 0.05, with no correction. With 30 against 30 samples, a d of 0.5 is close to the p = 0.05 line, so the d filter adds little protection.
- **Cloud VM.** An Azure F8s instance is shared hardware. The paper says it minimized noise but not how. No pinning, no frequency control, no information on run order. If all runs of one commit happened in one block, slow drift of the VM shows up as a "commit effect" (compare mytkowicz2009wrong and laaber2019cloud).
- **t-test on times.** Run times and resource metrics are usually skewed. The central limit theorem argument is weak for n = 30 with outliers. No non-parametric check.
- **Symmetry in RxJava.** Every one of the 91 commits has regressions and improvements, in every metric, and regressing and improving tests are about equal in number. The paper explains this as trade-offs and does not consider noise.
- **JMH and repetition.** The paper does not say how JMH was configured (forks, warm-up) or how "response time" was taken from a JMH run.
- **Resource metrics.** `psutil` gives sampled, process-level values. The paper does not say the sampling interval, whether CPU is a mean percentage or total time, whether memory is peak or mean, or whether child processes are included.
- **Hadoop tests are unit tests, not performance tests.** Many are short. Their run time is dominated by JVM start-up and setup, which is sensitive to noise.
- **Impacted-test heuristic** is by file name only.
- **Root causes are labelled by reading the diff**, with no check that the labelled change causes the regression. The authors admit this (Internal validity).
- **Inconsistency:** for "Having extra loops" the text says batching "can make this regression avoidable" and in the next sentence that all regressions in this class are un-avoidable (p. 347).
- **No base rates.** Share of bug-fix commits among all measured commits is not given. The number of measured commits after filtering is not given.
- **"Avoidable" is a judgment** with no stated criteria and no second rater.
- The data link (https://jinfuchen.github.io/icsmeData) is given in a footnote; I did not check that it still works.

## Open questions and future work (theirs, and ours)
- Theirs: more systems and languages; causal analysis by code mutation to confirm root causes; more metrics; cheap but representative performance tests; field data.
- Ours: would their counts survive an A/A control and isolated cores? Do kernel-level signals (syscall counts, page faults, futex wait, instructions) correlate better with the code change than sampled `psutil` values do?

## Link to our paper
- The key `chen2017regression` is in `paper/refs.bib`. I found no `\cite` of it in the `.tex` files under `paper/` when writing this note.
- Natural places: Related Work (closest earlier study that rebuilds and measures individual changes); Motivation for measuring more than time (Table III); Method (same workload on both versions, repetitions, effect size); Threats (workload coverage, causality between a diff and a measured change).
- See "Connection to Below the Stopwatch" below.

## Link to the thesis (tracing, kernel analysis)
- The study stops at process-level counters from `psutil`. It shows that resource metrics carry information that timing does not, but it cannot say why a metric moved. Kernel tracing (LTTng, eBPF) and hardware counters (`perf stat`) are the next level down: which syscalls, how much time blocked, how many page faults, how many instructions.
- Their "locks and synchronization" class is a case where the cost is waiting, not CPU. It is best seen as futex wait or off-CPU time, which `psutil` does not report.
- Their own threat ("may be not caused by the particular code change but due to unknown factors") is the gap that a mechanism-level trace comparison can close.

## Quotes for inline citation
- "We note that performance regression may not be performance bugs, since the performance may still meet the requirement, even though the performance is worse than the previous version." (p. 341)
- "To the best of our knowledge, our work is the first that extensively evaluates and studies performance at the commit level." (p. 342)
- "each test or performance micro-benchmark is executed 30 times independently." (p. 343)
- "Physical performance metrics are important complementary indicators of performance regressions." (p. 345)
- "we find the low correlation between the effect sizes calculated with response time and the physical metrics" (p. 345)
- "Performance regression and performance improvement co-exist." (p. 345)
- "A majority of the performance regressions are introduced with bug fixing, rarely with new features." (p. 345)
- "There always exists noise when monitoring performance" (p. 348)
- "the performance regression may be not caused by the particular code change but due to unknown factors." (p. 348)

## Suggested citation sentences
- Chen and Shang measured individual commits of Hadoop and RxJava and found that changes in response time and changes in CPU, memory and I/O use are almost uncorrelated \cite{chen2017regression}; timing alone therefore hides part of the effect of a change.
- In the same study, most commits that slowed one test sped up another \cite{chen2017regression}, so a verdict for a change holds only for the workload that was measured.
- Earlier commit-level studies used process-level resource counters \cite{chen2017regression}; we go one level lower, to kernel events and hardware counters, and add a base-against-base control.
- Reading a diff does not prove that it caused a measured change \cite{chen2017regression}; we therefore check the specific kernel or hardware signal that the claimed mechanism must move.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is the closest earlier work in method: take one code change, run the same test on the code before and after, repeat, and decide with statistics, using time and resource metrics. We build on that design.
  - What it does not do and we do: it has no claim to check (it looks for regressions, not for whether a stated speedup and its mechanism are real); it uses sampled process counters, not kernel traces or hardware counters; it runs on a cloud VM with no core isolation; it has no A/A control; it reuses existing tests, while our workload is written by a build agent that does not see the claim.
  - A point that cuts against us: improvements and regressions co-exist inside one commit across different tests. We measure one workload per PR. Our "faster / not faster" is therefore a statement about that workload, and another workload could give the opposite sign. This must be in our Threats.
  - A second honest point: their near-symmetric results in RxJava show how easily a repeat-and-test pipeline produces "significant, large" effects in both directions. The paper does not prove these are noise, but it does not rule it out. This is an argument for our A/A control, and also a warning that our own verdicts need it to be believed.
- **Safe to cite for:**
  - Measuring the performance of individual commits with repeated runs is feasible and was done before us: 1,126 Hadoop and 135 RxJava commits, each test "executed 30 times independently" (abstract p. 341; Section II.B.3, p. 343).
  - Resource metrics show effects that timing misses: "Physical performance metrics are important complementary indicators of performance regressions" and "we find the low correlation between the effect sizes calculated with response time and the physical metrics" (RQ1, p. 345; Table III, p. 347: all between -0.02 and 0.06).
  - One change can make some tests faster and others slower: "Performance regression and performance improvement co-exist" (RQ1 Discussion, p. 345; 70 Hadoop commits, all 91 RxJava commits, response time).
  - Regressions often touch several metrics at once: 154 commits and 203 tests in Hadoop, 91 commits and 777 tests in RxJava "have multiple physical performance metrics associated with performance regressions" (p. 345).
  - Locks, extra loops, more expensive calls and parameters are recurring code-level causes of regressions (RQ2, Table IV, p. 349). Say "identified by manual inspection".
  - A measured change after a diff is not proof that the diff caused it: "the performance regression may be not caused by the particular code change but due to unknown factors" (Internal validity, p. 348).
- **Do not cite for:**
  - A rate such as "X% of commits introduce a regression". The paper gives counts of regressing commits but not the number of commits measured after filtering, and it has no noise control.
  - "Bug fixes are more likely to cause regressions than other changes." It shows that most regressing commits are bug fixes (72% and 53%), with no base rate.
  - "Most optimizations cause regressions elsewhere." The co-existence result is about ordinary commits, not about commits meant as optimizations, and it may partly be noise.
  - Kernel tracing, hardware performance counters or system calls. None is used; the metrics come from `psutil`.
  - A/A testing, core isolation or cloud-noise handling. None is described.
  - A validated causal link between the six root causes and the measured regressions. The labels come from reading diffs.
  - Descriptions of Jin et al. or Zaman et al. Its Table V misdescribes both.
  - Anything about AI agents or pull requests.
