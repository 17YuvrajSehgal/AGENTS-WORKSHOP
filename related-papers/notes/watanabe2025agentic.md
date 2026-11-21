# On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub
- **Authors:** Miku Watanabe, Yutaro Kashiwa, Brittany Reid, Hajimu Iida (Nara Institute of Science and Technology, Japan); Hao Li, Ahmed E. Hassan (Queen's University, Canada)
- **Venue / year / status:** First page says "This manuscript is accepted at ACM Transactions on Software Engineering and Methodology (TOSEM)". The copy we have is arXiv:2509.14745v3 [cs.SE], dated 9 Feb 2026. Volume, article number and DOI are still placeholders. 24 pages. Peer-reviewed (accepted journal paper).
- **PDF:** `related-papers/watanabe2025agentic_2509.14745.pdf`
- **Cite key:** watanabe2025agentic
- **BibTeX-style reference:** Miku Watanabe, Hao Li, Yutaro Kashiwa, Brittany Reid, Hajimu Iida, and Ahmed E. Hassan. 2025. On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub. ACM Trans. Softw. Eng. Methodol. (accepted). arXiv:2509.14745.

## In short
The authors study 567 GitHub pull requests (PRs) that say "Generated with Claude Code", from 157 open-source repositories with at least 10 stars, created between February 24 and April 30, 2025. They compare them with 567 PRs written without the tool by the same authors in the same repositories. Main results: 83.8% of the Claude Code PRs were merged (human PRs: 91.0%), 54.9% of the merged ones needed no further commit, and when changes were needed the most common kind was a bug fix (47.7% of revised PRs). Claude Code PRs do more refactoring, tests and documentation, have much longer descriptions (median 355 words against 56), and more often mix several purposes in one PR. Performance PRs were 5.2% of the sampled Claude Code PRs against 1.4% of human PRs. The paper does not use the AIDev dataset; it collects its own data. Two of the authors (Hao Li, Ahmed E. Hassan) are also AIDev authors.

## Problem and motivation
- Earlier studies looked at chatbots such as ChatGPT. The authors say "no prior work has investigated the impact of agentic coding on the software development process and resulting artifacts" (Section 1).
- Agent PRs have mixed outcomes. Some are merged as they are. Some are closed with complaints. Some are merged only after "substantial revision by developers" (Section 2).
- Four research questions: RQ1 how agent PRs differ from human PRs in size and purpose; RQ2 how many are rejected and why; RQ3 how many are merged without revision and how much revision the others need; RQ4 what kinds of revisions are needed.

## Background / key terms (explain each term simply)
- **Agentic coding:** "the use of autonomous AI agents to generate, modify, and submit code". The agent plans, edits, tests and repeats with little human help.
- **Claude Code:** Anthropic's command-line coding agent. It can edit files, run commands and tests, use git and open PRs. Released February 24, 2025 (per the paper).
- **Agentic-PR (APR):** here, a PR whose description contains the string "Generated with Claude Code". **Human-PR (HPR):** a PR without that mark.
- **MCP (Model Context Protocol):** a way to connect an agent to outside tools and data (files, command line, cloud services).
- **Acceptance / rejection:** merged PR = accepted. Closed without merge = rejected.
- **Revision:** any commit added to the PR after the first commit and before merge.
- **Multi-label classification:** one PR may get several purpose labels (for example fix and test).
- **Label-level agreement:** the share of labels on which two annotators agreed. Used here in place of Cohen's kappa because of multi-label coding.
- **Cohen's kappa:** agreement between two annotators corrected for chance. 0.41 to 0.60 is usually called "moderate".
- **Mann-Whitney U test:** compares two groups without assuming a bell-shaped distribution. **Chi-squared test:** compares proportions. **Log-rank test:** compares time-to-event curves (here, time to merge).
- **Survival bias:** bias from looking only at cases that reached an end state (here, closed PRs).

## Method and setup
- **Agent PR collection (Section 3):** GitHub GraphQL API search for "Generated with Claude Code" in PR descriptions, PRs "submitted between February 24, 2025 (the release date of Claude Code) and April 30, 2025 (the date our study began)", repositories "with at least 10 GitHub stars".
- **Funnel:** 797 PRs found -> 54 still open removed -> 743 -> 176 removed because no matching human PRs could be found -> 567 Agentic-PRs in 157 repositories.
- **Human PR baseline:** same author, same repository, no Claude Code mark, randomly sampled "to match the number of Agentic-PRs and their authors per repository". Because not enough existed in the same weeks, the window was extended backward, "back to April 30, 2024". The paper calls this "approximately 10 months". 567 Human-PRs. The two sets do not overlap.
- **RQ1:** manual labels on a sample: 213 of 475 merged APRs and 221 of 516 merged HPRs (sizes chosen for 95% confidence, 5% margin of error). Labels from Zeng et al.'s scheme: purpose types (fix, feat, refactor, style, perf) and object types (docs, test, ci, build, chore). Multi-label. First and third authors labelled independently; label-level agreement 75.8% (disagreed on 172 of 675 labels for APRs and 113 of 501 for HPRs). Second author resolved conflicts, then all three discussed. Size metrics compared with Mann-Whitney U (α = 0.05).
- **RQ2:** merge rate, time to merge (log-rank test), chi-squared test on acceptance. Manual reading of all 92 rejected APRs using Pantiuchina et al.'s rejection categories plus new ones from open coding. Two annotators, 68.5% agreement, Cohen's kappa 0.4865 ("moderate").
- **RQ3:** share of merged PRs with a single commit; for the others, number of revision commits, files changed, lines added and deleted, and percent change against the first commit.
- **RQ4:** manual labels for all 214 revised merged APRs, aggregated per PR. Second and third authors; agreement 64.1% (541 of 844 labels). Also counts revision commits that carry "Co-Authored-By: Claude".
- No code is built or run. No performance is measured.

## Section-by-section notes

### 1. Introduction and 2. Motivating Example
- Claude Code and agents on Claude 4 Sonnet were "above 70% resolution rate" on SWE-bench as of May 2025 (Section 2).
- One PR was closed after the reviewer found a problem and "the author noted that the proposed change cannot be used at all".

### 3. Data Collection
- See Method. Open PRs are excluded on purpose.

### 4.1 RQ1: size and purpose
- fix is the top purpose for both (31.0% APR, 30.8% HPR; 66 and 68 PRs). feat is second (26.8%, 27.6%).
- More in APRs: refactor 24.9% vs 14.9% (53 vs 33 PRs), test 18.8% vs 4.5% (40 vs 10), docs 22.1% vs 14.0% (47 vs 31), build 10.8% vs 3.6%, style 7.5% vs 1.8% (16 vs 4), **perf 5.2% vs 1.4% (11 vs 3 PRs)**.
- More in HPRs: chore 10.4% vs 3.8%, ci 7.2% vs 6.1%.
- "Code refinement and optimization make up 12.7% of Agentic-PRs, compared to just 3.2% of Human-PRs" (style plus perf). The perf example given is "a PR eliminating wildcard column selections to optimize database queries" (mattermost PR 30424). The authors call these "repetitive, rule-based tasks" and "micro-optimizations".
- Multi-purpose PRs: 85 of 213 APRs (39.9%) against 27 HPRs (12.2%). Common pairs: feat + test 9.0%, refactor + test 7.7%, fix + test 7.7%.
- Size of the first submission: both change a median of 2 files. APRs add more lines (median 48 vs 24); deletions are similar (7 vs 8). Description length: median 355 words (APR) vs 56 (HPR). The text says the Mann-Whitney tests "confirm that the differences description length are statistically significant". It does not clearly say whether the added-lines difference is significant.
- The authors' reading of the long descriptions: "the agent is documenting its process, its reasoning, and the changes it made in detail. This could be helpful for reviewers."

### 4.2 RQ2: rejection
- 475 of 567 APRs merged (83.8%); 516 of 567 HPRs merged (91.0%). Chi-squared: the human rate is significantly higher (p < 0.05).
- Median time to merge: 1.23 hours (APR), 1.04 hours (HPR). Log-rank test: no significant difference.
- Reasons for the 92 rejected APRs (Table 3, percent of 92): 64.1% (59 PRs) closed with no comment at all, so the reason is unknown. Among the rest: another solution was chosen 12.0%; PR made only to trigger CI checks 5.4%; too large 3.3%; obsolete 3.3%; inactive 2.2%; non-optimal design 2.2%; then 1.1% each (one PR) for no added value, extra complexity, no confidence in AI code, introduced bugs, not in the community's interest, merge conflicts, and "not sure".
- **Performance-related rejection:** one PR (mattermost PR 30890) "was closed after maintainers determined the changes, while technically correct, failed to address the actual performance bottlenecks that mattered". This is the paper's own summary, not a quote from the maintainers. It is the "do not add value" case (1 PR).
- One PR was closed with the comment "this is badly extracted and has some hallucinations, new CSS changes, and more importantly breaks the UI".
- The authors conclude that most rejections come "from project context ... rather than inherent flaws in AI-generated code". This rests on 33 PRs with a known reason.

### 4.3 RQ3: merged without revision
- Merged with a single commit: 54.9% of merged APRs (261 PRs), 58.5% of merged HPRs (302 PRs). Chi-squared: no significant difference (p > 0.05).
- When revised: both groups have a median of 2 revision commits. No significant difference in commits, files, lines added or lines deleted (Mann-Whitney, α = 0.05).
- Relative to the first submission: changed files grow by a median 50.0% in both groups; changed lines by 121.1% (HPR) and 94.3% (APR).

### 4.4 RQ4: what gets revised
- 214 of 475 merged APRs (45.1%) had revisions. Share of these 214 with each revision type (Table 4, multi-label): fix 47.7% (102), docs 29.0% (62), refactor 27.1% (58), style 23.4% (50), chore 21.0% (45), test 16.4% (35), feat 15.4% (33), build 14.0% (30), ci 7.0%, **perf 1.4%**.
- On bug-fix revisions: "agent-generated code frequently implements optimistic error handling strategies that fail to distinguish between recoverable and non-recoverable failure conditions". This comes from a few examples, not a count.
- The one perf revision example: a reviewer "added a cache-busting mechanism to ensure data freshness for an efficient but potentially stale storage driver implemented by an agent". So the agent's fast version could return old data. This is a correctness cost hidden behind a speed gain.
- 41.1% (88 of 214) of revised APRs had Claude as co-author on a revision; that is 34.1% (298 of 873) of revision commits. So "human revision" is often done with the agent again.

### 5. Implications
- Researchers: measure the cost of trust; build PR-level benchmarks (SWE-bench misses documentation, style and review); record the whole human-AI workflow as "full-trace datasets" from prompts to "CI/CD logs, review iterations, and final merge decisions".
- Developers: give small tasks, split large PRs; keep project rules in a file such as CLAUDE.md.
- Agent builders: attach a "confidence card" with "the plan followed, key assumptions, considered alternatives, and known edge cases"; automate rebases; connect linters and "build-checking and test-coverage tools" through MCP.

### 6. Related Work
- Human-AI collaboration; AI help in issues and PRs (ChatGPT studies); studies of generated code (correctness, efficiency, security). They cite Niu et al. for "functional correctness rarely correlates with efficiency" (their ref [30]) and for needing "extra effort" to get efficient code (ref [31]). These are other papers' results.

### 7. Threats to Validity
- **Internal:** developers may edit generated code before commit, or use Claude Code without the mark. The mark gives "a binary classification that may overlook hybrid workflows". Human PRs may contain undisclosed AI code, which "would likely dilute the differences". Time mismatch: only 42.0% (238 of 567) of HPRs come from the same weeks as the APRs. Check on that subset: fix 27.0%, feat 24.7%, test 9.0%; acceptance 87.0% (full set 91.0%); median merge time 0.7 h (full set 1.0 h).
- **Construct:** the effects of agent abilities and MCP are not separated. Open PRs are excluded, which "creates a survival bias". Merge is the success measure, and it "does not account for long-term code quality or maintainability. A merged PR may still introduce latent bugs or negatively impact the codebase over time (e.g., causing regressions or necessitating subsequent reverts)."
- **External:** 567 PRs is "the full set we were able to retrieve". The tool was new, so behaviour may reflect "an 'enthusiastic phase'". Only Claude Code; results "may not generalize to other agentic coding tools".

### 8. Conclusion
- Agent PRs are accepted less often than human PRs but are widely merged; revision effort is similar; agent code is "a strong starting point that benefits from human oversight".

## Key results (with numbers) and what they mean
- 83.8% of Claude Code PRs merged vs 91.0% human (Table 2) -> a 7.2 point gap. Note the human PRs are by the same people in their own projects, so both rates are high.
- Median time to merge 1.23 h vs 1.04 h, no significant difference -> half of the agent PRs were merged within about 74 minutes. That leaves little time for anyone to benchmark a change.
- 54.9% of merged APRs merged as the first commit -> more than half of merged agent PRs were accepted with no change.
- Description length 355 vs 56 words (median) -> agent PRs come with about six times more text. For us: agents explain a lot, so there is plenty of claim text to extract a mechanism from.
- perf: 5.2% of sampled APRs (11 of 213) vs 1.4% of HPRs (3 of 221) -> the same developers opened perf PRs more often with Claude Code than without. The counts are very small.
- 47.7% of revised APRs needed a bug fix -> the most common reason a human touches an agent PR is that something was wrong.
- 64.1% of rejections have no stated reason -> the rejection analysis covers only 33 PRs. Each 1.1% is a single PR.
- 34.1% of revision commits co-authored by Claude -> revisions are not purely human work.

## Tables and figures
- **Figure 1 (p. 3):** a Claude Code terminal session doing a refactoring and creating a PR.
- **Figure 2 (p. 4):** a GitHub PR created by Claude Code, with follow-up commits by developers.
- **Figure 3 (p. 5):** data collection overview. APRs: mark present and stars > 10 (the figure writes "Stars > 10"; the text says "at least 10"). HPRs: same author, same repository, no mark.
- **Table 1 (p. 6), PR purposes, % APRs / % HPRs / difference:** fix 31.0 / 30.8 / +0.2; feat 26.8 / 27.6 / −0.8; refactor 24.9 / 14.9 / +10; docs 22.1 / 14.0 / +8.1; test 18.8 / 4.5 / +14.3; build 10.8 / 3.6 / +7.2; style 7.5 / 1.8 / +5.7; ci 6.1 / 7.2 / −1.1; perf 5.2 / 1.4 / +3.8; chore 3.8 / 10.4 / −6.6. Percentages sum to more than 100 because of multi-label. perf is defined as "Code changes that improve performance, such as enhancing execution speed or reducing memory consumption".
- **Figure 4 (p. 8):** box plots (log scale) of changed files, added lines, deleted lines for the first submission, APR vs HPR. Its caption says "in revised commits" and "do not include metrics from the first commit", which is the same caption as Figure 6. This looks like a copy error in the paper, because the text uses Figure 4 for initial submissions.
- **Table 2 (p. 9):** APRs 475 accepted, 92 rejected, 567 total, 83.8%, median 1.23 hours. HPRs 516, 51, 567, 91.0%, 1.04 hours.
- **Table 3 (p. 11):** rejection reasons for the 92 rejected APRs (listed above).
- **Figure 5 (p. 12):** number of revision commits, APR vs HPR; medians are equal (2).
- **Figure 6 (p. 13):** changed files, added and deleted lines in revision commits.
- **Table 4 (p. 14):** revision types for the 214 revised APRs (listed above).

## Ideas we can use
- Agent PR descriptions are long and explain reasoning. This supports our design choice to extract a claimed mechanism from the PR text.
- The paper's own threat ("A merged PR may still introduce latent bugs ... causing regressions") is a clean hook for our work: merge is not proof.
- Their "confidence card" proposal (plan, assumptions, alternatives, edge cases) is close to what our tool checks after the fact. We can say that our measurement gives evidence for one line of such a card: the performance claim.
- The cache-busting example (fast but possibly stale) is a real case of our "output changed" and "hidden cost" outcome classes.
- Their call for "full-trace datasets" covers prompts to CI logs. We add a layer they do not mention: what the code does in the kernel and CPU.

## Weaknesses and things glossed over
- Human PRs come from up to 10 months earlier. Only 42.0% are from the same weeks. The check on that subset shows a lower human acceptance (87.0%), so the gap to 83.8% becomes small. The paper still headlines 91.0%.
- Same-author, same-repository pairs mean many PRs are by maintainers in their own projects. Such PRs are merged easily. The high merge rates may not hold for outside contributors.
- "Merged with a single commit" is used as "accepted without revision". A force-push or squash rewrites history, so some revised PRs may look like single-commit PRs. The paper does not discuss this.
- 59 of 92 rejections have no reason. The claim that rejections are mostly not about code flaws rests on 33 PRs.
- Agreement between annotators is modest: 75.8% (RQ1), 68.5% with kappa 0.4865 (RQ2), 64.1% (RQ4).
- Annotator roles are described differently in Section 4.1 (first and third authors label, second resolves) and Section 4.4 (second and third label, second resolves "following the same process").
- Numbers in the Implications section do not always match the Results. "only 2.2% of rejected Agentic-PRs explicitly cited 'lack of confidence'" but Table 3 says 1.1%. "nearly one-third of merged Agentic-PRs still required bug fixes, style adjustments, or refactoring" but 45.1% were revised. "52.4% of Agentic-PR revisions" adds docs 29.0% and style 23.4%, and "8.4%" adds ci 7.0% and perf 1.4%; these are multi-label percentages, so the sums can count one PR twice.
- The claim that many rejections "followed slow reviews or repeated revision requests" (Section 5.1) has no number behind it in Section 4.2.
- "No significant difference" in revision effort is not proof of equal effort; no effect sizes or confidence intervals are given.
- Only RQ1 used a sample (213 and 221); a 5% margin of error is large next to small categories like perf (11 and 3 PRs).
- Only PRs that keep the default "Generated with Claude Code" mark are found. Developers who remove it are missed.
- One tool, about nine weeks right after release, repositories with at least 10 stars.
- No check of whether any PR does what its description says. For perf PRs, no speed is measured.

## Open questions and future work (theirs, and ours)
- Theirs: finer provenance tracking to separate agent and human code; longer time windows; other agents (they name GitHub Copilot); long-term stability and maintainability of merged agent code "through longitudinal analysis"; separating the effect of MCP.
- Ours: of the 11 perf PRs in their sample, how many were faster in reality? Nobody checked. This is exactly the question our pipeline answers on AIDev.
- Ours: are long agent descriptions accurate, or only long? Length is measured here; truth is not.

## Link to our paper
- This key is in `paper/refs.bib` but I found no `\cite{watanabe2025agentic}` in `paper/main.tex` or `paper/sections/` yet.
- Best places: Introduction or Related Work (agent PRs are merged at high rates and quickly; descriptions are long), and Threats (merge is not a quality measure, in the authors' own words).
- This study is not based on AIDev. Do not describe it as an AIDev study, even though two authors are shared.

## Link to the thesis (tracing, kernel analysis)
- Nothing on tracing or kernels. Performance appears only as a label ("perf") on PRs.
- The cache-busting revision shows why timing alone is not enough to judge a performance change: the faster version could serve stale data. A trace that shows fewer reads or fewer syscalls would explain the speed-up and also raise the question of whether needed work was skipped.
- Their idea of "full-trace datasets" is about workflow logs. A thesis angle: add system-level traces of the changed code to such datasets.

## Quotes for inline citation
- "we empirically study 567 GitHub pull requests (PRs) generated using Claude Code, an agentic coding tool, across 157 diverse open-source projects" (Abstract, p. 1)
- "83.8% of these agent-assisted PRs are eventually accepted and merged by project maintainers, with 54.9% of the merged PRs being integrated without further modification" (Abstract, p. 1)
- "APRs contain significantly longer PR descriptions with a median of 355 words, compared to 56 words in HPRs" (Section 4.1, p. 8)
- "one PR was closed after maintainers determined the changes, while technically correct, failed to address the actual performance bottlenecks that mattered" (Section 4.2, p. 10)
- "The majority (47.7%) of revisions to Agentic-PRs target bug fixes." (Section 4.4, p. 14)
- "our reliance on PR acceptance as a primary success metric does not account for long-term code quality or maintainability. A merged PR may still introduce latent bugs or negatively impact the codebase over time (e.g., causing regressions or necessitating subsequent reverts)." (Section 7.2, p. 21)
- "This exclusion creates a survival bias" (Section 7.2, p. 21)

## Suggested citation sentences
- In a study of 567 Claude Code PRs, 83.8% were merged, with a median time to merge of 1.23 hours \cite{watanabe2025agentic}.
- Agent PRs carry long descriptions (a median of 355 words against 56 for the same developers' own PRs) \cite{watanabe2025agentic}, which is the text we mine for the claimed mechanism.
- Studies of agent PRs use merge as the measure of success and note that a merged PR may still cause regressions \cite{watanabe2025agentic}; we measure the change itself.
- Performance changes were labelled in 5.2% of sampled Claude Code PRs against 1.4% of human PRs \cite{watanabe2025agentic}, but no study measured whether they were faster.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It shows what happens to agent PRs in review: most are merged, fast, and often with no change. We ask the next question for performance PRs: was the merged claim true?
  - It labels PRs as "perf" by reading them. It does not build, run or measure anything. We do, with timing, hardware counters and kernel traces.
  - It gives two real cases that match our outcome classes: a perf PR that was "technically correct" but missed the real bottleneck, and an agent's efficient storage driver that needed a fix for stale data.
  - Points that weaken or limit us: (a) the authors find that rejections come mostly from project context, "rather than inherent flaws in AI-generated code", and that revision effort is not different from human PRs, so this paper does not support a story that agent PRs are generally bad; (b) only 1.4% of revisions concern performance, so reviewers rarely act on performance, which can be read as "performance is rarely a problem" as well as "performance is rarely checked"; (c) the data is Claude Code only and is not AIDev.
- **Safe to cite for:**
  - Most Claude Code PRs are merged: Abstract, "83.8% of these agent-assisted PRs are eventually accepted and merged by project maintainers" (human PRs 91.0%, Table 2).
  - They are merged quickly: Table 2, median time to merge 1.23 hours; "no significant difference in merge times" (Section 4.2).
  - More than half of merged agent PRs are merged unchanged: Section 4.3, "54.9% of APRs (261 PRs) are merged as-is with a single commit".
  - Agent PR descriptions are long: Section 4.1, "a median of 355 words, compared to 56 words in HPRs".
  - Performance PRs are a visible share of Claude Code PRs in this sample: Table 1, perf 5.2% (11 of 213) vs 1.4% (3 of 221). Say "in a manually labelled sample".
  - Merge is not a quality measure: Section 7.2, "A merged PR may still introduce latent bugs or negatively impact the codebase over time (e.g., causing regressions or necessitating subsequent reverts)."
- **Do not cite for:**
  - Any result about AIDev. This paper has its own 567-PR dataset (repositories with at least 10 stars).
  - Any claim that agent performance PRs fail to speed code up, or that their explanations are wrong. No performance is measured. The "bottlenecks" case is one PR.
  - "Reviewers do not check performance claims." The paper does not study what reviewers verified.
  - All coding agents. It covers Claude Code only, February 24 to April 30, 2025.
  - "Agent PRs need more revision than human PRs." The paper finds no significant difference.
  - "Agent code has poor error handling" as a measured rate. It is an observation from examples.
  - "Functional correctness rarely correlates with efficiency." That is Niu et al. (their ref [30]), only cited here.
  - The "2.2% lack of confidence" number from Section 5.1. Table 3 says 1.1% (one PR).
