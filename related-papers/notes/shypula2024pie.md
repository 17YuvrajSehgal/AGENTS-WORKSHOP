# Learning Performance-Improving Code Edits
- **Authors:** Alexander Shypula, Aman Madaan (equal contribution), Yimeng Zeng, Uri Alon, Jacob Gardner, Milad Hashemi, Graham Neubig, Parthasarathy Ranganathan, Osbert Bastani, Amir Yazdanbakhsh (University of Pennsylvania, Carnegie Mellon University, Google, Google DeepMind)
- **Venue / year / status:** ICLR 2024, peer-reviewed conference paper ("Published as a conference paper at ICLR 2024" on every page). The PDF is arXiv:2302.07867v5, dated 26 Apr 2024. 25 pages: 9 pages of main text, references on pp. 10-13, appendix on pp. 14-25.
- **PDF:** `related-papers/shypula2024pie_2302.07867.pdf`
- **Cite key:** shypula2024pie
- **BibTeX-style reference:** Alexander Shypula, Aman Madaan, Yimeng Zeng, Uri Alon, Jacob Gardner, Milad Hashemi, Graham Neubig, Parthasarathy Ranganathan, Osbert Bastani, and Amir Yazdanbakhsh. 2024. Learning Performance-Improving Code Edits. In The Twelfth International Conference on Learning Representations (ICLR 2024). arXiv:2302.07867.

## In short
The authors build PIE, a dataset of more than 77K pairs of C++ competitive-programming submissions where the same programmer made their own program faster. They use it to teach LLMs to optimize code (prompting, retrieval, fine-tuning). They do not time programs on a real machine. They time them in the gem5 CPU simulator, because on real hardware 500 pairs of *identical* programs showed a mean "speedup" of 1.12× (top 5% of pairs: 1.91×). Their best model (fine-tuned GPT-3.5, best of 8 samples) reaches a mean speedup of 6.86×, against 3.66× for the human edits in the test set.

## Problem and motivation
- Compilers do low-level optimization well. High-level optimization (a better algorithm, a better API, a better data structure) is still done by people (Section 1, p. 1).
- Earlier learning-based work was "either narrow or difficult to build on due to the lack of open datasets and lack of reliable performance measurement techniques" (p. 1).
- Two questions: can pre-trained code LLMs be adapted to optimize programs, and how can speedups be measured in a way that other people can reproduce?

## Background / key terms (explain each term simply)
- **PIE (Performance-Improving Edits):** the dataset. Each item is a pair (slow program, fast program) for the same problem, written by the same user.
- **CodeNet:** an existing IBM dataset of competitive-programming submissions (Puri et al., 2021). PIE is built from it.
- **gem5:** a CPU simulator. It runs a program inside a software model of a processor and reports how long the modelled processor would need. The same program and input always give the same result. The paper calls it a "full system simulator" with "detailed microarchitectural emulation of modern processors" (p. 4).
- **Deterministic measurement:** a measurement that gives exactly the same number every time. Real machines are not like this. gem5 is.
- **HYPERFINE:** a benchmarking tool. The paper calls it "a Rust library designed to precisely benchmark binaries" (p. 3). The authors use it for the real-hardware noise test.
- **Phantom / spurious improvement:** a speedup that appears in the numbers but comes only from measurement noise.
- **%Opt:** share of the 978 test programs that the method made at least 10% faster while staying correct.
- **Speedup:** old time divided by new time (o/n). If the output is wrong or slower, the speedup is counted as 1.0.
- **%Correct:** share of test programs for which the output program passes every test case.
- **Best@k:** sample k outputs from the model, keep the fastest one that passes all tests.
- **Few-shot prompting:** show the model a few (slow, fast) examples before the program to optimize.
- **Chain-of-thought (CoT):** ask the model to first write a strategy in words, then the code.
- **Dynamic retrieval:** pick the few-shot examples that are most similar to the input program (CodeBertScore embeddings, FAISS search).
- **Performance-conditioned generation:** during training each fast program gets a tag from 1/10 to 10/10 saying how close it is to the best known solution. At test time the model is asked for "10/10".
- **Self-play / synthetic data:** let an LLM invent new problems and programs, then let a fine-tuned LLM optimize them, and add the good pairs to the training data.
- **LoRA:** a cheap fine-tuning method that changes only a small number of parameters.

## Method and setup
- **Dataset construction (Section 2, p. 3):** take one user's accepted submissions for one problem in time order. Build all pairs (earlier, later). Keep a pair only if the later one is more than 10% faster: (time(y_i) - time(y_>i)) / time(y_i) > 10%. Only C++, "since it is a performance-oriented language compatible with the gem5 simulator".
- **Sizes (Section 2, Tables 6-7, p. 19):** train 77,967 pairs from 1,474 problems. Validation 2,544 pairs from 77 problems. Test 978 pairs from 41 problems. A problem appears in only one split.
- **Timing labels:** CodeNet's own CPU times were "inconsistent" (Appendix A.9), so every program was re-timed in gem5. This took "over 42.8 million simulations" (p. 3).
- **Test cases:** CodeNet has on average 4 per problem. They add generated test cases from AlphaCode. After removing cases that time out (over 2 minutes in gem5), the median number of test cases per problem is 82.5 (train), 75 (validation), 104 (test). A program is rejected if one test fails.
- **Simulator configuration (p. 4):** gem5 with "the Verbatim configuration of the Intel Skylake architecture" (footnote 3: github.com/darchr/gem5-skylake-config). Two-minute timeout per run.
- **Compiler (p. 6):** GCC 9.3.0, C++17, -O3. So every reported speedup is on top of the optimizing compiler.
- **Models (Section 4, p. 5-6):** CodeLlama 7B, 13B, 34B (base, not instruction-tuned), gpt-3.5-turbo-0613 (prompted and fine-tuned), gpt-4-0613 (prompted only, fine-tuning was not available).
- **Decoding:** temperature 0.7, Best@1 and Best@8.
- **Fine-tuning data variants (Section 3.2):** "All" (full training set); "HQ" (4,085 high-quality pairs: highest speedup, at most 4 pairs per problem, 2.77 pairs per problem on average); "All w/ Perf-Cond"; "HQ + Self-Play" (HQ plus 1,485 synthetic pairs).
- **Training hardware (A.8, p. 19-20):** 8 × 48 GB GPUs (RTX A6000 / L40), batch size 32, learning rate 1e-5, AdamW. HQ fine-tuning under 12 hours. Full-data and performance-conditioned fine-tuning: 1 epoch, 24 to 36 hours.
- **Repetitions and statistics:** none for timing, because gem5 is deterministic. No confidence intervals or significance tests anywhere in the paper.

## Section-by-section notes

### Abstract and 1. Introduction (pp. 1-3)
- States the measurement problem directly: "A major challenge is the significant variability of measuring performance on commodity hardware, which can lead to spurious 'improvements'" (abstract).
- p. 2: "we find that benchmarking on real hardware can lead to large, phantom performance 'improvements' due only to random chance." The causes named are "server workload and configuration issues".
- gem5 is called "the gold standard CPU simulator in academia and industry". The evaluation strategy is "entirely deterministic, ensuring both reliability and reproducibility".
- Three contributions: the dataset with gem5 time labels; an evaluation of prompting and fine-tuning; three adaptation strategies (retrieval prompting, performance-conditioning, self-play).
- Figure 1 (p. 2): summing 1..N with a loop (O(N)) against a closed formula (constant time). This is the kind of edit they want.

### 2. Performance Improving Edits (PIE) Dataset (pp. 3-4)
- Dataset construction as above.
- **The measurement argument (the part most relevant to us):**
  - "Benchmarking program performance is notoriously difficult. For instance, code instrumentation introduces overhead, and there is substantial variance across executions due to factors such as server load and idiosyncrasies introduced by the operating system." (p. 3)
  - "If benchmarking is not performed carefully, it is easy to mistakenly over-report program optimization results. With enough samples and variance, benchmarking the same exact program can easily lead us to report significant optimizations." (p. 3)
  - **The experiment:** with HYPERFINE they benchmarked 500 program "pairs" where the slow and the fast program are the *same program*. The true ratio is 1. They "observed a mean speedup of 1.12×, with a standard deviation of 0.36, and the top 5% of pairs exhibited a speedup of 1.91×" (pp. 3-4).
  - What this means: an identical program looked 12% faster on average, and one pair in twenty looked almost twice as fast. Their own dataset filter keeps pairs with more than 10% improvement, so real-hardware noise of this size would let many fake pairs through.
  - This is an A/A test (same code on both sides). It is the same idea as our base-against-base control.
  - **The fix:** "Executing deterministic programs in gem5 provides deterministic performance results. This enables reproducibility in research and denoised performance measurements." (p. 4)
  - Footnote 2: "This assumes gem5 terminates. Our experiments use a two-minute timeout, which may introduce slight variability. Note that altering this timeout could change the results."
  - Extra benefit they claim: the framework "can be applied to other platforms like ARM or RISC-V without having access to hardware for those platforms."
- **What the paper does not say about the real-hardware experiment:** which machine, which OS, how many HYPERFINE runs per program, whether CPUs were pinned or isolated, whether frequency scaling was off, whether other jobs were running, and how the 500 programs were chosen. So the 1.12× is the noise of *one unspecified setup*, not a general number for real hardware.

### 3. Adapting Code LLMs to Program Optimization (pp. 4-5)
- 3.1 Prompting: instruction-only; few-shot with two random (slow, fast) pairs; CoT plus few-shot; dynamic retrieval of the K closest training programs.
- 3.2 Fine-tuning: plain; HQ subset; performance-conditioned (tags 1/10 to 10/10, Figure 2); synthetic data. For synthetic data GPT-3.5 produced new programs; after filtering they had 3,314 unique synthetic programs; they kept pairs where the optimized version was at least 5× faster and at most three semantic duplicates, giving 1,485 pairs.

### 4. Experiments (pp. 5-9)
- Metrics as defined above. "A program must be at least 10% faster and correct to contribute" to %Opt (p. 6).
- Wrong or slower outputs get speedup 1.0, "given that, in the worst case, the original program has a speedup of 1.0" (p. 6). So the mean speedup can never go below 1.
- **4.1 Prompting (Tables 2-3):**
  - Without PIE data the models are weak. Best baseline: GPT-3.5 with CoT, Best@8: 43.05% Opt, 1.60× speedup, 91.72% correct.
  - Few-shot with fixed random examples is often no better than a plain instruction (GPT-3.5 Best@8: instruction-only 1.54×, few-shot 1.38×).
  - GPT-4 with CoT beats GPT-3.5 at Best@1 (1.32× vs 1.25×) but loses at Best@8 (1.58× vs 1.60×). The authors guess GPT-4 outputs are less diverse.
  - Dynamic retrieval with K=4 (Table 3): GPT-4 Best@8 reaches 76.07% Opt, 3.93×, 95.71% correct. CodeLlama 34B: 42.54%, 2.43×, 73.62% correct.
  - "We note that increased speedup may, however, come with some cost of correctness." (p. 7)
- **4.2 Fine-tuning (Table 4):**
  - The small HQ set beats the full set: CodeLlama 13B Best@8 goes from 2.71× (All) to 3.43× (HQ).
  - Performance-conditioning on the full set: CodeLlama 13B Best@8 5.65×, 66.56% Opt, but only 70.96% correct.
  - GPT-3.5 fine-tuned on HQ: 6.74×, 86.71% Opt, 95.40% correct. With self-play data: 6.86×, 87.63% Opt, 95.09% correct. This is the headline model.
  - Footnote 4: to check that the gain comes from the kind of data and not the amount, they fine-tuned on the top 5,793 PIE pairs instead of the 5,570 pairs that include synthetic programs, and Best@1 got worse.
  - **Model against the best humans:** 39,129 model generations against 118,841 accepted human solutions (197,921 with incorrect or timed-out ones). Best human speedup 9.56×, model 9.64×.
- **4.3 Discussion:** open models can come close to closed ones with the right adaptation; fine-tuning beats prompting for the same model size; retrieval and performance-conditioning give the largest gains.

### 5. Related work and 6. Conclusion (p. 9)
- Related work lists machine learning for refactoring, compiler transformations, parameter search, auto-vectorization, GPU code, algorithm selection, DeepPERF (C# performance patches), superoptimization and MAGPIE (genetic improvement).
- No measurement-methodology papers are cited (no benchmarking-statistics or measurement-bias literature).
- Conclusion: "given a correctness oracle", LLMs enable "automatic code optimization beyond optimizing compilers".
- There is no threats-to-validity section and no future-work section. Future directions appear only in passing (combine with program repair, A.4).

### Appendix A.1: what kinds of edits make the code faster (p. 14)
- Manual analysis of 120 randomly sampled (source, optimized) pairs from the best model.
- Four categories: Algorithmic about 34.15%; Input/Output about 26.02% (for example `cin/cout` to `scanf/printf`, reading a string in one go); Data Structure about 21.14% (for example vectors to arrays); Miscellaneous about 18.70%.
- These four percentages match 42, 32, 26 and 23 out of 123 (my arithmetic). So they seem to count 123 labelled changes in 120 pairs. The paper does not say this.
- **Spurious speedups:** "in 10 out of the 120 cases we examined, the speedup stemmed from reducing the constants used to allocate arrays." The authors say these "might not always reflect genuine algorithmic improvements, and indicate that the test cases may not perfectly cover all the cases". So about 8% of sampled speedups came from an edit that is probably not safe in general, and the tests did not catch it.

### Appendix A.2: examples (pp. 15-17)
- Figures 3-7: remove a sort (O(n log n) to O(n)), remove a wasteful nested loop, remove an unneeded precomputation, use a modular-arithmetic property (O(10^6) to O(B)), restructure a loop to avoid a check.
- In most examples the fast version also switches `cin/cout` to `scanf/printf`, so several changes are mixed in one edit.

### Appendix A.3: more generations (p. 17)
- HQ and HQ + Self-Play converge as the number of samples grows (Figures 8-9).
- The text says "the speedup and correctness increase from 6.74 → 6.86 and 86.71 → 87.63". In Table 4 these two pairs are Speedup and %Opt. %Correct goes down, 95.40% to 95.09%. The same paragraph says "there is a slight drop in correctness after training with Self-Play". So the sentence mislabels %Opt as correctness.

### Appendix A.4: error analysis (p. 18, Table 5)
- For the programs the best model failed to optimize: 12.51% did not compile; 27.59% got 95-100% of tests wrong; 12.08% got (75, 95%] wrong; 10.84% got (25, 75%] wrong; 6.90% got (0, 25%] wrong; 9.93% correct but slower; 9.40% correct and same speed; 10.75% correct and faster but under 1.1×.
- Read: more than half of the failures are wrong programs (the four "tests wrong" rows sum to 57.41%), and when the model is wrong it is usually very wrong.
- Correlations: problem description length against accuracy -0.15, source length against accuracy -0.26; against speedup -0.16 and -0.11. Longer inputs hurt correctness a little.
- Performance-conditioning lowers correctness. Mixing tags 10/10, 9/10 and 8/10 (2 generations each) instead of six at 10/10 raised %Correct from 59.95% to 64.36% for the 7B model.

### Appendix A.5 to A.11 (pp. 19-25)
- A.5: dataset tables. Median program length in GPT-2 tokens (Table 8): train 417 (source) and 372 (target); test 362 and 319. These are short, single-file programs.
- A.6: self-play generation. 10,000 attempts, 6,553 not in PIE, 3,314 equivalence sets; over 1.4 million binary-input pairs executed; less than 72 hours on a 24-core Intel 13900k with 64 GB RAM.
- A.7 (Table 9): retrieval with K = 1, 2, 4. The paper calls K=4 "a preferable setting" (p. 7). It is not best everywhere: for GPT-4, K=2 gives a slightly higher speedup (Best@8 3.95× against 3.93×; Best@1 2.61× against 2.53×).
- **A.9 (p. 21):** CodeNet contains two identical submissions for problem p03160 (s766827701 and s964782197) for which "a speedup of 2.44× is reported, despite the programs and environments being identical." This is the evidence that the CodeNet time labels cannot be trusted. It is a single example; the paper gives no rate.
- A.10 (Table 10): LoRA fine-tuning is much weaker. Best@8 speedups 1.15× to 1.17×.
- A.11: the prompt templates (Figures 12-17).

## Key results (with numbers) and what they mean
- **A/A on real hardware: mean 1.12×, standard deviation 0.36, top 5% at 1.91× over 500 identical pairs (pp. 3-4)** -> naive wall-clock timing can "find" a speedup where none exists. Any study that reports speedups needs a same-code control or a noise-free measure.
- **CodeNet labels: 2.44× between identical submissions (A.9)** -> timing labels collected on an online judge are not usable as ground truth.
- **Human reference 3.66× (Table 1)** -> the mean speedup of the human edits in the test set. Their %Opt and %Correct are 100% by construction, because the test pairs were selected to be correct and more than 10% faster.
- **Best prompting without PIE: 1.60× (GPT-3.5, CoT, Best@8)** -> an LLM asked to "make it faster" with no examples usually gains little on these programs.
- **Instruction-only, Best@1: GPT-3.5 optimizes 16.26% and GPT-4 8.49% of programs (Table 2)** -> with one attempt and no help, a strong model fails to make most programs at least 10% faster.
- **Best fine-tuned: 6.86×, 87.63% Opt, 95.09% correct (GPT-3.5, HQ + Self-Play, Best@8)** -> above the human reference, but with 8 tries and picking the winner by measured time.
- **Performance-conditioned CodeLlama 13B: 5.65× but 70.96% correct** -> pushing for speed costs correctness. For about 3 in 10 test programs, none of the 8 samples was correct.
- **10 of 120 analysed speedups were spurious (A.1)** -> a measured speedup with passing tests is still not proof of a valid optimization.
- **9.64× (model) against 9.56× (best human)** -> the difference is under 1% and there is no noise to hide it, but the model had about 40 samples per program (39,129 generations) and the comparison is a best-of-many on both sides.

## Tables and figures
- **Figure 1 (p. 2):** slow and fast code for the sum 1..N. The motivating example.
- **Figure 2 (p. 5):** training and inference prompts with the score tag.
- **Table 1 (p. 6):** summary, best model per regime. Read: Speedup column 1.30× and 1.60× (prompt), 2.43× and 3.93× (retrieval), 5.65× and 6.86× (fine-tune), human 3.66×.
- **Table 2 (p. 7):** baselines, 5 models × 3 prompt styles, Best@1 and Best@8. Read: all Best@1 speedups are between 1.00× and 1.32×.
- **Table 3 (p. 7):** dynamic retrieval K=4. Read: GPT-4 jumps to 2.53× (Best@1) and 3.93× (Best@8).
- **Table 4 (p. 8):** fine-tuning variants. Read: compare within one model across datasets.
- **Table 5 (p. 18):** failure categories of the best model.
- **Tables 6-8 (p. 19):** dataset sizes and token lengths.
- **Table 9 (p. 20):** retrieval ablation over K.
- **Table 10 (p. 22):** LoRA results.
- **Figures 3-7 (pp. 15-17):** optimization examples.
- **Figures 8-9 (p. 17):** %Opt and speedup against number of generations for HQ and HQ + Self-Play.
- **Figure 11 (p. 21):** the duplicated CodeNet program with different reported CPU times.
- **Figures 12-17 (pp. 22-25):** prompts.

## Ideas we can use
- **Cite their A/A experiment as the reason for our A/A control.** They ran identical programs against each other and got a mean "speedup" of 1.12×. We run base against base for the same reason, per PR.
- **Use their words for the risk:** "phantom" or "spurious" improvements.
- **Their answer to noise is a simulator; ours is controlled hardware plus counters.** Instruction counts from `perf stat` are close to deterministic on a real machine, and they are available for real repositories. We can present counters as the middle way between noisy wall time and a simulator.
- **The 10% threshold.** Both their dataset filter and %Opt use "more than 10% faster". If we use a threshold for "faster", this is a precedent.
- **Their edit categories (A.1)** are a small precedent for labelling the *mechanism* of a speedup: algorithmic, I/O, data structure, miscellaneous. The I/O class (26.02%) is the one closest to something a kernel trace could see.
- **Spurious speedups from weak tests (10 of 120)** support our "output changed" verdict: faster is not enough, the behaviour must stay the same.

## Weaknesses and things glossed over
- **The real-hardware baseline is not described.** No machine, no number of runs, no CPU pinning, no load control. The 1.12× shows that *careless* benchmarking is noisy. It does not show that careful benchmarking on real hardware is noisy. The paper itself says the problem appears "if benchmarking is not performed carefully".
- **Deterministic is not the same as accurate.** The paper does not validate the gem5 Skylake model against a real Skylake machine. A simulator can be perfectly repeatable and still rank two programs differently from real hardware. This is not discussed.
- **One simulated machine.** All results are for one configuration. Whether a speedup holds on another CPU is not tested (the ARM and RISC-V remark is only a possibility).
- **Operating system and I/O.** About a quarter of the edits are I/O changes (`cin/cout` to `scanf/printf`). The paper does not say how the simulator handles I/O and system calls, or in which gem5 mode the programs run. So we cannot tell how much of the I/O gain would appear on a real kernel.
- **Timeout as a noise source.** The authors admit that the two-minute timeout "may introduce slight variability" (footnote 2), so the setup is not fully deterministic. The paper does not say how often this happens. Test cases that timed out were removed, which may remove the heaviest inputs.
- **Cost.** 42.8 million simulations for labels. The paper gives no simulation time per program. This approach does not scale easily to real repositories with builds, dependencies and long workloads.
- **Speedup metric is one-sided.** Wrong or slower outputs count as 1.0, so regressions are hidden in the mean. Best@8 picks the fastest correct sample using the same tests and the same timing that produce the score. In practice a user would need this oracle.
- **No uncertainty on model results.** Sampling at temperature 0.7 is random, but each configuration is run once. No confidence intervals.
- **Inconsistent numbers in the text:**
  - Section 4.3 says retrieval improved CodeLlama 34B "to 34.25% %Opt, 2.28× Speedup for Best@8". Table 3 (K=4) says 42.54% and 2.43×. The 34.25% / 2.28× values are the K=2 row of Table 9.
  - Section 4.1 says "Table 2 (bottom)" for retrieval results. They are in Table 3.
  - Section 4.3 compares performance-conditioning (trained on All) with the HQ model (47.75%, 3.43×). The like-for-like baseline is All: 43.76%, 2.71×.
  - A.3 calls the 86.71 → 87.63 change "correctness". It is %Opt.
  - The A.4 text rounds Table 5 loosely ("about 10%" syntax errors is 12.51%).
- **Scope.** Single-file C++ programs for competitive programming, median 362 tokens in the test set, 41 test problems. No repositories, no build systems, no concurrency, no real workloads.
- **Human reference is not a human upper bound.** 3.66× is the mean of the pairs in the test set, which include small steps of 10%.
- **No threats-to-validity section.**

## Open questions and future work (theirs, and ours)
- Theirs: combine program repair with PIE to fix the incorrect outputs (A.4). Fine-tune larger open models with performance-conditioning (Section 4.3). Apply the framework to ARM or RISC-V (p. 4). The paper has no separate future-work section.
- Ours: How large is the A/A "speedup" on a controlled real machine (dedicated cores, fixed frequency)? If it is far below 1.12×, that is a direct answer to their argument. How often do real-hardware and simulator verdicts disagree? The paper cannot answer this. Do I/O edits like theirs show up as fewer `read`/`write` system calls in a kernel trace?

## Link to our paper
- **Related work (LLMs that optimize code):** PIE is the standard dataset of human performance edits and the standard reference for teaching LLMs to optimize. It works on small single-file programs and scores by simulated time only.
- **Method (measurement and A/A control):** cite for "the same program measured against itself can show a large speedup on real hardware". This motivates our base-against-base control and our use of hardware counters next to wall time.
- **Threats:** cite as the opposite design choice (simulator instead of hardware) and say why we stay on real hardware: real repositories, real kernel, real I/O.
- **Verdicts:** their %Opt needs both "at least 10% faster" and "correct". Our per-PR verdict has the same two parts, plus mechanism and hidden costs.

## Link to the thesis (tracing, kernel analysis)
- The paper names two classic problems of performance measurement: "code instrumentation introduces overhead" and variance from "server load and idiosyncrasies introduced by the operating system" (p. 3). These are the probe effect and OS noise. Both are things kernel tracing can measure directly (scheduler events, interrupts, page faults) instead of removing them with a simulator.
- A simulator removes OS noise but also removes the chance to see what the OS did. For a thesis on kernel analysis, the useful point is the contrast: PIE treats the OS as noise, we treat it as signal.
- Their I/O category (26.02% of edits) is a natural case for tracing: buffered against unbuffered I/O changes the number and size of `read`/`write` calls.
- gem5 gives per-program deterministic time. `perf stat -e instructions` gives a nearly deterministic count on real hardware at almost no cost. This is a cheap way to get part of the benefit they want.

## Quotes for inline citation
- "A major challenge is the significant variability of measuring performance on commodity hardware, which can lead to spurious 'improvements'." (p. 1, abstract)
- "we find that benchmarking on real hardware can lead to large, phantom performance 'improvements' due only to random chance." (p. 2)
- "If benchmarking is not performed carefully, it is easy to mistakenly over-report program optimization results." (p. 3)
- "With enough samples and variance, benchmarking the same exact program can easily lead us to report significant optimizations." (p. 3)
- "we observed a mean speedup of 1.12×, with a standard deviation of 0.36, and the top 5% of pairs exhibited a speedup of 1.91×." (pp. 3-4)
- "Executing deterministic programs in gem5 provides deterministic performance results." (p. 4)
- "The CodeNet dataset includes CPU time, but we found the information to be inconsistent" (p. 3)
- "in 10 out of the 120 cases we examined, the speedup stemmed from reducing the constants used to allocate arrays." (p. 14)

## Suggested citation sentences
- On commodity hardware, even two copies of the same program can appear to differ: Shypula et al. measured a mean "speedup" of 1.12× over 500 identical pairs \cite{shypula2024pie}. We therefore run a base-against-base control for every PR.
- PIE avoids this noise by timing programs in the gem5 simulator \cite{shypula2024pie}; we instead keep real hardware and a real kernel, and add hardware counters and kernel traces to see why the time changed.
- Work on LLM-based optimization has so far used small, single-file programs and scored them by execution time and test results only \cite{shypula2024pie}.
- Passing tests do not prove that an optimization is valid: in a manual check of 120 model edits, 10 speedups came from shrinking array-size constants \cite{shypula2024pie}.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It gives the best-known A/A result for code optimization: identical program pairs showed a mean speedup of 1.12× on real hardware. We build our base-against-base control on the same idea, but we apply it per PR and on a controlled machine.
  - It measures only "how much faster" and "still correct". It has no claim to check. The edits come from humans (or a model) without a stated reason, and the edit categories in A.1 were assigned by the authors after the fact on 120 samples. We check whether the mechanism the agent *claimed* is the one that moved.
  - It works on single-file C++ puzzle programs in a simulator. We work on real repository PRs on a real kernel, where system calls, page faults and lock waits exist and can be traced.
  - **Where it pushes against us:** the paper's position is that real hardware is too noisy and a deterministic simulator is the reliable choice. We measure on real hardware. A reviewer who knows PIE may ask why our timings can be trusted. Our answers are the dedicated cores, the A/A control, and counters such as instruction count that vary little between runs. We should report our own A/A spread next to their 1.12× so the reader can compare. We should not claim that their real-hardware number is wrong; their setup is simply not described.

- **Safe to cite for:**
  - Naive timing on real hardware can report speedups for identical code. Section 2, pp. 3-4: "we observed a mean speedup of 1.12×, with a standard deviation of 0.36, and the top 5% of pairs exhibited a speedup of 1.91×" (500 identical pairs, HYPERFINE).
  - Careless benchmarking leads to over-reported optimizations. Section 2, p. 3: "If benchmarking is not performed carefully, it is easy to mistakenly over-report program optimization results."
  - Instrumentation and the operating system both disturb measurements. Section 2, p. 3: "code instrumentation introduces overhead, and there is substantial variance across executions due to factors such as server load and idiosyncrasies introduced by the operating system."
  - Some prior work uses a CPU simulator to get deterministic timings. Section 2, p. 4: "Executing deterministic programs in gem5 provides deterministic performance results."
  - Timing labels from online judges are unreliable. Section 2, p. 3, and A.9, p. 21: "a speedup of 2.44× is reported, despite the programs and environments being identical."
  - A speedup with passing tests can still be invalid. A.1, p. 14: "in 10 out of the 120 cases we examined, the speedup stemmed from reducing the constants used to allocate arrays."

- **Do not cite for:**
  - "Real hardware cannot be measured reliably." The paper shows noise in one undescribed setup and says the risk is when benchmarking "is not performed carefully".
  - "gem5 results match real hardware." The paper does not validate the simulator against a real machine.
  - Anything about coding agents, pull requests, or real repositories. The models produce one rewritten program for a competitive-programming task.
  - "LLMs are better than humans at optimization" in general. 6.86× against 3.66× is Best@8 with an oracle that picks the fastest correct sample, on 978 pairs from 41 problems, compared with average individual human edits.
  - Any claim that the model's stated reasoning matches its edit. The CoT prompt asks for a strategy, but the paper never checks the strategy against the code or the measurement.
  - Hardware counters, system calls, kernel behaviour or tracing. The paper reports only simulated execution time.
  - A general rate of spurious speedups. "10 out of 120" is one manual sample from one model.
