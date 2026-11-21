# Statistically Rigorous Java Performance Evaluation
- **Authors:** Andy Georges, Dries Buytaert, Lieven Eeckhout (Department of Electronics and Information Systems, Ghent University, Belgium)
- **Venue / year / status:** OOPSLA '07 (Object-Oriented Programming, Systems, Languages and Applications), Montréal, Canada, October 21-25, 2007. Peer-reviewed. Pages 57-76 (the page numbers are printed in the PDF).
- **PDF:** related-papers/georges2007rigorous.pdf
- **Cite key:** georges2007rigorous
- **BibTeX-style reference:** Andy Georges, Dries Buytaert, and Lieven Eeckhout. 2007. Statistically Rigorous Java Performance Evaluation. In Proceedings of OOPSLA '07. ACM, 57-76.

## In short
Java run times differ from run to run (JIT compilation, thread scheduling, garbage collection, system effects). The authors survey 50 Java performance papers and find that most report one number (best, mean, median, second best or worst of a few runs) and only 4 report confidence intervals. They then take one experiment (comparing five garbage collectors in Jikes RVM over 21 heap sizes on three machines) and check how often each "one number" method reaches a different conclusion than a method based on confidence intervals. The "one number" methods say "A is better than B" when the difference could be random in up to 16% of comparisons for start-up, and they give the opposite ranking in more than 3% for some methods. The paper recommends confidence intervals over several VM invocations, and offers a tool (JavaStats) that keeps measuring until the interval is narrow enough.

## Problem and motivation
- A benchmark result is one sample from a noisy process. If you report only the best or the mean of a few runs, you cannot tell a real difference from random variation.
- Every research group used its own method. About one third of the surveyed papers (16 of 50) did not describe their method at all (Section 2, p. 59).
- The paper asks: how often do the common methods give a misleading or wrong conclusion, compared with a statistically careful method?

## Background / key terms (explain each term simply)
- **VM invocation:** starting the Java virtual machine once. A new invocation is a fresh process.
- **Benchmark iteration:** one run of the benchmark inside an already running VM. Several iterations can run in one VM invocation.
- **Start-up performance:** time of one VM invocation with one iteration. It includes class loading and JIT compilation.
- **Steady-state performance:** time of later iterations, after most JIT compilation is done.
- **JIT (just-in-time) compilation:** the VM compiles hot methods while the program runs. In Jikes RVM this is driven by timer-based sampling, so different runs compile different methods. This is a source of non-determinism.
- **Replay compilation:** record which methods got compiled at which level, then force the same plan in later runs. It removes JIT non-determinism.
- **Systematic error vs random error:** a systematic error is a bias from a mistake in the setup; it pushes all results one way. A random error goes up or down without pattern. Statistics handles only random errors (Section 3.1).
- **Confidence interval (CI) for the mean:** a range around the sample mean that, with a chosen confidence level (for example 95%), is expected to contain the true mean.
- **Student's t-distribution:** used in place of the normal distribution when there are few measurements (the paper says n < 30), because the sample standard deviation is then a poor estimate.
- **ANOVA (analysis of variance):** a method to compare more than two alternatives. It splits the total variation into variation inside each alternative (noise) and variation between alternatives.
- **Tukey HSD test:** run after ANOVA to find which pairs differ, while keeping the chance of a false finding under control.
- **Coefficient of variation (CoV):** standard deviation divided by the mean. A unit-free measure of noise.
- **Threshold θ:** the authors' model of an analyst's judgement. A difference smaller than θ is "small", larger is "large". They vary θ from 1% to 3%.
- **Violin plot:** a box plot that also shows the shape of the distribution.

## Method and setup
- **Literature survey:** 50 Java performance papers from 2000 onwards in OOPSLA, PLDI, VEE, ISMM and CGO (Section 2, p. 59).
- **VM and collectors:** Jikes RVM (SVN version of February 12, 2007) with five garbage collectors from MMTk: CopyMS, GenCopy, GenMS, MarkSweep, SemiSpace (Section 5.1).
- **Benchmarks (Table 3, p. 67):** seven SPECjvm98 programs with the largest input (-s100) and seven DaCapo programs (release 2006-10-MR2, default input). 14 in total.
- **Heap sizes:** from the per-benchmark minimum up to 6 times the minimum in steps of 0.25 times the minimum. That is 21 heap sizes (Sections 5.2 and 6.2).
- **Machines (Section 5.3):** 2.1 GHz AMD Athlon XP (2 GB), 2.8 GHz Intel Pentium 4 (2 GB), 1.42 GHz Mac PowerPC G4 (1 GB). Linux 2.6.18. "In all of our experiments we consider an otherwise idle and unloaded machine." (p. 67)
- **Reference ("rigorous") method for start-up:** 30 VM invocations with one iteration each, then ANOVA and Tukey HSD to get simultaneous 95% confidence intervals for the five collectors, per benchmark and per heap size (Section 6.2).
- **Methods under test ("prevalent"):** best, second best, worst, mean and median of 3, 5, 10 and 30 VM invocations.
- **Comparison:** all pairs of collectors (10 pairs) at each of 21 heap sizes = 210 comparisons per benchmark. Each is put in one of six classes (Table 4).
- **Steady state:** 10 VM invocations with 30 iterations each for the variability figure; keep k = 10 iterations per invocation once their CoV is below 0.02 (Section 6.2.2).

## Section-by-section notes

### 1. Introduction (pp. 57-59)
- Sources of non-determinism: JIT compilation driven by timer-based sampling, thread scheduling, garbage collection timing, and system effects such as interrupts.
- Fig. 1 (db, 120 MB heap) is the motivating example. With "best of 30", CopyMS and GenCopy look about equal and SemiSpace looks clearly better than GenCopy. With mean and 95% CI, GenCopy is significantly better than CopyMS, and the SemiSpace and GenCopy intervals overlap. SemiSpace had one very good run among many worse ones, and "best" reported that run.
- Contributions: show the pitfall, argue for statistics, recommend a start-up and a steady-state method, release JavaStats.

### 2. Prevalent Java performance evaluation methodologies (pp. 59-61)
- 16 of 50 papers do not say how they measured. This was more common in papers from 2000 to 2003.
- What the papers report: mean in 8 papers, best in 10, median in 4, second best in 4, worst in 3 (p. 59-60). Number of runs: "typically more than 3 runs are considered; some go up to 50 runs."
- Only 4 of 50 report confidence intervals (p. 60).
- 7 of 50 use replay compilation.
- Other design choices they list: one or many VM invocations, including or excluding JIT time, a forced full garbage collection before measuring, one or many hardware platforms, one or many heap sizes, one or many VMs, and back-to-back ("aaabbb") against interleaved ("ababab") measurements.
- Table 1 describes 13 example methods (A to M). In that table only method B reports a confidence interval, and only method I is marked as interleaved. No method is marked as back-to-back, which the caption says can also mean "not documented".
- The SPEC run rules for SPECjvm98 ask for at least two runs and for reporting the best and the worst.

### 3. Statistically rigorous performance evaluation (pp. 61-65)
- 3.1: systematic errors must be removed by the experimenter. "If not, the overall conclusions, even with a statistically rigorous data analysis, may be misleading." (p. 62). Outliers caused by a disturbing event should be examined and discarded.
- 3.2: confidence interval for the mean. With n ≥ 30 use the normal z value. With n < 30 use Student's t with n - 1 degrees of freedom.
- 3.2.3: a larger confidence level gives a wider interval. They state that normal data is not required because of the central limit theorem.
- 3.3: comparing two alternatives. Simplest way: check if the two intervals overlap. If they overlap, the difference may be random. Better: compute the CI of the difference of the means; if it contains zero, there is no statistically significant difference. With fewer than 30 measurements on either side, use t with the degrees of freedom formula given on p. 63 (this is the Welch form).
- 3.4: more than two alternatives: one-factor ANOVA, then Tukey HSD. ANOVA assumes equal variance and normal errors but is "fairly robust towards non-normality" when the number of measurements per alternative is balanced.
- 3.5: multi-factor ANOVA (several inputs, with interactions) and MANOVA (several benchmarks at once).
- 3.6: they do not use the complex methods, because the output is hard to read and the number of measurements becomes too large. They stay with confidence intervals per benchmark.

### 4. A practical statistically rigorous methodology (pp. 65-66)
- **Start-up (4.1):** (1) measure p VM invocations, each with one iteration; (2) compute a CI, with z if more than 30 measurements, otherwise t. They discard the first VM invocation, because it changes system state (libraries loaded into memory, disk cache) and so is not independent of the later ones.
- **Steady state (4.2):** (1) p VM invocations with at most q iterations each; (2) in each invocation find the point where the CoV of the last k iterations falls below a threshold "say 0.01 or 0.02"; (3) take the mean of those k iterations per invocation; (4) compute the CI over the p means. Reason: iterations inside one VM are not independent of each other, but the per-invocation means are.
- **4.3 JavaStats:** runs VM invocations until the CI is within a wanted width (1% or 2% of the mean) or a maximum number of runs (for example 30) is reached. With few measurements the method still works but "the confidence intervals will be looser".

### 5. Experimental setup (pp. 66-67)
- See "Method and setup" above. GenRC, MarkCompact and RefCount collectors were left out (the first two did not run on some benchmarks; RefCount was significantly worse everywhere).

### 6. Evaluation (pp. 67-75)
- **6.1 Run-time variability.** Fig. 2 (start-up, 30 VM invocations) and Fig. 3 (steady state), both on the AMD Athlon with GenMS and a heap of twice the minimum. For most benchmarks the CoV is around 2%, higher for several. The gap between the fastest and slowest run is "generally around 8% for startup and 20% for steady-state" (p. 68). A Kolmogorov-Smirnov test does not reject normality in more than 90% of their experiments; a minority is skewed or bimodal.
- **6.2 Classification (Table 4).** If the rigorous intervals overlap and the prevalent method shows a difference below θ, the result is "indicative"; if at least θ, it is "misleading". If the intervals do not overlap: same ranking and difference at least θ is "correct"; opposite ranking and at least θ is "incorrect"; difference below θ is "misleading but correct" or "misleading and incorrect".
- **6.2.1 Start-up (Fig. 4).** Misleading conclusions in up to 16% of comparisons. Incorrect conclusions in more than 3% for some methods. Mean and median are consistently better than best, second best and worst, and they improve with more measurements while the others do not. Raising θ reduces incorrect conclusions but also reduces how often the method can conclude anything (Fig. 5, javac). Results differ between the three machines and between benchmarks (Fig. 6): jess and hsqldb are almost insensitive, db and javac show more than 3% incorrect conclusions.
- **Use cases.** Fig. 7: comparing only GenMS against the four others gives the same picture. Fig. 8 (db): for heaps between 80 MB and 120 MB the "best" method says CopyMS clearly beats MarkSweep and almost equals GenCopy; the intervals say CopyMS and MarkSweep may not differ and GenCopy is substantially better than CopyMS. Fig. 10 (antlr, heaps 6 to 20 times the minimum): most differences between CopyMS, GenCopy and SemiSpace are noise.
- **6.2.2 Steady state (Figs. 11, 12).** The first 3 iterations are clearly start-up and it takes more than 10 iterations to reach steady state (Fig. 11, Athlon). The prevalent methods (best of median, best, second best; with 1, 3 or 5 VM invocations and 3, 5, 10 or 30 iterations) are misleading in more than 20% of cases at θ = 1%, more than 10% at θ = 2%, and more than 5% at θ = 3%. Incorrect conclusions are "a few percent for small θ thresholds".
- **6.2.3 Replay compilation.** Plan taken from 7 runs (the one with the shortest time), GenMS, 512 MB heap. Replay and normal compilation, both analysed rigorously, agree in 56% to 72% of cases, are inconclusive in 17% to 37%, and disagree in up to 12% (Fig. 13, Table 5). So the experimental design itself changes conclusions. Under replay compilation, the prevalent data analysis is misleading in around 5% of cases for the mix (start-up) run and in less than 4% for the stable (steady-state) run (Figs. 14, 15).
- **6.3 In practice.** Fig. 16 (80 MB heap, Athlon): the width of the 95% CI falls as measurements are added, but at different speeds. GenCopy on jess is still above 3% after 30 measurements. MarkSweep and GenMS on db are around 1% after fewer than 10. Fig. 17: the number of VM invocations needed for a 2% interval (maximum 30) differs by benchmark, collector and heap size. This is the argument for a tool that adapts the number of runs.

### 7. Summary (pp. 75-76)
- Restates the two methods and JavaStats.
- Their own scope statement: if differences are large, a rigorous method will most likely not change the conclusion; for small differences inside the margin of error it can.

## Key results (with numbers) and what they mean
- 4 of 50 surveyed papers report confidence intervals; 16 of 50 do not describe the method -> in 2007, most Java performance claims could not be checked for noise.
- CoV around 2% for most benchmarks; fastest-to-slowest gap around 8% (start-up) and 20% (steady state) -> a single run, or the best run, can be far from the typical run.
- Up to 16% misleading and more than 3% incorrect conclusions for start-up -> a reader of a paper that reports "best of N" has a real chance of reading a ranking that is noise, and a small chance of reading the opposite of the truth.
- Mean and median beat best, second best and worst -> if you must report one number, a central value is the least bad choice. It is still not enough without a measure of spread.
- Raising θ lowers the wrong conclusions but does not remove the need for statistics (Fig. 5) -> a fixed "we only count differences above X%" rule is not a replacement for looking at the spread of the runs.
- Replay and normal compilation disagree in up to 12% of cases -> how you set up the experiment matters as much as how you analyse it.
- Runs needed for a 2% interval vary from a handful to more than 30 -> one fixed number of runs is too many for some programs and too few for others.

## Tables and figures
- **Fig. 1 (p. 58):** db at 120 MB heap; "best of 30" (left) against mean with 95% CI (right) for five collectors. Read: the ranking changes between the two panels.
- **Table 1 (p. 61):** 13 published methods (A to M) against data-analysis and design features. Read: almost no column has the "confidence interval" row ticked.
- **Table 2 (p. 64):** layout of measurements for ANOVA.
- **Table 3 (p. 67):** the 14 benchmarks and their minimum heap sizes (16 MB for mpegaudio up to 176 MB for hsqldb).
- **Figs. 2, 3 (pp. 67-68):** violin plots of run times normalized to the mean, start-up and steady state. Read: the height of a violin is the run-to-run spread.
- **Table 4 (p. 69):** the six classes (indicative, misleading, misleading but correct, misleading and incorrect, correct, incorrect).
- **Fig. 4 (p. 70):** share of comparisons in each class for every prevalent method, three machines, θ = 1% and 2%. Bars are hard to read exactly; the text gives the "up to 16%" and "more than 3%" figures.
- **Fig. 5 (p. 70):** classes for javac as θ goes from 0 to 3, "best" method, Athlon.
- **Fig. 6 (p. 71):** per-benchmark classes for the "best" method, Athlon, θ = 1%.
- **Fig. 7 (p. 71):** GenMS against the other four collectors.
- **Figs. 8-10 (pp. 71-72):** start-up time against heap size for db and antlr, CI method on top and "best of 30" below.
- **Fig. 11 (p. 72):** normalized time against iteration number; shows warm-up.
- **Fig. 12 (p. 73):** steady-state accuracy of prevalent methods, SPECjvm98, Athlon, θ = 1% and 2%.
- **Fig. 13 and Table 5 (pp. 73-74):** replay against normal compilation: agree, disagree, inconclusive.
- **Figs. 14, 15 (p. 74):** prevalent against rigorous analysis under replay compilation, θ = 1%.
- **Fig. 16 (p. 74):** CI width in percent of the mean against number of measurements (2 to 30) for jess, db, mtrt.
- **Fig. 17 (p. 75):** measurements needed to reach a 2% interval, by heap size and collector.

## Ideas we can use
- **Report the spread, not only the median.** For each PR we already have 10 base and 10 head wall times. A 95% interval for the ratio (or at least min and max per version) can be reported at no extra measuring cost.
- **Classify our own rule against a CI rule.** Their Table 4 is a ready design: for each PR compare our verdict (5% and complete separation) with a CI-based verdict on the same 20 runs, and count agreements. This would show in one line how conservative our rule is.
- **Adaptive run count.** Their JavaStats idea (measure until the interval is narrow, with a cap) fits PRs whose runs are noisy. Fig. 16 and 17 are the evidence that a fixed count does not fit all programs.
- **Discard the first invocation.** They drop the first VM invocation because it warms the disk cache and loads libraries. Our 3+3 warm-up runs do the same job; this paper is a citation for why.
- **Outliers.** They say to inspect outliers and discard them only if a disturbing event explains them. Our complete separation rule is sensitive to one outlier, so this point matters for us (see the last section).

## Weaknesses and things glossed over
- **The "truth" is itself an estimate.** The reference verdict comes from the same kind of data (30 VM invocations). A comparison classed as "misleading" only means the prevalent method concluded more than the 30-run intervals allow. The paper does not measure how often the reference method is wrong.
- **Loose wording about confidence intervals.** They write that a 90% interval "means that there is a 90% probability that the actual distribution mean ... is within the confidence interval" (p. 63). This is the common simplified reading. The stricter reading is about the procedure over many repeats.
- **Normality.** They say the method needs no normal data because of the central limit theorem (3.2.3). That argument is for large n. For n < 30 they use the t-distribution, which does assume roughly normal data. They report that a minority of their data is skewed or bimodal and still say this "does not affect the generality" (p. 68). Kalibera and Jones (kalibera2013rigorous, Section 4) say the theorem "does not fully justify this assumption".
- **Overlap test is conservative.** Checking whether two 95% intervals overlap rejects less often than a 5% test. The paper presents it as the simplest approach and does not discuss this.
- **Independence of iterations.** The steady-state method assumes the benchmark reaches a stable state where a CoV threshold can detect it. Kalibera and Jones later show that many DaCapo benchmarks never reach an independent state.
- **Only random error.** The method does not deal with bias (for example memory layout). They say this openly in 3.1 but give no method for it.
- **One VM, old hardware.** Jikes RVM only, three single-core-era machines. No multi-core or cloud noise.
- **θ is a model, not data.** The threshold stands in for "what an analyst would call a real difference". The real papers they surveyed were not re-evaluated.
- **Run order.** Back-to-back against interleaved order is listed as a design feature in Table 1 but never tested. The paper does not say in which order its own runs were made.
- **Figure 4 numbers** are given in the text only as upper bounds ("up to 16%", "more than 3%"); exact per-method values must be read off the bars.

## Open questions and future work (theirs, and ours)
- Theirs: they say a benchmarker who knows statistics "may perform more complex analyses" (multi-factor ANOVA, MANOVA). They give no explicit future work section.
- Ours: how often does our verdict (5% drop of the median and complete separation of 10 and 10 runs) agree with a t-based interval on the same runs? Is 10 runs enough for the noisier workloads, or should the count adapt?

## Link to our paper
- **Approach, measurement paragraph (paper/sections/02-approach.tex, lines 93-110):** cite here for "run-to-run variation must be handled by repeated runs and a statistical rule, not by one number".
- **Results, definition of "faster" (paper/sections/03-results.tex, lines 39-45):** cite here when we explain why a 5% threshold alone is not enough and why we add the separation rule (their Fig. 5 point).
- **Threats to validity:** cite when we admit that we report medians without confidence intervals.

## Link to the thesis (tracing, kernel analysis)
- The noise sources they name for the "system effects" part (interrupts, thread scheduling) are the events a kernel trace records (`sched_switch`, `irq_handler_entry`). The paper treats them as a black box and only measures their total effect on run time. A trace can say which of them caused a slow run.
- Their first-invocation effect (libraries and data staying in memory and in the disk cache) is page-cache state. It can be seen directly with page-fault and block I/O events.
- The paper has no tracing or counter measurements itself.

## Quotes for inline citation
- "This paper shows that prevalent methodologies can be misleading, and can even lead to incorrect conclusions. The reason is that the data analysis is not statistically rigorous." (p. 57)
- "In only a small minority of the research papers (4 out of 50), confidence intervals are reported to characterize the variability across multiple runs." (p. 60)
- "It is up to the experimenter to control and eliminate systematic errors." (p. 61)
- "For most of the benchmarks, the coefficient of variation (CoV), defined as the standard deviation divided by the mean, is around 2% and is higher for several benchmarks." (p. 68)
- "in up to 16% of the comparisons, the prevalent methodology makes too strong a statement saying that one alternative is better than another." (p. 69)
- "mean and median are consistently better than best, second best and worst." (p. 69)
- "increasing the θ threshold for a prevalent methodology does not replace a statistically rigorous methodology." (p. 70)
- "if the performance differences between the alternatives are large, a statistically rigorous method will not alter the overall picture nor affect the general conclusions obtained using prevalent methods." (pp. 75-76)

## Suggested citation sentences
- Reporting a single number from a few runs can give misleading or even wrong rankings \cite{georges2007rigorous}, so we do not call a PR faster on the median alone.
- A fixed threshold on the size of a difference does not replace a check of the run-to-run spread \cite{georges2007rigorous}; we therefore require, next to the 5\% threshold, that every run of one version beats every run of the other.
- We report medians without confidence intervals, which is weaker than the practice recommended by Georges et al. \cite{georges2007rigorous}.

## Connection to "Below the Stopwatch"
What we do (from paper/sections/02-approach.tex and 03-results.tex): per PR we run base, head and base again; 3+3 warm-up runs; 10 untraced timing runs per version; dedicated cores; a PR is "faster" if the median wall time drops by at least 5% and every head run is faster than every base run; a PR whose base-against-base (A/A) ratio is outside 0.95 to 1.05 is excluded.

- **How it relates:**
  - **We follow the core message.** The paper says: repeat in fresh processes, drop the warm-up run, use an idle machine, and do not decide from one number. We repeat 10 times per version, warm up first, isolate cores, and do not decide from the median alone.
  - **Where we fall short: no confidence interval, no effect size with error.** The paper's whole recommendation is to compute a confidence interval (with Student's t when n < 30, which is our case with n = 10) and to compare alternatives through intervals. We report a median and a yes/no verdict. A reader cannot see how precise our speedup numbers are. This is the clearest gap.
  - **Where we fall short: median as the reported number.** In their test the median was one of the "prevalent" single-number methods. It did better than best or worst, but it was still classed as misleading in part of the comparisons. Their recommended summary is the mean with an interval.
  - **Our 5% threshold is their θ.** They show that a threshold alone "does not replace a statistically rigorous methodology" (p. 70). Our answer is the complete separation rule, which is a rank-based check on the spread. The paper does not study such a rule, so it neither supports nor rejects it. Our own arithmetic (not from the paper): if 10 base and 10 head runs came from the same distribution and were independent, the chance that all 10 head runs beat all 10 base runs is 1 in C(20,10) = 1 in 184,756. So the rule gives very few false "faster" verdicts. The cost is low power: a real 6% speedup with one slow head run is reported as "no clear change", and one outlier decides the verdict. The paper says outliers should be inspected and discarded if a disturbing event explains them (p. 62); we do not do that.
  - **Other gaps against their advice.** They use three hardware platforms and many configurations (21 heap sizes) following Blackburn et al.; we use one machine type and one workload per PR. They let the number of runs adapt to the noise (JavaStats); we fix it at 10. Our independence assumption (base block, head block, base block) is not tested; the A/A control catches drift between the two base blocks but not every pattern.
- **Safe to cite for:**
  - Run-to-run variation is real and not small: "the coefficient of variation ... is around 2% and is higher for several benchmarks" and the gap between fastest and slowest run is "generally around 8% for startup and 20% for steady-state" (Section 6.1, p. 68). Say that this is for Java on Jikes RVM.
  - Single-number summaries can mislead: "in up to 16% of the comparisons, the prevalent methodology makes too strong a statement" (Section 6.2.1, p. 69), and can be wrong: "the fraction of incorrect comparisons can be more than 3%" (p. 69).
  - Central values are better than extremes: "mean and median are consistently better than best, second best and worst" (p. 69).
  - A threshold is not enough: "increasing the θ threshold for a prevalent methodology does not replace a statistically rigorous methodology" (p. 70).
  - Bias is outside what statistics can fix: "It is up to the experimenter to control and eliminate systematic errors." (Section 3.1, p. 61).
  - Large differences are robust to the choice of method: "if the performance differences between the alternatives are large, a statistically rigorous method will not alter the overall picture" (Section 7, pp. 75-76). Use this only for our large effects, and note the authors say "Most likely".
- **Do not cite for:**
  - **Medians as the recommended summary.** The paper recommends the mean with a confidence interval. It only shows the median is less bad than best or worst.
  - **A "complete separation" rule, rank tests, or non-parametric tests.** None of these appear in the paper.
  - **A/A (base against base) controls.** The paper does not mention them.
  - **Dedicated or isolated CPU cores, pinning, or disabling services.** The paper only says the machines were "otherwise idle and unloaded".
  - **A fixed number of runs such as 10 or 30.** The 30 in the paper is the border between z and t and the cap they chose in their experiments. The paper's point is that the needed number varies (Figs. 16, 17).
  - **Interleaved or random run order.** It is listed as a design feature in Table 1 and never evaluated.
  - **Memory layout bias, environment size, link order.** That is mytkowicz2009wrong and curtsinger2013stabilizer, not this paper.
  - **Programs other than Java.** The abstract says many issues "also apply to other programming languages and systems that build on a managed runtime system". The data are Java on Jikes RVM only. Our PRs are mostly Python; the transfer is by argument, not by their data.
