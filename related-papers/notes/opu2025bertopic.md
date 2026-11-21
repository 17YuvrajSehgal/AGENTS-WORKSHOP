# How Do Agentic AI Systems Address Performance Optimizations? A BERTopic-Based Analysis of Pull Requests
- **Authors:** Md Nahidul Islam Opu, Shahidul Islam, Shaiful Chowdhury (SQM Research Lab, Computer Science, University of Manitoba, Winnipeg, Canada), Muhammad Asaduzzaman (Computer Science, University of Windsor, Canada)
- **Venue / year / status:** arXiv preprint, arXiv:2512.24630v1 [cs.SE], 31 Dec 2025. 5 pages including references. The PDF itself names no venue. (qi2026merged lists it in its references as published in the MSR 2026 proceedings, pp. 1009-1013; that information is from Qi et al., not from this PDF.)
- **PDF:** related-papers/opu2025bertopic_2512.24630.pdf
- **Cite key:** opu2025bertopic
- **BibTeX-style reference:** Md Nahidul Islam Opu, Shahidul Islam, Muhammad Asaduzzaman, and Shaiful Chowdhury. 2025. How Do Agentic AI Systems Address Performance Optimizations? A BERTopic-Based Analysis of Pull Requests. arXiv:2512.24630.

## In short
The authors take the AIDev-POP subset of AIDev v3 (33,596 agent PRs), use an LLM to find the PRs that express a performance concern, and get 1,221 performance PRs. They cluster the PR text with BERTopic into 52 topics and group these into 10 categories (Low-level, Development, UI, Algorithmic, Networking, Caching, Query, Analytics, Hardware, AI). Performance PRs are rejected more often than non-performance PRs (36.5% vs 22.7%), and rejection rate and merge time differ by category. Everything is based on PR titles, bodies and metadata. No code is run. They say themselves that evidence that agent changes give measurable improvements "is currently limited" (Conclusion, p. 5).

## Problem and motivation
- Earlier work compares the speed of LLM-written code with human code in controlled settings. It does not show how agents handle performance in real projects (p. 1).
- Unknown: which kinds of performance issues agents target, at which layer of the software stack, in which development activity, and whether the kind of optimization affects acceptance and review time.
- RQ1: What categories of performance optimizations do agentic AIs address?
- RQ2: How do PR rejection rates and review times vary across categories?
- RQ3: What SDLC activities are associated with AI-generated performance-related PRs?

## Background / key terms (explain each term simply)
- **AIDev-POP:** the subset of the AIDev dataset with more popular repositories. Here: version v3, 33,596 agent PRs, obtained from Zenodo (p. 1). The paper does not state the star threshold.
- **SDLC (Software Development Life Cycle) activity:** the kind of work a PR does: feature, fix, refactor, test, docs, ci, build, chore, perf. AIDev gives one such label per PR, produced by an LLM.
- **Zero-shot classification:** asking an LLM to label an item with only instructions, no training examples.
- **BERTopic:** a topic-modelling pipeline. Text is turned into embedding vectors, the vectors are reduced in dimension (UMAP), clustered (HDBSCAN), and each cluster gets keywords (class-based TF-IDF). Each cluster is a "topic".
- **UMAP:** a method that reduces high-dimensional vectors to fewer dimensions while keeping neighbours close.
- **HDBSCAN:** a density-based clustering method. It can leave points unassigned as "outliers" (noise).
- **Topic coherence:** a score for how well the top words of a topic belong together. **Silhouette score:** a score for how well separated the clusters are.
- **Cohen's kappa / Gwet's AC1:** agreement between two raters, corrected for chance. AC1 is more stable when one label is very common.
- **Wilcoxon rank-sum test:** a rank test of whether one group tends to have larger values. **Cliff's delta:** effect size for the same comparison. **Kendall's tau:** a rank correlation between two variables.
- **Rejected PR (their definition):** "closed without being merged" (Section 3.2, p. 3).

## Method and setup
- **Data:** AIDev v3, AIDev-POP subset, 33,596 agentic PRs (Section 2, p. 1).
- **Why not AIDev's own label:** only 340 PRs are labelled `perf`. Many PRs labelled fix or feat also target performance (example: "Fix Gantt performance by removing useMouse from every column", shadcnblocks/kibo PR 166, labelled fix).
- **Keyword filter tried first and dropped:** 23 performance terms gave 10,894 PRs. The first author checked 100 random ones and found 92% false positives.
- **LLM detection:** `gpt-oss-20B`, zero-shot, binary (performance vs non-performance). The prompt says to label a PR as performance-related "only when performance is expressed as a concern", and includes the keyword list. Result: 1,160 PRs across 447 repositories, from five agents.
- **Check of the LLM filter:** the first two authors each inspected 200 random PRs. False positive rate 7.5%, where a false positive is a PR that at least one author labelled NonPerformance. Observed agreement 97.5%, Cohen's kappa 0.79, Gwet's AC1 0.97.
- **False positives were not removed.** They argue HDBSCAN will put them in the outlier group.
- **Adding back:** the LLM set missed 61 of the 340 `perf`-labelled PRs. These 61 were added. Final dataset: 1,221 performance PRs.
- **Recall of the LLM filter:** not measured. The paper does not say how many performance PRs among the other roughly 32,000 were missed.
- **Topic modelling:** title + body embedded with Qwen3-Embedding-8B; UMAP (n_components = 20, n_neighbors = 3); HDBSCAN (min_cluster_size = 10, min_samples = 1); chosen by a constrained grid search (coherence 0.47, silhouette 0.57). Output: 52 topics and 101 outliers.
- **Labelling:** the first two authors labelled all topics independently (Cohen's kappa 0.92, four disagreements resolved by discussion). They then merged topics into 10 categories together by discussion.
- **Statistics:** Wilcoxon rank-sum, Cliff's delta, Kendall's tau.
- **Replication package:** https://github.com/SQMLab/LLM-performance (footnote 1).
- **No code execution, no measurement of speed.**

## Section-by-section notes

### 1. Introduction (p. 1)
- Prior results on LLM code speed are mixed (some match or beat humans, others are inefficient).
- Headline answers: 52 topics in 10 categories; rejection 36.5% vs 22.7%; agents do worst on UI, AI and Analytics PRs; performance PRs are mostly tied to feature work.

### 2. Methodology (pp. 1-2)
See "Method and setup".

### 3.1 RQ1: topics and categories (pp. 2-3)
- **Fig. 1, share of the 1,221 PRs by category:** Low-level 21.0%, Development 18.2%, UI 11.1%, Algorithmic 9.7%, Networking 7.9%, Caching 7.1%, Query 5.0%, Analytics 5.0%, Hardware 4.0%, AI 2.6%. These sum to 91.6%. The remaining 8.4% is close to the 101 outliers (101 / 1,221 = 8.3%), but the paper does not say this.
- Low-level = for example compiler and transpiler improvements. AI = for example token usage and ChatAPI efficiency. Analytics = performance monitoring and evaluation. Development = for example CI/CD pipelines and testing.
- Caching was kept as its own category "due to its prevalence".
- "all categories, except Analytics, directly focus on performance optimization" (p. 3). So Analytics PRs are about measuring performance, not about making code faster.
- **Fig. 2 (radar chart, by agent):** OpenAI Codex dominates most categories, "especially Low-level tasks with over 90% of PRs", and has at least 30% in every category. Its share is lower in Analytics, AI and UI. Devin has its largest share in Analytics and UI. Cursor contributes most in AI. Exact per-agent numbers are not printed.
- They say a more balanced dataset is needed before drawing conclusions about agents.

### 3.2 RQ2: acceptance rate and merge time (pp. 3-4)
- Overall rejection rate of performance PRs: 36.5%. Non-performance PRs: 22.7%. The text says "significantly higher" but gives no test name or p-value for this comparison.
- **Fig. 3, rejection rate by category (read from the figure labels):** UI 46.7%, AI 46.4%, Query 45.8%, Analytics 44.0%, Algorithmic 42.9%, Development 36.7%, Hardware 35.7%, Caching 32.1%, Low-level 28.1%, Networking 28.0%, Non-performance 22.7%. The Query label is partly overlapped in the figure; 45.8% is the value in the extracted text.
- The text highlights UI, AI and Analytics as the highest. Query (45.8%) is higher than Analytics (44.0%) but is not mentioned in the text.
- **Merge time (Fig. 4):** analysed on "625 accepted PRs". UI, AI and Analytics have the longest median merge times; Low-level is merged fastest. The differences against Low-level are statistically significant (Wilcoxon rank-sum) with large Cliff's delta. No medians, p-values or delta values are printed.
- **Change size (Fig. 5):** total changed lines (added + deleted) differ much less across categories; the high-level vs low-level differences are "statistically insignificant". The highest Kendall's tau between merge time and total line changes is 0.38 (Hardware), which they call a weak association. So they argue that the type of change, not its size, drives rejection and merge time.
- Interpretation they offer: high-level changes "may require more context-sensitive reasoning or human intervention". This is a guess, not tested.

### 3.3 RQ3: SDLC activities (p. 4)
- The 340 `perf`-labelled PRs are excluded here, because that label hides the underlying activity.
- **Fig. 6 (counts printed on the bars, read from the page image):** feat: UI 53, Query 19, Networking 51, Low-level 127, Hardware 22, Development 67, Caching 40, Analytics 36, Algorithmic 29, AI 22. fix: UI 36, Networking 17, Hardware 24, Development 32, Caching 25, Algorithmic 15. Low-level also shows 18 in the refactor colour. Development also shows 29 (ci colour) and 19 (build colour). Colours for the smaller segments are hard to tell apart at this size, so treat the segment-to-activity mapping for 18, 29 and 19 as "(unclear in the PDF)" unless checked in the replication package.
- "For all categories except Hardware, most performance optimizations occur during feature implementation." In Hardware, fix (24) is slightly above feat (22).
- Conclusion: agents address performance mostly during development (feature work), less during testing and maintenance.

### 4. Threats to validity (p. 4)
- Internal: the LLM classifier still misclassifies ambiguous PR descriptions; they say BERTopic's tolerance of noisy data mitigates it. Topic labels and categories depend on manual judgment. "Differences in acceptance rates, merge times, and review effort may be affected by unobserved factors such as project contributors, review practices, or repository maturity."
- External: one dataset.

### 5. Related works (p. 4)
- Short. Cites studies of LLM code performance with mixed results, and Yi et al. (their ref. 38) for LLM patches that underperform human-optimized ones.

### 6. Conclusion (pp. 4-5)
- Performance PRs are rejected more often, "suggesting potential trust or verification issues with AI-generated performance optimizations".
- "UI-related PRs experience the highest rejection rates, whereas low-level optimizations are more frequently accepted and merged more quickly."
- Future work: larger and more diverse datasets; "We also need to empirically evaluate whether agent-generated changes yield measurable improvements, as such evidence is currently limited."

## Key results (with numbers) and what they mean
- 1,221 performance PRs found vs 340 with AIDev's `perf` label -> the dataset's own `perf` label misses most PRs that talk about performance. Selecting by that label alone under-counts.
- Keyword filtering: 92% false positives in a 100-PR sample -> words like "performance" and "optimize" are not enough to find performance PRs.
- 52 topics in 10 categories, from compiler-level work to UI and AI token usage -> "performance PR" is a wide label. Not all of these claim faster code (Analytics is monitoring; Development includes CI/CD pipelines).
- Rejection 36.5% (performance) vs 22.7% (non-performance) -> maintainers accept agents' performance PRs less often than other agent PRs. The paper does not show why.
- Rejection from 28.0% (Networking) and 28.1% (Low-level) up to 46.7% (UI) -> outcome differs by kind of optimization, but agent and repository are not controlled (Codex writes over 90% of Low-level PRs).
- Kendall's tau at most 0.38 between merge time and size -> size alone does not explain the slower review of UI/AI/Analytics PRs.

## Tables and figures
- **Fig. 1 (p. 2):** tree of the 10 categories with their shares of the 1,221 PRs.
- **Fig. 2 (p. 3):** radar chart, percentage of PRs by agent (Claude_Code, Copilot, Cursor, Devin, OpenAI_Codex) in each category. Read: the Codex line is far outside the others, mostly towards Low-level.
- **Fig. 3 (p. 3):** stacked bars (log scale) of accepted and rejected PRs per category plus Non-Performance; the number on each bar is the rejected percentage.
- **Fig. 4 (p. 3):** box plots of time to merge in hours (log scale) per category. Read: Low-level's box is lowest.
- **Fig. 5 (p. 4):** box plots of total line changes (log scale) per category. Read: the boxes overlap much more than in Fig. 4.
- **Fig. 6 (p. 4):** stacked bars of SDLC activity types per category (PR counts).
- There are no tables.

## Ideas we can use
- **Selection:** do not rely on AIDev's `perf` label only, and do not rely on keywords only. Their numbers (340 vs 1,221; 92% false positives) justify an LLM or hand-checked classification step.
- **Category check for our sample:** some of their categories are not "this code is now faster" claims (Analytics, parts of Development such as CI/CD, AI token usage). We should say how we exclude or handle such PRs, since they have no kernel-level mechanism to check.
- **Mechanism families:** Caching (7.1%), Query (5.0%), Networking (7.9%) and Low-level (21.0%) are the categories where a claimed mechanism maps most directly to syscalls, I/O or hardware counters.
- **Their future-work sentence** is a direct motivation for measuring: evidence of measurable improvement "is currently limited".

## Weaknesses and things glossed over
- **Text only.** No PR is built or run. Nothing is said about whether any optimization works.
- **No recall estimate** for the LLM classifier. Only precision was checked (200 PRs, 7.5% false positives by the strict rule).
- **Known false positives stay in the data.** They assume HDBSCAN isolates them as outliers, but this is not checked. A false positive that looks like a topic stays in that topic.
- **The 61 added PRs** come from AIDev's LLM-made `perf` label and were rejected by their own classifier. Adding them mixes two definitions of "performance PR".
- **Outliers:** 101 PRs are outliers. The paper does not say whether they are left out of the category shares and rejection rates (the category shares sum to 91.6%).
- **Denominators are missing.** Counts per category are not printed. "625 accepted PRs" is given, but not the number rejected or open. With rejection = closed without merge, 36.5% of 1,221 would be about 446, and 625 + 446 is less than 1,221, so some PRs are open or the rate uses another denominator. The paper does not say.
- **"Significantly higher" (36.5% vs 22.7%)** has no named test or p-value. Category-level significance is reported only in words.
- **Confounding by agent and repository.** Codex dominates (over 90% of Low-level). qi2026merged later shows that acceptance follows the agent and the repository's history, and that pooled differences by optimization type mostly disappear under hand coding. The authors list unobserved factors as a threat but do not control for them.
- **Text vs figure:** the text names UI, AI and Analytics as worst, but Query (45.8%) is above Analytics (44.0%) in Fig. 3.
- **BERTopic settings:** n_neighbors = 3 and min_samples = 1 are very small values, which tend to give many small clusters. Coherence 0.47 and silhouette 0.57 are moderate. Stability of the 52 topics across seeds is not reported.
- **Categories were derived by two authors in discussion**; no agreement score for the category step.
- **Five agents, AIDev v3 only.** Short paper (4 pages of text).
- **"Performance" includes non-speed work** (monitoring, CI pipelines, token usage), so the 36.5% is not a rejection rate of "make the code faster" PRs.

## Open questions and future work (theirs, and ours)
- Theirs: validate the categories on larger, more diverse datasets; test whether agent changes "yield measurable improvements"; make agents address performance across the whole SDLC.
- Ours: Which of their categories carry a checkable mechanism claim? Does the rate of true mechanisms differ by category (for example Caching vs UI)? Are the higher rejection rates for UI/AI/Analytics related to claims being harder to verify? The paper only speculates.

## Link to our paper
- **Introduction (`paper/sections/01-introduction.tex`, line 7):** cited among studies that "read their text". Correct: this paper uses PR titles, bodies and metadata only.
- **Related work (`paper/sections/04-discussion.tex`, line 23):** "characterize topics ... all from text and code". For this paper "from text" is exact. It does not analyse code diffs (only the total line counts from metadata). If the sentence must be exact for each cited paper, keep "topics" tied to "text".
- **Dataset section:** it supports the statement that AIDev's `perf` label under-counts performance PRs (340 labelled vs 1,221 found, in AIDev-POP v3). Our draft uses AIDev version 5, so quote their numbers with their version.

## Link to the thesis (tracing, kernel analysis)
- No tracing, no measurement. The link is indirect: it gives a map of what agents say they optimize. Low-level, Caching, Query, Networking and Hardware are the layers where kernel and hardware signals (syscalls, block and network I/O, cache misses, instructions) are the natural evidence.
- UI and AI-token categories would need other evidence (render counts, frame times, API token counts), not kernel traces. This marks a limit of a kernel-signal approach.

## Quotes for inline citation
- "it is unclear how exactly the agentic AI systems address performance concerns in practice" (abstract, p. 1)
- "only 340 PRs are labeled as perf, substantially under-representing performance-related changes" (p. 2)
- "manual inspection of 100 randomly sampled PRs by the first author ... shows a 92% false positives, making this approach unsuitable" (p. 2)
- "the overall rejection rate is 36.5%, which is significantly higher than non-performance PRs with a rate of 22.7%" (p. 3)
- "performance-related PRs are rejected more frequently than non-performance PRs, suggesting potential trust or verification issues with AI-generated performance optimizations" (p. 5)
- "We also need to empirically evaluate whether agent-generated changes yield measurable improvements, as such evidence is currently limited." (p. 5)

## Suggested citation sentences
- Agents' performance PRs span the software stack, from compiler-level changes to caching, queries and UI \cite{opu2025bertopic}.
- In AIDev, performance PRs from agents are rejected more often than their other PRs (36.5\% against 22.7\%) \cite{opu2025bertopic}.
- The dataset's own \texttt{perf} label misses most performance-related PRs, and keyword matching gives mostly false positives \cite{opu2025bertopic}, so we classify PRs with an LLM and check a sample by hand.
- Text-based studies describe what agents say they optimize \cite{opu2025bertopic} and call for evidence that the changes give measurable improvements.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is a text-level map of agent performance PRs in AIDev (topics, categories, rejection rates). We build on its motivation: performance PRs exist in large numbers, are rejected more often, and nobody has measured whether they work. Its last paragraph asks for exactly the kind of measurement we do.
  - It does not build, run or measure anything, and it does not extract the claimed mechanism per PR. Its categories are topic clusters, not mechanism claims. We do both.
  - It supports our selection step: AIDev's `perf` label and keyword filters are not good enough, so an LLM classification with a manual check is reasonable.
  - A point that limits us: about 37% of its performance PRs are in categories with no clear kernel-level footprint (Development 18.2%, UI 11.1%, Analytics 5.0%, AI 2.6%; the sum and the "no kernel footprint" reading are ours). If our sample is drawn the same way, many "performance PRs" will have no mechanism our signals can check. Also, its category-level acceptance differences are weakened by qi2026merged (p. 32 there), so we should not lean on them.

- **Safe to cite for:**
  - Agents apply performance changes at many layers of the stack. "We identified 52 performance topics grouped into 10 categories, ranging from low-level optimizations to UI- and AI-related concerns" (Introduction, p. 1; Section 3.1).
  - Agent performance PRs are rejected more often than other agent PRs in AIDev-POP v3. "the overall rejection rate is 36.5%, which is significantly higher than non-performance PRs with a rate of 22.7%" (Section 3.2, p. 3).
  - AIDev's `perf` label under-counts. "only 340 PRs are labeled as perf, substantially under-representing performance-related changes" (Section 2, p. 2); their final set has 1,221 PRs.
  - Keyword filtering is unreliable for finding performance PRs. "92% false positives" in a 100-PR sample (Section 2, p. 2).
  - Measured evidence of improvement is missing in this line of work. "We also need to empirically evaluate whether agent-generated changes yield measurable improvements, as such evidence is currently limited." (Conclusion, p. 5).
  - Performance PRs by agents are mostly attached to feature work. "For all categories except Hardware, most performance optimizations occur during feature implementation." (Section 3.3, p. 4).

- **Do not cite for:**
  - Any statement that agent performance PRs do or do not make code faster. Nothing was executed.
  - Why performance PRs are rejected. "trust or verification issues" is a suggestion in the conclusion, not a finding.
  - A causal effect of optimization type on acceptance. Agent and repository are not controlled, and the authors list unobserved factors as a threat.
  - Per-agent quality comparisons. They say a more balanced dataset is needed.
  - Mechanism-level claims (for example "agents mostly use caching"). Caching is 7.1% of PRs as a topic category here; the "caching is the most common resolution" result is from qi2026merged, not from this paper.
  - Numbers for the whole AIDev dataset or for other versions. This is AIDev-POP, v3, 33,596 PRs, five agents.
  - Recall of LLM-based performance-PR detection. Only a false positive rate (7.5% on 200 PRs) is reported.
