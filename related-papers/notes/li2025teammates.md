# The Rise of AI Teammates in Software Engineering (SE) 3.0: How Autonomous Coding Agents Are Reshaping Software Engineering
- **Authors:** Hao Li, Haoxiang Zhang, Ahmed E. Hassan (all Queen's University, Canada)
- **Venue / year / status:** arXiv preprint arXiv:2507.15003v1 [cs.SE], 20 Jul 2025. Marked "Manuscript submitted to ACM". The conference name in the ACM reference block is still a template placeholder, so the copy we have is not shown as peer-reviewed. 22 pages.
- **PDF:** `related-papers/li2025teammates_2507.15003.pdf`
- **Cite key:** li2025teammates
- **BibTeX-style reference:** Hao Li, Haoxiang Zhang, and Ahmed E. Hassan. 2025. The Rise of AI Teammates in Software Engineering (SE) 3.0: How Autonomous Coding Agents Are Reshaping Software Engineering. arXiv:2507.15003.

## In short
This is the first paper that introduced the AIDev dataset, in an early and smaller form: 456,535 pull requests (PRs) opened by five coding agents (OpenAI Codex, Devin, GitHub Copilot, Cursor, Claude Code) in 61,453 repositories by 47,303 developers, collected up to June 22, 2025. All analysis is done on a small subset called AIDev-pop: 7,122 agent PRs from 856 repositories with more than 500 stars, compared with about 6,600 human PRs from the same repositories. Main results: agent PRs are merged less often than human PRs (human 76.8%; Codex 65.3%, Devin 48.9%, Copilot 38.2%), Codex PRs are closed much faster (median 0.3 hours against 3.9 hours for accepted human PRs), most PRs get no explicit review at all, and performance PRs are rare (0.0% to 1.6% of each agent's PRs). The paper ends with ten findings, nine research directions and a vision section.

**Version warning.** These numbers are for the June 22, 2025 snapshot. The later MSR '26 dataset paper (li2026aidev) reports 932,791 PRs with a 100-star subset. AIDev v5, which we use, is later again. Do not mix numbers between the three.

## Problem and motivation
- Earlier work on "AI-native" software engineering was "primarily conceptual or forward-looking" (Section 1). There was no large data on how agents behave in real projects.
- Benchmarks such as SWE-bench use "static and curated datasets" and "fail to capture the messy and emergent nature of real-world SE" (Section 1).
- Questions the authors ask: do agents produce mergeable code, how do they affect productivity and review time, how do human teams adapt.

## Background / key terms (explain each term simply)
- **Autonomous Coding Agent:** an AI tool that plans a task, uses tools, runs code and opens a PR with little human help. The paper lists four properties: memory, tool-use planning, self-reflection, and handing control back to a human when needed (Section 2.2).
- **Agentic-PR / Human-PR:** a PR opened by an agent / a PR not opened by an agent.
- **SE 1.0, 1.5, 2.0, 3.0 (Section 2.1, Table 1):** the authors' timeline. 1.0 = hand-written code. 1.5 = autocomplete. 2.0 = LLM assistant that writes functions on request. 3.0 = agents that do whole tasks while the developer sets goals and reviews.
- **AIDev-pop:** in THIS paper, the subset of AIDev limited to repositories with 500 or more stars. (Section 3.2 writes "≥ 500"; Section 4.1 and the captions write "over 500" and ">500". The paper is not consistent on whether exactly 500 is included.)
- **Acceptance rate:** share of PRs that were merged.
- **Turnaround time:** time from PR creation to closure (merge or reject).
- **Resolution time / during-work time:** how long the agent actively worked on a PR, measured only for GitHub Copilot.
- **Conventional Commits:** a set of change types (feat, fix, perf, refactor, style, docs, test, chore, build, ci, other). "perf" is a change meant to improve performance.
- **Cyclomatic complexity:** a count of independent paths through code (more branches = higher number). Used as a rough measure of how complicated code is.
- **Mann-Whitney U test:** a test that compares two groups without assuming a bell-shaped distribution. **Cliff's delta:** a measure of how large the difference between two groups is (negligible, small, medium, large).

## Method and setup
- **Collection (Section 3.1, Table 2):** GitHub REST API with search queries "adapted from PRarena". One rule per agent:

| Agent | Search query | Start date |
|---|---|---|
| OpenAI Codex | `is:pr head:codex/` | 2025-05-16 |
| Devin | `is:pr author:devin-ai-integration[bot]` | 2024-12-24 |
| GitHub Copilot | `is:pr head:copilot/` | 2025-01-01 |
| Cursor | `is:pr head:cursor/` | 2025-01-01 |
| Claude Code | `is:pr "Co-Authored-By: Claude"` | 2025-02-24 |

  So Codex, Copilot and Cursor are found by branch-name prefix, Devin by bot author name, Claude Code by a text line in the PR. For Copilot they also check that the user login is "copilot". Start dates are release dates where known; for Cursor and Copilot they use "a conservative start date of January 1, 2025".
- **Cutoff:** "The data collection cut-off date is June 22, 2025."
- **AIDev-pop:** repositories with 500+ stars "as of June 22, 2025": 7,122 PRs, 1,240 developers, 856 repositories.
- **Human baseline:** PRs "from the same popular repositories created in 2025, excluding those created by Autonomous Coding Agents". Section 3.2 says 6,628 PRs, 2,515 developers, 818 repositories ("we cannot sample enough PRs for some repositories"). Table 4 prints the human total as 6,618. The two numbers do not match and the paper does not explain why.
- **Task labels:** each PR's title and body is classified into 11 Conventional Commits categories "using GPT-4.1-mini" (Section 4.1). No manual check of the labels is reported.
- **Statistics:** Mann-Whitney U at α = 0.05, done separately for accepted and rejected PRs; Cliff's delta for effect size (Section 4.2).
- **Reviewers:** split into human or bot by username pattern (suffix `[bot]`) and GitHub's type field.
- **Complexity:** one project only (OpenHFT/Chronicle-Wire), cyclomatic complexity change per PR.
- "All downstream applications of the AIDev dataset presented in this paper (Section 4) are based on AIDev-pop." So every finding rests on 7,122 PRs, about 1.6% of the 456,535 (my calculation).
- No code is built or run. No performance is measured.

## Section-by-section notes

### 1. Introduction
- "OpenAI Codex alone has created over 400,000 PRs in open-source GitHub repositories in less than two months since its release in May 2025".
- Contributions: the dataset, three case studies, nine research directions.

### 2. Background
- Table 1 compares SE 1.5, 2.0 and 3.0 by unit of work, autonomy, context, benefit and risk. For SE 3.0 the "Main risk" is "Unintended repo or infra changes".
- 2.3: benchmarks (SWE-bench and others) show a gap to real-world software engineering.

### 3. The AIDev Dataset
- Table 3 gives per-agent sizes (see Tables below). Codex "dominates the overall volume, surpassing Devin, the second highest, by approximately 17 times".
- Figure 2 schema, 10 tables: pull_request (id, number, title, body, user_id, user, state, created_at, closed_at, merged_at, repo_id, repo_url, html_url), repository (id, url, full_name, language, forks, stars), user, pr_timeline, pr_reviews, pr_comments, pr_commits, pr_commit_details (includes filename, additions, deletions, changes, patch), related_issue, issue.
- "All tables are provided as CSV files".

### 4.1 Productivity (Findings 1 to 4, Research Directions 1 to 3)
- **Finding 1:** "over 55% of PRs submitted by Autonomous Coding Agents are either feature development (feat) or bug remediation (fix)". Copilot is 42.2% fix. Cursor and Claude Code are mostly feat (41.7% and 49.5%). The authors add that Cursor and Claude Code "are mainly used locally", so GitHub data shows them poorly.
- **Finding 2:** acceptance rates "consistently lag behind human performance, particularly for feature development (feat), bug fixes (fix), and performance optimization (perf) tasks". Text gives Codex 64%, Devin 49%, Copilot 35%, "ranging from 15 to 40 percentage points below human performance". Table 5 gives 65.3%, 48.9%, 38.2%. The Copilot numbers differ (35% in text, 38.2% in Table 5) and the paper does not explain. They contrast this with SWE-bench Verified, where top systems report "success rates exceeding 70%".
- **Finding 3:** documentation PRs are accepted more often for Codex (88.6%) and Claude Code (85.7%) than for humans (76.5%).
- **Finding 4:** Copilot "delivers half of its PRs within 12.8 minutes", 75% within 18.5 minutes, with "the 95th percentile exceeding one hour" (Figure 4). The long tail "suggests potential infrastructure issues such as cold starts, dependency resolution, or API throttling". This is a guess; no cause is measured.
- **RD 1:** benchmarks based on real integration, not only correctness. **RD 2:** study rejected PRs for failure modes. **RD 3:** "Latency-aware orchestration". They say GitHub Actions logs already record "environment setup, MCP server start-up, and inference steps" of Copilot, a "foundation for root-cause analysis".

### 4.2 Review dynamics (Findings 5 to 7, Research Directions 4 to 6)
- **Finding 5:** accepted Codex PRs close in a median 0.3 hours (18 minutes) against 3.9 hours for humans, medium effect size. Copilot is the opposite: accepted PRs take 17.2 hours, rejected ones 4.6 hours (human rejected: 27.6 hours). Rejected agent PRs are closed faster than human ones for all agents except Devin (93.9 hours). The authors warn: "this rapid pace may suggest superficial review rather than genuine confidence".
- **Finding 6:** most PRs get no explicit review: 75.3% of human PRs and 58.2% of agent PRs (Figure 6). Bots are involved in review of 20.1% of agent PRs against 10.0% of human PRs. Copilot PRs: 37.4% reviewed by human plus bot.
- **Finding 7:** review bots often come from the same company as the agent. Text: "PRs from GitHub Copilot are often reviewed by copilot-pull-request-reviewer[bot], responsible for 91.0% of bot reviews on GitHub Copilot PRs". **But Figure 7 (checked on the page image) puts the 91.0 in the row "copilot-swe-agent[bot]"; the row "copilot-pull-request-reviewer[bot]" shows 6.9 for Copilot PRs.** Text and figure disagree on which bot it is. Also: "cursor[bot] is responsible for reviewing 13.5% (53.8% of bot reviews) of PRs submitted through Cursor". Only `github-advanced-security[bot]` among the top 10 is rule-based.
- **RD 4:** lower the human cost of review. **RD 5:** study bot reviews. **RD 6:** triage systems for review effort.

### 4.3 Beyond agentic coding (Findings 8 to 10, Research Directions 7 to 9)
- **Finding 8:** one project (OpenHFT/Chronicle-Wire), one developer: "Between May 30 and June 3, 2025, a single developer submitted 164 Codex-assisted PRs, nearly matching the 176 human-authored PRs produced over the preceding three and a half years (from November 2021 to May 2025)". "only 9.1% of the Agentic-PRs introduced changes in cyclomatic complexity, compared to 23.3% for Human-PRs". (The abstract and introduction say "three days" and "three years"; the body says May 30 to June 3 and three and a half years.) The authors ask whether "this simplicity [might] be a liability in domains where complexity, such as in highly optimized code, is essential".
- **Finding 9:** Devin, Copilot and Cursor mark their authorship in commit metadata. "OpenAI Codex and Claude Code attribute their contributions to human developers." Claude Code adds a default "Co-Authored-By: Claude" line "(which can be disabled)"; "OpenAI Codex provides no attribution at all".
- **Finding 10:** languages differ by agent (Table 6). TypeScript is the top language overall. Codex leans to Python, Copilot to C#.
- **RD 7:** long-term quality, going "beyond static complexity metrics"; different project types "may each exhibit different tolerances for simplicity vs. optimization". **RD 8:** study the planning phase. **RD 9:** how language features (strong types) affect agents.

### 5. The Road Ahead
- 5.1: treat repositories as training environments with rewards such as "successful CI builds, merged pull requests, or positive reviewer feedback". 5.2: living leaderboards from live repository data. 5.3: new methods for orchestration, review and governance. This section is opinion, with no data.

### 6. Conclusion
- "Agentic-PRs are significantly less likely to be merged, particularly when they involve complex reasoning tasks such as feature development or bug fixing."
- There is no threats-to-validity section.

## Key results (with numbers) and what they mean
- 456,535 PRs, 47,303 developers, 61,453 repositories (Table 3a) -> the size of the June 2025 snapshot. 411,621 of them (about 90%, my calculation) are Codex.
- AIDev-pop: 7,122 PRs, 856 repositories (Table 3b) -> every finding is about this small popular-repository slice. Claude Code has only 101 PRs and Cursor 144, so their rows are weak evidence.
- Performance PRs (Table 4, %perf): Human 1.3, Codex 0.6, Devin 1.6, Copilot 1.4, Cursor 0.7, Claude Code 0.0 -> perf PRs are about 1% or less of everything. In absolute terms this is only a few dozen PRs in AIDev-pop (my rough calculation from the percentages: about 16 for Codex, 44 for Devin, 20 for Copilot, 1 for Cursor, 0 for Claude Code). The paper gives no perf counts itself.
- Acceptance (Table 5): Human 76.8%, Codex 65.3%, Claude Code 52.5%, Cursor 51.4%, Devin 48.9%, Copilot 38.2% -> merge is harder for agents. But "accepted" only means a maintainer pressed merge.
- Median turnaround of accepted PRs: Human 3.9 h, Codex 0.3 h, Devin 2.2 h, Cursor 2.4 h, Claude Code 6.9 h, Copilot 17.2 h -> some agent PRs are merged within minutes. The Cursor and Claude Code differences are not statistically significant.
- No review at all: 58.2% of agent PRs, 75.3% of human PRs (Figure 6) -> for most merged PRs nobody left a visible review. A merge is therefore weak proof that the change was checked.
- Copilot work time: median 12.8 minutes, 75% under 18.5 minutes (Finding 4).
- Complexity: 9.1% of Codex PRs changed cyclomatic complexity against 23.3% of human PRs, in one project -> an anecdote from one developer, not a general result.

## Tables and figures
- **Figure 1 (p. 2):** cumulative PR count per agent, (a) full AIDev, (b) AIDev-pop. Read: Codex jumps from zero to about 400,000 after mid-May 2025.
- **Table 1 (p. 4):** SE 1.5 / 2.0 / 3.0 comparison.
- **Table 2 (p. 6):** search query and start date per agent (copied above).
- **Table 3 (p. 7):**

| Agent | AIDev #PR | #Dev | #Repo | AIDev-pop #PR | #Dev | #Repo |
|---|---|---|---|---|---|---|
| OpenAI Codex | 411,621 | 41,619 | 53,702 | 2,686 | 522 | 467 |
| Devin | 24,893 | 2,897 | 3,857 | 2,729 | 300 | 130 |
| GitHub Copilot | 16,531 | 1,916 | 3,097 | 1,462 | 309 | 215 |
| Cursor | 1,981 | 753 | 828 | 144 | 66 | 52 |
| Claude Code | 1,509 | 585 | 645 | 101 | 68 | 61 |
| Total | 456,535 | 47,303 | 61,453 | 7,122 | 1,240 | 856 |

- **Figure 2 (p. 7):** database schema (10 tables).
- **Table 4 (p. 9):** percent of PRs per task type.

| | feat | fix | perf | refac | sty | doc | test | chore | build | ci | other | #total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Human | 29.4 | 26.9 | 1.3 | 5.6 | 0.9 | 7.8 | 2.8 | 12.8 | 9.3 | 1.5 | 1.7 | 6,618 |
| OpenAI Codex | 28.4 | 27.2 | 0.6 | 7.1 | 0.8 | 21.3 | 9.2 | 2.6 | 1.6 | 1.1 | 0.1 | 2,686 |
| Devin | 35.8 | 27.4 | 1.6 | 10.4 | 0.4 | 12.0 | 3.0 | 6.2 | 1.9 | 1.0 | 0.1 | 2,729 |
| GitHub Copilot | 29.7 | 42.2 | 1.4 | 5.2 | 0.3 | 9.8 | 4.4 | 1.8 | 3.5 | 1.4 | 0.2 | 1,462 |
| Cursor | 41.7 | 34.7 | 0.7 | 2.8 | 1.4 | 6.9 | 2.8 | 4.2 | 3.5 | 0.0 | 1.4 | 144 |
| Claude Code | 49.5 | 18.8 | 0.0 | 8.9 | 0.0 | 13.9 | 3.0 | 1.0 | 3.0 | 2.0 | 0.0 | 101 |

- **Figure 3 (p. 10):** radar charts of acceptance rate per task type, one per agent against the human line. The numbers are not printed on the chart. Only the documentation values are given in the text (88.6%, 85.7%, 76.5%). The perf acceptance rates cannot be read exactly from the figure (unclear in the PDF).
- **Figure 4 (p. 11):** box plot of Copilot resolution time, 0 to 60 minutes.
- **Table 5 (p. 12):** turnaround time. MT = median turnaround in hours.

| | %Accepted | MT (h) | Sig. | Effect size | %Rejected | MT (h) | Sig. | Effect size |
|---|---|---|---|---|---|---|---|---|
| Human | 76.8 | 3.9 | NA | NA | 16.1 | 27.6 | NA | NA |
| OpenAI Codex | 65.3 | 0.3 | yes | medium (+) | 21.3 | 2.4 | yes | small (+) |
| Devin | 48.9 | 2.2 | yes | negligible (+) | 48.4 | 93.9 | yes | negligible (−) |
| GitHub Copilot | 38.2 | 17.2 | yes | small (−) | 32.1 | 4.6 | yes | small (+) |
| Cursor | 51.4 | 2.4 | no | NA | 21.5 | 1.1 | yes | small (+) |
| Claude Code | 52.5 | 6.9 | no | NA | 32.7 | 1.8 | yes | small (+) |

  Accepted plus rejected is below 100% in each row. The rest are presumably still open; the paper does not say. The paper does not define the (+) and (−) signs; from the numbers, (+) goes with "faster than human".
- **Figure 5 (p. 13):** box plots of turnaround times, accepted and rejected, per agent.
- **Figure 6 (p. 14), share of PRs by reviewer type (only human / human + bot / only bot / no reviews):** Human 14.7 / 3.6 / 6.4 / 75.3. All agents 21.8 / 11.0 / 9.1 / 58.2. Devin 33.2 / 2.5 / 6.1 / 58.3. Cursor 32.6 / 6.9 / 18.1 / 42.4. Claude Code 23.8 / 9.9 / 12.9 / 53.5. Copilot 15.7 / 37.4 / 2.9 / 44.0. Codex 12.8 / 5.4 / 15.0 / 66.8.
- **Figure 7 (p. 15):** heat map, top-10 review bots by share of bot reviews on PRs from Human, Codex, Claude Code, Cursor, Devin, Copilot (column order checked on the page image). Examples: coderabbitai[bot] 40.2 on human PRs; cursor[bot] 53.8 on Cursor PRs and 31.3 on Devin PRs; copilot-swe-agent[bot] 91.0 on Copilot PRs.
- **Figure 8 (p. 17):** distribution of non-zero cyclomatic complexity change, Codex against human, one project.
- **Table 6 (p. 18):** top-10 repository languages in AIDev-pop. All agents: TypeScript 226 (26.4%), Python 172 (20.1%), C# 78 (9.1%), Go 72 (8.4%), Rust 49 (5.7%), C++ 42 (4.9%), JavaScript 40 (4.7%), Java 25 (2.9%), C 20 (2.3%), PHP 18 (2.1%). Counts are repositories (they sum toward 856), not PRs.

## Ideas we can use
- The detection rules in Table 2 tell us what "agent-authored" means in AIDev. For Claude Code the rule is only a "Co-Authored-By: Claude" line, so a human may have written or edited the PR text. This matters for us because we treat the PR text as the agent's claim.
- Table 4 gives a base rate: perf PRs are around 1% of agent PRs in popular repositories. This explains why our candidate set is small next to the dataset.
- Finding 6 (most PRs merged without any visible review) and the authors' own worry about "superficial review" support our point that a merge does not prove a performance claim.
- Table 6 tells us which toolchains a build agent must handle first: TypeScript, Python, C#, Go, Rust.

## Weaknesses and things glossed over
- No threats-to-validity section at all.
- Detection by branch prefix (`codex/`, `copilot/`, `cursor/`) can catch human branches with the same prefix. No precision or recall check is reported. Only Copilot gets an extra login check.
- The Claude Code rule misses PRs where the co-author line was disabled and catches PRs with heavy human editing.
- Task labels come from GPT-4.1-mini on title and body only, single label per PR, with no manual validation. The perf percentages depend fully on this.
- The human baseline is "stratified" from the same repositories in 2025, but the sampling steps are not given. 6,628 (text) against 6,618 (Table 4). It is not said whether undeclared AI help was excluded from "human" PRs (it cannot be).
- Acceptance is used as a sign of quality. Nothing is built, tested or run. The paper itself admits fast merges may be shallow review.
- Comparing merge rates (38% to 65%) with SWE-bench success (over 70%) mixes two different things: one is a maintainer's choice, the other is passing tests.
- Open PRs are counted in the denominator but not discussed. Agents released weeks before the cutoff (Codex: 2025-05-16) have many PRs that had little time to be merged.
- Text and tables disagree in places: Copilot acceptance 35% vs 38.2%; the bot behind the 91.0% in Finding 7 vs Figure 7; "three days / three years" vs "May 30 to June 3 / three and a half years"; "≥ 500" vs ">500" stars.
- Finding 4's human comparison uses issue resolution times in Apache Jira projects from another paper. This compares agent work time on a PR with human time to close an issue, which are not the same thing.
- Finding 8 is one developer in one project.
- Small samples for Cursor (144) and Claude Code (101).
- The writing is promotional in places ("The revolution is already underway").

## Open questions and future work (theirs, and ours)
- Theirs: the nine research directions (integration benchmarks, failure modes in rejected PRs, latency-aware orchestration, review cost, bot review, review triage, long-term quality, planning, language features).
- Ours: RD 7 asks to go "beyond static complexity metrics" and names optimization as a place where simple code may not be enough. They do not measure run-time behaviour. We do.
- Ours: are perf PRs accepted with as little review as other PRs? The dataset could answer this, and it would strengthen our motivation.

## Link to our paper
- This key is in `paper/refs.bib` but I found no `\cite{li2025teammates}` in `paper/main.tex` or `paper/sections/` yet.
- Best use: (1) motivation, agent PRs are merged with little review; (2) how agent PRs are identified in AIDev (Table 2), with the caveat that this is the June 2025 collection and the paper for later versions (li2026aidev) does not restate the rules; (3) perf PRs are a small share.
- Our approach section calls the more-than-100-stars subset "AIDev-pop". In this paper "AIDev-pop" means 500+ stars. A reviewer who knows this paper (its authors are on the PC) may notice. Check what the v5 dataset card calls the subset.

## Link to the thesis (tracing, kernel analysis)
- Finding 4 and RD 3 are about latency: a heavy tail in Copilot's work time, and a call for "root-cause analysis" from GitHub Actions logs covering "environment setup, MCP server start-up, and inference steps". This is a performance-analysis problem on agent runs. Kernel tracing of the agent host (scheduling waits, I/O, network) would show where the tail comes from, which log timestamps alone cannot.
- The authors' guessed causes ("cold starts, dependency resolution, or API throttling") are not measured. A trace-based study could test them.
- The paper never measures the performance of the code that agents write.

## Quotes for inline citation
- "we introduce AIDev, a new large-scale dataset comprised of 456,535 Agentic PRs created by five leading Autonomous Coding Agents: OpenAI Codex, GitHub Copilot, Devin, Cursor, and Claude Code on GitHub" (Section 1, p. 2)
- "The data collection cut-off date is June 22, 2025." (Section 3.1, p. 6)
- "we filter the AIDev dataset by retaining only repositories with ≥ 500 GitHub stars, resulting in a subset named AIDev-pop" (Section 3.2, p. 6)
- "PR acceptance rates consistently lag behind human performance, particularly for feature development (feat), bug fixes (fix), and performance optimization (perf) tasks" (Finding 2, p. 9)
- "Given the scale of contributions and the lack of strong accountability mechanisms, this rapid pace may suggest superficial review rather than genuine confidence." (Finding 5, p. 13)
- "both Human-PRs and Agentic-PRs receive no explicit review in the majority of cases (75.3% and 58.2%, respectively)" (Finding 6, p. 13)
- "OpenAI Codex and Claude Code attribute their contributions to human developers." (Finding 9, p. 16)
- "Future work should go beyond static complexity metrics and examine how AI-authored code performs over time" (Research Direction 7, p. 17)

## Suggested citation sentences
- In the first AIDev study, performance changes were at most 1.6% of each agent's PRs in popular repositories \cite{li2025teammates}.
- Most agent PRs in popular repositories (58.2%) received no explicit review \cite{li2025teammates}, so a merge alone says little about whether a performance claim was checked.
- Accepted OpenAI Codex PRs closed in a median of 0.3 hours, and the authors note that such speed "may suggest superficial review" \cite{li2025teammates}.
- AIDev identifies agent PRs by branch prefix, bot account or a co-author line \cite{li2025teammates}; for some agents the PR text may therefore include human edits.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is the origin of our dataset and the only one of the two AIDev papers that explains how agent PRs are detected and that reports a share of perf PRs.
  - It judges agent PRs by merge rate, review time and code complexity. It never builds or runs the code. We measure what the change does at the kernel and hardware level.
  - It supports our motivation: most PRs get no visible review, and the authors themselves doubt the depth of fast reviews.
  - Points that weaken us: (a) perf PRs are a very small share (0.0% to 1.6%), so a reader can ask how much the problem matters in volume; (b) Claude Code and Codex PRs are attributed to human developers and found by a text line or branch name, so "the agent claimed X" may partly be "the developer claimed X"; (c) the numbers here are from a snapshot much older and smaller than v5, and from a 500-star subset, not our 100-star subset.
- **Safe to cite for:**
  - How agent PRs are found: Section 3.1, "bot author names (e.g., 'devin-ai-integration[bot]'), branch prefixes (e.g., 'head:copilot/'), and explicit messages in the PR body (e.g., 'Co-Authored-By: Claude')".
  - Perf PRs are rare among agent PRs in popular repositories: Table 4, %perf between 0.0 (Claude Code) and 1.6 (Devin); human 1.3. State that labels are from GPT-4.1-mini.
  - Agent PRs are merged less often than human PRs in AIDev-pop: Table 5, 76.8% human against 38.2% to 65.3% for agents; Section 6: "Agentic-PRs are significantly less likely to be merged".
  - Most PRs get no explicit review: Finding 6, "no explicit review in the majority of cases (75.3% and 58.2%, respectively)".
  - Fast merges may mean shallow review (authors' own caution): Finding 5, "may suggest superficial review rather than genuine confidence".
  - A call to look past static metrics at how agent code behaves: RD 7, "go beyond static complexity metrics".
- **Do not cite for:**
  - The size of the dataset we use. 456,535 is the June 2025 snapshot; li2026aidev says 932,791; v5 is larger again.
  - A 100-star subset. Here AIDev-pop is 500+ stars with 7,122 PRs.
  - Any claim that agent performance PRs do not deliver a speed-up, or that their explanations are wrong. The paper measures no performance.
  - Acceptance rate of perf PRs as a number. Figure 3 shows it only as an unlabeled radar chart.
  - "Agents write simpler code" as a general fact. Finding 8 is one developer in one project.
  - Causes of Copilot's latency tail. They are guesses.
  - The 19% slowdown of experienced developers. That is the METR study (their ref [2]), only mentioned here.
  - The exact bot behind "91.0% of bot reviews on GitHub Copilot PRs". Text and Figure 7 disagree.
