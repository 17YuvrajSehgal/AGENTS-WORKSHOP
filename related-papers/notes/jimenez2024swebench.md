# SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
- **Authors:** Carlos E. Jimenez*, John Yang*, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, Karthik Narasimhan (* equal contribution; Princeton University, Princeton Language and Intelligence, University of Chicago)
- **Venue / year / status:** ICLR 2024 (peer-reviewed conference paper, "Published as a conference paper at ICLR 2024"). Our copy is arXiv:2310.06770v3 [cs.CL], 11 Nov 2024, which adds Claude 3 Opus and GPT-4-turbo rows to Table 5.
- **PDF:** related-papers/6-agent-benchmarks/jimenez2024_swe-bench.pdf
- **Cite key suggestion:** jimenez2024
- **BibTeX-style reference:** Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik Narasimhan. 2024. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? In The Twelfth International Conference on Learning Representations (ICLR 2024). arXiv:2310.06770.

## In short
SWE-bench is a benchmark of 2,294 real GitHub issues from 12 popular Python repositories, each paired with the pull request that fixed it. A model gets the issue text and the codebase and must write a patch. The patch is judged by running the repository's own tests: the tests the original fix made pass (fail-to-pass) must pass, and tests that already passed (pass-to-pass) must still pass. In this paper, models are not agents: they get files chosen by BM25 retrieval or an "oracle" and produce one patch in one shot. The best model with BM25 (Claude 2) resolved 1.96%; Claude 3 Opus (added in v3) resolved 3.79%.

## Problem and motivation
- Existing code benchmarks (HumanEval and similar) are short, self-contained problems and are near saturation.
- Real software work needs navigation of large codebases, edits across functions and files, and long context.
- Coding tasks are attractive because results can be checked by running tests.
- The authors want a benchmark that is realistic, hard, easy to verify, and easy to refresh with new issues (to avoid training data contamination).

## Background / key terms
- **Task instance:** one issue + the codebase at the PR's base commit + hidden tests + the reference ("gold") patch.
- **Gold patch (δ):** the non-test part of the real PR's code change.
- **Test patch (T):** the test-file part of the PR. It is applied before running tests and is not shown to the model.
- **Fail-to-pass (F2P) tests:** tests that fail before the gold patch and pass after. They check that the issue is fixed.
- **Pass-to-pass (P2P) tests:** tests that pass before and after. They check that nothing else broke.
- **Resolved:** the patch applies and all F2P and all P2P tests pass.
- **BM25:** a classic keyword-based search method. Here it picks which source files to put into the model's context.
- **Oracle retrieval:** give the model exactly the files the gold patch edited. Not realistic; used for analysis.
- **Execution context:** a conda environment per repository release version with the right Python version and dependencies.
- **SWE-bench Lite:** 300 instances chosen to be more self-contained, for cheaper evaluation.
- **SWE-bench Verified:** not part of this paper (it is a later, separate subset). Our study uses it, so we must cite it separately.

## Method and setup
- **Construction (Section 2.1, Appendix A):**
  - Stage I: pick the top 100 of the 5,000 most downloaded PyPI packages (Aug 2023), keep those with permissive licenses and GitHub repos; crawl 93,139 PRs from 12 repos.
  - Stage II: keep merged PRs that resolve an issue (linked with "fixes #N" style keywords) and change test files: 11,407 candidates.
  - Stage III: install, apply test patch, run tests, apply gold patch, run tests again. Drop if any step fails, if `ImportError`/`AttributeError` appears before the fix (naming the model cannot guess), or if no test goes fail to pass. Final: 2,294. The validation step "generally removes half of the candidate task instances".
- **Problem statement:** issue title and body plus issue comments created before the PR's first commit (to avoid leaking the solution). PR comments before the first commit are kept as `hints_text` but not used.
- **Evaluation (Appendix A.4):** checkout base commit, activate conda env, install, apply test patch, apply model patch (with an automatic repair step if it fails to apply), run tests, parse logs per repository. A missing test counts as failed.
- **Models:** ChatGPT-3.5 (gpt-3.5-turbo-16k-0613, 16,385 tokens), GPT-4 (gpt-4-32k-0613, 32,768 tokens; only a 25% random subset of 574 instances for BM25 27k and oracle, due to budget), Claude 2 (100,000 tokens), SWE-Llama 7b and 13b (≥100,000 tokens). v3 adds Claude 3 Opus and GPT-4-turbo.
- **SWE-Llama:** CodeLlama-Python 7b / 13b fine-tuned with LoRA (r = 16, α = 16, dropout 0.05, on q/k/v/o attention projections), learning rate 6e-4, batch 32 sequences, up to 4 epochs, checkpoint every 50 steps, best by validation loss on 100 held-out instances. Training data: 19,000 issue-PR pairs from 37 other repos (disjoint from the test repos), cut to 10,000 after dropping sequences over 30,000 tokens. 7b trained 20 h on 4 A100s; 13b 47 h on 8 A100s. DeepSpeed Ulysses and FlashAttention.
- **Inference:** one patch per instance, greedy decoding (Pass@1 style). Prompt: instructions, issue, retrieved files with README, an example patch, request for a single patch (Appendix D.3).
- **Retrieval limits:** BM25 with 13k, 27k, 50k token budgets; report the best for each model.
- **Hardware for running the tests:** not stated. Run times of evaluation: not stated.
- **Statistics:** percentages only; no repeated runs, no confidence intervals.

## Section-by-section notes
### 1. Introduction (p. 1-2)
Benchmarks are saturated; real software engineering needs large-repo reasoning. Contributions: SWE-bench (2,294), SWE-bench-train (19,000 instances from 37 repos), SWE-Llama 7b/13b. With BM25, Claude 2 resolves 1.96%.

### 2. SWE-bench (p. 2-4)
- 2.1 three-stage pipeline (above), Fig. 2.
- 2.2 task: input = issue + full codebase; output = patch; metric = % resolved.
- 2.3 features: real tasks; continually updatable; long inputs (issue 195 words on average; codebases thousands of files); robust evaluation (at least one F2P test, 40% have two or more; median 51 P2P tests); cross-context edits (gold patch average 1.7 files, 3.0 functions, 32.8 lines); wide scope for solutions, "from retrieval and long-context models to decision-making agents".
- 2.4 SWE-bench Lite: 300 instances, 11 of the 12 repos. (The text of this section and of Appendix A.7 is incomplete in the PDF: sentences break off.)
- Fig. 3 and Table 1: task count per repo and size statistics (below).

### 3. SWE-Llama (p. 4)
Off-the-shelf CodeLlama gives placeholder or unrelated output, so they fine-tune. Details above.

### 4. Experimental setup (p. 4-5)
- 4.1 BM25 vs oracle. With 27k tokens, BM25 retrieves a superset of oracle files in about 40% of instances, and none of the oracle files in almost half.
- 4.2 input format. 4.3 models and context limits (Table 4: share of instances that fit: 58.1% for 16k, 84.1% for 32k, 96.4% for 100k).

### 5. Results (p. 6-9)
- Table 5 (BM25): Claude 3 Opus 3.79% resolved (46.56% patches apply), Claude 2 1.97% (43.07%), ChatGPT-3.5 0.17% (26.33%), GPT-4-turbo 1.31% (26.90%), SWE-Llama 7b 0.70% (51.74%), 13b 0.70% (53.62%). Lite: Claude 3 Opus 4.33%, Claude 2 3.00%.
- Oracle (Table 18): Claude 2 4.80%, ChatGPT-3.5 0.52%, GPT-4 1.74% (subset), SWE-Llama 7b 3.01%, 13b 3.97%.
- Difficulty varies by repo (Fig. 4, Table 19). In oracle, Claude 2 and SWE-Llama 13b resolve 110 and 91, but Claude 2 solves only 42% of SWE-Llama's solved ones. Images in issues: 32% of matplotlib and 10% of seaborn instances, 2% overall.
- Longer context lowers performance (Fig. 5, Table 2): Claude 2 1.96% at 13k, 1.87% at 27k, 1.22% at 50k, although recall of oracle files rises (Table 3: 29.58%, 44.41%, 51.06% average recall).
- Oracle-collapsed (only edited lines ±15): Claude 3 Opus 9.39%, Claude 2 5.93%, GPT-4 3.40%, ChatGPT-3.5 1.09% (Table 6).
- No clear link to date (Table 7, Table 21): Claude 2 4.87% before 2023 vs 4.23% after.
- SWE-Llama is sensitive to context distribution shift (trained on oracle, bad on BM25).
- Patches are easier than full files: Claude 2 2.2% when regenerating whole files vs 4.8% with patches.
- Models make shorter edits (Table 8): applied model patches are 16.7-30.1 lines vs 74.5 lines for all gold patches.
- 5.1 qualitative: sphinx-8713 example (Fig. 6), the model edits the right function but ignores a config flag; 2 tests fail. Models write "primitive" Python, ignore existing helpers, solve "greedily".

### 6. Related work (p. 9)
Multi-task LM benchmarks; HumanEval and its extensions; ML for SE (commit generation, review, bug localisation, testing, program repair). Existing repair datasets (Defects4J, ManySStuBs4J) lack this scale of context.

### 7. Discussion (p. 10)
Python only. Baselines are the simplest approaches; future work should try "agent-based approaches, tool augmented LMs". Execution-based tests alone cannot guarantee quality: model code can be less comprehensive, efficient, or readable.

### 8-10. Ethics, reproducibility, acknowledgements (p. 11)
Public, permissively licensed repos; no human subjects; full code and data released.

### Appendix (p. 16-52)
- A.1-A.4: construction and evaluation details (above). Table 9: instance fields (`base_commit`, `created_at`, `hints_text`, `instance_id`, `patch`, `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`, `env install commit`, etc.). Table 10: funnel per repo (93,139 -> 11,407 -> 2,294).
- A.5: per-repo stats (Table 11), licenses (Table 12), issue tag categories (Table 13: Bug 442, Feature 167, Regression 39, Other 1,641), CDFs (Fig. 9): median issue 140 words, codebase just under 1,900 files and 400K lines, gold patch edits about 15 lines in one function, one F2P test and 51 P2P tests. Table 14: patch generation, apply and auto-fix rates (for example Claude 2 BM25: 2,281 generated, 988 applied, 30.57% needed the fix).
- A.6: development set of 225 instances from 6 other repos (created after 1 Jan 2019): 19.9 average / 2 median F2P tests; 171.3 / 79.0 P2P; 191.2 / 101.0 total.
- B: SWE-Llama training details (above).
- C.1-C.4: oracle results, per-repo results, GPT-4 subset results (Table 20, subset is not easier or harder), temporal analysis by year (Table 21).
- C.5: six outcome types for applied patches (Table 22): Resolved, Breaking Resolved (F2P all pass, some P2P fail), Partially Resolved, Work in Progress, No-Op (nothing changes), Regression (no F2P passes and some P2P fail). Table 23: for Claude 2 oracle, 1,078 applied: 110 resolved, 26 breaking resolved, 15 partially, 20 work in progress, 471 no-op, 436 regression. Of unresolved, 60-70% are no-ops.
- C.6-C.7: patch size on all patches (Table 24); software metrics with Radon (cyclomatic and Halstead) on a requests example (Fig. 10: model patch raises `HTTPAdapter` complexity 3 -> 5).
- D: retrieval details (file paths prepended to documents), greedy decoding, prompt template.
- E: societal impact (AI safety testbed).
- F: ten qualitative case studies (Tables 25-34), for example correct but "primitive" fixes, an image-based seaborn issue, a SWE-Llama fix that breaks other code because it ignores callers of the changed function.

## Key results (with numbers) and what they mean
- **2,294 tasks from 12 repos; django alone has 850 (37%), sympy 386** -> the benchmark is dominated by a few repos. A small sample (like our 10 issues) may come mostly from them.
- **Median 51 pass-to-pass tests, mean 120.8 total tests (max 9,459)** -> "solved" includes running many existing tests. Test runs are a real CPU and memory load inside tool time.
- **Resolved needs all F2P and P2P tests to pass; a missing test counts as failed** -> if a machine limit kills a test process (OOM) or a test times out, the run is scored as not solved. Machine limits can change the benchmark score without changing the model's skill.
- **Best BM25 result 1.96% (Claude 2), 3.79% (Claude 3 Opus)** -> one-shot, non-agent models were very weak in 2023-2024. Today's agents score far higher (not in this paper), which is why agent runtime now matters.
- **More context lowered score (1.96% -> 1.22% from 13k to 50k)** -> finding the right code is the hard part; this motivates agents that search and run tools, which is the workload we study.
- **One greedy sample per instance, no repeats** -> these numbers have no error bars.

## Tables and figures
- **Fig. 1:** the task: issue + codebase -> model -> patch -> unit tests.
- **Fig. 2:** three-stage filtering pipeline.
- **Fig. 3:** task count per repo (django 850, sympy 386, scikit-learn 229, sphinx 187, matplotlib 184, pytest 119, xarray 110, astropy 95, pylint 57, requests 44, seaborn 22, flask 11).
- **Table 1:** mean / max per instance: issue 195.1 / 4,477 words; codebase 3,010 / 5,890 non-test files and 438K / 886K lines; gold patch 32.8 / 5,888 lines, 1.7 / 31 files, 3 / 36 functions; tests F2P 9.1 / 1,633, total 120.8 / 9,459.
- **Tables 2-3:** BM25 context length vs resolve rate and vs recall of oracle files.
- **Table 4:** context window per model and share of instances whose oracle input fits.
- **Table 5:** main results (BM25) for full and Lite.
- **Fig. 4 / Table 19:** resolve rate per repo; requests is easiest (Claude 2 15.91% oracle), seaborn 0% for all.
- **Fig. 5:** Claude 2 performance by total input tokens and by issue tokens; both fall as length grows.
- **Table 8 / Table 24:** model patches are shorter than gold patches.
- **Table 10:** construction funnel per repo.
- **Table 11:** per-repo means; xarray has the largest test sets (356.1 tests on average, 58.5 F2P).
- **Tables 22-23:** outcome categories for applied patches.

## Ideas we can use
- Use their exact definition of "resolved" and cite it: our "solved = target tests pass and previously passing tests still pass" is the SWE-bench F2P + P2P rule.
- Use their outcome categories (Table 22) to describe what limits do to correctness: for example, under a memory limit a run might move from "Resolved" to "Breaking Resolved" if some P2P tests are killed. This would make our behaviour findings (silent kills inside tests) more precise.
- Report per-repo test-suite sizes (Table 11) for our 10 issues, since test count likely explains why some tasks are long and heavy.
- The paper says evaluation is "time-consuming" and costly but gives no runtimes. Our work fills that gap for agent runs.

## Weaknesses and things glossed over
- **No runtime or resource data.** No wall time, CPU, memory, or disk numbers for setup, test runs, or evaluation. Execution environment hardware not stated.
- **Not an agent benchmark in this paper.** Models get retrieved files and produce one patch; agents are only listed as future work.
- **No repeats or error bars** (single greedy sample).
- **GPT-4 run only on a 25% subset** for budget.
- **Tests as the only judge:** the authors admit tests cannot prove quality; also tests can be weak or flaky (flakiness not discussed).
- **Some tasks may be unfair or underspecified**; the paper filters some (new names in tests) but does not validate solvability by humans. (This gap motivated the later Verified subset; that history is outside this paper.)
- **Python only; 12 repos; django heavy.**
- **Contamination:** they argue the date analysis shows little effect, but older issues and fixes may be in training data.
- **Unfinished text:** Section 2.4 and Appendix A.7 have broken sentences; abstract says 1.96% while Table 5 says 1.97% for Claude 2.
- **Environment:** conda per release version, so results can depend on dependency versions installed at evaluation time.

## Open questions and future work (theirs, and ours)
- Theirs: more languages and domains; agent and tool-augmented approaches; better metrics than tests (software engineering metrics in C.7); execution feedback so models can test before submitting (end of C.5); image understanding.
- Ours:
  - How often do machine limits flip an agent's result from solved to unsolved through test failures, not through the agent's reasoning?
  - How long do SWE-bench test suites take under CPU, memory and disk limits, and is the test phase the main local cost in long tasks?
  - Do benchmark leaderboards hide hardware differences? Two labs on different machine sizes could report different resolve rates for the same agent.

## Link to our paper
- **Study Design:** cite as the source of the task format and of the solved rule (F2P + P2P). Cite SWE-bench Verified separately for the subset we draw from.
- **Intro / Related Work:** SWE-bench measures whether an issue is solved, not how long it takes or what machine it needs. Our paper adds the machine side: how cgroup limits change wall time and outcome.
- **RQ on behaviour (finding 4):** their rule that "a missing test or non-pass status counts as fail" means our silent kills inside tests directly lower the measured solve rate. This links our OOM findings to benchmark validity.
- **Threats:** our 10 issues are a small sample of a benchmark that is itself concentrated in a few repos (django 37%).

## Link to the thesis (tracing, kernel analysis)
- Not a tracing paper. But the test phase it defines (install, apply patches, run pytest/tox) is a clear, repeatable workload to trace: process creation storms, imports (disk reads), and memory peaks. It could be a standard "tool time" workload for kernel analysis of agents.
- Their per-repo test counts (Table 11) could predict tool-time cost; we could check this against trace-derived CPU time per tool call.

## Quotes for inline citation
- "The best-performing model, Claude 2, is able to solve a mere 1.96% of the issues." (p. 1, abstract)
- "If the patch applies successfully and all of these tests pass we consider the proposed solution to have successfully resolved the issue." (p. 3)
- "In addition, a median of 51 additional tests run to check whether prior functionality is properly maintained." (p. 3)
- "Evaluating LMs on SWE-bench can be time-consuming and, depending on the model, require a costly amount of compute or API credits." (p. 3)
- "If a test is missing or has a non-pass status, it is considered a fail status." (p. 21)
- "As defined and used in the main paper, a task is considered solved if all tests across FAIL TO PASS and PASS TO PASS pass." (p. 21)
- "we do not intend to constrain future methodologies to the same type of approach and encourage future work to investigate different methods (e.g., agent-based approaches, tool augmented LMs)." (p. 10)

## Suggested citation sentences
- We use issues from SWE-bench \cite{jimenez2024}, where a run counts as solved only if the tests fixed by the original pull request pass and all previously passing tests still pass.
- SWE-bench scores correctness only and does not report how long tasks take or what machine they need \cite{jimenez2024}; we study the machine side of the same tasks.
- Because SWE-bench counts a missing or killed test as a failure \cite{jimenez2024}, a memory limit that kills a test process lowers the measured solve rate even when the agent's patch is correct.
