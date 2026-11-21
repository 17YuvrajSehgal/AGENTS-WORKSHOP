# What Do AI Agents Actually Change? An Empirical Taxonomy of Mutation Patterns in Performance-Improving Pull Requests
- **Authors:** Illia Dovhoshliubnyi, Nima Soroush, Ashkan Sami (Edinburgh Napier University, UK), Alexander Brownlee (University of Stirling, UK)
- **Venue / year / status:** arXiv:2607.05666v1 [cs.SE], 6 Jul 2026. 6 pages in Springer LNCS style. The paper does not name a venue. The replication package is called `ssbse-challenge-2026`, which suggests the SSBSE 2026 Challenge track, but the paper does not say this and does not say whether it is peer-reviewed or accepted. Check before writing a venue in the bibliography.
- **PDF:** related-papers/dovhoshliubnyi2026mutation_2607.05666.pdf
- **Cite key:** dovhoshliubnyi2026mutation
- **BibTeX-style reference:** Illia Dovhoshliubnyi, Nima Soroush, Ashkan Sami, and Alexander Brownlee. 2026. What Do AI Agents Actually Change? An Empirical Taxonomy of Mutation Patterns in Performance-Improving Pull Requests. arXiv:2607.05666v1.

## In short
The authors take the performance-labelled pull requests (PRs) of AIDev-pop and look at what the code edits look like at the syntax level. They split each PR diff into hunks (blocks of changed lines), keep 1,254 "performance-relevant" hunks from 216 PRs, and label each hunk with one or more of 18 syntactic "mutation" categories from an earlier taxonomy (Even-Mendoza et al. 2025). Two LLMs do the labelling and only the labels both agree on are kept. Three categories lead: name modification 37.0%, object creation 26.4%, type change 22.7%. Each agent and each performance strategy uses a different subset of categories. The paper never runs any code and never measures performance. It describes the shape of the edits, not whether they work.

## Problem and motivation
- Agents are black boxes. We cannot see how they decide, but we can see what they change.
- The audience is search-based software engineering (SBSE). Genetic improvement (GI) is a technique that searches for a better program by applying small edits ("mutation operators") again and again. GI needs a list of operators that match how code is really changed.
- Existing mutation taxonomies come from human patches or from LLM patches inside a GI pipeline. The authors want a map of how agents really edit code when they optimise performance, so that a GI tool can pick a smaller set of operators.
- They stress that the map is "descriptive of agent behaviour ... not prescriptive of agent behaviour as an optimum" (Sec. 1, p. 2).

## Background / key terms (explain each term simply)
- **AIDev-pop:** the subset of the AIDev dataset of agent-written PRs that the paper uses. The paper gives 33,596 PRs from five agents (Devin, GitHub Copilot, Cursor, OpenAI Codex, Claude Code).
- **Performance label:** a tag saying the PR is about performance. The paper says 324 of 33,596 PRs carry it (<1%) and cites Opu et al. [5] and Peng et al. [6] for this.
- **Hunk:** one contiguous block of changed lines in a diff. One PR has many hunks.
- **Mutation (here):** a small syntactic change to code, for example renaming a variable or changing a type. It is not "mutation testing" in the usual sense, even though the keywords list it.
- **Genetic improvement (GI):** automatic search over program edits to improve a property such as speed.
- **Mutation operator:** one kind of edit the search is allowed to make.
- **LLM-as-a-judge:** using an LLM to assign labels instead of a human.
- **Dual-LLM intersection:** two LLMs label the same hunk. Only the categories both chose are kept.
- **Multi-label:** one hunk can get several categories, so the percentages add up to more than 100%.
- **Apriori mining / lift:** a way to find labels that appear together. Lift above 1 means two labels occur together more often than chance.
- **Sentinel categories:** two "nothing really happened" categories in the taxonomy (the paper says "plus two sentinel categories" without naming them; `no_change` and `extra_brackets` both have count 0 in Table 1).

## Method and setup
- **Data funnel (Sec. 2.1):** 324 performance-labelled PRs -> 280 with a retrievable diff -> 269 with at least one source-code hunk (tests, configuration, documentation and lock files removed) -> 216 PRs with at least one accepted hunk -> 1,254 hunks.
- **Performance-relevance filter:** `claude-sonnet-4-6` keeps only hunks "plausibly affecting runtime, memory, or I/O". This is the LLM's opinion from reading the hunk. Nothing is executed.
- **Performance pattern per PR:** each PR is assigned to one of nine optimisation patterns from Peng et al. [6]. The nine names appear only on the axis of Fig. 1: Algorithm-Level, Build & Infrastructure, Code Smells, Control-Flow & Branching, Data Structure, I/O & Sync, Loop Transforms, Memory & Locality, Network & DB.
- **Taxonomy (Sec. 2.2):** 18 categories from Even-Mendoza et al. [1], made by hand from LLM patches on Java projects in a GI pipeline. The authors changed one definition: `object_creation` (category 14) now also covers import-statement changes.
- **Classification (Sec. 2.3):** `claude-sonnet-4-6` and `gpt-5.4` label each hunk with the same prompt. Cost $22.
  - Full agreement: 48.4% (n=607). The label set is used as is.
  - Partial agreement: 51.6% (n=647). The intersection is used.
  - Full disagreement: discarded. The paper does not say how many hunks were discarded this way.
- **Validation:** six prompt-design rounds on a 40-hunk sample by three researchers. "two independent runs confirmed 67.5% exact and 22.5% partial accuracy". That is 27 of 40 hunks exactly right and 9 of 40 partly right (my arithmetic).
- **Statistics:** Apriori lift, Spearman rank correlation, Cliff's delta. No significance tests on the agent or pattern differences.
- **Replication package:** https://github.com/5uper6rain/ssbse-challenge-2026

## Section-by-section notes

### 1. Introduction
- Performance PRs are rare: "only 324 of the 33,596 PRs in AIDev-pop [4] carry a performance label (<1%)".
- RQ1: which syntactic mutation patterns characterise "successful performance PRs" from agents, and how do they differ from earlier GI work?
- RQ2: do the patterns differ across agents and across performance strategies?

### 2. Dataset and Methodology
- See the funnel above. The text says AIDev-pop PRs are "against 100 starred repositories". This is probably a wording slip for repositories with more than 100 stars (gong2026inconsistency describes the same subset as "33,596 PRs from 2,807 repositories with >100 stars"). Do not repeat "100 repositories" from this paper.
- The taxonomy covers structural edits (control flow, statement splitting), identifier edits (name modification, type change) and resource-management edits (synchronization, object creation).

### 3.1 RQ1: Category distribution (Table 1)
- Name modification 463 hunks (37.0%), object creation 330 (26.4%), type change 284 (22.7%), control flow 262 (20.9%), statement splitting 232 (18.5%), comment modification 167 (13.3%).
- The top category is misleading by name. "In 78% of name modification cases (Devin PRs following the Performance-Optimized Dependency Selection pattern), optimisation manifests as swapping library imports for faster alternatives (e.g., chalk -> picocolors)." So most "name modification" is really "replace one library with a faster one". The authors call it a "carrier category" and say it should be split in a future taxonomy.
- Rare categories: synchronization 10 hunks (0.8%), inlining 2 (0.2%), exception handling 17 (1.4%). The authors call these "runtime-risk categories" that "are seldom employed as performance optimisations".
- Name modification and type change appear together (lift 3.07).
- Comparison with the GI corpus of Even-Mendoza et al.: there `no_change` was 84% of patches. Here `no_change` is 0. The authors conclude that taxonomies tuned on GI data "do not transfer directly to agent-generated code". Note that `no_change` being 0 is partly by construction: the pipeline first drops hunks that are not performance-relevant.

### 3.2 RQ2: Variation by performance pattern and agent
- By pattern (Fig. 1): type change sits in Data Structure (253 of 284, 89%). Name modification sits in Build & Infrastructure (345 of 463, 75%). Object creation is spread over Data Structure (103) and Memory & Locality (96). Control flow co-occurs with object creation in 36.6% of PRs.
- By agent and language: Devin/TypeScript (n=461) is 77% name modification. Copilot/Rust (n=219) is 95% type change. Codex/Go (n=120) is 63% control flow.
- By agent (Table 2, label assignments, not hunks): Devin 670 total, of which name modification 361 (54%). Copilot 591, type change 224 (38%). Codex 574, control flow 136 (24%) and object creation 101 (18%). Cursor 184, comment modification 41 (22%). Claude Code is left out because it has only n=16.
- The authors admit agent and language are tangled: "each agent's profile co-varies with the language mix it targets."

### 4. Threats to validity
- Construct: taxonomy made for Java, corpus is multi-language. The widened `object_creation` definition means its 26.4% "is not directly comparable to prior corpus statistics".
- Internal: "LLM accuracy is bounded at 67.5% after six calibration rounds." Counts are lower bounds, but shares can be inflated for edits the filter finds easily (imports, renames).
- External: merged hunks n=324, unmerged hunks n=927. The two groups share 4 of the 5 top categories (Spearman rho = 0.90). Control flow and statement splitting are about 3 times more common in merged hunks. Name modification and type change are more common in unmerged hunks (Cliff's |delta| <= 0.28). Percentages are hunk-weighted, so a PR with many hunks counts more. Performance labels come from Peng et al. [6], so their labelling errors carry over. Agent and language are correlated (Devin -> TypeScript, Copilot -> Rust, Codex -> Go).

### 5. Conclusion
- "In a GI loop conditioned on (target strategy, agent), per-context priors from Tables 1-2 narrow the operator space from 18 categories to roughly five." This is a suggestion. The paper does not run a GI loop to test it.

## Key results (with numbers) and what they mean
- 324 of 33,596 AIDev-pop PRs are performance-labelled (<1%), and only 216 give usable hunks -> the pool of agent performance PRs is small. Any study on it, ours included, works with a few hundred PRs at most.
- Name modification 37.0%, and 78% of those are Devin dependency swaps -> the largest single thing "agent performance work" does in this corpus is replace a library, mostly by one agent in one ecosystem. This is not a general finding about agents.
- Type change 89% in Data Structure, name modification 75% in Build & Infrastructure -> syntactic category and performance strategy are strongly linked, so one predicts the other.
- Synchronization 0.8% (10 hunks) -> lock or concurrency edits are very rare in this corpus. For us: claims of the "remove the lock" kind (futex wait signal) will be few.
- Merged hunks 324 against unmerged hunks 927 -> about three quarters of the analysed hunks come from PRs that were not merged. RQ1 says "successful performance PRs", but the data is mostly unmerged work.
- 67.5% exact accuracy on 40 hunks -> about one hunk in three is not labelled exactly right. Small differences between categories should not be trusted.

## Tables and figures
- **Table 1 (p. 3):** all 18 categories with count, percent of 1,254 hunks and a one-line description. Read: percentages are multi-label and sum to more than 100%. The bottom rows (`no_change` 0, `extra_brackets` 0, `dead_code` 1, `duplicate_code` 1, `inlining` 2) show most of the taxonomy's small categories are almost unused.
- **Fig. 1 (p. 5):** heatmap, 16 non-zero mutation categories (rows) by 9 performance patterns (columns). Cells are counts of hunk-category assignments. The two hot cells are name modification x Build & Infrastructure (345) and type change x Data Structure (253). Memory & Locality is the broadest column (for example statement splitting 112, object creation 96, control flow 88, read from the figure image). The synchronization row reads 4, 2, 0, 0, 0, 2, 0, 2, 0 (sum 10, matching Table 1), so the 10 synchronization hunks are spread over Algorithm-Level, Build & Infrastructure, I/O & Sync and Memory & Locality. Small cell values are read from a low-resolution image; check the PDF before quoting any of them.
- **Table 2 (p. 6):** top 8 categories by agent (Devin, Copilot, Codex, Cursor), plus the total of all categories per agent (670, 591, 574, 184). Read: each agent has one clear lead category. Counts are label assignments, so they are larger than hunk counts.

## Ideas we can use
- The paper gives us a second, independent count of the AIDev-pop performance pool (324 labelled, 280 with a diff, 269 with source hunks). We can compare our own funnel to it. Any difference must be explained from our pinned data, not from this paper.
- The nine performance patterns of Peng et al. [6] are the natural "claimed mechanism" vocabulary. This paper shows they map well to code-level edits, which supports using them as a starting point for our claim-to-signal mapping.
- The "carrier category" problem is a warning for us: a label can hide very different mechanisms. A dependency swap (chalk -> picocolors) has no single kernel signal. It is a pure user-space CPU claim (fewer instructions), and many of these PRs are build or tooling changes that are hard to drive with a workload.
- Agent and language are confounded in AIDev-pop. If we report results per agent, we need the same caveat.

## Weaknesses and things glossed over
- No performance is measured. "Performance-improving" in the title means "carries a performance label". The paper cannot say any of the 216 PRs made anything faster.
- "Performance-relevant hunk" is decided by one LLM reading the hunk. There is no human check of this filter and no error rate for it.
- RQ1 says "successful performance PRs", but unmerged hunks (927) outnumber merged hunks (324) almost 3 to 1. The paper never defines "successful".
- 324 + 927 = 1,251, not 1,254. Three hunks are not accounted for. The paper does not explain.
- The validation is 40 hunks. The paper does not say what the ground truth was (who labelled the 40 hunks, with what agreement). The sample is called "held-out" but the prompt was tuned on it over six rounds, so 67.5% is an optimistic number. "seeds 42->777" is not explained.
- "substantially above chance" is stated without a chance baseline.
- The number of hunks discarded for full disagreement is not given, so we cannot tell how selective the intersection was.
- The comparison to Even-Mendoza et al. (84% `no_change`) compares a filtered corpus to an unfiltered one, in different languages, with one category redefined. The authors admit part of this.
- "Each performance strategy activates a largely disjoint category subset" (abstract) is stronger than Fig. 1 shows. Memory & Locality and Algorithm-Level use many categories.
- "narrow the operator space from 18 categories to roughly five" is not tested.
- Everything is hunk-weighted. A few large Devin PRs can drive the headline 37.0%.
- The AIDev reference is given as "Li, H., et al. ... (2024), arXiv 2412.02551". Other papers in this folder cite AIDev differently (gong2026inconsistency cites arXiv:2507.15003). Do not copy this paper's AIDev citation; use our own verified one.

## Open questions and future work (theirs, and ours)
- Theirs: split name modification into sub-types (import additions, call-to-cached-variable substitutions, API-level substitutions). Check cross-language stability. No separate future-work section.
- Ours: which of the nine patterns and 18 categories can be tied to a kernel or hardware signal at all? Dependency swaps and build changes probably cannot. Does the merged / unmerged difference they see (control flow and statement splitting about 3 times more common in merged hunks) line up with PRs whose mechanism we can confirm?

## Link to our paper
- **Related work:** this is a "what do agents change in performance PRs" study on the same AIDev performance subset. It stays at the syntax level and runs nothing. We can cite it as work that describes the edits, and state that nobody in this line checks the claimed effect by measurement.
- **Dataset section:** cite for the rarity of performance PRs in AIDev-pop only if our own pinned numbers agree. If they differ, attribute the 324 figure to this paper (which takes it from [5,6]).
- **Threats:** agent-language confounding and reliance on upstream performance labels apply to us too.

## Link to the thesis (tracing, kernel analysis)
- No tracing, profiling or kernel content at all. The only link is indirect: the mutation categories with a clear system-level meaning are rare here (synchronization 0.8%), while the common ones (library swap, type change) show up, if at all, as fewer instructions or fewer allocations in user space. That shapes which kernel signals a tracing study on this corpus can expect to see.

## Quotes for inline citation
- "AI coding agents are black boxes: we cannot inspect how they generate code, but we can inspect what they change." (Abstract, p. 1)
- "Fewer than 1% of the 33,596 agent PRs in AIDev-pop target performance" (Abstract, p. 1)
- "only 324 of the 33,596 PRs in AIDev-pop [4] carry a performance label (<1%)" (Sec. 1, p. 2)
- "Of the 324 PRs carrying a performance label [6], 280 had a retrievable diff; 269 contained at least one source-code hunk" (Sec. 2.1, p. 2)
- "Three categories dominate: name modification (37.0%), object creation (26.4%), and type change (22.7%)" (Abstract, p. 1)
- "Runtime-risk categories—synchronization (0.8%), inlining (0.2%), exception handling (1.4%)—are seldom employed as performance optimisations." (Sec. 3.1, p. 4)
- "LLM accuracy is bounded at 67.5% after six calibration rounds." (Sec. 4, p. 5)
- "Performance labels themselves originate from [6]; upstream mislabelling would propagate to our scope." (Sec. 4, p. 5)

## Suggested citation sentences
- Earlier studies of agent-written performance PRs describe the edits themselves, for example their syntactic form \cite{dovhoshliubnyi2026mutation}, but do not run the code to check that it became faster.
- Performance PRs are a small part of AIDev-pop: Dovhoshliubnyi et al. report that 324 of 33,596 PRs carry a performance label and that 269 of them contain a source-code change \cite{dovhoshliubnyi2026mutation}.
- In that corpus the most common edit is a dependency substitution, and synchronization changes account for 0.8% of performance-relevant hunks \cite{dovhoshliubnyi2026mutation}.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - Same data source as ours: the performance-labelled PRs of AIDev-pop. It tells us what the code edits look like. We ask a different question: did the claimed mechanism happen at the kernel or hardware level, and did the code get faster.
  - It runs no code and reads no PR description. There is no claim extraction, no build, no workload, no timing, no counters, no A/A control. All of that is ours.
  - It warns us about the corpus. Much of it is dependency swapping in TypeScript by Devin (Build & Infrastructure pattern), about three quarters of the analysed hunks are from unmerged PRs, and lock-related edits are very rare. So the share of PRs with a mechanism that maps to a clean kernel signal (fewer `read` calls, less futex wait) may be small, and the buildable, measurable subset may be smaller still. This is a real limit on our approach, and a reviewer who knows this paper may raise it.
  - Its labels come from LLMs with 67.5% exact accuracy on 40 hunks. If we use an LLM to extract mechanisms, we face the same question and should report our own validation.
- **Safe to cite for:**
  - Performance PRs are rare in AIDev-pop. "only 324 of the 33,596 PRs in AIDev-pop [4] carry a performance label (<1%)" (Sec. 1, p. 2). Attribute the number to this paper; it takes the label from Peng et al.
  - Not every labelled PR has a usable code change. "280 had a retrievable diff; 269 contained at least one source-code hunk after discarding tests, configuration, documentation, and lock files" (Sec. 2.1, p. 2).
  - Agent performance edits are led by three syntactic categories. "name modification (37.0%), object creation (26.4%), and type change (22.7%)" (Abstract; Table 1, p. 3).
  - Much of the top category is library substitution. "optimisation manifests as swapping library imports for faster alternatives (e.g., chalk -> picocolors)" (Sec. 3.1, p. 4).
  - Synchronization edits are rare in agent performance PRs: 10 of 1,254 hunks, 0.8% (Table 1, p. 3).
  - Agent and language are confounded in AIDev-pop. "Agent and language ecosystem are correlated in AIDev-pop (Devin->TypeScript; Copilot->Rust; Codex->Go)" (Sec. 4, p. 5).
- **Do not cite for:**
  - That agent performance PRs do or do not improve performance. Nothing is measured.
  - That these PRs are "successful" or merged. Most analysed hunks are from unmerged PRs (927 against 324).
  - Anything about PR descriptions, claims, or whether the description matches the code. The paper looks only at diffs.
  - The number of repositories in AIDev-pop ("100 starred repositories" looks like a slip).
  - A tested benefit for genetic improvement. The "18 to roughly five" operator reduction is a proposal, not a result.
  - Agent-specific behaviour as a property of the agent. The authors say the profiles follow the language mix.
