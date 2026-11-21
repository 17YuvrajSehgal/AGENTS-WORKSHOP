# Analyzing Message-Code Inconsistency in AI Coding Agent-Authored Pull Requests
- **Authors:** Jingzhi Gong (King's College London), Giovanni Pinna (University of Trieste), Yixin Bian (Harbin Normal University), Jie M. Zhang (King's College London, corresponding author)
- **Venue / year / status:** MSR '26 (23rd International Conference on Mining Software Repositories), April 13-14, 2026, Rio de Janeiro, Brazil. ACM, 5 pages, DOI 10.1145/3793302.3793583. The paper uses the AIDev dataset and is 5 pages long; it does not say which MSR track it is in. arXiv:2601.04886v2, 26 Jan 2026.
- **PDF:** related-papers/gong2026inconsistency_2601.04886.pdf
- **Cite key:** gong2026inconsistency
- **BibTeX-style reference:** Jingzhi Gong, Giovanni Pinna, Yixin Bian, and Jie M. Zhang. 2026. Analyzing Message-Code Inconsistency in AI Coding Agent-Authored Pull Requests. In 23rd International Conference on Mining Software Repositories (MSR '26), April 13-14, 2026, Rio de Janeiro, Brazil. ACM, 5 pages. https://doi.org/10.1145/3793302.3793583

## In short
The paper asks how often the description of an agent-written pull request (PR) does not match the code change. It scores 23,247 AIDev PRs with a cheap heuristic that never reads the meaning of the code: it compares description length to change size, the file types the description mentions to the file types changed, and the wording to the task label. 406 PRs (1.7%) fall below the threshold and are called "high-MCI" (high message-code inconsistency). Two authors also hand-label 974 PRs and sort 432 partly or fully misaligned ones into eight types. The most common type is "Phantom Changes" (45.4%): the description claims changes that are not in the code. High-MCI PRs are accepted far less often (28.3% against 80.0%) and take longer to merge (55.8 h against 16.0 h). Performance PRs are not in the studied set.

## Problem and motivation
- Agent PRs are black boxes for reviewers. Reviewers rely on the PR title and body to understand the change.
- Generative models can write statements that are wrong. If the description is wrong, reviewers are misled and trust drops.
- Message-code inconsistency was studied for human commit messages. The authors say it "remains unexplored" for agent PR descriptions.

## Background / key terms (explain each term simply)
- **Agentic-PR:** a pull request written and opened by an AI coding agent.
- **MCI (message-code inconsistency):** the text that describes a change says something different from what the code change does.
- **PR-MCI:** MCI measured between a PR description (title + body) and the PR's code changes.
- **High-MCI:** a PR whose similarity score is below the threshold 0.61. In RQ1 and RQ3 "partially aligned" PRs count as aligned, so high-MCI means clearly misaligned.
- **Phantom Changes:** the description claims changes that were not implemented.
- **Scope Understated:** the description leaves out significant changes.
- **Placeholder/Incomplete:** the description is generic or boilerplate text.
- **Wilson confidence interval:** a standard interval for a proportion that behaves well for small counts.
- **Cohen's kappa:** agreement between two annotators beyond chance. 1 is perfect.
- **Cramér's V / Cliff's delta:** effect sizes. V is for two categorical variables, delta for two groups of numbers. Both say how big a difference is, not only whether it is significant.
- **Mann-Whitney U test:** a rank test for whether one group tends to have larger values than another. It does not assume a normal distribution.

## Method and setup
- **Data:** AIDev-pop, "33,596 PRs from 2,807 repositories with >100 stars". Filters: closed PRs, permissive licenses (MIT or Apache 2.0), and the "six most common task types (95.2%)". Result: 23,247 PRs from five agents. The six task types, from Tables 1 and 2, are feature, bug fix, refactor, test, documentation and chore. **Performance is not one of them.**
- **Per-agent sizes (from Table 2, low + high counts):** OpenAI Codex 16,779; Devin 2,891; GitHub Copilot 2,675; Cursor 682; Claude Code 220. Codex is 72% of the data (my arithmetic).
- **PR-MCI score (Sec. 3.1):** s = 0.3·s_s + 0.4·s_f + 0.3·s_t, between 0 and 1.
  - s_s, scope adequacy: does the description length fit the amount of code churn.
  - s_f, file-type consistency: are the file types the description mentions (tests, documentation) really modified.
  - s_t, task-type alignment: does the wording fit the labelled task type.
  - The weights are chosen by argument (file type is "the most concrete and verifiable evidence"), not fitted. An ablation is in the supplementary material.
- **Validation:** two authors labelled 600 PRs (stratified by agent, task type and score bin) as aligned, partially aligned or misaligned. Kappa = 0.892. Threshold 0.61 chosen to maximise F1 on these labels. Five-fold cross-validation of the threshold: mean 0.606, std 0.008.
- **Heuristic quality (Table 1, n=600):** precision 0.742, recall 0.548, F1 0.630. An embedding method (Qwen3-Embedding-0.6B) gets F1 0.150. Requiring both methods to agree gets F1 0.567.
- **Taxonomy (Sec. 3.2):** GPT-5.2 proposes a codebook of eight categories. Two annotators refine it by discussion and label 432 partial or misaligned PRs out of 974 (the 600 validation PRs plus 374 more high-MCI PRs from RQ1).
- **Outcome tests (Sec. 3.3):** acceptance rate, time to merge, review count, comment count. Chi-square with Cramér's V for acceptance. Mann-Whitney U with Cliff's delta for the others. p < 0.05. Regression with log code churn, files changed, task type and agent as controls (details only in supplementary material).

## Section-by-section notes

### 1. Introduction
- Three RQs: how often descriptions misalign (RQ1), which types of inconsistency occur (RQ2), whether inconsistency is associated with acceptance and review effort (RQ3).
- Contributions: the 974 annotated PRs, the 1.7% prevalence "with a 20-fold variation across agents", the eight types, and the outcome differences.

### 2. Background and related work
- Prior MCI work is on human commit messages and on benchmarking LLMs to detect text-code inconsistency.
- Footnote 1: PR descriptions differ from commit messages because they "may span multiple commits and serve as the primary communication channel for reviewers".

### 3. Methodology
- See above. One point to keep in mind: "RQ1 and RQ3 use a strict binary definition of high-MCI (treating partially aligned PRs as aligned)", while RQ2 includes partial and misaligned PRs. So the 1.7% and the 45.4% are about different sets.

### 4.1 RQ1: Prevalence
- 406 of 23,247 PRs (1.7%, 95% CI [1.6, 1.9]) are high-MCI.
- By agent (Table 1): GitHub Copilot 8.7% [7.7, 9.9] (234 of 2,675); Cursor 4.5% [3.2, 6.4] (31 of 682); Claude Code 0.9% [0.2, 3.3]; OpenAI Codex 0.8% [0.6, 0.9]; Devin 0.4% [0.2, 0.7]. The "20x" is Copilot against Devin.
- By task type: chore 4.0% (24 of 600); refactor 3.5% (54 of 1,553); bug fix 2.1% (113 of 5,319); feature 1.5%; documentation 1.0%; test 1.0%.
- Fig. 2 (agent x task heatmap): Copilot is high almost everywhere, with test 13.7% and refactor 13.2% the highest.
- Footnote 3: with thresholds from 0.55 to 0.65 the relative order stays the same (supplementary material).

### 4.2 RQ2: Taxonomy
- Eight types: Phantom Changes, Scope Understated, Placeholder/Incomplete, Scope Overstated, Intent/Change Type Mismatch, Misleading Specifics, Vague/Generic, Other/Mixed.
- Overall (n=432): Phantom Changes 45.4%, Scope Understated 22.0%, Placeholder/Incomplete 18.8%. The shares of the five smaller types are in Fig. 3 only; two small segments read 6.7% and 3.0% but I could not match them to a type with certainty (unclear in the PDF).
- By agent: Copilot (n=250) is 74.0% Phantom Changes. Cursor (n=36) 52.8% and Devin (n=39) 41.0% are led by Scope Understated. Codex (n=93) is split between Scope Understated 41.9% and Placeholder/Incomplete 39.8%. Claude Code has n=14.
- By task: test (55%) and bug fix (53.5%) PRs are most often Phantom Changes. Refactor PRs are led by Scope Understated (40.5%).

### 4.3 RQ3: Review outcomes (Table 2)
- Acceptance: 28.3% (high-MCI, n=406) against 80.0% (low-MCI, n=22,841), p < 0.001, Cramér's V = 0.166 (labelled "small").
- Time to merge, merged PRs only: 55.8 h (n=115) against 16.0 h (n=18,282), p < 0.001, Cliff's delta = 0.310 (labelled "small").
- Reviews per PR: 0.42 against 0.74 (p = 0.039, negligible effect). Comments: 0.37 against 0.64 (p = 0.012, negligible). So high-MCI PRs get fewer reviews and comments, not more.
- By agent, acceptance: only Copilot (3.4% against 59.4%, medium effect) and Codex (62.5% against 87.2%, negligible effect) are significant. Claude Code (p = 1.000, n=2 high), Cursor (p = 0.638) and Devin (p = 0.580, n=11 high) are not.
- By task, acceptance: all six significant at p < 0.001 with small effects.
- By agent, time to merge: only Codex is significant (38.6 h against 5.7 h, medium effect). For Copilot, Devin and Claude Code the high-MCI merged PRs were merged faster on average, not slower, but these rest on 8, 5 and 1 PRs.
- Regression: PR-MCI stays significant for acceptance and merge time (p < 0.001 for both) after the controls. No coefficients in the paper.

### 5. Discussion
- Advice to agent users: "verify that agents actually commit changes".
- Advice to reviewers: check the diff is not empty, check the description is not too brief for the change, check for template markers such as "[WIP]", "[Failed]" or "I'm starting to work on it".
- Advice to tool builders: add automated PR-MCI verification before review.
- "high-MCI PRs take 3.5x longer to merge, wasting around 40 hours per PR". This reads the association as a cause, which the threats section says the study cannot do.

### 5.4 Threats to validity
- The metric "is a heuristic proxy for semantic consistency and may miss subtle mismatches or penalize concise but accurate descriptions".
- The threshold is tuned on the validation set, "which weakens absolute prevalence claims".
- Agent sizes are imbalanced ("Claude Code has only 220 PRs").
- "Our analysis is observational and does not establish causal relationships between PR-MCI and review outcomes."

### 6. Conclusion and data
- Data, scripts and supplementary material: https://github.com/gjz78910/PR-MCI

## Key results (with numbers) and what they mean
- 406 of 23,247 PRs (1.7%) are high-MCI -> this is the share of PRs that a shallow, structure-only check flags. It is not the share of PRs whose description is wrong. With recall 0.548 on the validation set, the check misses almost half of the PRs the annotators called misaligned, and it cannot see a wrong claim inside a description that has the right shape.
- Copilot 8.7% against Devin 0.4% -> the differences between agents are large, but the paper's own advice (empty diffs, "[WIP]" markers) suggests much of Copilot's high-MCI is PRs that never got finished, not subtle misdescription.
- Phantom Changes 45.4% of 432 -> when descriptions do misalign, the usual form is "says it did something that is not in the diff". That is the closest thing in the literature to our "claimed mechanism did not happen", but at the level of code presence, not runtime behaviour.
- Acceptance 28.3% against 80.0% -> a large gap in percentage points. The overall effect size is small (V = 0.166) because only 406 PRs are in the high group. Most of the gap comes from Copilot: 234 of the 406 high-MCI PRs are Copilot's, with 3.4% acceptance.
- 55.8 h against 16.0 h to merge -> also mostly one agent. Only Codex shows a significant per-agent difference.
- Fewer reviews and comments on high-MCI PRs -> reviewers do not spend more effort on these PRs. They seem to ignore or close them. This sits badly with "wasted review effort".

## Tables and figures
- **Fig. 1 (p. 2):** workflow: dataset filter (23,247 PRs) -> RQ1 score and manual annotation -> RQ2 codebook and taxonomy -> RQ3 tests and regression.
- **Table 1 (p. 2):** high-MCI prevalence overall, by agent and by task type for three methods (heuristic, embedding, agreement), with 95% Wilson intervals for the heuristic, and precision / recall / F1 on n=600. Read: the embedding method flags 60.0% of all PRs and has precision 0.083, so it is useless here; the heuristic is the only usable one and still has recall 0.548.
- **Fig. 2 (p. 3):** heatmap of high-MCI rate by agent and task type. Rows read (feat, fix, refactor, test, docs, chore): Claude Code 0.8, 0.0, 0.0, 0.0, 0.0, 12.5; Copilot 9.5, 7.1, 13.2, 13.7, 7.5, 10.7; Cursor 8.1, 2.6, 1.7, 10.0, 0.9, 0.0; Devin 0.3, 0.4, 0.7, 0.0, 0.3, 0.9; Codex 0.7, 0.7, 2.6, 0.3, 0.4, 3.1. The text confirms only Copilot test 13.7 and refactor 13.2; the rest are from the garbled text layer. Cells have no counts, so a value like Claude Code chore 12.5% may be one PR.
- **Table 2 (p. 3):** outcome metrics for low- and high-MCI PRs with p-value, effect-size label and group sizes, overall, by agent and by task type. Read the "# High" column first: many rows rest on fewer than 25 PRs.
- **Fig. 3 (p. 4):** stacked bars of the eight types overall (432), by agent and by task type. Read: Copilot's bar is almost all Phantom Changes; the other agents are mixed.

## Ideas we can use
- The paper gives the motivation sentence we need: agent PR descriptions are not always faithful to the code, and unfaithful ones are linked to worse review outcomes.
- Their taxonomy is a model for our verdict labels. "Phantom Changes" is the static cousin of our "claimed mechanism did not happen". We could name our runtime version clearly so the two are not confused.
- Their check is text against diff. Ours is text against measured behaviour. A PR can pass theirs (the caching code is in the diff) and fail ours (the cache is never hit, so `read` syscalls do not drop). This contrast is a clean way to state our contribution.
- Their reviewer heuristics (empty diff, template markers) are cheap pre-filters we could apply before spending build and measurement time on a PR.

## Weaknesses and things glossed over
- **Performance PRs are excluded.** The six task types do not include performance. Nothing in this paper is measured on the PRs we study.
- The heuristic does not read code semantics or check any specific claim. It checks shape: length, file types, task wording. The paper admits it is a "proxy".
- Recall 0.548 and precision 0.742: about a quarter of flagged PRs are not misaligned by the annotators' labels, and almost half of misaligned ones are missed. The 600 validation PRs are stratified by score bin, so these rates do not carry over directly to the full set, and the paper does not correct the 1.7% for them.
- The threshold is tuned and evaluated on the same 600 PRs (cross-validation only checks threshold stability).
- "51.7% lower acceptance rates" is a difference of 51.7 percentage points (80.0 - 28.3), not a relative drop. Write "51.7 percentage points" if we use it.
- Copilot acceptance: the text says "3.4% vs. 59.4%, a 55.9 percentage point drop". The subtraction gives 56.0. A rounding detail, but do not quote "55.9".
- Table 2, time to merge: the overall row has n=115 high-MCI merged PRs, but the per-agent rows sum to 112 (1 + 8 + 21 + 5 + 77) and the per-task rows also sum to 112. The low-MCI per-agent rows sum to 18,224 against 18,282. The paper does not explain the gap.
- Effect sizes are "small" or "negligible" in almost every row; the abstract's "Statistical tests confirmed" reads stronger than that.
- The pooled outcome gap is mostly a Copilot effect, and three of five agents show no significant acceptance difference. The regression controls for agent, but its results are not in the paper.
- "wasting around 40 hours per PR" and "helping recover thousands of hours of wasted review effort" treat time-to-merge as review effort and association as cause. Time to merge is waiting time, and high-MCI PRs get fewer reviews.
- The 432 taxonomy PRs come partly from a sample stratified by score and partly from heuristic-flagged PRs, so the type shares describe what the heuristic finds, not all inconsistency. Annotator agreement for the eight-type labelling is not reported (kappa = 0.892 is for the aligned / partial / misaligned labels).
- The codebook was started by GPT-5.2.
- Only closed PRs under MIT or Apache 2.0 licenses.

## Open questions and future work (theirs, and ours)
- Theirs: find out why agents differ in how well they describe changes; build standard metrics for description quality; improve description generation with prompts, fine-tuning or reinforcement learning; build automated PR-MCI verification.
- Ours: what is the inconsistency rate for performance PRs, which this paper leaves out? How many PRs are consistent at the text-diff level but wrong at the behaviour level? Is a failed mechanism check associated with rejection, as high-MCI is here?

## Link to our paper
- **Introduction / motivation:** cite for "PR descriptions are what reviewers rely on, and they are not always faithful to the code".
- **Related work:** this is the nearest prior work on claim-versus-reality for agent PRs. Position: they check description against diff with a static heuristic; we check the description's performance mechanism against kernel and hardware measurements.
- **Discussion:** their call for "automated PR-MCI verification mechanisms" is a call our pipeline answers for one class of claims (performance mechanisms). Say "one class", not "PR-MCI in general".

## Link to the thesis (tracing, kernel analysis)
- No tracing or runtime content. The link is conceptual: this paper shows the limit of static checks on agent claims. A claim like "reads the file once" can only be confirmed by counting `read` syscalls at run time. That is the case for using kernel traces as a claim checker.

## Quotes for inline citation
- "Pull request (PR) descriptions generated by AI coding agents are the primary channel for communicating code changes to human reviewers." (Abstract, p. 1)
- "AI-generated descriptions (title + body) are not always faithful to the underlying code, as generative models can produce hallucinated or incorrect statements" (Sec. 1, p. 1)
- "AI agent-authored PRs (Agentic-PRs) are largely black boxes [30], forcing reviewers to rely on PR descriptions to understand changes and assess correctness" (Sec. 1, p. 1)
- "406 out of 23,247 Agentic-PRs (1.7%) exhibited high PR-MCI" (Sec. 4.1, p. 2)
- "the most common PR-MCI type was Phantom Changes (45.4%), where PR descriptions claim unimplemented changes" (Sec. 4.2, p. 3)
- "even when AI-generated code is acceptable, PR descriptions may misstate scope or claim phantom changes" (Sec. 5.1, p. 4)
- "Our PR-MCI metric is a heuristic proxy for semantic consistency and may miss subtle mismatches or penalize concise but accurate descriptions." (Sec. 5.4, p. 4)
- "Our analysis is observational and does not establish causal relationships between PR-MCI and review outcomes." (Sec. 5.4, p. 4)

## Suggested citation sentences
- Reviewers rely on the PR description to understand an agent's change, and these descriptions do not always match the code \cite{gong2026inconsistency}.
- Gong et al. compare agent PR descriptions to the diff with a static heuristic and find that, among misaligned descriptions, the most common problem is a claimed change that is not in the code \cite{gong2026inconsistency}. Their check does not run the code and their dataset excludes performance PRs; we check a performance claim against measured behaviour.
- PRs flagged as inconsistent were accepted less often (28.3\% against 80.0\%) \cite{gong2026inconsistency}, so an unreliable description is associated with a worse review outcome.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is the closest prior work on "does the agent's PR text match what the PR does". It supports our starting point: descriptions can be wrong, and reviewers depend on them.
  - Its check is static and shallow (length, file types, task wording). It cannot tell whether a claimed mechanism happens at run time. We extract the mechanism and measure the kernel or hardware signal that must move. This is the gap we fill.
  - It leaves out performance PRs entirely (only feature, bug fix, refactor, test, documentation, chore). So it gives no base rate for our population. We cannot say "X% of performance PR descriptions are inconsistent" from it.
  - A point against over-claiming: at the level this paper measures, clear inconsistency is rare (1.7%), and much of it looks like unfinished Copilot PRs. A reviewer could argue that agent descriptions are mostly fine. Our answer has to be that a description can match the diff and still be wrong about behaviour, and we need our own numbers for that.
- **Safe to cite for:**
  - Reviewers rely on agent PR descriptions. "forcing reviewers to rely on PR descriptions to understand changes and assess correctness" (Sec. 1, p. 1).
  - Agent PR descriptions are not always faithful to the code. "AI-generated descriptions (title + body) are not always faithful to the underlying code" (Sec. 1, p. 1).
  - A static heuristic flags 1.7% of 23,247 AIDev agent PRs as clearly inconsistent. "406 out of 23,247 Agentic-PRs (1.7%) exhibited high PR-MCI" (Sec. 4.1, p. 2). Say "by a heuristic" and say performance PRs were not included.
  - The most common inconsistency type is a claimed but unimplemented change. "Phantom Changes (45.4%), where PR descriptions claim unimplemented changes" (Sec. 4.2, p. 3). The base is the 432 annotated partial or misaligned PRs.
  - Flagged PRs have worse outcomes: acceptance "28.3% vs. 80.0%" and merge time "55.8 hours vs. 16.0 hours" (Sec. 4.3, p. 3). Use "associated with", as the paper's threats section requires.
  - There is a stated need for automated checking of agent PR descriptions: "implement automated PR-MCI verification mechanisms" (Sec. 5.2, p. 4).
- **Do not cite for:**
  - Any rate of inconsistency in performance PRs. They are not in the data.
  - "1.7% of agent PR descriptions are wrong." The 1.7% is what a heuristic with recall 0.548 flags, and it treats partial misalignment as aligned.
  - That inconsistency causes rejection or longer review. The paper says it is observational.
  - That agents make false performance claims, or false claims about runtime behaviour. The paper checks no runtime behaviour.
  - That the outcome gap holds for every agent. It is significant for Copilot and Codex only.
  - "51.7% lower acceptance" as a relative figure. It is 51.7 percentage points.
  - Per-agent conclusions about Claude Code (220 PRs, 2 high-MCI).
