# Producing Wrong Data Without Doing Anything Obviously Wrong!
- **Authors:** Todd Mytkowicz, Amer Diwan (University of Colorado, Boulder), Matthias Hauswirth (University of Lugano), Peter F. Sweeney (IBM Research)
- **Venue / year / status:** ASPLOS '09 (14th International Conference on Architectural Support for Programming Languages and Operating Systems), Washington DC, March 2009. Peer-reviewed. Pages 265-276. Also in SIGPLAN Notices 44(3).
- **PDF:** related-papers/3-variability-method/mytkowicz2009_wrong-data.pdf
- **Cite key suggestion:** mytkowicz2009
- **BibTeX-style reference:** Todd Mytkowicz, Amer Diwan, Matthias Hauswirth, and Peter F. Sweeney. 2009. Producing Wrong Data Without Doing Anything Obviously Wrong! In Proceedings of the 14th International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS '09). ACM, 265-276.

## In short
The authors show that two "harmless" parts of an experiment setup, the size of the UNIX environment variables and the order in which object files are linked, change program speed enough to flip a conclusion. Using gcc -O3 vs -O2 on SPEC CPU2006 C programs, the measured "O3 speedup" for one program ranged from a 7% slowdown to an 8% speedup depending only on link order. This bias appeared on two real CPUs, one simulator and two compilers, and none of 133 surveyed papers handled it. They propose two fixes from other sciences: setup randomization (measure in many random setups and use statistics) and causal analysis (intervene on the suspected cause and check the effect changes as expected).

## Problem and motivation
- Researchers measure system S and S+O and conclude O helps. If the setup itself favours one side, the conclusion is wrong. This is **measurement bias**, well known in medicine and social sciences.
- The paper asks: is measurement bias significant (big enough to change conclusions) and commonplace (happens often) in computer systems?

## Background / key terms (explain each term simply)
- **Measurement bias:** the setup systematically favours one option. It is not random noise; repeating the run in the same setup gives the same (wrong) answer.
- **UNIX environment size:** total bytes of environment variables. The environment is loaded into memory before the stack, so its size moves the stack start address, which changes alignment of local variables.
- **Link order:** order of .o files given to the linker. It changes where code and data sit in memory, so it changes alignment in caches and other hardware buffers.
- **O2 / O3:** gcc optimization levels. "Speedup of O3" = cycles(O2) / cycles(O3). Above 1 means O3 helps.
- **Violin plot:** a box plot with the shape of the distribution drawn around it.
- **Loop stream detector (LSD):** a Core 2 hardware feature that replays small loops from a buffer without fetching instructions again. Whether a hot loop fits depends on alignment.
- **Setup randomization:** run the comparison in many randomly generated setups, so the bias averages out, and summarize with statistics.
- **Causal analysis (from Pearl):** to test "X causes Y", change X while keeping everything else the same, measure, and confirm Y changes as expected.
- **PEBS (precise event based sampling):** Intel feature that maps hardware events to exact instructions.

## Method and setup
- **Benchmarks:** all C programs in SPEC CPU2006 v1.0 CINT and CFP: gcc, libquantum, perlbench, bzip2, h264ref, mcf, gobmk, hmmer, sjeng (CINT); sphinx3, milc, lbm (CFP). Train inputs. Each benchmark run 5,940 times. Generating data for sjeng took 12 days.
- **Machines (Table 2):** Core 2 (Linux 2.6.25, gcc 4.1.3 and icc 10.1, PAPI 3.5.1 / perfmon 2.8, 2.4 GHz, 8 GB, L2 128K, L3 4096K as printed in the table), Pentium 4 (Linux 2.4.21, gcc 4.2.1, PAPI 3.0.8 / perfctr 5.2.16 as printed, 2.4 GHz, 2 GB), m5 simulator O3CPU (Alpha, gcc 4.1.0). Most data is from Core 2 (quad core, single-threaded benchmarks).
- **Measurement:** cycles via PAPI in an LD_PRELOAD "inter-loper" that wraps libc_start_main, so measurement does not change the program's static memory layout.
- **Best practices followed:** minimal environment, minimally loaded machines, local disks, repeated runs, two hardware platforms plus a simulator, stack address randomization disabled.
- **Repetitions and statistics:** 5 runs per point with 95% confidence intervals of the mean shown as whiskers. Violin plots across setups. For setup randomization: 484 setups (22 link orders x 22 environment sizes), 3 runs each, t-test.
- **Bias factors varied:** link order (default, alphabetical, 31 random = 33 orders for perlbench); environment size (0 to about 4,096 bytes in steps of 63 bytes).

## Section-by-section notes

### 1. Introduction
- Overview: bias in all architectures and compilers tried, most SPEC programs. Literature survey of 133 papers (ASPLOS, PACT, PLDI, CGO) found none adequately consider bias. Two fixes: setup randomization and causal analysis.
- Benchmark suites are not diverse enough to cancel bias (they show this for SPEC CPU2006 C programs).

### 2. Origin of measurement bias
- Fig. 1: a tiny loop (increment three static ints 65,536 times, compiled without optimization). Adding bytes to an unused environment variable changes cycles "frequently by about 33% and once by almost 300%". Points are mean of 5 runs with 95% CI.
- Reason: environment is placed before the call stack, so stack location and alignment move.

### 3. Experimental methodology
- Bias defined: the setup favours S1 over S2 or vice versa.
- Ioannidis: of 49 highly cited medical articles, later work contradicted 16% and found 16% overstated.
- Other sources mentioned: room temperature (affects clock), benchmark selection.
- OS activity argument: back-to-back runs; the shortest benchmark would need OS activity lasting over 6.5 s to bias results; they judge this unlikely and saw reproducible results on re-runs.

### 4. Measurement bias is significant and commonplace
- **4.1 Link order (Core 2, gcc):** perlbench O3 speedup ranges 0.92 to 1.10 across 33 link orders (Fig. 2a). Some random orders beat both default and alphabetical. Five benchmarks (libquantum, perlbench, bzip2, sphinx, lbm) have violins that straddle 1.0, so the conclusion "O3 helps" depends on link order. On Pentium 4 all non-FP violins straddle 1.0. Perlbench violin height 0.15: "we may think we have a 7% slowdown when in fact we have a 8% speedup!" Median violin height 0.02 on Core 2, 0.08 on Pentium 4. m5 simulator: bzip2 speedup 0.8 to 1.1.
- **4.1.2 Cause:** in m5, whether a hot loop of bzip2 fits in one cache line decides speed (instruction queue latch). On Core 2 the LSD is a likely equivalent, but they cannot confirm: Intel does not document it, no counter measures it, and it cannot be disabled.
- **4.2 Environment size:** perlbench speedup ranges 0.91 to 1.07 as environment grows, not monotonic (Fig. 3a). Four violins straddle 1.0 on Core 2; six of 9 CINT on Pentium 4. lbm ranges 0.88 to 1.09 ("we may think we have a 12% slowdown when in fact we have a 9% speedup!"). Median violin height 0.01 Core 2, 0.04 Pentium 4.
- **4.2.2 Cause:** (1) stack start address; verified by fixing the stack start: same O3 speedup for all benchmarks except perlbench. (2) perlbench copies the environment to the heap; fixing heap start removed most of its bias. Of 340 Core 2 events, 42 differ by more than 25% between the fastest and slowest environment; LOAD_BLOCK:OVERLAP_STORE increases 10x. PEBS does not support that event, so they cannot map it to code.
- **4.3 Intel compiler (icc):** bias also present: 10 violins straddle 1.0 for link order (6 for gcc), median height 0.03 (0.02 gcc); 6 straddle for environment size (4 for gcc), median height 0.006 (0.01 gcc).

### 5. Measurement bias is unpredictable
- Bigger environment does not consistently mean more or less bias.
- Fig. 5: for perlbench, the best link order and best environment size on Pentium 4 are not the best on Core 2. So software vendors cannot tune link order once for all machines.

### 6. Literature review
- 133 papers from ASPLOS 2008, PACT 2007, PLDI 2007, CGO 2007; 88 have an experimental section. 36 of 88 used simulation (also biased, as shown). Median reported speedup 10%, small enough to be hidden by the bias they show. None mention environment size or link order. 83 used more than one benchmark (mean 10.6 ± 1.8).

### 7. Solutions
- **7.1.1 Large benchmark suite:** Fig. 6: average O3 speedup over the whole suite in 66 memory-layout setups varies by 7% between setups. So SPEC CPU2006 C programs are not diverse enough to cancel the bias. "it is not the size of the benchmark suite that is important; it is the diversity of the suite".
- **7.1.2 Setup randomization:** perlbench, 484 setups, 3 runs each, t-test: speedup 1.007 ± 0.003 at 95% (Fig. 7). Not perfect: if you do not vary the right factor, bias from another factor remains. Ioannidis: up to 32% of the most-cited medical studies later found wrong or exaggerated.
- **7.2 Causal analysis:** intervene, measure, confirm. Example: fix stack start, vary environment size, confirm O3 speedup no longer changes. Confirmed for all benchmarks except perlbench, where the analysis rejected the first explanation and led to the heap explanation. Causal analysis does not give untainted data; it gives confidence that conclusions hold.

### 8. Call to action
- More diverse benchmark suites; tools that automatically generate randomized setups; more hardware information from vendors (OpenSparc as an example); hardware that lets you collect data from all major units, disable features, and map events to code (PEBS supports only nine events).

### 9. Related work
- Counter accuracy studies (Korn, Maxwell, Moore). Statistical rigor (Georges et al., Kalibera et al.). Input shaking (Tsafrir et al.), many heap sizes for GC (Blackburn et al.), random cache-miss latency in simulators (Alameldeen and Wood). Each domain has its own bias sources; bias "is here to stay".

### 10. Conclusions
- Election poll analogy: do not predict a national election from one small town; do not predict an optimization's benefit from one setup.

## Key results (with numbers) and what they mean
- Environment size changes a micro-kernel's cycles by about 33% often and by almost 300% once -> a variable your program never reads can dominate its speed.
- Perlbench O3 speedup 0.92 to 1.10 by link order -> the same optimization can look like a 7% loss or an 8% gain.
- Median violin height 2% (Core 2) and 8% (Pentium 4) -> typical setup bias is the same size as the median speedup reported in papers (10%).
- Suite-average speedup varies 7% across setups -> using 12 benchmarks does not cancel the bias.
- With randomization: 1.007 ± 0.003 -> the real O3 benefit for perlbench is tiny, under 1%.
- Best layout on one CPU is not best on another -> bias does not transfer across machines, so one-machine results may not generalize.

## Tables and figures
- **Fig. 1 (p. 267):** code of a micro-kernel and its cycles vs bytes added to the environment (0 to 4,000). Read: a sawtooth with big jumps, mean of 5 runs with tight 95% CIs, so jumps are real.
- **Table 1 (p. 267):** benchmarks with mean cycles and seconds (gcc 1.3 s to sjeng 175 s).
- **Table 2 (p. 268):** machine and toolchain details.
- **Fig. 2 (p. 268):** (a) perlbench O3 speedup for 33 link orders with 95% CI whiskers; (b) violins for all benchmarks, "+" default order and "x" alphabetical. Read: any violin crossing 1.0 means the conclusion can flip.
- **Fig. 3 (p. 270):** same for environment size.
- **Fig. 4 (p. 271):** same with Intel's compiler.
- **Fig. 5 (p. 272):** cycles on Pentium 4 vs Core 2 for each link order and environment size; circled points = best per machine. Read: the circles are different points.
- **Fig. 6 (p. 273):** histogram of suite-average O3 speedup over 66 setups, roughly 1.00 to 1.08.
- **Fig. 7 (p. 273):** histograms of O2 and O3 cycles for perlbench over 484 setups.

## Ideas we can use
- **Setup randomization:** we vary machines (M0, M1, M2; Intel and AMD; 2, 4, 8 vCPU) and repeat sets. That is a form of setup diversity. We can say our main claims (CPU breaking point 0.75 core on all machines) survive changes of machine, which is the kind of check Mytkowicz et al. ask for.
- **Causal analysis:** our prompt-sentence experiment (one sentence removes Haiku's extra work) is a clean "intervene, measure, confirm". The replay model held out on 89 settings is another confirmation step. The fixed page-cache drop before every run removes one bias source.
- **Non-transfer across machines:** some of our numbers scale with vCPU or depend on disk and kernel. Their Fig. 5 is a citation for "best settings on one machine are not best on another".
- **Measurement perturbation:** they used LD_PRELOAD to avoid changing memory layout. Our LTTng tracing could, in principle, change the agent's behaviour. We already tested tracing on vs off (main.tex line 434). Cite this paper for why that check matters.
- **Hidden layout factors for Node.js:** Claude Code runs on Node.js; environment size, ASLR and JIT state could matter for local time. Probably small next to model wait, but it is a possible unmeasured bias for local time.

## Weaknesses and things glossed over
- Only memory layout factors (environment size, link order). Other bias sources (temperature, frequency scaling, background daemons) are named but not measured.
- 5 runs per point and parametric 95% CIs of the mean (t-based) without checking normality; hoefler2015 would object. 3 runs per setup in the randomization experiment.
- Root causes not confirmed on real hardware (LSD and load-store overlap are "probably" the causes).
- The OS activity argument (needs to persist over 6.5 s) is reasoning, not a measurement.
- Single-threaded programs only. No multi-threaded, I/O, network or cloud programs. Results are about microarchitecture, not OS scheduling.
- The literature survey judges "adequately consider bias" by their own criteria; one reviewer.
- Randomization covers only the factors you think of. They admit this.
- Run order: all runs of one configuration back-to-back, not randomized. A slow drift could line up with one configuration. They argue it did not, but random order would have removed the question.

## Open questions and future work (theirs, and ours)
- Theirs: more diverse benchmark suites; automatic setup-randomization tools; more hardware transparency and counters.
- Ours: Does measurement bias from setup (container image, Node.js version, environment, ASLR) change the agent's local time at the scale of our effects (10% threshold)? Our effects are large (x1.8 to x4.8), so layout bias of 1-8% is unlikely to flip them, but it could move a breaking point by one step near the 10% threshold.

## Link to our paper
- **Study Design (main.tex line 311):** we cite this paper for random run order. Careful: Mytkowicz et al. do not randomize run *order*; they randomize the *setup* (link order, environment) and they run each configuration back-to-back. Random run order is better supported by maricq2018 (Section 7.1, "Randomize experiment orderings") and hoefler2015 (Section 4.1.1). Suggest: cite maricq2018 and hoefler2015 for run order, and keep mytkowicz2009 for "the setup can bias results, so we compare runs only within one machine and set and check claims across machines".
- **Threats (Internal and External):** cite for "innocuous setup changes can bias results; we repeat claims on three machine types and two CPU vendors". Also for the tracing-cost check (observer effect).
- **Related Work:** listed under measurement methodology (line 195). Fine.
- **Statistics:** their method (mean of 5 runs, t CI) is weaker than ours (median, bootstrap, rank tests). Their message, many setups instead of one, we follow with M0/M1/M2 and sets 1 and 2.

## Link to the thesis (tracing, kernel analysis)
- Shows that hardware counters (340 events, PAPI/perfmon) can find the mechanism (LOAD_BLOCK:OVERLAP_STORE x10) but cannot locate it without precise sampling. Modern `perf record -e <event>:pp` (PEBS) and `perf mem` now cover more events, which partly answers their call to action.
- Causal analysis = the method behind good trace analysis: form a hypothesis from the trace, intervene (pin CPU, fix a limit, disable a feature), and re-trace to confirm.
- Tracing adds probe effects. Any thesis measurement with LTTng/eBPF should include a tracing-off control, as their LD_PRELOAD design tries to avoid layout changes.

## Quotes for inline citation
- "changing a seemingly innocuous aspect of an experimental setup can cause a systems researcher to draw wrong conclusions from an experiment." (p. 265)
- "Our results demonstrate that measurement bias is significant and commonplace in computer system evaluation." (p. 265)
- "changing the size (in bytes) of an unused environment variable, can dramatically (frequently by about 33% and once by almost 300%) change the performance of our program." (p. 266)
- "In other words we may think we have a 7% slowdown when in fact we have a 8% speedup!" (p. 269)
- "the best link order or best UNIX environment size on one machine is not necessarily the best on another machine." (p. 272)
- "it is not the size of the benchmark suite that is important; it is the diversity of the suite that determines whether or not the suite can factor our measurement bias." (p. 273)
- "the problem of measurement bias is here to stay" (p. 276)

## Suggested citation sentences
- Small, unrelated details of the setup can bias performance results enough to flip a conclusion \cite{mytkowicz2009}, so we repeat each main claim on three machine types and two CPU vendors.
- Following the advice to confirm a cause by changing only that cause \cite{mytkowicz2009}, we add one sentence to the prompt and show that Haiku's extra work disappears.
- A tracer can itself change what it measures \cite{mytkowicz2009}; we therefore compare traced and untraced runs at the tightest limits.
