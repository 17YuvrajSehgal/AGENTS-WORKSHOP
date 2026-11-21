# Rigorous Benchmarking in Reasonable Time
- **Authors:** Tomas Kalibera, Richard Jones (University of Kent, Canterbury)
- **Venue / year / status:** ISMM '13 (ACM SIGPLAN International Symposium on Memory Management), Seattle, Washington, USA, June 20-21, 2013. Peer-reviewed. Pages 63-74 (from the repository cover sheet). The PDF is the Author's Accepted Manuscript from the Kent Academic Repository: page 1 is a cover sheet, the paper is PDF pages 2 to 13, and no page numbers are printed. In this note "PDF p. N" is the page of the file; the published page should be N + 61, but that mapping is my own count, not printed.
- **PDF:** related-papers/kalibera2013rigorous.pdf
- **Cite key:** kalibera2013rigorous
- **BibTeX-style reference:** Tomas Kalibera and Richard Jones. 2013. Rigorous Benchmarking in Reasonable Time. In Proceedings of the 2013 ACM SIGPLAN International Symposium on Memory Management (ISMM '13). ACM, 63-74. DOI 10.1145/2464157.2464160.

## In short
Careful benchmarking needs repetition, but repeating everything many times (many builds, many executions, many iterations) costs days. The authors show how to spend a fixed time budget well. First find out where the randomness is: between iterations inside one run, between executions, or between builds. Then repeat mostly at the level that has the most variation, using a formula that takes the cost and the variance of each level. They also argue that results should be reported as an effect size with a confidence interval (for example "faster by 5.5% ± 2.5%") and not with a significance test, and they give a formula for the confidence interval of a ratio of two execution times. They apply all this to DaCapo (Java) and SPEC CPU2006 (C) on recent machines.

## Problem and motivation
- Programs are non-deterministic. A small speedup can be inside the measurement error. Mytkowicz et al. report a median reported improvement of 10% in the field, small enough for this to matter.
- Their survey: of 122 papers from 2011 at PLDI, ASPLOS and ISMM, or in TOPLAS (nos. 1-4) and TACO (nos. 1-2), 90 use execution time as the key measurement, and 71 of those "failed to provide any measure of variation" (Section 1, PDF p. 2).
- Following all earlier advice at once is very slow: SPEC INT with 30 link orders takes 3 days; DaCapo 2006 and 2009 with 20 executions and 10 iterations to compare two systems takes almost 3 days (Section 1).
- Question: how many repetitions, at which level, give a valid and precise result for the least time?

## Background / key terms (explain each term simply)
- **Levels of an experiment:** the points where you can repeat. Here: compilation (build a new binary), execution (start the program or VM again), iteration (run the benchmark again inside the same VM). The highest level is the first one in the sequence that brings randomness.
- **Controlled variable:** something you set on purpose (platform, heap size, compiler options).
- **Random variable:** changes from run to run without control (time between hardware interrupts, scheduling order).
- **Uncontrolled variable:** fixed during the experiment but not chosen by you (for example one particular link order). If it affects the result it causes bias. The experimenter must turn it into a controlled or a random variable.
- **i.i.d. (independent and identically distributed):** each measurement does not depend on the earlier ones and comes from the same distribution. Variance and confidence interval formulas need this.
- **Initialised state:** iterations no longer show clear start-up cost (dynamic linking, filling I/O buffers, JIT compilation).
- **Independent state:** iteration times are i.i.d. The authors take this as a precise definition of "steady state". Independent implies initialised.
- **Run-sequence plot:** time of each iteration against its number. Used to see trends by eye.
- **Lag plot:** each measurement against the one before it (or h before it). A visible pattern means dependence.
- **ACF (auto-correlation function) plot:** correlation of the series with itself shifted by h. Values outside the noise band, or any regular pattern, mean dependence.
- **Significance test and p-value:** tests whether two means differ. The p-value is the chance of seeing a difference at least this large if the true means were equal.
- **Effect size confidence interval:** an interval for how large the difference (or ratio) is. It gives size and uncertainty together.
- **Fieller interval:** a confidence interval for the ratio of two means, from Fieller (1954).
- **Dimensioning experiment (initial experiment):** a one-time pilot run that measures the variance and the cost at each level, so the repetition counts for the real experiment can be chosen.
- **Half-width:** half of the width of a confidence interval, here given as a percent of the mean.
- **LTO (link-time optimisation):** the compiler optimises across source files at link time.

## Method and setup
- **Benchmarks (Section 5, PDF p. 4-5):** DaCapo 2006 (2006-10-MR2) and 2009 (9.12-bach) on OpenJDK 7 (7u2, build 13), 'small' and 'large' sizes, default production VM settings. SPEC CPU2006 CINT version 1.2, built with gcc 4.7 at O3, 'train' and 'reference' sizes.
- **Platforms (Table 1, PDF p. 5), all Ubuntu Linux:**
  - P1: Linux 3.0.0, 64 bit, 4x16(x1) AMD Opteron 2.1 GHz, 12M L3, 64G
  - P2: Linux 2.6.38, 64 bit, 2x4(x2) Intel Xeon 2.27 GHz, 8M L3, 12G
  - P3: Linux 3.0.0, 64 bit, 1x4(x2) Intel Core i7 3.4 GHz, 8M L3, 16G
  - P4: Linux 2.6.35, 64 bit, 1x2(x1) Intel Core 2 2.4 GHz, 4M L2, 4G
  - P5: Linux 2.6.35, 32 bit, 1x1(x2) Intel Pentium 4 3.2 GHz, 1M L2, 4G
  - "2x4(x2)" means 2 processors, 4 cores each, 2-way hyper-threading. P1 and P2 have non-uniform memory access.
- **Noise control:** "We disable all system services that might interfere with measurements." (Section 5). Nothing is said about pinning or isolating cores.
- **Independence study:** 3 executions of each DaCapo benchmark with 300 iterations each; manual inspection of run-sequence, lag (lags 1 to 4) and ACF plots, each next to a randomly reordered copy of the same data (Section 6.1).
- **Execution-level variation:** 30 executions with 40 iterations each on OpenJDK/P1 (Section 7.1). For SPEC: 30 executions of each 'large' (reference) CINT binary on P3 and P4 (Section 7.2).
- **Layout study:** a patched gcc that randomises the order of functions in each module, the order of modules, and the global order of functions under LTO (Section 8).
- **Statistics:** variance components per level, t-based interval for the mean over the top level, Fieller interval for ratios. Full proofs are in their technical report [14], not in this paper.

## Section-by-section notes

### 1. Introduction (PDF p. 2-3)
- Survey numbers as above. Speedups are often small, so they can fall "within the bounds of measurement error". "Even if reported speedups are relatively large, a rigorous study should estimate the measurement error."
- Approach: adapt the experiment design to the platform and benchmark. Groups run the same benchmarks on the same systems for years, so a one-time investment pays back. Any major system change needs the dimensioning done again.
- "Note that repetition is most needed where most non-determinism occurs in the experiment."
- Contributions: critique of common statistics; observational study of non-determinism in DaCapo and SPEC CPU; a method to choose repetition counts; comparison with heuristics; a new look at code layout effects.

### 2. Related work (PDF p. 3)
- Mytkowicz et al.: environment size and link order bias; they used only 'training' input sizes because of cost. The authors repeated this and confirm it for training sizes, but find the effect very small for reference sizes (Section 8.2).
- Georges et al.: as this paper describes it, they drop warm-up iterations by finding the first window of N (say 10) iterations whose 95% CI for the mean is narrower than 5% of the mean. (Note: georges2007rigorous itself describes the rule with a CoV threshold of 0.01 or 0.02, Section 4.2. The two descriptions differ.)
- DaCapo'09 harness: waits until the relative variation over a window of three iterations drops below 3%, then reports one iteration.
- Both automatic methods "do not perform well" (shown in Section 6.3).
- Stabilizer (curtsinger2013stabilizer): re-randomises layout during a run. Benefit: the experimenter need not know the source of layout bias. Criticism: "the results may include far more variation than in real systems, and hence can mislead." The authors call their own approach "less intrusive" but it "expects the experimenter to find potential sources of bias".

### 3. The challenge of reasonable repetition (PDF p. 3-4)
- Three kinds of variables (controlled, random, uncontrolled). First task: find uncontrolled variables that matter and make them controlled or random. Example: "randomising link order turns an uncontrolled variable into a random one."
- Goal of a benchmark experiment: a confidence interval for the mean execution time. With 95% intervals and sound methods, about 95% of intervals cover the true mean.
- 65 of the 90 surveyed papers estimate a speedup; such an estimate should also have a confidence interval.
- "At the very least, repetition must be done at the highest level that has random variation to avoid bias, but sometimes repeating at lower levels can reduce experimentation time without sacrificing precision."

### 4. The challenge of summarising results (PDF p. 4)
- Large improvements (2x or more) are often said to need no statistics. The authors still want error bounds, to allow comparison between studies.
- **Significance testing:** deprecated in other fields. It does not give the wanted number (the ratio and its uncertainty). With a large sample, even a tiny and uninteresting difference becomes "significant"; in computing it is easy to produce large samples. p-values are often misread as the probability that the systems are equal.
- **Visual test (do the two confidence intervals overlap?):** shows the size of the difference, but has no known error rate and is conservative: "with 95% confidence intervals, the probability of error is not 5%, but less than 1% under the normality assumption [23]."
- **Normality:** the central limit theorem "does not fully justify" using parametric methods on non-normal data, but such methods have been found robust. Their own method is based on analysis of variance. A non-parametric alternative is in the technical report.
- **Recommendation (bold in the paper):** "Analysis of results should be statistically rigorous and in particular should quantify any variation. Report performance changes with effect size confidence intervals."

### 5. Benchmarks and platforms (PDF p. 4-5)
- See "Method and setup".

### 6. Repeating iterations (PDF p. 5-7)
- "it does not makes sense to repeat measurements unless the system has reached an independent state. If measurements are not i.i.d., the variance and confidence interval estimates will be biased." (wording as printed)
- Averaging dependent iterations (as in Georges et al.) is "not incorrect if the results are correctly interpreted", but it changes what is measured and always needs repetition at a higher level. They do not encourage it.
- **6.1 Independent state.** Manual procedure with an interactive R script; under a minute per benchmark with practice. Table 2: which DaCapo benchmarks reach an independent state on P1 and P2, for small and large sizes. Results for small and large sizes disagree a lot, and platforms disagree too. "Over half the DaCapo/OpenJDK benchmarks reach an independent state." Jikes RVM gave different results.
- **6.2 Initialised state.** Benchmarks that never become independent show drifts, trends, sudden state changes, or regular switching (odd and even iterations with different times). Which iteration you pick can change the result "by tens of percent". Recommendation: "If a benchmark does not reach an independent state in a reasonable time, take the same iteration from each run."
- **6.3 Time savings.** Table 3 compares four warm-up counts per benchmark: manual initialised, manual independent, the DaCapo'09 harness, and Georges' method (maximum over three runs). The heuristics are sometimes too long (lusearch9 on P1: Georges' method 247 iterations, independent state after 5) and sometimes too short (luindex6 on P2: initialised after 13, harness says 4, Georges' method 8). Too short makes the results "prone to initialisation noise and hence unusable".

### 7. Repeating executions (PDF p. 7-8)
- **7.1 DaCapo.** Only benchmarks that are independent by the 11th iteration are studied; the others get one live iteration per execution. Table 4 (variation as percent of the mean, P1): lusearch9 has 3.3% between iterations but 30.3% between executions. xalan6: 7.0% and 9.1%. bloat6: 14.1% and 3.7%. xalan9: 3.5% and 1.0%. eclipse9, tradebeans9, tradesoap9 have execution variation of 0.4% (text: "below 0.5%").
- **7.2 SPEC CPU.** One iteration per execution. SPEC rules ask for 3 executions; Mytkowicz et al. used 5. On P3 all measurements were i.i.d., so no warm-up is needed. On P4, 10 of 12 CINT benchmarks were i.i.d.; mcf (times going up) and gobmk (times going down) were auto-dependent through at least the first 20 executions, which already take nearly 4 hours. Conclusion for their platforms: one execution per binary is enough in place of 3, saving about 7 hours.

### 8. Repeating compilation (PDF p. 8-9)
- If the build is a source of variation, or if performance depends on code layout, you must build several binaries and randomise the layout.
- **8.1 DaCapo.** 30 executions with 30 different binaries of the VM against 30 executions of one binary, P1, always the 10th iteration. Of 24 DaCapo benchmarks, 8 had more variation over binaries, never by more than one percentage point, except antlr6 (9% over binaries, 3% over executions). Same picture with Jikes RVM. "we found little evidence of this problem with DaCapo on our platforms despite looking hard."
- **8.2 SPEC CPU, training size.** P3, P4, P5; 30 binaries with different link order, each run 5 times, 5th execution taken; same again without randomisation. Nearly all benchmarks vary more with random link order (xalancbmk 4% against 1%, libquantum 1.9% against 0.3%, on P3). Some are also slower on average with random link order (xalancbmk by 4%, libquantum by 2.6%).
- **8.2 SPEC CPU, reference size.** P3, each benchmark 30 times with a different binary each time, with LTO; once randomised and once not. Variation is higher with random layout for every benchmark (Fig. 2) but small: 1.7% for xalancbmk, 1.6% for mcf, below 1% for all others. Only xalancbmk (3.3% slower) and mcf (6.8% slower) are consistently worse with randomisation.
- Advice: repeating with different layouts is still useful if you want layout-independent results, and is cheap. But layout randomisation "can impact performance consistently, and not just introduce noise."

### 9. Multi-level repetition (PDF p. 9-10)
- More repetitions at the top level always narrow the interval. Repeating at a lower level can be cheaper. Costs: an extra iteration costs its own time; an extra execution costs the warm-up again; an extra build costs build time (OpenJDK takes about 20 minutes to compile on their platforms).
- **9.1 Initial experiment:** choose 20 repetitions per level, "30 if possible", fewer (say 10) at lower levels if needed. Record cost c_i per level and all times.
- **9.2 Variance estimators:** S_i^2 (biased) and T_i^2 (unbiased) per level, equations (1) and (2). If T_i^2 is zero or very small, drop that level.
- **9.3 Real experiment:** optimum repetitions at level i (all but the top) are r_i = ceil( sqrt( (c_{i+1} / c_i) * (T_i^2 / T_{i+1}^2) ) ), equation (3). The top level count is free: add repetitions until the interval is narrow enough. The interval, equation (4), is a t-interval over the top-level means with r_n - 1 degrees of freedom. It uses only data from the real experiment, so it stays sound if variances changed.
- This corrects earlier work (Kalibera and Tuma), which used biased estimators and so gave non-optimal counts and intervals that were too wide.
- **9.4 DaCapo (Table 5, P1):** bloat6 c1 = 35.5 s, c2 = 110.0 s, t1 = 14.0%, t2 = 2.7%, optimum 10 iterations per execution. lusearch9: 1.7 s, 12.3 s, 3.4%, 30.3%, optimum 1. xalan6: 10.8 s, 24.6 s, 7.2%, 8.9%, optimum 2. xalan9: 6.7 s, 71.8 s, 3.5%, 0.8%, optimum 15. Meaning: when executions differ a lot (lusearch9), spend the time on new executions; when iterations differ a lot and start-up is expensive (xalan9), take many iterations per execution.

### 10. Measuring speedup (PDF p. 10-11)
- 65 of 90 papers report execution time ratios; only 3 tried to give a confidence interval for the ratio.
- **10.1:** Fieller's interval for the ratio of the two means, equation (5), built from the two single-system half-widths h and h'. It does not assume the ratios are normally distributed. To their knowledge it had not been used in computer performance evaluation before.
- **10.2:** for narrow intervals the relative half-width of the ratio is about (Y'/Y) * sqrt(e^2 + e'^2), equation (6), where e and e' are the relative half-widths of the two systems. "if we were comparing one system with itself, the relative width of the ratio interval would be √2 times wider than the interval for the system itself." The repetition counts that are best for one system are also best for the ratio.
- **Recommendation:** "Always provide effect size confidence intervals for results (equation 4 for single systems or 5 for speedups)."

### 11. Good repetition counts (PDF p. 11)
- **Table 6 (DaCapo, OpenJDK/P1):** executions needed for a 95% interval half-width of 1%, 1.5%, 2.5% and 5% of the mean. Counts below 5 are not shown, because fewer than 5 "could hardly be used to get the variance estimate right". Examples: bloat6 99, 46, 18, 7 (with 10 iterations each). xalan6 311, 140, 52, 15. sunflow9 70, 33, 14, 6. pmd6 52, 25, 11, 5. lusearch9 ∞, ∞, 548, 139 (∞ means that 1000 are not enough). Many others need 5 to 15 executions for 1%.
- **Table 7 (SPEC CPU, P3, layout-randomising gcc, each binary run once):** executions (= builds) needed for half-widths of 0.5%, 1%, 1.5%, 2%. Five benchmarks need fewer than 5 for 0.5% (astar 4, bzip2 4, gcc 4, h264ref 4, hmmer 3; the authors would still run 5). gobmk 6, sjeng 6, omnetpp 7 for 0.5%. perlbench 12 and 5. libquantum 14 and 6. mcf 42, 13, 7, 5. xalancbmk 48, 14, 8, 6. SPEC is "much more stable than DaCapo".

### 12. Summary (PDF p. 11-12)
- Automatic steady-state detection (DaCapo harness, Georges' method) "is not applicable" when benchmarks never reach a steady state, and can create "an error of tens of percent". Manual inspection, done once per system, is needed. Automating it well is an open problem.
- Code layout effects are small for SPEC reference sizes and not significant for DaCapo when the HotSpot JVM's layout is randomised.
- "it is essential that experimenters do not use our dimensioning results at face value but apply our method to their systems, where their results are likely to differ."

## Key results (with numbers) and what they mean
- 71 of 90 execution-time papers give no measure of variation -> in 2011 most performance claims in top venues could not be judged for noise.
- lusearch9: 3.3% variation between iterations, 30.3% between executions -> if you repeat only inside one process, you see a tight result that is wrong by a large amount. Repetition must reach the level where the noise is.
- lusearch9 needs 139 executions for a 5% half-width, while SPEC astar needs 4 for 0.5% -> no single repetition count fits all programs. A count that is generous for one program is far too small for another.
- Heuristic warm-up detection gives 247 iterations where 5 are enough, or 4 where 13 are needed -> automatic "wait until stable" rules both waste time and let start-up noise into the data.
- Layout randomisation on SPEC reference inputs: variation at most 1.7% -> the large layout effects reported by Mytkowicz et al. for training inputs shrink for realistic input sizes on these machines. But mcf is 6.8% slower on average under random layout, so layout can still shift a mean.
- An A/A style ratio has an interval √2 times wider than a single system's interval -> the noise of a ratio is larger than the noise of each side. A threshold on a ratio must allow for that.
- The visual overlap test has an error under 1%, not 5% -> "non-overlapping 95% intervals" is a strict rule, stricter than its name suggests.

## Tables and figures
- **Table 1 (PDF p. 5):** the five platforms.
- **Fig. 1 (PDF p. 6):** lag plots and ACF plots of lusearch9 iteration times (large size, Jikes RVM, P2), real order on the left and random order on the right. Read: the left lag plot has a clear shape and the left ACF has large bars, so iterations depend on each other.
- **Table 2 (PDF p. 7):** x = reached independent state, - = did not, for each DaCapo benchmark, small and large size, P2 and P1. The lusearch6 row is empty; the paper does not say why.
- **Table 3 (PDF p. 7):** warm-up iterations by four methods on P1 and P2. Blank cells in the "Indep." column are benchmarks that did not reach independence. Some "Georges" cells show ∞ (bloat6, sunflow9 on both platforms, xalan6 on P1); the paper does not define ∞ for this table.
- **Table 4 (PDF p. 8):** iteration and execution variation in percent for seven benchmarks on P1.
- **Fig. 2 (PDF p. 8):** relative variation in percent per SPEC CINT benchmark, original gcc against randomising gcc, reference size. Read: light bars (random layout) are higher everywhere, but the axis only goes to about 1.7%.
- **Table 5 (PDF p. 10):** costs, variations and optimum iteration counts for four DaCapo benchmarks.
- **Table 6 (PDF p. 11):** suggested warm-up, iterations and executions for DaCapo by target precision.
- **Table 7 (PDF p. 11):** suggested executions for SPEC CPU by target precision.

## Ideas we can use
- **Report a ratio with a confidence interval.** Equation (5) (Fieller) or the simple form (6) can be computed from our 10 base and 10 head runs with no new measurement. This is the paper's main recommendation and the cheapest fix for our reporting.
- **Use the A/A runs as the dimensioning data.** The two base blocks are exactly the "same system twice" case. Their spread tells us the half-width we can reach with 10 runs per PR, and so which PRs need more runs.
- **Check independence once.** For a few workloads, make a run-sequence plot and a lag plot of the 10 (or more) timing runs. If run k depends on run k-1 (drift, warm caches), our separation rule and any interval are both affected.
- **Levels in our setting.** Our levels are: build (the build agent builds each version once), process start, and run. We repeat only at the run level. The paper says repetition must reach the highest level that has random variation. Whether our build level has variation is something we have not measured.
- **Language for uncontrolled variables.** Their three kinds of variables give us clean wording for the threats section: what we control (cores, machine type), what we randomise, and what stays uncontrolled (one build, one layout, one machine type).

## Weaknesses and things glossed over
- **Manual and subjective.** Independence is judged by eye on plots. Two people could decide differently. The authors say automation is an open problem.
- **The key derivations are not in the paper.** Proofs, assumptions and the non-parametric alternative are in technical report [14].
- **Parametric intervals.** The intervals rest on analysis of variance and the t-distribution. Robustness to non-normal data is argued by citation, not shown on their data.
- **Dimensioning is itself expensive** (20 to 30 repetitions per level) and must be redone when the benchmark, VM or platform changes. This fits a lab that reuses one benchmark suite for years. It does not fit a study like ours with a new workload for every PR.
- **Results are specific to their machines.** They say so. The finding "layout matters little" holds for their platforms, gcc 4.7 and these benchmarks.
- **Steady state only.** Start-up performance is left out (Section 6).
- **Only the mean.** Medians, tails and outliers are not discussed.
- **The description of Georges' warm-up rule** (CI width below 5%) does not match the rule printed in georges2007rigorous (CoV below 0.01 or 0.02). The comparison in Table 3 uses their version.
- **Noise control is one sentence.** No detail on which services were disabled, frequency scaling, or CPU pinning.
- **Table 3 has undefined cells** (∞ and blanks).

## Open questions and future work (theirs, and ours)
- Theirs: accurate and robust automatic detection of independence. They also ask benchmark developers to ship the dimensioning method with the benchmark.
- Ours: is there variation at our build level (two builds of the same commit by the build agent)? Are our 10 timing runs independent, or do they drift? What half-width does 10 runs give on our noisiest workloads?

## Link to our paper
- **Approach, measurement paragraph (paper/sections/02-approach.tex, lines 93-110):** cite when we state how many runs we take and at which level we repeat.
- **Results, definition of "faster" (paper/sections/03-results.tex, lines 39-45):** cite when we explain that we give a yes/no verdict and not an effect size interval, and for the A/A ratio band.
- **Threats to validity:** cite for "we repeat at the run level only and did not dimension the experiment per workload".

## Link to the thesis (tracing, kernel analysis)
- The random variables they name (time between hardware interrupts, scheduling order on a multi-processor, context switches) are kernel events. A trace with `sched_switch` and interrupt events can attribute execution-level variation, such as the 30.3% of lusearch9, to a cause. The paper only measures the size of the variation.
- Initialisation cost from "dynamic linking, filling I/O buffers" is visible as page faults and block I/O in a kernel trace. A trace could replace part of the manual plot inspection for finding the initialised state.
- P1 and P2 are NUMA machines. The paper does not look at NUMA placement as a noise source.

## Quotes for inline citation
- "71 failed to provide any measure of variation (such as variance or a confidence interval) for their results." (Section 1, PDF p. 2)
- "Even if reported speedups are relatively large, a rigorous study should estimate the measurement error." (Section 1, PDF p. 2)
- "Note that repetition is most needed where most non-determinism occurs in the experiment." (Section 1, PDF p. 3)
- "At the very least, repetition must be done at the highest level that has random variation to avoid bias" (Section 3, PDF p. 4)
- "Analysis of results should be statistically rigorous and in particular should quantify any variation. Report performance changes with effect size confidence intervals." (Section 4, PDF p. 4)
- "with 95% confidence intervals, the probability of error is not 5%, but less than 1% under the normality assumption" (Section 4, PDF p. 4)
- "If measurements are not i.i.d., the variance and confidence interval estimates will be biased." (Section 6, PDF p. 5)
- "if we were comparing one system with itself, the relative width of the ratio interval would be √2 times wider than the interval for the system itself." (Section 10.2, PDF p. 11)
- "it is essential that experimenters do not use our dimensioning results at face value but apply our method to their systems, where their results are likely to differ." (Section 12, PDF p. 12)

## Suggested citation sentences
- Kalibera and Jones recommend reporting a speedup as an effect size with a confidence interval \cite{kalibera2013rigorous}; we report a median ratio and a conservative yes/no verdict, which is weaker.
- Repetition must reach the highest level of the experiment that has random variation \cite{kalibera2013rigorous}; we repeat runs but build each version once, so build-level variation is not covered.
- The number of repetitions needed for a given precision differs widely between programs \cite{kalibera2013rigorous}, so our fixed count of 10 runs gives different precision for different PRs.

## Connection to "Below the Stopwatch"
What we do (from paper/sections/02-approach.tex and 03-results.tex): per PR we run base, head and base again; 3+3 warm-up runs; 10 untraced timing runs per version; dedicated cores with system services confined to other cores; "faster" means the median wall time drops by at least 5% and every head run is faster than every base run; a PR whose base-against-base (A/A) ratio is outside 0.95 to 1.05 is excluded.

- **How it relates:**
  - **Same goal, different answer.** The paper asks how to get a trustworthy before/after comparison at reasonable cost. Its answer is a per-system pilot and an effect size interval. Ours is a fixed small design with a strict decision rule. We build on its vocabulary (levels, i.i.d., uncontrolled variables) and on its warning that repetition count depends on the program.
  - **Where we fall short: no effect size confidence interval.** This is the paper's bold recommendation, twice. We give a median ratio with no error bound. Our verdict says "faster or not" but a reader cannot tell if a reported 12% is 12 ± 1 or 12 ± 8.
  - **Where we fall short: no dimensioning, fixed 10 runs.** Their Tables 6 and 7 show needed counts from under 5 to more than 1000 for the same precision. Our 10 is inside the range they find for stable SPEC programs (5 to 14 executions for a 0.5% to 1% half-width for most of Table 7), but they warn not to reuse their numbers on other systems. For a noisy workload 10 runs may be too few, and then our rule reports "no clear change" for a real effect.
  - **Where we fall short: one level only.** We repeat runs. We do not repeat the build. If two builds of the same version differ (or if layout matters), we have one sample of that level and the paper calls the result biased. Our A/A control re-runs the same base build, so it does not test this.
  - **Where we fall short: independence is assumed.** We do not check that the 10 runs are i.i.d. The A/A control (base before and after head) catches a drift between blocks, which is in the spirit of the paper, but it is not the per-run check they ask for. The paper's √2 remark also applies to our A/A band: a base-against-base ratio is noisier than each side, so a fixed 0.95 to 1.05 band is a rule of thumb, not a derived bound.
  - **Where the paper is closer to us than it looks.** It criticises significance tests and notes that a strict visual rule (non-overlapping intervals) has an error below 1%. Our complete separation rule is in that strict family. Our own arithmetic (not from the paper): with 10 and 10 i.i.d. runs, complete separation in a given direction has a chance of 1 in C(20,10) = 1 in 184,756 if there is no difference. So false "faster" verdicts are rare if the runs are independent. The paper would still say this is a decision without the number it wants, the size of the change with its error. Medians are not discussed in the paper at all; its method is about means.
- **Safe to cite for:**
  - Most papers did not report variation: "71 failed to provide any measure of variation" out of 90 papers that used execution time (Section 1). State the year (2011) and the venues.
  - Repetition should be placed where the randomness is: "repetition is most needed where most non-determinism occurs in the experiment" (Section 1) and "repetition must be done at the highest level that has random variation to avoid bias" (Section 3).
  - Measurements must be independent before statistics apply: "If measurements are not i.i.d., the variance and confidence interval estimates will be biased." (Section 6).
  - Speedups should come with an interval: "Report performance changes with effect size confidence intervals." (Section 4).
  - The needed number of runs depends on program and platform: "the required and optimum numbers of repetitions depend on the platform, VM, and benchmark." (Section 11), with Table 6 and Table 7 as evidence.
  - Code layout effects exist but were small for realistic inputs on their machines: for SPEC reference sizes "the variation was quite small overall (1.7% with xalancbmk, 1.6% with mcf and below 1% with all the other benchmarks)" (Section 8.2). Say "on their platforms".
- **Do not cite for:**
  - **"10 runs are enough" or any fixed run count.** The paper gives per-benchmark counts for its own machines and says not to take them at face value.
  - **Medians, rank tests, or a complete separation rule.** Not in the paper. Its method is means with t-based and Fieller intervals. It only says a non-parametric alternative is in the technical report.
  - **A/A testing as a method.** The paper has one sentence on the width of a ratio when "comparing one system with itself". It does not propose A/A controls.
  - **CPU pinning, isolated or dedicated cores.** The paper only says system services were disabled.
  - **"Layout does not matter".** The finding is for their platforms and benchmarks, and mcf was still 6.8% slower under random layout. They keep recommending layout randomisation when layout-independent results are wanted.
  - **Start-up or one-shot workloads.** The study is restricted to steady state.
  - **Significance tests being wrong.** The paper says they are deprecated in other fields and answer the wrong question. It does not say their results are invalid.
  - **Python or cloud VMs.** The data are Java (OpenJDK, Jikes RVM) and C (SPEC CPU) on physical machines.
