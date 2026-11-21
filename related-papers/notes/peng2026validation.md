# How Do Coding Agents Optimize Software and Report Performance Validation? A Large-Scale Empirical Study of Open-Source Pull Requests
- **Authors:** Huiyun Peng, Ricardo Calvo (these two contributed equally), Kelechi G. Kalu, James C. Davis (all Purdue University, West Lafayette, Indiana, USA)
- **Venue / year / status:** arXiv:2610.03969v1 [cs.SE], 2 October 2026. Preprint. The paper does not name a venue. It is typeset in a Springer journal style and the replication repository is called `EMSE-perf-pr-study`, which suggests a submission to Empirical Software Engineering, but the paper does not say this. 46 pages (text ends on p. 40, references pp. 40-46). Funded by NSF award #2343596.
- **PDF:** `related-papers/peng2026validation_2610.03969.pdf`
- **Cite key:** peng2026validation
- **BibTeX-style reference:** Huiyun Peng, Ricardo Calvo, Kelechi G. Kalu, and James C. Davis. 2026. How Do Coding Agents Optimize Software and Report Performance Validation? A Large-Scale Empirical Study of Open-Source Pull Requests. arXiv:2610.03969.
- **Data and code:** dataset on Hugging Face (`rcalvome/EMSE-perf-pr-study`), scripts and prompts at `github.com/PurdueDualityLab/EMSE-perf-pr-study` (Section 8.5).

## In short
The authors rebuild and extend the AIDev collection to June 1, 2026 and take a balanced sample of 1,130 agent-authored and 1,130 human-authored performance pull requests (PRs). They read what each PR says (title, description, comments, commit messages, CI names, diff) with three LLMs and a majority vote. They never run any code. Agents and humans use almost the same optimization types and report validation at almost the same rate (82.3% vs 80.6%). The form differs: agents lean on static reasoning (51.4% vs 39.3% of validated PRs), humans on benchmarks (57.2% vs 46.1%), but the benchmark gap closes by 2026-Q2 (60.1% vs 58.7%). In both groups only about half of the PRs with validation contain any number (50.9% vs 52.4%), and trade-offs such as extra memory are almost never reported.

## Problem and motivation
- Agents now open many PRs that claim to improve performance. It is unclear whether these PRs follow known optimization practice and whether they give enough evidence for the claim (Abstract, Section 1).
- Their earlier pilot (MSR 2026 Mining Challenge, cite key `peng2025optimization`) had a small, unbalanced sample (324 agent vs 83 human PRs) with different repository thresholds (at least 100 stars for agents, at least 500 for humans). This paper fixes that and adds two new questions (Section 1).
- Four research questions (Section 1):
  - RQ1: adoption (merge rate, time to merge), patch size, maintainability indicators.
  - RQ2: which optimization patterns occur.
  - RQ3: reported testing and validation, and how it changes over time.
  - RQ4: which quantitative metrics are reported, and whether they fit the optimization.

## Background / key terms (explain each term simply)
- **Agentic PR:** a PR "authored and submitted by an autonomous coding agent" (Section 3.1.2). A PR where a human only used AI help (generated code, a Co-Authored-By line, an AI review) is called **AI-assisted** and is not agentic. AI-assisted PRs are removed from both groups.
- **Human-authored PR:** here it only means "no visible sign of bots or AI". Footnote 4: this "does not confirm human authorship".
- **Performance PR (perf PR):** a PR whose task type is "perf". Found in two steps: first by the title prefix (Conventional Commit style, for example a title that starts with `perf`), then by an LLM for the rest.
- **SysLLMatic catalog:** a list of source-level optimization techniques from the same group. Original: 43 patterns in 7 categories. Refined in the pilot to 59 patterns in 9 categories. A **category** is the broad strategy (for example Memory and Data Locality). A **pattern** is the specific mechanism (for example Caching).
- **Validation evidence types (Section 2.1.2 and 3.4.1):**
  - *Benchmark-Based Validation:* "quantitative measurements (e.g., unit tests or microbenchmarks) to directly assess performance impact". The prompt says "unit tests/microbenchmarks with before-and-after metrics".
  - *Profiling-Based Validation:* profiling artifacts such as "hotspot traces, CPU samples, or flame graphs" that show where the cost is.
  - *Static-Reasoning-Based Validation:* an argument about the algorithm (complexity, allocations) "without relying on runtime data".
  - *Anecdotal or Informal Local Testing:* a validation claim "without quantitative measurements or analytical support" (for example "tested locally, feels faster").
  - *No performance validation:* no evidence at all.
- **NLOC:** lines of code without comments. **AvgCCN:** average cyclomatic complexity (how many independent paths a function has). Both computed with the tool Lizard, version 1.24.0.
- **Chi-square test:** checks whether two categorical variables (for example author type and validation type) are related. **Cramér's V:** the strength of that relation, 0 = none, 1 = perfect.
- **Mann-Whitney U test:** compares two groups without assuming a normal distribution. **Cliff's delta:** its effect size, from -1 to 1; positive here means larger for agents.
- **Benjamini-Hochberg correction, q-value:** a p-value adjusted for running many tests at once.
- **Logistic regression, odds ratio per year:** how much the odds of a yes/no outcome multiply per year. 1.0 means no change.
- **Wilson interval:** a confidence interval for a proportion that behaves well with small samples.
- **Permutation test:** shuffle the labels many times to see what result chance alone would give.
- **Metric dimensions M1 to M9 (Table 1, p. 6):** M1 latency / execution time, M2 throughput, M3 memory, M4 CPU / compute work ("cycles, instructions, and function-call counts"), M5 I/O and network ("bytes transferred, database queries, network round trips, or API calls", cache hit rate), M6 artifact size, M7 build and CI time, M8 energy and cost, M9 scalability / concurrency. **M0** is added in Section 3.5.1 for a number with no named metric (for example "3-5x overall performance improvement").

## Method and setup
**Dataset (Section 3.1.2, Table 2, Fig. 2)**
- Based on AIDev-v3 (collection ends August 1, 2025). Footnote 1: AIDev-v4 exists, extends to November 2025 and adds Google Jules, but they did not use it.
- They re-run AIDev's pipeline on its frame of 2,807 repositories, same threshold (at least 100 stars) for both groups, from December 24, 2024 to June 1, 2026 ("extending the observation window by ten months").
- Mining gives 1,603,213 PRs. Attribution: 78,696 agentic, 1,524,066 human-authored, 451 unresolved.
- Perf classification: the title-prefix rule classifies 703,044 PRs, of which 7,952 are perf. The other 900,169 go to an LLM (`gpt-5.6-luna` with AIDev's prompt, in place of AIDev's `gpt-4.1-mini`), which finds 21,531 more perf PRs, cost about $110. Total 29,483 perf PRs: 1,356 agentic and 28,127 human-authored.
- Stricter human filter (bots, agent accounts, AI co-author trailers, AI statements, AI review signals, AI-generated metadata) removes 3,447, leaving 24,680.
- Quality filters (empty filenames, configuration-only, deleted repositories, merge-only): agentic 1,356 -> 1,130 (204 empty filenames, 20 config-only, 2 merge-only). Human 24,680 -> 24,235 (61, 375, 9).
- Sampling: keep all 1,130 agentic PRs and draw the same number of human PRs inside each of 65 ISO weeks. Final sample 2,260 PRs, balanced 1:1 overall and per week.
- Agents in the sample (Fig. 3, p. 13): GitHub Copilot 458 (40.5%), OpenAI Codex 392 (34.7%), Cursor 160 (14.2%), Devin 65 (5.8%), Claude Code 55 (4.9%).
- Overlap with the pilot: only 134 of the pilot's 407 PRs (32.9%) are in the new sample. Of the 324 pilot agentic PRs: 134 kept, 45 missing from the new collection, 75 "no longer meet the performance classification", 70 removed by quality filters. None of the 83 pilot human PRs are in the new sample.

**Accuracy of the perf classifier (Section 3.1.2)**
- Against AIDev's own labels on shared PRs: 64.4% precision, 72.5% recall, F1 68.2%. So the two pipelines often disagree on what a perf PR is.
- Against 100 PRs labelled by hand by one author: 83.3% precision, 84.7% recall, F1 84.0%.
- On the 28 hand-labelled PRs that are in both datasets: their classifier recall 82.4% vs AIDev 52.9%, F1 80.0% vs 64.3%; AIDev precision 81.8% vs 77.8%.

**RQ1 (Section 3.2):** merge status, time to merge (merged PRs only), added + deleted lines, changed files, commits, and percentage change in mean file NLOC, AvgCCN and function count. Structural metrics exist for 2,029 PRs (1,005 agentic, 1,024 human).

**RQ2 (Section 3.3):** three LLMs (GPT-5.6-sol, Gemini-3.1-Pro-Preview, Qwen3.8-27B, temperature 0) each give one category and one pattern per PR. A label is kept when at least two models agree on the pair. No human adjudication. All three agree on 1,238 PRs, two agree on 845, so 2,083 are labelled (92.2%): 1,049 agentic and 1,034 human. 177 are unresolved and dropped.

**RQ3 (Section 3.4):** same three models. Input per PR: "title, description, issue and review comments, commit messages, CI workflow names, and code diff". 2,258 PRs had complete evidence (1,129 per group).
- Stage 1, is there validation? Majority vote of three yes/no votes. Yes: 1,839 (929 agentic, 910 human). No: 419 (200 agentic, 219 human).
- Stage 2, which **one primary** type? Kept when two models agree: 1,396 with three agreeing, 423 with two (98.9%). 20 unresolved (11 agentic, 9 human). Final: 1,819 PRs (918 agentic, 901 human).
- The prompt rule: set validation present "only if explicit evidence is shown; never infer validation from performance intent alone".
- Time analysis: logistic regression with author type, time, and their interaction; standard errors clustered by repository.

**RQ4 (Section 3.5):** only PRs with validation and an RQ2 label: 1,699 (858 agentic, 841 human).
- Metrics are found with **regular expressions**, not LLMs. A match needs a metric keyword (throughput, heap, bundle size) plus a number with a unit (120ms, 4MB) or a comparison (2.5x faster, -40%).
- Precision check: three LLMs reviewed 88 PRs (44 + 44): 77 true positives, 11 false positives (12.5%). Recall was not measured.
- Fit to the optimization: for each pattern, the catalog says which metrics it should improve; they check whether the PR reports at least one of them, against a 20,000-iteration permutation baseline.
- Trade-off check: caching and buffering PRs with benchmark or profiling evidence; do they report a runtime-side metric (M1, M2 or M5) and memory (M3)? Three LLMs then decide whether memory got worse (a trade-off) or better.
- Code-smell check: compare the category Code Smells and Structural Simplification with the other eight.

**What they did not do:** "we do not execute the changed code, repeat benchmarks or profiling, or independently verify reported values or performance claims" (Section 3.5).

## Section-by-section notes

### 1. Introduction
- States the headline numbers: validation 82.3% vs 80.6%; merge 54.4% vs 73.3%; benchmarks 46.1% vs 57.2%; metric present 50.9% vs 52.4%.
- Main message: agents have become like humans in **what** they optimize, but neither group gives strong evidence that it works. "An important open problem for agent-authored optimization is therefore producing measurements that establish the intended effect and expose its trade-offs."

### 2. Background and related work
- 2.1.3 lists known trade-offs: caching and memoization cut time but raise memory; parallel code cuts wall-clock time but raises CPU and memory; compression cuts bandwidth and storage but raises CPU work.
- 2.3 Related work: RAPGen, Yi et al. (LLM against developer patches with JMH benchmarks), Watanabe et al., Li et al. (AIDev). They state that before their pilot "no work had compared agentic and human-authored performance pull requests".
- No related work on kernel tracing, hardware counters or re-executing PRs is discussed.

### 3. Methodology
- See "Method and setup" above.
- 3.3.2: they checked 20 of the 177 unresolved RQ2 cases by hand. About half touch several categories, about a quarter are low-level or front-end optimizations that the catalog does not cover, the rest are not clearly about performance.
- 3.4.2: models disagree on validation presence mostly when a PR states an expected gain as motivation. Some models read that as evidence.
- 3.5.1 consistency check: the extractor finds a metric in 42 of 382 PRs that RQ3 labels as having no validation (11.0%; 11.6% agentic, 10.4% human).

### 4.1 RQ1: adoption, size, maintainability
- Merge rate 54.4% (615/1130) agentic vs 73.3% (827/1129) human; q < 0.001, V = 0.195 (Fig. 4).
- Median time to merge, merged PRs only: 4.99 h vs 19.16 h; q < 0.001, delta = -0.207. Footnote 12: this does not show agents get faster review overall.
- Median added + deleted lines 130.5 vs 81.0; median commits 3 vs 2 (q < 0.001; delta 0.113 and 0.097). Median changed files 3 in both (q = 0.222).
- Median NLOC growth 1.70% vs 0.87% (delta 0.120); function count 0.50% vs 0.00% (delta 0.110); both q < 0.001. AvgCCN no difference (q = 0.624, delta 0.013).
- Meaning: agent PRs are somewhat bigger and add a bit more code, but all effect sizes are small. The merge-rate gap is the only clear difference.

### 4.2 RQ2: optimization patterns
- Category shares (Fig. 6, agentic / human): Memory and data locality 33.2% / 33.3%; Algorithm-level 21.2% / 20.8%; Structural simplification (code smells) 12.9% / 15.0%; I/O and synchronization 8.8% / 12.0%; Build and infrastructure 9.4% / 7.4%; Network and database 8.8% / 7.2%; Data structures 3.3% / 1.9%; Control-flow 2.0% / 1.7%; Loop transformations 0.5% / 0.8%.
- chi-square(8) = 16.14, p = 0.040, V = 0.088. Significant but very small. Largest gap is 3.2 points (I/O and synchronization).
- Pattern coverage: agents use 44 of 59 patterns, humans 43.
- The extra NLOC growth of agent PRs sits in two categories: build and infrastructure (median 2.43% vs 0.21%, q = 0.0004, delta 0.403) and network, database, data access (2.74% vs 1.05%, q = 0.041, delta 0.241).

### 4.3 RQ3: validation evidence
- **Presence:** 929 of 1,129 agentic PRs (82.3%) and 910 of 1,129 human PRs (80.6%). chi-square(1) = 0.95, p = 0.330, V = 0.021. No difference.
- **Type** (Fig. 7, share of the 918 agentic and 901 human PRs with validation and a resolved type; one primary type per PR):

| Primary type | Agentic (n=918) | Human (n=901) |
|---|---|---|
| Static reasoning | 51.4% | 39.3% |
| Benchmark | 46.1% | 57.2% |
| Profiling | 2.1% | 2.4% |
| Anecdotal | 0.4% | 1.1% |

- chi-square(3) = 28.52, p < 0.001, V = 0.125.
- Total counts over both groups (Fig. 1, p. 8): Benchmark 938, Static reasoning 826, No evidence 419, Profiling 41, Anecdotal testing 14, unresolved type 20.
- **Over time (4.3.2, Fig. 8):** validation presence per quarter. I matched the labels in the figure to the groups by checking that the counts add up to 929/1,129 and 910/1,129.

| Quarter | Agentic | Human |
|---|---|---|
| 2025-Q1 | 70.0% (7/10) | 70.0% (7/10) |
| 2025-Q2 | 63.9% (76/119) | 76.1% (89/117) |
| 2025-Q3 | 74.7% (136/182) | 72.2% (135/187) |
| 2025-Q4 | 76.4% (133/174) | 76.6% (128/167) |
| 2026-Q1 | 86.3% (278/322) | 79.6% (262/329) |
| 2026-Q2 | 92.9% (299/322) | 90.6% (289/319) |

- Odds of reporting validation grow by a factor of 3.06 per year for humans (95% CI [1.71, 5.49]) and 6.47 for agents (95% CI [3.30, 12.70]); both p < 0.001. First half of the period: 69.5% agentic vs 74.1% human. Second half: 88.0% vs 83.5%. The group-by-time interaction is **not** significant (p = 0.093), so the authors read the crossover "descriptively".
- Benchmark as primary type over time: humans stable (odds ratio per year 0.98, 95% CI [0.56, 1.73], p = 0.950); agents rising (3.63, 95% CI [1.32, 9.96], p = 0.012). Interaction is significant (odds ratio 3.69, 95% CI [1.24, 10.97], p = 0.019). 2025-Q2: 31.6% agentic vs 49.4% human. 2026-Q2: 60.1% vs 58.7%. The bottom panel of Fig. 8 has no printed values for the other quarters.
- The authors' own warning: "A benchmark-based label therefore establishes only that a measurement is reported, not that the measurement was produced by a sound experiment or can be reproduced."

### 4.4 RQ4: reported metrics
- At least one metric: 437 of 858 agentic PRs (50.9%), 441 of 841 human PRs (52.4%). So about half of the "validated" PRs contain no number that the extractor can find.
- Of the 878 PRs with a metric, 501 (57.1%) report exactly one (239 agentic, 262 human). Two or more metrics: 198 agentic (23.1%) and 179 human (21.3%).
- Fig. 9 (share of validated PRs, agentic / human): 0 metrics 49% / 48%; 1 metric 28% / 31%; 2 metrics 10% / 14%; 3 metrics 9% / 5%; 4 or more 4% / 2%.
- Which metrics (text of 4.4.1): latency / execution time 300 agentic PRs (35.0%) and 328 human (39.0%); memory 145 (16.9%) and 160 (19.0%); artifact size 115 (13.4%) and 38 (4.5%). "No other metric reaches 6% in either group." Energy or cost: 6 agentic and 2 human PRs.
- Fig. 10 rounded values for the rest (agentic / human): M9 scalability 5% / 5%; M0 unspecified 5% / 5%; M5 I/O and network 5% / 3%; M2 throughput 4% / 3%; M4 CPU / compute work 4% / 2%; M7 build and CI time 2% / 1%; M8 energy and cost 1% / 0%.
- Fit to the optimization: 34.5% of the 1,699 PRs report at least one metric that the pattern should improve, against 23.7% by chance (p = 0.002). Agentic 32.3% vs 23.5% baseline; human 36.7% vs 24.6%.
- Metric detection by evidence type (1,684 PRs with a type): benchmark 79.8%, profiling 30.8%, static reasoning 21.6%, anecdotal 18.2%.
- **Trade-offs (4.4.2):** 130 caching or buffering PRs with benchmark or profiling evidence (74 agentic, 56 human). 96 (73.8%) report a runtime-side improvement (74.3% vs 73.2%). 29 of the 96 also report memory (co-reporting 23.0% vs 21.4%). Of these 29, the LLMs call 17 a real trade-off (runtime better, memory worse) and 12 a joint improvement. Trade-offs: 10 of 17 agentic (58.8%), 7 of 12 human (58.3%). So 17 of 96 (17.7%; 18.2% agentic, 17.1% human) report the memory cost.
- **Code smells vs other changes (Table 5):** 290 code-smell refactoring PRs vs 1,791 others.

| Author | Category | Validation evidence | at least 1 metric (of validated) | Validation and at least 1 metric (of all) |
|---|---|---|---|---|
| Agentic | Refactorings | 83.0% | 45.5% | 37.8% |
| Agentic | Perf. changes | 81.7% | 51.7% | 42.3% |
| Human | Refactorings | 73.5% | 34.2% | 25.2% |
| Human | Perf. changes | 82.8% | 55.3% | 45.8% |

- Humans: all three contrasts significant (q <= 0.013). Agents: none significant (q >= 0.33). Interaction p, q: 0.043, 0.043 / 0.034, 0.043 / 0.007, 0.021.
- The authors read this as humans using judgment (a refactoring is obvious from the code, so less evidence), while agents treat every change the same.

### 5. Threats to validity
- Construct: merge is not quality; NLOC and CCN are not readability. Perf classifier checked on 100 PRs by one author. "The accepted RQ2 and RQ3 consensus labels were not independently re-audited and may contain classification errors." RQ3 measures what is written, not what was done. "a reported benchmark does not establish that it was executed as described or that its results were reported accurately." Agents may copy "the form of human validation reports, including plausible benchmark claims"; the analysis "cannot distinguish such imitation from genuine execution". Extractor precision 87.5%, recall unknown.
- Internal: observational; weekly balancing does not balance repository, language, contributors or workflow.
- Conclusion: repository clustering is handled only in the RQ3 time models; "the remaining inferences are unadjusted".
- External: public GitHub, at least 100 stars, five agents, until June 1, 2026.

### 6. Discussion
- 6.1: matching human practice should not be the goal, because human practice is also weak.
- 6.2: similar patterns may mean agents are capable, or that they copy human blind spots. Loop transformations are the least used category.
- 6.3: "The assurance target should therefore be the appropriateness and completeness of evidence, not merely the presence of validation or a benchmark". "our data cannot distinguish improved measurement from improved presentation". Existing CI benchmarking "is unlikely to scale to agent-driven workloads".
- 6.4: uses their MAGE framework (Model-Based Agentic Software Engineering). A performance "model" should state "the target metric, workload, baseline, measurement protocol, and acceptable costs in other resources". "performance cannot be inferred from code alone: a functionally correct change may yield no improvement, regress on other workloads, or appear beneficial because of measurement noise or experimental conditions". "PR descriptions provide only authors' accounts of what was measured."
- 6.5: an agentic dataset is a snapshot in time; results depend on the observation period.

### 7. Conclusion
- "These findings shift the central challenge from generating plausible optimizations to demonstrating that they work."

## Key results (with numbers) and what they mean
- Validation is reported in 82.3% of agentic and 80.6% of human perf PRs (p = 0.330) -> over the whole sample you cannot say that agents validate less often than humans. The pilot's finding (45.7% vs 63.6%) does not hold here.
- Among validated PRs with a type: static reasoning 51.4% vs 39.3%, benchmark 57.2% (human) vs 46.1% (agentic) -> agents more often argue, humans more often measure. The effect is small (V = 0.125).
- Benchmark share for agents rises from 31.6% (2025-Q2) to 60.1% (2026-Q2); humans 49.4% -> 58.7% -> the gap is gone at the end. The static-vs-benchmark claim describes the whole window, and mostly its early part.
- Profiling is the primary evidence in only 2.1% (agentic) and 2.4% (human) of validated PRs -> almost nobody shows where the time goes.
- Only 50.9% / 52.4% of validated PRs contain a number -> "has validation" does not mean "has a measurement".
- CPU / compute work (the dimension that contains cycles and instructions) appears in about 4% / 2% of validated PRs; I/O and network in about 5% / 3% -> low-level evidence is very rare in PR text.
- 17 of 96 caching or buffering PRs with a runtime gain report the memory cost (17.7%) -> hidden costs are almost never documented, by agents or by humans.
- Agents report validation for code-smell refactorings as often as for real resource changes (83.0% vs 81.7%); humans do not (73.5% vs 82.8%) -> agent validation text looks uniform, not adapted to the change.
- Merge rate 54.4% vs 73.3% -> maintainers accept agent perf PRs less often.

**Shares of all PRs (my calculation, not printed in the paper).** The paper gives type percentages only among validated PRs. From the per-group counts and percentages one can rebuild the counts (they add up exactly to the totals in Fig. 1). Out of 1,129 PRs per group:

| Outcome | Agentic count | Agentic share | Human count | Human share |
|---|---|---|---|---|
| No validation | 200 | 17.7% | 219 | 19.4% |
| Static reasoning | 472 | 41.8% | 354 | 31.4% |
| Benchmark | 423 | 37.5% | 515 | 45.6% |
| Profiling | 19 | 1.7% | 22 | 1.9% |
| Anecdotal | 4 | 0.4% | 10 | 0.9% |
| Type unresolved | 11 | 1.0% | 9 | 0.8% |

The "no validation" counts (200, 219) and the unresolved counts (11, 9) are printed in Section 3.4.2. The four type counts per group are my rounding of percentage x n. Do not present the shares in this table as numbers "reported by" the paper. If used, say "computed from their counts".

## Tables and figures
- **Table 1 (p. 6):** the nine metric dimensions M1 to M9 with definitions.
- **Fig. 1 (p. 8):** overview of the four analyses with the main counts (2,083 labelled / 177 unresolved; 938 / 826 / 419 / 41 / 14 / 20; 878 metrics detected / 821 not detected).
- **Fig. 2 (p. 8) and Table 2 (p. 12):** dataset pipeline and counts per stage.
- **Fig. 3 (p. 13):** agent mix of the 1,130 agentic PRs.
- **Table 3 (p. 15):** the nine patterns in the two new categories (five build / infrastructure, four network / database).
- **Table 4 (pp. 15-16):** patterns per category: Memory and Data Locality 12, Code Smells 8, Control-Flow 7, Algorithm-Level 6, Loop Transformations 6, I/O and Synchronization 7, Build and Infrastructure 5, Data Structure 4, Network and Database 4. Total 59.
- **Fig. 4 (p. 24):** merge rate bars and cumulative time-to-merge curves.
- **Fig. 5 (p. 25):** box plots of NLOC, AvgCCN and function-count change (n = 2,029). Medians near zero, agent PRs have longer upper tails.
- **Fig. 6 (p. 26):** category shares per group.
- **Fig. 7 (p. 28):** primary validation type per group. This is the figure behind the 51.4 / 39.3 / 46.1 / 57.2 numbers.
- **Fig. 8 (p. 29):** quarterly trends with 95% Wilson intervals. 2025-Q1 has only 10 PRs per group, so its interval is very wide.
- **Fig. 9 and 10 (p. 31):** number of metrics per PR; share of PRs per metric.
- **Fig. 11 (p. 33):** heat map of metrics per category. The "none" column (no metric) is between 33% and 67% in every row, except human loop transformations (25%, only 4 PRs). Code smells: 54% (agentic) and 66% (human) have no metric. Agentic network / database PRs report M5 (I/O and network) in 16% of cases, the highest of any category; humans 3%. I/O and synchronization PRs report M9 (scalability) in 19% (agentic) and 17% (human).
- **Table 5 (p. 34):** code-smell refactorings vs other changes.

## Ideas we can use
- Their taxonomy of evidence (benchmark, profiling, static reasoning, anecdotal, none) is a ready vocabulary for describing what a PR claims before we measure it.
- Their metric table M1 to M9 maps onto our signals: M4 names "cycles, instructions", M5 names I/O counts and round trips, M3 names RSS and allocation counts. We can say which of their dimensions each of our kernel or hardware signals measures.
- Their "expected metric per pattern" idea is the text-level version of our mechanism-to-signal map. They check whether the PR **reports** the fitting metric (34.5%). We check whether the fitting signal **moves**.
- The caching trade-off check (runtime better, memory worse) is a hidden-cost category we also look for. They show it is rarely documented (17.7%).
- Their list of what a performance "model" must state (target metric, workload, baseline, measurement protocol, acceptable costs) is a good checklist for describing our harness.
- Time-balanced sampling by ISO week is a clean way to compare groups if we ever add human PRs.

## Weaknesses and things glossed over
- **Nothing is executed.** Every result is about what the PR text says. The authors say this several times.
- **All labels come from LLM majority votes without human adjudication.** In the pilot, a human audit found a 10% error rate even where two models agreed. The new labels "were not independently re-audited".
- **One primary type per PR.** A PR that gives both a complexity argument and a benchmark gets one label. The paper does not say how the models choose. The static vs benchmark split may depend on this rule.
- **"Benchmark-Based" is broad.** It includes unit tests. Only 79.8% of benchmark-labelled PRs contain an extractable number, so about one in five has a "benchmark" label without a metric found in the text.
- **The pilot gap is not fully explained.** The pilot found 45.7% (agentic) vs 63.6% (human) validation. Here even the first half of the window shows 69.5% vs 74.1%. The paper says the early gap is "consistent with the pilot study" but does not explain why the levels are so much higher. Possible reasons that the paper does not test: different LLMs, more evidence sources (commit messages, CI workflow names, diff), a different sample (only 32.9% overlap), and the pilot removed 50 "No Meaningful Performance Change" PRs.
- **The perf classifier disagrees with AIDev** (F1 68.2% against AIDev labels) and was checked on 100 PRs by one author. 75 of the 324 pilot agentic PRs are no longer classified as perf.
- **"Human-authored" is defined by missing signals.** Some may be AI-assisted without a visible trace.
- **Regex extraction.** Precision 87.5% was judged by LLMs on 88 PRs, not by humans. Recall is unknown. Numbers in screenshots, figures or linked dashboards are missed. So "about half report no metric" could be too high or too low.
- **No per-agent results.** The sample is 40.5% Copilot and 34.7% Codex. The paper does not report validation per agent, and does not check whether the rise in benchmarks comes from a change in the agent mix over time.
- **Not balanced by repository or language.** A few repositories with many agent PRs could drive results. Clustering is used only for the two time models.
- **Small inconsistencies.** Fig. 4 uses 827/1129 for the human merge rate although the sample has 1,130 human PRs; the paper does not explain the missing one. Section 3.5.1 says 382 PRs have no validation evidence, Section 3.4.2 says 419; the 382 probably counts only PRs with an RQ2 label, but the paper does not say.
- **2025-Q1 has 10 PRs per group**, so "from approximately 70%" rests on very few PRs.
- The interaction for validation presence over time is not significant (p = 0.093). The "crossover" is descriptive only.

## Open questions and future work (theirs, and ours)
- Theirs: evaluation infrastructure that connects the optimization to "representative workloads, expected metrics, and likely trade-offs"; standardized benchmarks and shared profiling platforms; comparisons "on matched bottlenecks" to separate capability from imitation; datasets that keep raw attribution signals and version the rules.
- Theirs, open: are the rising benchmark reports real measurements or "improved presentation"? They cannot tell.
- Ours: this is exactly the gap we fill. Do reported benchmarks and claimed mechanisms hold when the code is rebuilt and measured by someone who does not see the claim?
- Ours: does the share of confirmed mechanisms differ between PRs labelled static reasoning and PRs labelled benchmark?
- Ours: for caching PRs, do we see the memory cost (page faults, RSS) that only 17.7% report?

## Link to our paper
- **Introduction (`paper/sections/01-introduction.tex`, lines 7-12):** we cite this paper for "agents rely more on static reasoning and less on benchmarks than humans do". This is supported (51.4% vs 39.3% static; 46.1% vs 57.2% benchmark, Section 4.3.1). To be exact, add "among PRs that report validation", and consider adding that the benchmark gap closes by 2026-Q2 (60.1% vs 58.7%). The same sentence groups this paper under studies that "read their text"; correct, they also read the diff but never run it.
- **Discussion, related work (`paper/sections/04-discussion.tex`, lines 22-26):** cited for "how agents report validation ... all from text and code". Correct.
- **Conclusion ("Agents' performance claims are mostly unmeasured"):** do not lean on this paper for "mostly unmeasured" without care. It says 82.3% of agentic PRs report validation. What it does support: only 50.9% of validated agentic PRs contain a metric, and Table 5 gives 37.8% and 42.3% of agentic PRs with both validation and at least one metric. So a majority of agentic perf PRs have no reported number.
- **Dataset:** our intro says AIDev has six agents. This paper uses AIDev-v3 with five agents and notes that v4 adds Google Jules. No conflict, but be clear which AIDev version we use.

## Link to the thesis (tracing, kernel analysis)
- The paper never mentions syscalls, kernel traces, eBPF, LTTng or hardware counters as evidence. The closest are Table 1 (M4 "cycles, instructions", M5 I/O counts) and the profiling type ("hotspot traces, CPU samples, or flame graphs"), which is the primary evidence in about 2% of validated PRs.
- This gives a measured baseline for how rare low-level evidence is in practice: a tracing-based check adds a kind of evidence that PR authors almost never give.
- Their trade-off examples (caching raises memory, parallelism raises CPU) are things a kernel trace shows directly: page faults and RSS for memory, sched and futex events for parallel code.

## Quotes for inline citation
- "agentic PRs are merged less often than human-authored PRs (54.4% vs. 73.3%), but the two groups use similar optimization strategies and report validation at comparable rates." (Abstract, p. 1)
- "Agentic PRs rely more on static reasoning and less on benchmarks (46.1% vs. 57.2%), although benchmark use converges by the end of the study period." (Abstract, p. 1)
- "Across both groups, about half of validated PRs report no quantitative performance metric, and relevant trade-offs are rarely quantified." (Abstract, pp. 1-2)
- "we do not execute the changed code, repeat benchmarks or profiling, or independently verify reported values or performance claims." (Section 3.5, p. 20)
- "A benchmark-based label therefore establishes only that a measurement is reported, not that the measurement was produced by a sound experiment or can be reproduced." (Section 4.3.2, p. 28)
- "a reported benchmark does not establish that it was executed as described or that its results were reported accurately." (Section 5, p. 35)
- "our data cannot distinguish improved measurement from improved presentation." (Section 6.3, p. 37)
- "performance cannot be inferred from code alone" (Section 6.4, p. 38)
- "PR descriptions provide only authors' accounts of what was measured." (Section 6.4, p. 38)
- "These findings shift the central challenge from generating plausible optimizations to demonstrating that they work." (Section 7, p. 39)

## Suggested citation sentences
- Among performance PRs that report validation, agents rely more on static reasoning than humans (51.4% vs 39.3%) and less on benchmarks (46.1% vs 57.2%), although the benchmark gap closes by mid-2026 \cite{peng2026validation}.
- Only about half of the performance PRs that report validation contain any quantitative metric (50.9% of agentic, 52.4% of human-authored) \cite{peng2026validation}.
- Profiling is the primary evidence in about 2% of validated performance PRs \cite{peng2026validation}, so low-level evidence for a claimed mechanism is almost never given.
- Peng et al. study what PRs report and do not execute the changed code \cite{peng2026validation}; we rebuild and measure it.
- Fewer than one in five caching or buffering PRs that report a runtime gain also report the memory cost \cite{peng2026validation}, which motivates our check for hidden costs.

## Connection to "Below the Stopwatch"

**How it relates**
- It is the closest text-level study to ours and the best source for "what agents say about validation". It gives the taxonomy (benchmark, profiling, static reasoning, anecdotal, none) and the numbers for how often each appears. We build on its finding that reported evidence is thin: half of validated PRs have no number, profiling is about 2%, trade-offs are rarely reported.
- It does not run anything. It cannot say whether a PR is faster, whether the claimed mechanism happened, or whether a reported benchmark is real. The authors say so and call for "independent evidence". Our pipeline (blind rebuild, untraced timing, perf counters, LTTng, A/A control) is that independent evidence.
- Its "expected metric per pattern" analysis is the nearest thing to our mechanism-to-signal map, but at the level of reported words (34.5% report a fitting metric against 23.7% by chance).
- **Where it weakens or complicates our story:**
  - The simple message "agents do not measure" is out of date in this paper. Validation reporting rises to 92.9% for agents in 2026-Q2 and benchmark use reaches the human level (60.1% vs 58.7%). If our PRs come from AIDev (which ends in August 2025 for v3), they come from the early period where the gap was large. We should say that our sample is from that period.
  - Their classifier finds that AIDev's own perf label is noisy: on 28 hand-labelled shared PRs AIDev's recall was 52.9% and precision 81.8%, and 75 of the 324 pilot agentic PRs lost the perf label under the new classifier. A reviewer from this group may ask how we know our AIDev perf PRs are really performance PRs.
  - 12.9% of agentic perf PRs are code-smell or structural simplification changes. For those a kernel or hardware signal may not exist, so our "mechanism confirmed" rate must be reported with the share of PRs where a signal can be defined.
  - Human PRs are also weak (52.4% with a metric). Our paper should not suggest that the problem is special to agents unless we measure human PRs too.

**Safe to cite for**
- Agents and humans report validation at similar rates over December 2024 to June 2026: "Validation evidence is reported in 929 of 1,129 agentic PRs (82.3%) and 910 of 1,129 human-authored PRs (80.6%)" (Section 4.3.1, p. 27).
- Agents use static reasoning more and benchmarks less than humans, among validated PRs: "static reasoning is the evidence more often in agentic PRs than in human-authored PRs (51.4% vs. 39.3%), whereas benchmark-based evidence is more frequent in human-authored PRs (57.2% vs. 46.1%)" (Section 4.3.1, p. 27).
- Many validated PRs give no number: "only 50.9% of agentic PRs and 52.4% of human-authored PRs report an extractable performance metric" (RQ4 summary box, p. 35).
- Profiling evidence is rare: "Profiling is in 2.1% of agentic PRs and 2.4% of human-authored PRs" (Section 4.3.1, p. 27; shares of validated PRs with a resolved type).
- Prior work reads PR artifacts and does not re-run them: "we do not execute the changed code, repeat benchmarks or profiling, or independently verify reported values or performance claims" (Section 3.5, p. 20).
- Hidden costs are rarely reported: "only 17 of 96 caching or buffering PRs reporting a runtime-side gain also report an adverse memory effect (17.7%)" (RQ4 summary box, p. 35).

**Do not cite for**
- "Agents validate less often than humans." This paper finds no difference (p = 0.330). That claim belongs to the pilot (`peng2025optimization`) and its 407-PR sample only.
- "Agent performance claims are wrong / do not hold / are hallucinated." Nothing is executed. The paper only says claims may be inaccurate and that it cannot tell.
- "X% of agent PRs are actually faster" or any measured speedup. There are no measurements.
- "46.1% of agent perf PRs use benchmarks." The 46.1% is a share of the 918 agentic PRs with validation and a resolved type, not of all agentic perf PRs.
- Anything about kernel-level, syscall-level or hardware-counter evidence. The paper does not study it; it only lists "cycles, instructions" as examples in Table 1.
- Per-agent claims (Copilot vs Codex vs Claude Code). Only the agent mix of the sample is given (Fig. 3); no result is split by agent.
- "Agent PRs are harder to maintain." Structural differences are small (delta about 0.11 to 0.12) and complexity does not differ.
- AIDev facts in general (size of AIDev, its agents, its official labels). This paper rebuilds its own collection with a different classifier and time window. Cite the AIDev paper for AIDev facts.
