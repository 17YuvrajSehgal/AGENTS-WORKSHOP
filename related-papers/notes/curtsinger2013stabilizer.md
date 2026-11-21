# STABILIZER: Statistically Sound Performance Evaluation
- **Authors:** Charlie Curtsinger, Emery D. Berger (Department of Computer Science, University of Massachusetts Amherst)
- **Venue / year / status:** ASPLOS '13 (18th International Conference on Architectural Support for Programming Languages and Operating Systems), Houston, Texas, USA, March 16-20, 2013. Peer-reviewed. 10 pages. The PDF prints no page numbers; paper/refs.bib gives pages 219-228, which I could not confirm from the PDF. In this note "PDF p. N" is the page of the file.
- **PDF:** related-papers/curtsinger2013stabilizer.pdf
- **Cite key:** curtsinger2013stabilizer
- **BibTeX-style reference:** Charlie Curtsinger and Emery D. Berger. 2013. STABILIZER: Statistically Sound Performance Evaluation. In Proceedings of the 18th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS '13). ACM.

## In short
The usual way to test an optimization is to time the program before and after the change. The authors argue this is unsound on modern CPUs. Caches and branch predictors depend on the memory addresses of code, stack and heap objects, and any code change moves those addresses. So a measured speedup can come from the new layout and not from the change itself. Running one binary many times does not help, because all runs share one layout. STABILIZER is an LLVM compiler pass plus a runtime library that moves functions, stack frames and heap objects to random places and repeats this every 500 ms while the program runs. Each run then averages over many layouts. This removes layout as a bias and makes run times close to normally distributed, so t-tests and ANOVA can be used. Median overhead is 6.7%. As a demonstration on SPEC CPU2006 with LLVM: -O2 against -O1 is significant only at the 90% level over the whole suite, and -O3 against -O2 is not significant.

## Problem and motivation
- Researchers and developers compare run times before and after a change. Large projects run automatic performance regression tests (Firefox and Chromium are the examples given).
- A sound evaluation must test the null hypothesis "the new version is not different from the old". That needs several samples from the space of possible situations.
- Memory layout is such a situation. "A single binary constitutes just one sample from the space of program layouts, regardless of the number of runs." (abstract)
- A small code change (adding a stack variable, changing the order of heap allocations) can move every other function, stack frame and heap object.
- Size of the problem as stated in the introduction: Mytkowicz et al. show a slowdown of up to 300% from the size of environment variables; the authors write that changing link order "can cause performance to decrease by as much as 57%".

## Background / key terms (explain each term simply)
- **Memory layout:** the addresses where code (functions), stack frames and heap objects are placed.
- **Measurement bias:** "a systematic error due to uncontrolled factors". Here the uncontrolled factor is layout.
- **Null hypothesis:** the assumption that the change had no effect. A test tries to reject it.
- **p-value:** the probability of seeing a difference at least as large as the measured one if the null hypothesis were true.
- **α (alpha):** the threshold for the p-value, typically 5%. It is the chance of a type-I error.
- **Type-I error:** rejecting a null hypothesis that is true (a false alarm).
- **Statistical power:** the probability of correctly rejecting a false null hypothesis (finding a real effect).
- **Parametric test:** a test that assumes a known distribution, usually the normal one (t-test, ANOVA). It has more power than a non-parametric test when the assumption holds.
- **Central Limit Theorem:** the mean of many independent random values is approximately normal, whatever the distribution of each value.
- **Re-randomization:** changing the layout again at regular times during one run.
- **Shapiro-Wilk test:** tests whether data come from a normal distribution. A small p-value means "not normal".
- **Brown-Forsythe test:** tests whether two samples have the same variance.
- **Wilcoxon signed-rank test:** a non-parametric alternative to the t-test.
- **ANOVA (analysis of variance):** splits total variance into parts (benchmarks, treatment, random variation). It tests one treatment over all benchmarks at once.
- **QQ plot:** plots the quantiles of the sample against the quantiles of a normal distribution. Points on a straight line mean the sample is normal.
- **TLB (translation lookaside buffer):** a CPU cache for address translations. Spreading a program over more memory causes more TLB misses.
- **Branch aliasing:** two branches at addresses that share predictor table entries disturb each other's predictions.

## Method and setup
- **Tool:** an LLVM optimization pass and a runtime library. A compiler driver `szc` replaces the normal compiler and linker call. C and C++ go through clang, or gcc with the dragonegg plugin; Fortran through gfortran with dragonegg (Section 3.1).
- **Evaluation machine (Section 5, PDF p. 6-7):** dual-core Intel Core i3-550 at 3.2 GHz, 12 GB RAM, 256 KB L2 per core, shared 4 MB L3. Linux kernel 3.5.0-22 (unmodified), x86_64. Programs built with gcc 4.6.3 as front-end, dragonegg, LLVM 3.1.
- **Benchmarks:** SPEC CPU2006. 18 programs are used (they appear in Table 1 and Figs. 5 to 7). Not run: the C++ programs omnetpp, xalancbmk, dealII, soplex and povray, because STABILIZER does not support exceptions; and the Fortran programs bwaves, calculix, gamess, GemsFDTD and tonto, which did not build with their toolchain.
- **Repetitions:** 30 runs per benchmark with re-randomization and 30 with one-time randomization for the normality study (Section 5.1). 30 runs per configuration for the overhead study (Section 5.2). For the optimization study in Section 6 the paper does not say how many runs were made.
- **Statistics:** Shapiro-Wilk for normality, Brown-Forsythe for variance, two-sample t-test per benchmark (Wilcoxon signed-rank for the non-normal ones), one-way within-subjects ANOVA over the suite.
- **Noise control beyond layout:** the paper does not describe any (no pinning, no service control). It names "large numbers of runs and a quiescent system" as current best practice in the introduction.

## Section-by-section notes

### 1. Introduction (PDF p. 1-2)
- Statistically sound evaluation needs the effect size and a test of the null hypothesis.
- "even when using current best practices (large numbers of runs and a quiescent system), the conventional approach is unsound."
- Reason: caches and branch predictors depend on addresses, and "Small changes to code, such as adding or removing a stack variable, or changing the order of heap allocations, can have a ripple effect that alters the placement of every other function, stack frame, and heap object."
- Contribution: STABILIZER, which they describe as, to their knowledge, the first system of its kind. It makes execution "independent of the execution environment" and gives normal run times. They also mention it could be used at deployment to make performance outliers less likely; they do not test that.

### 2. STABILIZER overview (PDF p. 2-3)
- 2.1: code is randomized per function; each function call uses a randomly placed stack frame; heap objects get random addresses; code and stack are re-randomized during the run.
- 2.2: each layout period contributes a small part of the run time. The total is a sum over many random layouts, so by the Central Limit Theorem it is approximately normal. "With a sufficient number of randomizations (30 is typical), and no other significant sources of measurement bias, execution time will follow a Gaussian distribution."
- 2.3: with normal data, parametric tests can be used, and they need fewer samples than non-parametric tests to find a real effect.
- 2.4: for one code change: run with and without the change under STABILIZER and apply Student's t-test. They stress that the test "can detect arbitrarily small differences in the means of two populations (given a sufficient number of samples) regardless of the value of α", and that STABILIZER's own overhead (the example is 4.8%) does not stop the test from finding effects smaller than that.
- 2.5: for a compiler or runtime change over many benchmarks, use ANOVA; it is less likely to give type-I errors than many separate t-tests. The three randomizations can be switched on separately, for example to test a stack-layout optimization with only code and heap randomized.

### 3. Implementation (PDF p. 3-5)
- 3.2 Heap: a power-of-two, size-segregated base allocator (TLSF optional; DieHard was the original but has high overhead). A shuffling layer keeps an array of N pointers per size class; each malloc swaps the new object with a random array entry and returns the old one; free works the same way. N = 256 passes the same six NIST randomness tests as libc's lrand48 and DieHard (all fail only the Rank test). Only the cache index bits (bits 6-17 on Core2) need to be random.
- 3.3 Code: at start, every function begins with a trap instruction (`int 3`). On first call the runtime (SIGTRAP handler) copies the function to a random address from an executable heap, builds a relocation table next to it, and replaces the trap by a jump. A timer (500 ms by default) triggers re-randomization: traps are put back, and functions are moved again when next called. Old copies are freed when no return address on the stack points into them. Floating point constants are turned into globals; int/float conversion helpers are the only code that cannot be moved.
- 3.4 Stack: before each call the stack is moved down by a random amount, up to 4096 bytes. Each function has a 256-byte pad table and a one-byte index; the byte is multiplied by 16 (stack alignment on x86_64). Tables are refilled at each re-randomization.
- 3.5: runs on x86, x86_64 and PowerPC, with some platform-specific handling (32-bit jump range on x86_64; fixed relocation tables on PowerPC and x86).

### 4. Statistical analysis (PDF p. 5-6)
- Base case: a program that is one loop. With a different layout per iteration, total time is a sum of samples from the population of layout times, so it is normal by the Central Limit Theorem ("30 samples is typically sufficient").
- Re-randomization is triggered by wall-clock time, not by iteration; the argument still holds by redefining an iteration as n passes.
- Programs with phases: split the program into sub-programs that are each like the loop; the sum of normal variables is normal.
- Limits they state: programs with only one function are not re-randomized; live heap objects cannot be moved (C/C++ rules), so heap normality needs many short-lived objects; large single allocations and custom allocators cannot be randomized, so such programs "may not have normally distributed execution times".

### 5. Evaluation (PDF p. 6-8)
- **5.1 Normality (Table 1, Fig. 5).** With one-time randomization, five benchmarks are not normal at the 95% level: astar, cactusADM, gromacs, h264ref, perlbench. With re-randomization all of these become normal except cactusADM (p = 0.003 in both cases). hmmer goes the other way: normal with one-time randomization (0.552), not normal with re-randomization (0.016). The authors guess this "may be due to hmmer's use of alignment-sensitive floating point operations".
- **Variance (Brown-Forsythe).** Re-randomization significantly lowers the variance for eight benchmarks (astar, gcc, gobmk, gromacs, h264ref, perlbench, sjeng, zeusmp). They explain this as regression to the mean: a very slow run would need many more unlucky than lucky layouts. For cactusADM and mcf the variance is slightly but significantly higher.
- Their summary: STABILIZER "nearly always imposes a Gaussian distribution on execution time, and tends to reduce variance."
- **5.2 Overhead (Fig. 6).** With all randomizations on, median overhead is 6.7%. The caption says overhead is below 40% for all benchmarks; the text says more than 30% for "just four benchmarks". For gobmk, gcc and perlbench most of it comes from stack randomization (many functions, each with a pad table). For cactusADM it comes from the heap (power-of-two size classes waste space). Most overhead is lost locality and TLB pressure.
- Overhead applies equally to both versions under test, so, they argue, it does not hurt validity.
- Four benchmarks (astar, hmmer, mcf, namd) run slightly faster with code randomization. They attribute this to removed branch aliasing and conclude the default layout of these programs is slightly worse than the median layout.

### 6. Sound performance analysis (PDF p. 8)
- Test case: LLVM -O2 against -O1 and -O3 against -O2. Speedup of -O3 is time(-O2) / time(-O3).
- Per benchmark at the 95% level: significant difference for 17 of 18 with -O2 and for 9 of 18 with -O3 (Fig. 7). Some significant changes are slowdowns: bzip2, libquantum and milc with -O2; bzip2, gobmk and zeusmp with -O3.
- **6.1 ANOVA.** "Evaluating optimizations with pairwise t-tests is error prone." Fig. 7 holds 36 tests, each with a 5% false positive risk, so 36 x 0.05 = 1.8 false positives are expected. One-way within-subjects ANOVA over the 18 benchmarks: -O2 against -O1 gives F = 3.235 with one degree of freedom, p = 0.0898, so significant at the 90% level but not at 95%. -O3 against -O2 gives F = 1.335, p = 0.264. "We fail to reject the null hypothesis and must conclude that compared to -O2, -O3 optimizations are not statistically significant."

### 7. Related work (PDF p. 9)
- Table 2: earlier layout randomization (ASLR, TRR, ASLP, Address Obfuscation, Dynamic Offset Randomization, Bhatkar et al., DieHard) was built for security and covers only part of code, stack and heap, mostly without re-randomization.
- Against Mytkowicz et al.: their experimental setup randomization (many link orders and environment sizes) "requires far more runs than STABILIZER, and cannot eliminate bias as effectively". Link order only changes placement between modules; environment size only moves the base of the stack. Any factor not randomized (for example a different shared library version) can still change layout.
- Georges et al. are cited as rigorous techniques for Java. Alameldeen and Wood (simulators) and Tsafrir et al. ("input shaking") are cited as similar ideas.

### 8. Future work (PDF p. 9)
- Randomize at basic-block level, which would also randomize the history part of the branch predictor.
- Use re-randomization to improve performance: sample with performance counters to detect cache misses and branch mispredictions caused by layout, then re-randomize to get away from a bad layout.

### 9. Conclusion (PDF p. 9-10)
- "Two versions of a program, regardless of the number of runs, are only two samples from the distribution over possible layouts."
- Tool available at http://www.stabilizer-tool.org (as printed).

## Key results (with numbers) and what they mean
- Median overhead 6.7%, below 40% for all 18 benchmarks -> the tool is cheap enough to run a full benchmark suite under it.
- Normality: 5 of 18 benchmarks not normal with one fixed random layout per run; 2 of 18 not normal with re-randomization (cactusADM, hmmer) -> re-randomization mostly delivers the normal distribution it promises, but not always. hmmer got worse.
- Variance drops significantly for 8 of 18 benchmarks -> averaging over many layouts inside one run also makes runs more alike, so fewer runs are needed.
- -O3 against -O2: 9 of 18 benchmarks "significant" one by one, three of them slowdowns, but over the suite p = 0.264 -> once layout is treated as noise, the extra -O3 optimizations in LLVM 3.1 have no detectable overall effect on this suite. A per-benchmark win may be a layout effect or a multiple-testing artefact.
- -O2 against -O1: p = 0.0898 -> even a whole optimization level is only weakly detectable across a suite. This warns how small real optimization effects can be next to layout effects.
- 36 tests at 5% give 1.8 expected false positives -> many individual verdicts need a correction or a joint test.

## Tables and figures
- **Fig. 1 (PDF p. 3):** the shuffling layer around the base allocator.
- **Fig. 2 (PDF p. 3):** build process through `szc`.
- **Fig. 3 (PDF p. 4):** code randomization in four steps: trapped, relocated, re-randomizing, re-randomized.
- **Fig. 4 (PDF p. 5):** default stack against randomized stack with padding between frames.
- **Fig. 5 (PDF p. 6):** QQ plots for all 18 benchmarks, one-time randomization and re-randomization. Read: points on the diagonal mean normal; a steeper slope means larger variance.
- **Fig. 6 (PDF p. 7):** overhead per benchmark for code, code+stack, and code+heap+stack randomization. The caption says the baseline is runs with randomized link order.
- **Table 1 (PDF p. 7):** Shapiro-Wilk p-values (one-time randomization and re-randomization) and Brown-Forsythe p-values for 18 benchmarks. Values below 0.05 mean "not normal" and "different variance".
- **Fig. 7 (PDF p. 8):** speedup of -O2 over -O1 and -O3 over -O2 per benchmark; dark bars are significant; asterisks mark slowdowns.
- **Table 2 (PDF p. 9):** feature comparison with earlier randomization systems.

## Ideas we can use
- **A clear statement of the layout threat.** A PR changes code, so it changes layout. Part of any wall-time change we measure could be a layout effect. This paper gives the wording and the citation for the threats section.
- **Why our mechanism signals help.** Our own reasoning (not from the paper): counts such as number of `read` syscalls or number of futex waits do not depend on where code and data sit in memory. A wall-time change that comes with the claimed drop in such a count is harder to explain by layout than a wall-time change alone. Cache misses and branch mispredictions are the opposite: they are exactly what layout changes.
- **Multiple testing.** We give one verdict per PR for many PRs. The 36 x 0.05 = 1.8 argument is the reason to state the expected number of false verdicts under our rule.
- **Per-benchmark results can contradict the suite result.** Same lesson for us: individual PR verdicts and any aggregate claim ("X% of PRs are faster") are different statements and need separate care.
- **Tool not usable for us.** STABILIZER works on programs compiled through LLVM (C, C++, Fortran). Our PRs are mostly Python. We cannot apply it; we can only cite the problem.

## Weaknesses and things glossed over
- **The 57% link-order figure has no data in the paper.** It is stated in the introduction as "we find", with no experiment, table or figure behind it.
- **Section 6 and Table 1 do not agree.** Section 6 says the three non-normal benchmarks are hmmer, wrf and zeusmp (Shapiro-Wilk p below 0.05). Table 1 shows wrf at 0.935 and zeusmp at 0.815 under re-randomization, and lists cactusADM (0.003) and hmmer (0.016) as the non-normal ones. The paper does not explain the difference. The Section 6 runs may be a different data set, but this is not said.
- **Baseline of the overhead figure is unclear.** The text says overhead is "relative to unrandomized execution"; the caption of Fig. 6 says "relative to runs with randomized link order".
- **Run count for Section 6 is not given.**
- **The central claim is argued, not measured.** The paper never shows a case where an optimization looked good or bad without STABILIZER and the verdict changed with it. There is no side-by-side of the same -O2/-O3 comparison done the conventional way.
- **Normal by argument.** The Central Limit Theorem argument assumes many independent layout periods. With a 500 ms period, a short run has few periods. The paper does not give run lengths or discuss short programs.
- **Loose statistics wording.** α is described once as "the probability of observing the measured speedup, given that the optimization actually has no effect" (Section 6.1). That is not the definition; α is the chosen threshold for the p-value.
- **Only layout.** Other noise (scheduling, frequency scaling, interrupts) is covered by the phrase "no other significant sources of measurement bias". One dual-core machine, one kernel.
- **It measures a different program.** Results are for the average over random layouts with added indirection, not for the binary that users run. Kalibera and Jones (kalibera2013rigorous, Section 2) say the results "may include far more variation than in real systems, and hence can mislead". The authors' answer is that overhead applies equally to both versions.
- **Coverage.** 10 SPEC programs were left out (no exception support, build failures). Programs with custom allocators or large arrays are not well randomized. The hmmer anomaly has only a guess as explanation.
- **Effect sizes are not reported** with intervals; the evaluation is in terms of significant or not.

## Open questions and future work (theirs, and ours)
- Theirs: basic-block level randomization; using re-randomization and performance counters to escape bad layouts at run time; exception support.
- Ours: how large are layout effects for Python workloads, where the interpreter binary is the same for both versions and only the Python-level objects and the heap differ? The paper has no data on interpreted languages. Does address space randomization between our 10 process starts already sample some of this space? We have not measured it.

## Link to our paper
- **Threats to validity:** the main place. Cite for "a code change also changes memory layout, and repeated runs of one build do not sample layouts".
- **Approach, measurement paragraph (paper/sections/02-approach.tex, lines 93-110):** cite when we say what our repeated runs do and do not control.
- **Results (paper/sections/03-results.tex, lines 39-45):** cite next to the definition of "faster" if we add a sentence on why a wall-time change alone is weak evidence and the mechanism signal adds to it.

## Link to the thesis (tracing, kernel analysis)
- The effects the paper worries about are hardware events: cache misses, TLB misses, branch mispredictions. They are measured with hardware counters (`perf stat -e cache-misses,branch-misses,dTLB-load-misses`). The paper itself reports only run times and uses counters only as a future-work idea.
- The tool's own mechanism is visible to a kernel tracer: SIGTRAP delivery on first call of each function, a timer signal every 500 ms, and `mmap` calls for the code heap. A trace of a STABILIZER run would contain these as extra events, which matters if one traces a stabilized program.
- Kernel-level signals (syscall counts, block I/O, futex waits) are not expected to move with user-space layout. This is our reasoning, not a claim of the paper.

## Quotes for inline citation
- "A single binary constitutes just one sample from the space of program layouts, regardless of the number of runs." (abstract, PDF p. 1)
- "Since compiler optimizations and code changes also alter layout, it is currently impossible to distinguish the impact of an optimization from that of its layout effects." (abstract, PDF p. 1)
- "even when using current best practices (large numbers of runs and a quiescent system), the conventional approach is unsound." (Section 1, PDF p. 1)
- "Small changes to code, such as adding or removing a stack variable, or changing the order of heap allocations, can have a ripple effect that alters the placement of every other function, stack frame, and heap object." (Section 1, PDF p. 1)
- "the t-test can detect arbitrarily small differences in the means of two populations (given a sufficient number of samples) regardless of the value of α." (Section 2.4, PDF p. 2)
- "Evaluating optimizations with pairwise t-tests is error prone." (Section 6.1, PDF p. 8)
- "We fail to reject the null hypothesis and must conclude that compared to -O2, -O3 optimizations are not statistically significant." (Section 6.1, PDF p. 8)
- "Two versions of a program, regardless of the number of runs, are only two samples from the distribution over possible layouts." (Section 9, PDF p. 10)

## Suggested citation sentences
- A code change also changes memory layout, and repeated runs of one build are a single sample of that layout \cite{curtsinger2013stabilizer}; our timing runs do not control for this.
- Layout randomization as in STABILIZER \cite{curtsinger2013stabilizer} needs an LLVM-compiled program and is not available for the Python projects we study.
- Because a wall-time difference alone can be a layout effect \cite{curtsinger2013stabilizer}, we also check whether the kernel or hardware signal named by the claimed mechanism moved.

## Connection to "Below the Stopwatch"
What we do (from paper/sections/02-approach.tex and 03-results.tex): per PR we run base, head and base again; 3+3 warm-up runs; 10 untraced timing runs per version; dedicated cores; "faster" means the median wall time drops by at least 5% and every head run is faster than every base run; a PR whose base-against-base (A/A) ratio is outside 0.95 to 1.05 is excluded.

- **How it relates:**
  - **This paper attacks the kind of comparison we make.** We time a base version and a head version, one build each, many runs each. The paper says this is unsound even with many runs and a quiet machine, because the two builds are "only two samples from the distribution over possible layouts". Our 10 runs, dedicated cores, medians and separation rule all reduce random noise. None of them samples layouts. A consistent 5% difference with complete separation is exactly what a layout effect would also produce: it is stable across runs of the same two builds.
  - **Our A/A control does not answer it.** Base against base uses the same code and so the same layout. It shows the machine is quiet. It cannot show that a base-against-head difference is not layout.
  - **What we do that the paper does not.** The paper stops at "is the time difference real over all layouts". We ask a second question: did the mechanism named in the PR happen, measured by a signal such as syscall counts or futex wait. Many of these signals do not depend on layout (our reasoning, not the paper's). So a PR that is faster and whose mechanism signal moved has support that the paper's objection does not reach. A PR that is faster by a small margin with no mechanism signal, or whose only signal is cache misses or branch mispredictions, is fully exposed to the objection.
  - **Limits of the objection for our data.** The paper's evidence is for compiled C and Fortran programs on one 2010-era desktop CPU. It has no data for Python, where both versions run on the same interpreter binary. It gives no typical size of layout effects in its own experiments (the 57% and 300% figures are extremes, and the 57% has no data shown). Kalibera and Jones found layout variation of at most 1.7% for SPEC reference inputs on their machines. So we cannot say how much of a 5% effect could be layout; we can only say we did not control it. Our 5% threshold is not derived from any layout measurement.
  - **Statistics.** The paper wants a hypothesis test (t-test, or ANOVA over many benchmarks) on run times that are normal. We use medians and a separation rule with no test and no interval. Our own arithmetic (not from the paper): with 10 and 10 independent runs and no real difference, complete separation in a given direction has a chance of 1 in C(20,10) = 1 in 184,756, so the rule is strict about random noise. It has less power than the tests the paper recommends, and like them it says nothing about layout unless layout is randomized. The paper's multiple-testing point (36 x 0.05 = 1.8) also applies to us, since we give one verdict per PR.
- **Safe to cite for:**
  - Repeated runs of one binary do not cover layout: "A single binary constitutes just one sample from the space of program layouts, regardless of the number of runs." (abstract).
  - A code change moves layout: "Small changes to code, such as adding or removing a stack variable, or changing the order of heap allocations, can have a ripple effect that alters the placement of every other function, stack frame, and heap object." (Section 1).
  - Before/after timing is confounded: "it is currently impossible to distinguish the impact of an optimization from that of its layout effects." (abstract). Add "without controlling layout".
  - Layout effects act through caches and branch predictors (Section 1: "caches and branch predictors make performance dependent on machine-specific parameters and the exact layout of code, stack frames, and heap objects", abstract).
  - Many separate tests produce false positives: "Evaluating optimizations with pairwise t-tests is error prone." and the 36 x 0.05 = 1.8 example (Section 6.1).
  - A measured effect can vanish under sound evaluation: -O3 against -O2 in LLVM on SPEC CPU2006, F = 1.335, p = 0.264 (Section 6.1).
- **Do not cite for:**
  - **A typical size of layout effects** (for example "layout changes performance by X%"). The 300% is from Mytkowicz et al. and the 57% is stated without data. Do not use either as what one should expect.
  - **Python, JIT or interpreted programs.** Only C, C++ and Fortran through LLVM were studied.
  - **Medians, complete separation, a 5% threshold, or A/A controls.** None appear in the paper.
  - **Dedicated cores or system quiescing.** The paper only names "a quiescent system" as existing best practice and says it is not sufficient.
  - **"-O3 does not help".** The finding is for LLVM 3.1, 18 SPEC CPU2006 programs, one machine. 9 of 18 programs did change significantly, some for the worse.
  - **STABILIZER proving that conventional results are wrong.** The paper shows no case where a conventional verdict was reversed.
  - **Number of runs needed.** "30" appears as a rule of thumb for the Central Limit Theorem and as their run count. It is not derived.
  - **Our own claim that syscall-level signals are layout-independent.** That is our argument and needs our own support, not this citation.
