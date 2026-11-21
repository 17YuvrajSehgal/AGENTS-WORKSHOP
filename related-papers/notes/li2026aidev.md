# AIDev: Studying AI Coding Agents on GitHub
- **Authors:** Hao Li, Haoxiang Zhang, Ahmed E. Hassan (all Queen's University, Kingston, ON, Canada)
- **Venue / year / status:** Page header says "MSR '26, April 13-14, 2026, Rio de Janeiro, Brazil" (Mining Software Repositories conference). The copy we have is the arXiv preprint arXiv:2602.09185v1 [cs.SE], dated 9 Feb 2026. The ACM DOI and ISBN on the first page are still placeholders ("10.1145/nnnnnnn.nnnnnnn"). The paper does not say which MSR track it belongs to. 5 pages, of which about 2 are references.
- **PDF:** `related-papers/li2026aidev_2602.09185.pdf`
- **Cite key:** li2026aidev
- **BibTeX-style reference:** Hao Li, Haoxiang Zhang, and Ahmed E. Hassan. 2026. AIDev: Studying AI Coding Agents on GitHub. In MSR '26, April 13-14, 2026, Rio de Janeiro, Brazil. arXiv:2602.09185.

## In short
This is a short dataset paper. It describes AIDev, a dataset of pull requests (PRs) that AI coding agents opened on GitHub. In the version this paper describes, AIDev has 932,791 agent PRs from five agents (OpenAI Codex, Devin, GitHub Copilot, Cursor, Claude Code), in 116,211 repositories, involving 72,189 developers, with a cutoff of August 1, 2025. A smaller subset of 33,596 PRs from 2,807 repositories with more than 100 GitHub stars has extra tables: comments, reviews, commits, file diffs, linked issues, event timelines and an automatic label for the PR's purpose. The paper has no analysis and no results. It lists the tables, the download links, and a set of research questions other people could study.

**Version warning (read this first).** The paper never gives a version number for the dataset. Every number in this note is the paper's number, for the snapshot with cutoff August 1, 2025. Our work uses AIDev v5, which is later and larger. Our numbers (for example 7,685,281 PRs, 361,296 subset PRs, six agents) are NOT in this paper and must not be presented as if this paper reports them.

## Problem and motivation
- Coding agents now open "thousands of pull requests (PRs) daily" (Section 1), but, in the authors' words, "the research community lacks a comprehensive dataset capturing how these agents are used in real-world projects" (Abstract).
- Most earlier evidence on coding agents comes "from controlled studies, benchmarks, or small-scale deployments" (Section 5.1). The dataset is meant to show agents "in the wild", on real repositories.

## Background / key terms (explain each term simply)
- **Pull request (PR):** a proposed code change on GitHub. Someone reviews it and then merges it (accepts) or closes it (rejects).
- **Coding agent:** an AI tool that does a whole task alone (reads code, edits, runs tools, opens a PR), not only line-by-line suggestions.
- **Agentic-PR:** the paper's name for a PR authored by a coding agent (footnote 1: "We refer to PRs authored by Coding Agents as Agentic-PRs").
- **AI Teammate / SE 3.0:** the authors' words for agents that take part in the normal team workflow, and for the new period of software engineering where this is common. Both come from their earlier vision paper (Hassan et al. 2024, their ref [13]).
- **Curated subset:** the part of AIDev limited to repositories "with more than 100 GitHub stars". Only this part has the detailed tables. **This paper never uses the name "AIDev-pop".** It only says "curated subset" or "enriched subset".
- **Conventional Commits:** a naming rule for commit types (feat, fix, docs and so on). AIDev uses these categories to label what each PR is for.
- **Stars:** GitHub's "like" count for a repository, used here as a sign that a project is popular.

## Method and setup
The paper gives almost no method. This is the main thing to know before citing it.
- **How agent PRs were found:** the paper does not say. There are no search queries, no detection rules and no start dates in this paper. (These are in the earlier arXiv paper, li2025teammates, Table 2, for an older and smaller snapshot.)
- **Cutoff:** "dataset cutoff: August 1, 2025" (Section 1). No start date is given.
- **Subset rule:** repositories "with more than 100 GitHub stars" (Section 1 and Table 1). The abstract says "over 100 stars". The paper does not say on which date the stars were counted.
- **Purpose labels:** "automated annotations of PR purpose (e.g., bug fix, feature, documentation), following the Conventional Commits categories" (Section 2). Table 1 calls it "GPT-based". The paper does not name the model, the prompt, or any check of label accuracy.
- **Human PRs:** the paper mentions "Human-PRs" only inside one research question (Section 4.2). Table 1 lists no table of human PRs.
- **Schema:** "The complete relational schema is available in our dataset on Hugging Face and Zenodo" (Section 2). It is not printed in the paper.
- No statistics, no repetitions, no experiments. Nothing is measured.

## Section-by-section notes

### Abstract
- 932,791 Agentic-PRs, five agents, 116,211 repositories, 72,189 developers.
- Curated subset: 33,596 Agentic-PRs from 2,807 repositories "with over 100 stars", with "comments, reviews, commits, and related issues".

### 1. High-Level Overview
- Agents "now contribute thousands of pull requests (PRs) daily".
- The five agents, in the paper's order: "OpenAI Codex, Devin, GitHub Copilot, Cursor, and Claude Code".
- "Each PR is linked to its corresponding repository and developer, along with additional metadata."
- The subset "provides review comments, commit-level diffs, event timelines, and related issues".
- Figure 1 is one example: GitHub Copilot is assigned an issue, opens a PR, a human reviewer comments, and the agent answers with a follow-up commit. Footnote 2: "Not all Coding Agents currently support addressing review comments."

### 2. Internal Structure
- Three levels of metadata: PR, repository, developer.
- Extra tables only for the more-than-100-stars subset: inline review comments, commit-level diffs, linked issues, full PR timelines.
- Automatic PR purpose labels (see Method above).

### 3. How to Access (Links)
- Hugging Face: https://huggingface.co/datasets/hao-li/AIDev (has a "Data Studio" page for SQL in the browser).
- Zenodo: https://doi.org/10.5281/zenodo.16899501
- GitHub: https://github.com/SAILResearch/AI_Teammates_in_SE3 (example Jupyter notebooks with Google Colab links).
- The paper does not state a licence for the dataset. It does not say which dataset version each link points to.

### 4. Potential Research Questions
These are suggestions, not findings. Five groups:
- **4.1 Adoption and Practices:** who uses agents, which practices (PR size, task type, commit granularity) go with quality.
- **4.2 Code Patch Characteristics:** item (1) asks "How do Agentic-PRs change code (e.g., additions, deletions, files touched)? How consistent are their descriptions with the actual code changes?" This second sentence is very close to our question (does the PR do what its text says).
- **4.3 Testing Behavior:** how often agents add tests, and whether developers add them later.
- **4.4 Review Dynamics:** what reviewers look at, whether agents answer review comments.
- **4.5 Failure Patterns and Risks:** failure patterns, predicting rejection, security, and item (4): "Which Agentic-PRs reach production and persist (i.e., are not reverted or hotfixed)?"
- Performance, speed or efficiency of the changed code is not named in any of the questions.

### 5. Related Work
- **5.1 AI Coding Agents:** SWE-agent, OpenHands, AutoCodeRover, SWE-bench. Prior evidence is mostly from "controlled studies, benchmarks, or small-scale deployments". Position papers ask for "verifiable analyses, richer testing, and auditable traces" (their ref [4]).
- **5.2 Automated Contributions in Open Source Software:** older rule-based bots (dependency updates). Bot PRs "tend to have lower acceptance rates". PRs with ChatGPT involvement "are substantially slower to close and entail heavier review" (their refs [6, 7]).
- **5.3 Empirical Studies of AI Adoption and Developer Productivity:** surveys, lab studies and telemetry. One number from another paper: a regional ban on LLM access gave "a 6.4% productivity reduction during the ban" (their ref [2]). This is not an AIDev result.

### What is missing
- No threats-to-validity section, no limitations, no conclusion, no future work beyond the question list.

## Key results (with numbers) and what they mean
There are no experimental results. The only numbers are sizes (all for the paper's snapshot, cutoff August 1, 2025):
- 932,791 Agentic-PRs, 116,211 repositories, 72,189 developers, five agents (Abstract, Section 1, Table 1) -> the full dataset has metadata only (PR text, state, timestamps, repository, user). It has no diffs.
- 33,596 PRs, 2,807 repositories, 1,796 users in the more-than-100-stars subset (Table 1) -> this is about 3.6% of all PRs (my calculation: 33,596 / 932,791). Any work that needs code (like ours) can only use this small part.
- 711,923 rows of file-level diffs and 88,576 commits (Table 1) -> the subset holds the patches needed to see what a PR changed.
- 4,923 PR-to-issue links and 4,614 issues (Table 1) -> only a minority of the 33,596 subset PRs can have a linked issue.
- The paper gives no per-agent counts, no language breakdown, no merge rates and no share of performance PRs.

## Tables and figures
- **Figure 1 (p. 2):** screenshot of one GitHub Copilot PR ("Fix inconsistent scrolling behavior in notebook outline entries"). Labels show the PR title, PR body, related issue, a reviewer's inline comment ("this test doesn't actually do anything, just remove this test") and the agent's reply after removing the test. Read: it shows what parts of a PR the dataset captures.
- **Table 1 (p. 2), "Overview of the AIDev Dataset"** (checked on the page image):

| Group | Table | # Records | Content (as printed) |
|---|---|---|---|
| Core metadata (all) | all_pull_request | 932,791 | PR metadata (title, body, agent, state, timestamps, repository, user) |
| Core metadata (all) | all_repository | 116,211 | Repository metadata (name, license, language, URL, stars, forks) |
| Core metadata (all) | all_user | 72,189 | Developer/user metadata (login, followers, creation date) |
| Core metadata (subset) | pull_request | 33,596 | Same fields as all_pull_request, restricted to curated subset |
| Core metadata (subset) | repository | 2,807 | Same fields as all_repository, restricted to curated subset |
| Core metadata (subset) | user | 1,796 | Same fields as all_user, restricted to curated subset |
| Comments & Reviews | pr_comments | 39,122 | Discussion-style comments on PRs (author, body, timestamp) |
| Comments & Reviews | pr_reviews | 28,875 | Review verdicts (e.g., approve or request changes) with metadata (author, body, timestamp) |
| Comments & Reviews | pr_review_comments | 19,450 | Inline code review comments with file-level context (path, diff hunk, timestamp) |
| Commits & Diffs | pr_commits | 88,576 | Commits linked to PRs with metadata (SHA, author, message) |
| Commits & Diffs | pr_commit_details | 711,923 | File-level commit diffs including additions, deletions, and patches |
| Issues & Events | related_issue | 4,923 | Mapping between PRs and related issues |
| Issues & Events | issue | 4,614 | GitHub issues related to PRs (title, body, state, user, timestamps) |
| Issues & Events | pr_timeline | 325,500 | Full PR event history (e.g., committed, closed, merged, labeled, reviewed) |
| Annotation | pr_task_type | 33,596 | Automated classification of PR purpose (Conventional Commits categories, GPT-based) |

  The table has a divider line: "The following is a subset of PRs from repositories with more than 100 GitHub stars". Everything below that line exists only for the subset. Read: 15 tables in total, 3 for the full dataset and 12 for the subset.

## Ideas we can use
- The subset tables `pr_commits` and `pr_commit_details` (SHA and patches) are what lets us find the code before and after a PR and rebuild both.
- `pull_request` title and body hold the claim text. `pr_task_type` is a ready-made first filter, but it is an unvalidated GPT label, so our own keyword filter and classifier are the safer route (as we already do).
- `pr_timeline` and `pr_reviews` could tell us whether a reviewer asked for a benchmark before merge.
- Research question 4.2(1) ("How consistent are their descriptions with the actual code changes?") is a direct hook: the dataset authors themselves ask whether PR text matches the change. We answer a harder form of it, with measurement.

## Weaknesses and things glossed over
- No description of how agent PRs were identified. A reader cannot judge false positives (human PRs counted as agent PRs) or misses from this paper alone.
- No version number, no changelog, and no start date. The Zenodo DOI is given, but the paper does not say which version it resolves to.
- "More than 100 stars" has no reference date.
- The purpose labels are "GPT-based" with no model name and no accuracy check.
- No per-agent breakdown. The earlier snapshot (li2025teammates, Table 3a) was dominated by OpenAI Codex. This paper does not say whether that is still true.
- No threats section. No talk of bias from public-only repositories, from agents that leave no trace, or from deleted PRs.
- Detailed tables cover only about 3.6% of the PRs (my calculation), so most of the dataset cannot support code-level work.
- "72,189 developers" is the row count of `all_user`. The paper does not say whether bot accounts are included in that count.

## Open questions and future work (theirs, and ours)
- Theirs: the list in Section 4 (adoption, patch characteristics, testing, review, failures and risks).
- Ours: none of their questions asks whether an agent's change really makes the code faster, or whether the stated reason is what happened in the machine. That gap is our paper.
- Ours: does the more-than-100-stars filter bias performance PRs toward projects that are easier or harder to build and measure?

## Link to our paper
- **Introduction (`paper/sections/01-introduction.tex`, line 5):** the sentence says AIDev "records \nAllPRs agent-authored PRs from six agents~\cite{li2026aidev}", with \nAllPRs = 7,685,281. **This does not match the cited paper.** The paper says 932,791 PRs and five agents. If v5 really has 7,685,281 PRs and six agents, the sentence must say the numbers are from version 5 of the dataset, not from the paper (for example "version 5 of AIDev [cite] records ..."), and the sixth agent's name should be checked in the pinned data, not in this paper.
- **Approach (`paper/sections/02-approach.tex`, line 18):** "its \emph{AIDev-pop} subset of \nPop agent PRs from \nPopRepos repositories with more than 100 stars". Two points. (1) The paper's subset is 33,596 PRs from 2,807 repositories; our 361,296 and 25,402 are v5 numbers. (2) The paper does not use the name "AIDev-pop" at all. In the earlier arXiv paper (li2025teammates) "AIDev-pop" means repositories with more than 500 stars (7,122 PRs). I did not check what the v5 dataset card calls the subset. Please confirm the name on the dataset card before using it. The "more than 100 stars" threshold itself does match this paper.

## Link to the thesis (tracing, kernel analysis)
- The paper has nothing on tracing, kernels or performance measurement.
- It is still useful as a source of real-world code changes with a stated intent. Performance PRs from it are natural test cases for trace-based checks (syscall counts, page faults, futex waits).
- Its related work says trust in agents needs "verifiable analyses, richer testing, and auditable traces of thought, action, and result trajectories" (Section 5.1, citing their ref [4]). "Traces" there means agent action logs, not kernel traces. Do not mix the two meanings.

## Quotes for inline citation
- "the research community lacks a comprehensive dataset capturing how these agents are used in real-world projects" (Abstract, p. 1)
- "AIDev comprises 932,791 Agentic-PRs authored by five agents: OpenAI Codex, Devin, GitHub Copilot, Cursor, and Claude Code, across 116,211 repositories involving 72,189 developers (dataset cutoff: August 1, 2025)." (Section 1, p. 1)
- "we curated a subset of 33,596 Agentic-PRs from 2,807 repositories with more than 100 GitHub stars. This enriched subset provides review comments, commit-level diffs, event timelines, and related issues." (Section 1, p. 1)
- "the dataset also includes automated annotations of PR purpose (e.g., bug fix, feature, documentation), following the Conventional Commits categories" (Section 2, p. 1)
- "How consistent are their descriptions with the actual code changes?" (Section 4.2, p. 2)
- "much of the existing evidence derives from controlled studies, benchmarks, or small-scale deployments" (Section 5.1, p. 3)

## Suggested citation sentences
- We take our pull requests from AIDev \cite{li2026aidev}, a public dataset of PRs opened by coding agents on GitHub. (Safe for any version.)
- We use version 5 of AIDev, which is later and larger than the snapshot described in the dataset paper \cite{li2026aidev} (932,791 PRs from five agents, cutoff August 1, 2025).
- Commit-level diffs are released only for repositories with more than 100 GitHub stars \cite{li2026aidev}, so we restrict our study to that subset.
- The dataset authors list the match between a PR's description and its code change as an open question \cite{li2026aidev}; we test it for performance claims by measurement.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is our data source. We take performance PRs, their text (the claim) and their commits (to rebuild before and after) from the more-than-100-stars subset.
  - The paper only describes data. It runs no code, measures no performance, and has no result on whether any PR does what it says. All of that is ours.
  - Its Section 4.2(1) asks how consistent PR descriptions are with the code change. This supports our motivation, and the request comes from the dataset authors themselves.
  - Points that weaken us, said plainly: (a) the paper does not explain how a PR was decided to be agent-authored, so we cannot show from this paper that the claim text was written by the agent and not by a human; (b) the paper describes an older snapshot than the v5 we use, so the paper cannot back any v5 number; (c) only the popular-repository subset has diffs, so our results say nothing about the large majority of agent PRs in small repositories.
- **Safe to cite for:**
  - AIDev is a dataset of agent-authored PRs from real GitHub repositories. Abstract: "a large-scale dataset focused on agent-authored pull requests (Agentic-PRs) in real-world GitHub repositories".
  - The size of the paper's snapshot, if stated as the paper's snapshot: "932,791 Agentic-PRs produced by five agents: OpenAI Codex, Devin, GitHub Copilot, Cursor, and Claude Code" (Abstract), cutoff "August 1, 2025" (Section 1).
  - The detailed tables exist only for repositories with more than 100 stars. Table 1: "The following is a subset of PRs from repositories with more than 100 GitHub stars"; Section 2: "enriched artifacts such as inline review comments, commit-level diffs, linked issues, and full PR timelines".
  - The dataset has file-level patches. Table 1, pr_commit_details: "File-level commit diffs including additions, deletions, and patches".
  - Agents open PRs at scale. Section 1: "They now contribute thousands of pull requests (PRs) daily".
  - Whether PR descriptions match the code change is an open question. Section 4.2(1): "How consistent are their descriptions with the actual code changes?"
- **Do not cite for:**
  - Any v5 number: 7,685,281 PRs, 361,296 subset PRs, 25,402 subset repositories, or "six agents". The paper says 932,791, 33,596, 2,807 and five.
  - The name "AIDev-pop". It is not in this paper.
  - How agent PRs are detected (branch prefixes, bot names, co-author lines). That is in li2025teammates, for an older snapshot.
  - Merge or acceptance rates, review times, or the share of performance ("perf") PRs. None are in this paper. (li2025teammates has them for 7,122 PRs.)
  - Any claim that agent PRs are wrong, unverified, or misleading about performance. The paper makes no quality claim at all.
  - The accuracy of the `pr_task_type` labels. The paper reports no validation.
  - The 6.4% productivity number. It belongs to another paper (their ref [2]).
