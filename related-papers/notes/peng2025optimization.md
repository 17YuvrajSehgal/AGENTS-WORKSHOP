# How Do Agents Perform Code Optimization? An Empirical Study
- **Authors:** Huiyun Peng, Antonio Zhong, Ricardo Andrés Calvo Méndez, Kelechi G. Kalu, James C. Davis (all Purdue University, West Lafayette, Indiana, USA)
- **Venue / year / status:** MSR 2026 (23rd International Conference on Mining Software Repositories), Rio de Janeiro, Brazil, April 2026. The PDF we have is the arXiv version, arXiv:2512.21757v1 [cs.SE], 25 December 2025, 6 pages. The PDF itself does not say "Mining Challenge"; the follow-up paper (`peng2026validation`) calls it "our MSR 2026 Mining Challenge paper" and cites it as pp. 732-736, DOI 10.1145/3793302.3793564, with the second author written as "Qiu AZ". The DOI in our PDF is still a placeholder.
- **PDF:** `related-papers/peng2025optimization_2512.21757.pdf`
- **Cite key:** peng2025optimization
- **BibTeX-style reference:** Huiyun Peng, Antonio Zhong, Ricardo Andrés Calvo Méndez, Kelechi G. Kalu, and James C. Davis. 2025. How Do Agents Perform Code Optimization? An Empirical Study. In Proceedings of the 23rd International Conference on Mining Software Repositories (MSR 2026). ACM. arXiv:2512.21757.
- **Data and code:** `https://anonymous.4open.science/r/perf_patch_study` (Data Availability).

## In short
A short pilot study. The authors take the pull requests (PRs) labelled `perf` in the AIDev dataset: 324 written by AI agents and 83 written by humans (407 in total). With two LLMs plus human checking they label (1) which optimization pattern each PR uses and (2) what validation the PR text reports. Agents and humans use the same kinds of optimization. Agents report validation less often (45.7% vs 63.6%, p = 0.007). When agents do report validation, it is mostly static reasoning (67.2%); humans more often give benchmarks (49% vs 25%). Nothing is executed; everything is read from the PR.

## Problem and motivation
- Agents now open many PRs, some about performance. Performance changes "often have non-local effects, rely on implicit assumptions about workloads or hardware, and require strong empirical evidence (e.g., benchmarking or profiling)" (Section 1).
- Nobody had compared agent and human performance PRs. The paper claims to be "the first empirical study" of this.
- Two research questions (Section 1):
  - RQ1: how do agents and humans differ in the optimization patterns they apply?
  - RQ2: how do they differ in testing and validation of the improvement?

## Background / key terms (explain each term simply)
- **AIDev:** a dataset of GitHub PRs by agents and humans (Li, Zhang, Hassan 2025). Two subsets are used: **AIDev-Pop** (33,596 PRs, repositories with at least 100 stars) and **Human-PR** (6,618 PRs, repositories with at least 500 stars).
- **perf PR:** a PR with the AIDev task label `perf`.
- **SysLLMatic catalog:** a list of 43 optimization patterns in seven categories from the same research group. A category is a broad strategy (for example Memory/Data Locality Optimization). A pattern is the specific mechanism (for example Caching).
- **Validation types (Section 2.1.2 and 3.3):**
  - *Benchmark-Based Validation:* "quantitative measurements (e.g., unit tests or microbenchmarks) to directly assess performance impact".
  - *Profiling-Based Validation:* profiling artifacts "such as hotspot traces, CPU samples, or flame graphs to localize performance costs".
  - *Static-Reasoning-Based Validation:* "algorithmic arguments without relying on runtime data", for example pointing out a worse complexity class.
  - *Anecdotal or Informal Local Testing:* added by the authors for "validation claims that lack quantitative and analytical support".
  - PRs with no evidence are "no performance validation".
- **Cohen's kappa:** agreement between two labellers beyond chance. 0 = chance, 1 = perfect.
- **Chi-square test, Cramér's V:** test for a relation between two categorical variables, and the strength of that relation (0 to 1).
- **Mann-Whitney U:** compares two groups without assuming a normal distribution.
- **Permutation test and rarefaction:** two ways to compare the number of distinct patterns fairly when one group is much larger than the other.
- **NLOC, AvgCCN:** lines of code without comments; average cyclomatic complexity. Measured with the tool Lizard.

## Method and setup
**Data (Section 3.1, Fig. 1)**
- `perf` label gives 340 agent PRs and 88 human PRs.
- Human-PR has no commit-level diffs, so they mined GitHub and rebuilt 7,874 commit-detail records for the 88 human PRs. With AIDev-Pop this gives 15,284 records over 428 PRs.
- Filters: missing filenames (46), configuration-only changes (44), merge commits (10,166), deleted repositories (74). Result: 4,954 valid records for 407 PRs.
- Kept: 324 of 340 agent PRs (95.3%) and 83 of 88 human PRs (94.3%). Fig. 1 shows 4,306 changes for agents and 648 for humans.

**RQ1 labelling (Section 3.2)**
- Two LLMs, GPT-5.1 and Gemini-3-Pro-Preview, temperature 0, label each patch on its own. If they agree, the label is accepted. If not, two human annotators (both Ph.D. students) decide.
- First pass with the original catalog: kappa = 0.53 / 0.48 for agent PRs and 0.42 / 0.35 for human PRs (category / pattern).
- The catalog was then refined on the disagreement cases: from 43 to 59 patterns "through 17 additions, 1 deletion, and 5 edits", plus two new categories: *Build, Compilation, and Infrastructure Optimization* and *Network, Database, and Data Access Optimization*.
- After refinement: kappa = 0.61 / 0.47 (human PRs) and 0.62 / 0.47 (agent PRs).
- Human annotators on the remaining cases: kappa = 0.66 / 0.58 (human PRs), 0.60 / 0.60 (agent PRs). A label *No Meaningful Performance Change* was added for trivial or non-perf edits; 50 PRs got it.
- Error check: where the LLMs disagreed, they matched the final human label only in 35.9% / 18.0% (GPT) and 38.0% / 22.1% (Gemini) of cases (category / pattern); 48.3% / 24.1% and 51.0% / 29.7% after removing the 50 no-change cases. Where the LLMs agreed, a hand audit of a 10% sample (20 PRs) found a 10% error rate.

**RQ2 labelling (Section 3.3)**
- Evidence read: "PR descriptions, comments, and documentation" (Fig. 1 says "description, comment, and .md").
- The 50 *No Meaningful Performance Change* PRs are removed, leaving 357 PRs (280 agent, 77 human).
- Same two LLMs: kappa = 0.74 for validation presence, 0.75 for validation type. Disagreements go to two authors (kappa = 0.62 and 0.58).
- Error check: in disagreement cases GPT matched the human label in 32.8% (presence) and 12.1% (type); Gemini in 75.9% and 65.5%. In agreed cases, an audit of 29 PRs (10%) found 6.9% error for presence and 10% for type.
- Important limit stated by the authors: AIDev has no record of what developers actually did, so the analysis "captures how validation is described in pull request artifacts (i.e., self-report)". They "use claims of testing and evaluation as evidence that these activities were performed, but acknowledge that LLMs may not be trustworthy in this regard."

**Statistics:** chi-square with Cramér's V, Mann-Whitney U, a label-shuffling permutation test, and rarefaction. No correction for multiple tests is mentioned.

## Section-by-section notes

### 1. Introduction
- Summary of findings: agent PRs "rely on optimization patterns similar to those used by humans, but offer weaker validation of performance impact and mostly rely on static reasoning rather than benchmarking".
- The introduction says the extended catalog adds "14 new patterns spanning two additional categories". Section 3.2.2 says 17 additions (43 -> 59 with 1 deletion). These two numbers do not match and the paper does not explain it.

### 2. Background and related work
- 2.1.2 says validation matters because "performance is highly sensitive to measurement noise, workload choice, and experimental design", citing Jain's book.
- Related work: RAPGen, Yi et al. (LLM against developer performance patches), and general studies of agent PRs. No prior comparison of agent and human performance PRs.

### 3. Methodology
- See "Method and setup" above.

### 4.1 Initial dataset characterization
- Merge rate: agent 57% vs human 65%.
- Median time to merge (merged PRs): 0.03 hours for agents vs 2.65 hours for humans (Mann-Whitney U, p < 0.001). Agent PRs "cluster near immediate merge". 0.03 hours is under two minutes, which suggests many agent PRs are merged by the person who started the agent; the paper does not discuss this.
- Maintainability (Fig. 2): Total NLOC, AvgCCN and function count overlap, "no significant differences" (p > 0.05). AvgCCN goes up in 40.14% of AI PRs and 41.94% of human PRs; agents have a heavier upper tail.

### 4.2 RQ1: optimization patterns
- Category shares (Fig. 3, AI agent / human, read from the figure): Memory and Data Locality 32.9% / 28.6%; Algorithm-Level 22.5% / 19.5%; Code Smells and Structural Simplification 11.8% / 13.0%; Build, Compilation and Infrastructure 10.0% / 7.8%; I/O and Synchronization 7.9% / 15.6%; Network, Database and Data Access 5.4% / 7.8%; Control-Flow and Branching 5.4% / 5.2%; Data Structure Selection 3.6% / 2.6%; Loop Transformations 0.7% / 0.0%.
- chi-square(8) = 6.10, p = 0.636, Cramér's V = 0.13 on a 2 x 9 table: no significant relation between author type and category.
- Distinct patterns used: agents 38, humans 21, of 59. After correcting for the larger agent sample this is not significant (permutation p = 0.12, rarefaction p = 0.13).
- Meaning: agents do the same kinds of optimization as humans. The largest visible gap is I/O and synchronization, where humans do about twice the share, but the overall test is not significant.

### 4.3 RQ2: testing and evaluation
- **Presence:** 128 of 280 agent PRs (45.7%) include validation; 49 of 77 human PRs (63.6%). chi-square(1) = 7.06, p = 0.007, Cramér's V = 0.14. The authors call this "statistically significant but weak".
- **Type** (Fig. 4, shares of the validated PRs: 128 agent, 49 human):

| Validation type | Agent | Human |
|---|---|---|
| Static reasoning | 67.2% | 44.9% |
| Benchmark-based | 25.0% | 49.0% |
| Anecdotal | 3.1% | 6.1% |
| Profiling-based | 4.7% | no bar in the figure (the other three human bars add up to 100%) |

- The text gives 67.2% vs 44.9% and "49% ... versus 25%". The anecdotal and profiling values are only in Fig. 4; I read them from the page image.
- chi-square(3) = 12.43, p = 0.006, Cramér's V = 0.26.
- Examples the authors found by reading PRs: agents add benchmarks (for example "inserting time.perf_counter() around the optimized call"), give complexity arguments (string concatenation replaced by StringBuilder, from O(n^2) to amortized O(n)), but also "report benchmark data without supporting evidence (e.g., 7400x speedup stated in the PR description without corresponding benchmark code), exposing such claims to the risk of hallucination".

### 5. Threats to validity
- Construct: validation done outside the PR is not seen, so validation may be underestimated. LLM labels may be wrong.
- Internal: chi-square assumes independent observations and large enough cell counts, "which may be violated by repository/author clustering and sparse categories". Results are "associative, not causal".
- External: AIDev's limits, "including potential PR author-labeling errors and its asymmetric repository filters for agent vs. human PRs (> 100 vs. > 500 stars)".

### 6. Discussion
- 6.1: loop transformations are absent from human PRs and are 0.7% of agent PRs. Agents could try techniques humans avoid, but this "requires agents tightly integrated with profiling feedback, correctness checks, and automated evaluation pipelines".
- 6.2: "Although static reasoning can indicate plausible performance effects, it lacks quantitative grounding and is therefore susceptible to incorrect assumptions or hallucinated claims." CI benchmarking built for human contribution rates is "unlikely to scale to agent-driven workloads"; they ask for "standardized benchmarking services and shared profiling resources".

## Key results (with numbers) and what they mean
- 45.7% of agent perf PRs vs 63.6% of human perf PRs report any validation (p = 0.007, V = 0.14) -> in this early AIDev sample, more than half of agent perf PRs give no evidence at all. By subtraction that is 152 of 280 agent PRs (54.3%) and 28 of 77 human PRs (36.4%); these two percentages are my calculation.
- Of validated agent PRs, 67.2% use static reasoning and 25.0% a benchmark; humans 44.9% and 49.0% -> an agent that does justify a speedup usually argues from the code, it does not measure.
- Benchmark evidence in agent PRs: 25.0% of 128 is 32 PRs, which is about 11% of the 280 agent PRs (my calculation) -> very few agent perf PRs in this sample come with any measurement.
- Profiling is 4.7% of validated agent PRs (about 6 PRs, my calculation) and absent for humans -> evidence about where the time goes is almost never given.
- Pattern use does not differ (p = 0.636) -> agents know the standard optimization repertoire; the weak point is evidence, not ideas.
- Agent PRs merged in a median of 0.03 hours -> many are merged almost at once, so review is unlikely to catch an unsupported claim.
- A "7400x speedup" with no benchmark code -> a concrete example of an unverifiable agent claim.

## Tables and figures
- **Fig. 1 (p. 2):** data pipeline and how it feeds RQ1 ("LLM + human manual analysis on diff") and RQ2 ("Inspect description, comment, and .md"). The figure is drawn twice on top of each other in the PDF (two versions), so the text extraction is garbled; the counts match the text of Section 3.1.
- **Fig. 2 (p. 3):** box plots of percentage change in Total NLOC, AvgCCN and function count. Boxes are medians and interquartile ranges, whiskers 10th and 90th percentiles. Read: medians near zero for both, agents more spread.
- **Fig. 3 (p. 3):** category shares for agents and humans. Read: bars are similar; I/O and synchronization is the main visible gap.
- **Fig. 4 (p. 4):** validation type shares among validated PRs. Read: agent bar is tallest for static reasoning, human bar is tallest for benchmark. The human side rests on 49 PRs.
- There are no numbered tables.

## Ideas we can use
- The four-way taxonomy of reported validation (benchmark, profiling, static reasoning, anecdotal) plus "none". The follow-up paper keeps it unchanged, so it is a stable vocabulary.
- The refined 59-pattern catalog with its two new categories (build / infrastructure and network / database / data access) as a list of mechanisms that PRs claim. Each pattern is a candidate for a kernel or hardware signal in our map.
- The "No Meaningful Performance Change" label: 50 of 407 PRs labelled `perf` in AIDev (12.3%, my calculation) were judged trivial or not about performance. We need the same kind of screen before measuring.
- The "7400x" example as motivation for checking claims by execution.

## Weaknesses and things glossed over
- **Small and unbalanced sample:** 280 agent vs 77 human PRs for validation; only 49 validated human PRs. Fig. 4 percentages for humans move by about 2 points per PR.
- **Sparse cells:** the type test has cells with about 0 to 6 PRs (profiling, anecdotal). A chi-square test is not reliable with such counts. The authors mention this risk but still report p = 0.006.
- **Different populations:** agent PRs come from repositories with at least 100 stars, human PRs from at least 500 stars. The human group may be from more mature projects with stricter habits. The gap in validation may partly be a project effect.
- **Self-report only:** nothing is run. "Validation present" means the PR text says so.
- **LLM labels are weak where it matters:** when the two models disagreed, GPT matched the human label for validation type in only 12.1% of cases; and 10% of agreed labels were wrong in the audit (on 20 and 29 PRs only).
- **Pattern-level agreement is moderate** (kappa 0.47 after refinement), so pattern counts are noisy.
- **Catalog numbers do not match** inside the paper (14 new patterns in the introduction, 17 additions in Section 3.2.2).
- **No per-agent analysis.** The paper does not say which agents wrote the 324 PRs.
- **No dates.** The paper does not state the time window of the PRs. (The follow-up paper says the collection ended in August 2025.)
- **Time to merge of 0.03 hours** is reported without comment on self-merging or on which repositories these are.
- **One primary type per PR** seems to be assumed (the bars add up to 100%), but the paper does not say how a PR with both a benchmark and a complexity argument is labelled.
- The abstract says "commits" in one place ("performance optimization commits") while the unit of analysis is the PR.
- Superseded: the follow-up paper with a balanced sample finds **no** difference in validation presence. See below.

## How this paper differs from the follow-up (`peng2026validation`)
The follow-up says it "extends our MSR 2026 Mining Challenge paper" and that "All results reported in this work are recomputed from the large-scale sample". All numbers below are from the two papers.

| | This paper (pilot, MSR 2026) | Follow-up (arXiv 2610.03969) |
|---|---|---|
| Length | 6 pages | 46 pages |
| Sample | 407 perf PRs: 324 agent, 83 human | 2,260 perf PRs: 1,130 agentic, 1,130 human-authored |
| Source | AIDev as published (`perf` label) | AIDev pipeline re-run on 2,807 repositories, own perf classifier, Dec 24, 2024 to June 1, 2026 |
| Repository threshold | at least 100 stars (agent), at least 500 (human) | at least 100 stars for both |
| Balance | none | 1:1 inside each of 65 ISO weeks |
| Labelling | 2 LLMs (GPT-5.1, Gemini-3-Pro-Preview) + two humans decide disagreements | 3 LLMs (GPT-5.6-sol, Gemini-3.1-Pro-Preview, Qwen3.8-27B), majority vote, no human adjudication |
| Research questions | RQ1 patterns, RQ2 validation | RQ1 adoption / size / maintainability, RQ2 patterns, RQ3 validation + change over time, RQ4 reported metrics and trade-offs |
| Validation present | 45.7% agent vs 63.6% human (p = 0.007) | 82.3% vs 80.6% (p = 0.330, no difference) |
| Static reasoning (of validated) | 67.2% vs 44.9% | 51.4% vs 39.3% |
| Benchmark (of validated) | 25% vs 49% | 46.1% vs 57.2%; equal by 2026-Q2 (60.1% vs 58.7%) |
| Profiling (of validated) | 4.7% agent, none for humans | 2.1% vs 2.4% |
| Category distribution | chi-square(8) = 6.10, p = 0.636, V = 0.13 | chi-square(8) = 16.14, p = 0.040, V = 0.088 |
| Distinct patterns | 38 vs 21 of 59 | 44 vs 43 of 59 |
| Merge rate | 57% vs 65% | 54.4% vs 73.3% |
| Median time to merge | 0.03 h vs 2.65 h | 4.99 h vs 19.16 h |
| Metrics, trade-offs, code-smell contrast | not studied | studied (RQ4) |

- The main change in the message: the pilot says agents validate **less often**. The follow-up says they validate **as often**, but in a different **form**, and that both groups rarely give numbers.
- Only 134 of the 407 pilot PRs (32.9%) are in the follow-up sample, and none of the 83 human PRs. So the two papers are close to independent samples.
- The follow-up states the evidence sources of the pilot as "title, description, issue and review comments, commit messages, CI workflow names, and code diff". This paper itself says "PR descriptions, comments, and documentation". The two descriptions are not the same; I cannot tell from the PDFs which is exact.
- The catalog (59 patterns, 9 categories) and the validation taxonomy were created here and reused unchanged in the follow-up.

## Open questions and future work (theirs, and ours)
- Theirs: agents "tightly integrated with profiling feedback, correctness checks, and automated evaluation pipelines"; shared benchmarking and profiling services for agent workloads; observing real behaviour would need IDE-level event data.
- Ours: of the agent PRs with static reasoning only, how many are actually faster when measured, and does the argued mechanism show up in the kernel or hardware signal?
- Ours: do PRs with a reported benchmark do better under our measurement than PRs with none?

## Link to our paper
- **Introduction (`paper/sections/01-introduction.tex`, lines 7-8):** cited among studies that "read their text". Correct: RQ1 reads diffs with LLMs and humans, RQ2 reads descriptions, comments and .md files. Nothing is run.
- **Discussion, related work (`paper/sections/04-discussion.tex`, line 24):** cited for "optimization patterns". Correct, this is RQ1 here.
- **`paper/refs.bib`:** the entry is `@misc` with the arXiv number. The follow-up paper lists the published version: Proceedings of MSR 2026, ACM, pp. 732-736, DOI 10.1145/3793302.3793564. Consider citing the published version. Check the author list on the ACM page, because the second author's name differs between the arXiv PDF ("Antonio Zhong") and the follow-up's reference list ("Qiu AZ").
- If we want the strong sentence "agents report validation less often than humans", it must be tied to this paper and its AIDev sample, and we should add that the larger follow-up did not find the difference.

## Link to the thesis (tracing, kernel analysis)
- The paper names profiling ("hotspot traces, CPU samples, or flame graphs") as one of three accepted forms of evidence and finds it in only 4.7% of validated agent PRs and no validated human PRs. It cites Gregg's flame graph article and Systems Performance book.
- No syscall, kernel or hardware-counter evidence is discussed.
- Their call for agents "integrated with profiling feedback" is an opening for trace-based feedback loops.

## Quotes for inline citation
- "AI-authored performance PRs are less likely to include explicit performance validation than human-authored PRs (45.7% vs. 63.6%, p = 0.007)." (Abstract, p. 1)
- "AI-authored PRs largely use the same optimization patterns as humans." (Abstract, p. 1)
- "our analysis captures how validation is described in pull request artifacts (i.e., self-report)." (Section 3.3, p. 3)
- "We use claims of testing and evaluation as evidence that these activities were performed, but acknowledge that LLMs may not be trustworthy in this regard." (Section 3.3, p. 3)
- "Agent-authored PRs predominantly rely on static-reasoning-based validation, which appears in 67.2% of validated AI PRs, compared to 44.9% for human PRs." (Section 4.3, p. 4)
- "they may also report benchmark data without supporting evidence (e.g., 7400x speedup stated in the PR description without corresponding benchmark code), exposing such claims to the risk of hallucination." (Section 4.3, p. 4; the paper prints the multiplication sign)
- "Although static reasoning can indicate plausible performance effects, it lacks quantitative grounding and is therefore susceptible to incorrect assumptions or hallucinated claims." (Section 6.2, p. 5)

## Suggested citation sentences
- In the AIDev performance PRs, agents apply the same optimization patterns as humans \cite{peng2025optimization}.
- In an early AIDev sample, fewer than half of agent-authored performance PRs (45.7%) reported any validation, and two thirds of those relied on static reasoning \cite{peng2025optimization}; a later, larger study found validation rates had risen to the human level \cite{peng2026validation}.
- Peng et al. note that static reasoning "lacks quantitative grounding" and observed a claimed 7400x speedup with no benchmark code \cite{peng2025optimization}; such claims can only be settled by measurement.
- Existing studies analyse what performance PRs say and change, not what happens when they run \cite{peng2025optimization,peng2026validation}.

## Connection to "Below the Stopwatch"

**How it relates**
- Same dataset family as ours: perf-labelled PRs from AIDev. It tells us what these PRs claim and what evidence they carry: in this sample most agent perf PRs have no validation (my calculation: 152 of 280) and most of the rest only argue from the code. That is the reason an outside measurement is needed.
- It gives the pattern catalog (59 patterns) that describes the mechanisms agents use. We go one step further: for each claimed mechanism we name the kernel or hardware signal that must move, and we measure it. The paper does not execute anything and says its evidence is "self-report".
- Its 50 "No Meaningful Performance Change" PRs out of 407 warn us that the AIDev `perf` label is not clean. Some of our PRs may have no mechanism to check.
- **Where it weakens or complicates our story:** its headline (agents validate less than humans) was not confirmed by the authors' own larger study. If we cite the 45.7% vs 63.6% gap as a current fact, a reviewer who knows the follow-up will object. The human group also came from a different repository population (at least 500 stars), so the comparison was not like for like. The sample is small (77 human PRs).

**Safe to cite for**
- Agents and humans use similar optimization patterns in AIDev perf PRs: "The test finds no significant association between author type and optimization category (chi-square(8) = 6.10, p = 0.636; Cramér's V = 0.13)" (Section 4.2, p. 3; the paper prints the Greek letter).
- In this 2025 AIDev sample, agents reported validation less often: "Among agent PRs, 128 of 280 (45.7%) include validation, while 49 of 77 (63.6%) human-authored PRs include validation." (Section 4.3, p. 4). Say that this is the pilot sample.
- Validated agent PRs lean on static reasoning: "which appears in 67.2% of validated AI PRs, compared to 44.9% for human PRs" and "49% of validated human PRs including benchmark results, versus 25% for agents" (Section 4.3, p. 4).
- Existence of unsupported numeric claims: "7400x speedup stated in the PR description without corresponding benchmark code" (Section 4.3, p. 4). This is one example, not a rate.
- The study is based on PR text, not execution: validation is analysed as it "is described in pull request artifacts (i.e., self-report)" (Section 3.3, p. 3).
- The need for tooling: realizing better agent optimization "requires agents tightly integrated with profiling feedback, correctness checks, and automated evaluation pipelines" (Section 6.1, p. 4).

**Do not cite for**
- "Agents validate less than humans" as a general or current fact. The follow-up finds 82.3% vs 80.6%, no difference.
- "Agent performance claims are false" or "agents hallucinate speedups" as a measured rate. The paper gives one example and a risk statement. Nothing was re-run.
- "25% of agent perf PRs include benchmarks". The 25% is a share of the 128 validated agent PRs, not of all agent perf PRs.
- Any measured speedup, or any statement that agent optimizations work or do not work.
- Per-agent differences (Copilot, Codex, Devin and so on). Not reported.
- Reported metrics, trade-offs, or change over time. Those are only in the follow-up.
- Kernel, syscall or hardware-counter evidence. Not studied.
- The catalog having "14 new patterns" or "17 new patterns" without checking: the paper gives both numbers. The safe statement is "expanded from 43 to 59 patterns and two new categories".
