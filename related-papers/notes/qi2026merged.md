# Merged, Not Measured: An Empirical Study of Performance Issues Fixed by Coding Agents
- **Authors:** Zhenyu Qi, Haotang Li, Tomas Cerny, Bo Liu, Sen He (University of Arizona), Jinfu Chen (Wuhan University), Huashan Chen (Institute of Information Engineering, Chinese Academy of Sciences), Yutong Zhao (California State University, Long Beach), Derui Zhu (Rochester Institute of Technology). Corresponding authors: Jinfu Chen and Sen He.
- **Venue / year / status:** arXiv preprint, arXiv:2609.37985v1 [cs.SE], 29 Sep 2026. 52 pages (45 pages of text, then references). The PDF names no venue. It has a "Declarations" section and the data link says "[upon acceptance]", so it reads as a journal submission under review. Treat it as not peer-reviewed. Page numbers below are the printed page numbers.
- **PDF:** related-papers/qi2026merged_2609.37985.pdf
- **Cite key:** qi2026merged
- **BibTeX-style reference:** Zhenyu Qi, Haotang Li, Jinfu Chen, Huashan Chen, Yutong Zhao, Derui Zhu, Tomas Cerny, Bo Liu, and Sen He. 2026. Merged, Not Measured: An Empirical Study of Performance Issues Fixed by Coding Agents. arXiv:2609.37985.

## In short
The authors take the 71,677 agent PRs of AIDev v4 (repositories over 100 stars), filter and hand-code them, and get 1,262 confirmed performance fixes by six agents in 582 repositories. They study who gets merged and why, what the fixes look like, and what tests they carry. They also re-execute 53 fixes in two separate small experiments: 23 rejected fixes (a three-run pilot, mostly on workloads an LLM agent wrote) and 30 merged fixes (12 forks at three workload sizes, with statistics). In the rejected arm the claim reproduced in 6 of 23. In the merged arm 18 of 30 met their "delivery criterion", 3 improved but less than claimed, 9 showed no significant gain or regressed, and 14 changed behaviour on inputs the PR's tests never reach. Their main message: a merge follows the repository's history with the agent, not the content of the fix, and "a merge does not show that the fix delivers what it claims" (abstract, p. 2).

## Problem and motivation
- Agents open PRs that claim a speed-up. A passing test cannot show a speed-up. A maintainer has to judge from a measurement, and a reliable measurement needs repetition and control that a PR thread rarely shows (p. 2, citing Georges 2007 and Mytkowicz 2009).
- A wrong decision "merges a regression or discards a real improvement" (p. 2).
- Gap they claim (p. 3, in bold in the paper): no study of agent performance fixes in real repositories (a) confirms each fix by hand, (b) separates the fix's content from the repository that received it, or (c) re-executes what the fix claims.
- Research questions (p. 3):
  - RQ1: How often are agents' performance fixes accepted or rejected?
  - RQ2: What factors are associated with acceptance or rejection?
  - RQ3: How frequently do the fixes involve architectural changes?
  - RQ4: What evidence do agents provide to support their fixes?

## Background / key terms (explain each term simply)
- **Performance issue (their definition):** "a runtime inefficiency of the product (time, memory, I/O, queries, start-up) that a change to production code removes" (p. 2). CI speed-ups, compiler output, benchmark-only PRs and features that only mention performance are excluded (p. 10).
- **Fix / issue / PR:** each performance issue is identified through the agent PR that fixes it. They count "issues" and "fixes" and use "PR" only for the GitHub object (p. 3).
- **Rejected:** closed without a merge in AIDev's snapshot. It is a recorded state, not always a human decision (p. 9).
- **Acceptance (Eq. 1, p. 12):** merged / (merged + rejected). Open PRs are left out of both.
- **HLP (heuristic linguistic pattern):** a text rule that matches one sentence that talks about performance ("takes too long", "high CPU"). From Zhao et al. 2024 (80 rules). Used here as the first text filter (p. 9).
- **Codebook coding:** two coders label each item independently against a written rule book; a third resolves disagreements.
- **Cohen's kappa (κ):** agreement between two coders, corrected for agreement by chance. 1 is perfect. They read it on the Landis and Koch scale (p. 10).
- **Consensus set:** the 1,262 fixes that the authors confirmed by hand. All main tables use it.
- **Account model:** who owns the account that opens the PR. For Copilot, Devin and Jules it is a bot account, so someone else must merge. For Codex, Cursor and Claude Code it is the human operator, who usually merges their own agent's work (p. 11).
- **Author association:** GitHub's label for the PR account: OWNER, MEMBER, CONTRIBUTOR or NONE (p. 11).
- **Deleted-line share (Eq. 3, p. 14):** deleted lines / (added + deleted lines). Near 0.5 = rewrites code in place. Near 0 = only adds code.
- **Pre-opening merge rate (Eq. 4, p. 14):** share of the repository's other agent PRs that were merged, counting only PRs decided before this fix opened.
- **Track record (Eq. 5, p. 14):** number of PRs of the same agent that the repository merged before this fix opened.
- **Functional-level vs architectural-level fix:** functional-level changes at most one production file. Architectural-level changes several production files together for one performance mechanism (coded by hand, not by file count) (pp. 15-16).
- **Root cause codes (Zhao et al. 2023):** RC repeated computation, RDP redundant data processing, GIC general inefficient computation, ISC inefficiency under special cases, IAU inefficient API usage, IS inefficient synchronization, IDS inefficient data structure, II inefficient iteration.
- **Base and head:** base = the commit before the fix. Head = the PR's head commit (the fix). Both are built and measured.
- **rc and rm (p. 13):** rc = the improvement the PR claims, rm = the improvement they measure. Both are "base cost / head cost" on the same workload. A claimed 2x speed-up gives rc = 2. A value below 1 is a regression.
- **Reproduced (rejected arm, Eq. 2, p. 13):** rm - 1 >= 1/2 (rc - 1). In words: the measured gain reaches at least half of the claimed gain. A claim without a number counts as reproduced when rm >= 1.2. **Partly reproduced:** head is faster than base but below this bound. **Not reproduced:** no improvement or a regression. This is the meaning of "held" in the abstract ("only 6 of the 23 re-executed rejected claims held").
- **Delivery criterion (merged arm, p. 18):** read at the largest workload (L). The fix **delivers** when the head beats the base by at least 5% in median cost, with Mann-Whitney p < 0.05 and |Cliff's δ| >= 0.147, and, when the PR claims a number, the confidence interval of the ratio reaches that number. **Below the claim:** faster by these criteria but the interval stays under the claimed number. **Does not deliver:** change below 5%, not significant, or in the wrong direction.
- **Fork:** a fresh process run of the benchmark (the paper does not define the word; it is the JMH-style meaning). 12 forks per version per size in the merged arm.
- **Mann-Whitney U test:** a rank test of whether one group tends to have larger values. **Cliff's δ:** an effect size from -1 to 1 that says how often values in one group beat the other. The paper uses 0.147 as the threshold and does not explain the value (outside this paper it is commonly used as the border between a "negligible" and a "small" effect).
- **McFadden's pseudo R2:** a fit measure for logistic regression, 1 - lnL(model)/lnL(null). Higher is better; values are much smaller than a normal R2.

## Method and setup

### Dataset (Section 3.1, pp. 9-11, Table 1, Fig. 2)
- **Source:** AIDev **v4** (Li et al. 2025a, Hugging Face dataset `hao-li/AIDev`, "version v4", accessed 2026-09-28, reference list p. 49). The intro says AIDev has 932,791 agent PRs at its MSR 2026 release and 2.7 million at the v4 snapshot (p. 2). They use the 71,677 PRs in repositories with more than 100 stars, by six agents (Copilot, Codex, Devin, Cursor, Claude Code, Jules), up to 2025-10-24.
- **Step 1, text filter:** 80 HLPs of Zhao et al. 2024 re-implemented, plus 28 new patterns for fix words (memoize, debounce, lazy load, batch, N+1 query) and 3 for excluded categories. Two logistic regressions (one on matched patterns, one on TF-IDF) give a score; the screen score is the mean of the two. Trained on 1,219 PRs labelled in an earlier round plus 8,000 weak negatives. Cut at 0.5 keeps 7,660 PRs (10.7%). In five-fold cross-validation **on AIDev v3**, the cut recovers 80% of labelled fixes and flags 1.7% of unlabelled PRs. An audit of 200 PRs under the cut found 3 performance fixes (1, 0 and 2 in the three audit groups). They put recall "at roughly 90%". The 94% precision / 87% recall often quoted for HLPs are Zhao et al.'s numbers on issue reports, "not a measurement of this screen" (p. 10).
- **Step 2, model coding:** Claude Sonnet and GPT-5.6 label each of the 7,660 candidates independently (verdict, category, root cause). Gemini 3.5 Flash resolves disagreements. κ = 0.86 on the verdict. Result: 1,613 model-positive. Of the 6,047 rejected by the models, authors audited every tenth (604); κ = 0.96 and the rejections were confirmed.
- **Step 3, author coding:** three authors; two code each field independently, a third resolves. κ = 0.91 on the verdict. 1,262 of 1,613 confirmed. Of the 351 not confirmed, 270 are features or refactors that mention performance.
- **Consensus set:** 1,262 fixes in 582 repositories: 488 Copilot, 438 Codex, 147 Devin, 112 Cursor, 60 Claude Code, 17 Jules. 625 merged, 480 rejected, 157 open. So 1,105 closed.
- **Enrichment:** merger, author association, commit SHAs and per-file patches fetched from GitHub for 1,527 PRs; AIDev's commit details used for 86 that returned 404. Per-file patches missing for 3 fixes, so file analyses cover 1,259 fixes (1,102 closed).

### Re-execution arm 1: rejected fixes (the "pilot", Section 3.2.1 p. 12, Section 3.2.2 p. 13, results Section 4.3 pp. 22-24)
- **Sample:** 30 rejected fixes that report a measurement in the PR text, in TypeScript, JavaScript, Python, Go or Rust, with base and head commits in the snapshot. Random with seed 7, stratified by language.
- **Dropped:** 7 could not be run: 3 need a live database, 4 are whole-workspace Rust builds. All shares are over **23** fixes.
- **Build:** check out the base commit and the PR head commit (GitHub keeps the head under a pull-request reference after the branch is deleted). Build both in a language container with **2 CPUs, 4-6 GB memory, 30 minutes**.
- **Who runs it:** "a Claude Opus agent with shell access carries out the run from the repository, the two commit ids, the PR text and the claimed numbers, without the PR's outcome" (p. 12). So the agent sees the claim. It is blind only to merged/rejected.
- **Workload, in this order of preference:** (1) the workload the PR names, (2) otherwise a benchmark or test that the fix adds, (3) otherwise "a small workload constructed on the changed path". Case 3 applies to **16 of the 23** fixes. One workload is run on both trees.
- **Runs:** **three repetitions per tree**. They record the median ratio of base cost to head cost. No significance test in this arm.
- **Also:** the tests that the fix touched are run on the head, pass or fail is recorded.
- **Verdict:** Eq. 2 (see key terms). They say both thresholds "are operational choices of this study" (p. 13).
- **Build success:** a workload ran on both trees for all 23, but the base built in only 18 and the head in 17. The rest are script projects that run without a build step (p. 22).
- **Hardware, CPU pinning, noise control:** the paper does not say for this arm, beyond "one container".

### Re-execution arm 2: merged fixes (Section 3.5.1 p. 17, Section 3.5.2 p. 18, results Section 7.3 pp. 38-40)
- **Sample:** 30 fixes drawn from the 216 merged consensus fixes that change at least one test file. The sample is **purposive** (chosen by judgment, not random). A fix was eligible when "a deterministic in-process harness can drive its performance-relevant change (no network, GPU, user interface or database)" and the project builds with their toolchains. This excluded Android apps, very large builds and C# projects.
- They ranked 30 main cases and 10 reserves across five languages. One main case (SkBlaz/py3plex PR 100) was replaced by a reserve, because it adds a new API beside the old code, so no pre-merge version computes the same function.
- **Languages:** Java 11, Python 7, TypeScript 6, Go 4, Rust 2.
- **Versions:** the pre-merge commit and the merged commit.
- **Workload sizes:** S = the size of the PR's own test. M = one to two orders of magnitude larger. L = the size of the PR's claim, or the largest that keeps one base run under a few seconds. L is the "primary workload" that sets the verdict.
- **Runs:** each size runs in **12 forks per version**, interleaved base-head-head-base, "in a controlled experiment environment that avoids resource contention" (p. 17). The paper gives no more detail on this environment (no machine type, no pinning, no frequency settings).
- **Recorded:** median cost per operation, ratio of base to head with a bootstrap 95% confidence interval, Mann-Whitney U test, Cliff's δ.
- **Test check:** the PR's own tests are run on both trees. If a test passes on the base (the unfixed code), it does not guard the improvement.
- **Behaviour check:** they generate tests for every changed line by slicing the diff, repair them until they compile, run them on both trees and record every input where outputs differ.
- **Verdict:** the delivery criterion (see key terms).
- **Who builds the harness:** Section 3.5.1 does not say. Section 3.1 (p. 10) mentions "the judge and executing agents of RQ1, RQ2 and RQ4", so an LLM agent is involved in RQ4 too, but the paper does not describe its role in the merged arm.
- The two arms share the build step and the container but "are described in parallel and are not compared as one experiment" (p. 12).

### Other analyses
- **RQ1:** acceptance by agent, repository category (labelled by two model passes, 85% agreement, κ = 0.83, third pass resolved 88 disagreements), star tercile (small <= 347, mid 348-2,576, large >= 2,577), account model, author association; time to decision; coded closing reason of the 480 rejections.
- **RQ2:** pooled, within-agent, within-repository (74 repositories that hold both outcomes), 40 blind pairs (one merged and one rejected fix from the same repository and agent, judged by Claude Opus with outcome fields removed), and nested logistic models M0-M4 on 1,102 closed fixes with standard errors clustered by repository.
- **RQ3:** root cause (8 codes), resolution (15 codes), scope, pattern, functions touched (from hunk headers, a lower bound).
- **RQ4:** test change detection from file paths, coder reading of what tests check, acceptance by test kind, and the merged-arm re-execution.
- **Statistics:** Fisher's exact test, χ2 with Cramér's V, Mann-Whitney U, Wilcoxon signed-rank, binomial test, Kruskal-Wallis, logistic regression with odds ratios and 95% CIs. No correction for multiple tests (they say so in threats).

## Section-by-section notes

### 1. Introduction (pp. 2-4)
- Human performance fixes are small: median of 8 changed lines (Jin et al. 2012); 73% of JavaScript optimizations under 20 lines (Selakovic and Pradel 2016). About a third of performance reports carry a measurement (Zaman et al. 2012). These are other papers' numbers, as reported by Qi et al.
- They describe Peng et al. (2026) as selecting performance PRs by AIDev's task label without hand confirmation, and Opu et al. (2026) as using a language-model classifier.
- Benchmarks (SWE-Perf, GSO, SWE-fficiency) measure speed-ups "in a harness rather than in the repository the agent submitted to" (p. 3).
- Four contributions (p. 4): acceptance tracks repository history and patch shape; the two re-executions "with the protocol for both"; a characterization of inefficiencies and resolutions; a dataset of 1,262 coded fixes.

### 2. Background and related work (pp. 4-8)
- 2.1 Performance analysis: Georges 2007, Mytkowicz 2009, Laaber 2019, Traini 2023. Their re-execution "borrows the smallest safeguards (repeated runs of one workload on both trees, one container)" (p. 5). This is their own description of how light the pilot is.
- 2.2 PR acceptance: author standing explains merges (Tsay 2014); bot PRs merged 37% vs 73% for humans (Wyrich 2021).
- 2.3 LLM optimizers and benchmarks. They quote Peng et al. (2026): 324 agent performance PRs state a validation less often than 83 human ones (45.7% versus 63.6%). They quote Yi et al. (2025): about a third of plausible LLM patches for 65 Java tasks show no measurable gain.
- 2.4 Human performance fixes: Zhao et al. 2023 coded 570 issues in 13 projects, found 27% architectural-level and 15% with test changes. These are the comparison numbers for RQ3 and RQ4. They warn that the two corpora are different populations.
- Fig. 1 (p. 5): anatomy of one fix (calcom/cal.com PR 21371, Devin, merged after 1.1 h; claim "~6s to ~70ms (85x faster)"; nobody reports re-running the measurement).

### 3. Study design (pp. 8-18)
See "Method and setup" above. Extra details:
- "Silent" = closes with no human text. "Direct rejection" = silent rejection within 24 hours. "Prolonged rejection" = rejection after seven days or more (p. 13).
- Model blocks: M0 controls; F1 agent and description style; F2 diff shape (deleted-line share, file count, noise files, churn share of largest file); F3 added machinery (adds production file, architectural-level, new shared abstraction); F4 repository history (author association, pre-opening merge rate, number of agent PRs) (p. 15).
- The models "condition on closure by the snapshot and so exclude the 157 open fixes" (p. 15).

### 4. RQ1: acceptance (pp. 18-24)
- **Overall:** 57% of 1,105 closed fixes merged (625). In January-April 2025 nearly all fixes were Devin's and acceptance was near zero; since May 2025 the monthly rate is between 53% and 69%.
- **By size:** small 64%, mid 61%, large 44% (χ2 = 32.8, V = 0.17). **By association:** OWNER 77%, CONTRIBUTOR 51%, NONE 6% (3/48).
- **By agent (Table 6):** Codex 73% (296/408), Claude Code 73% (37/51), Jules 73% (11/15), Copilot 50% (200/397), Cursor 42% (37/89), Devin 30% (44/145). χ2 = 104, V = 0.31.
- **By category (Table 6):** Content 69%, Library 68%, Server-client 67%, Search 60%, Language 51%, Cloud 50%, Big-data 47%, Build Management 40%, Other ASF 55%, Other 52%.
- Two repositories dominate: mochilang/mochi has 80 of 143 closed Language fixes (all Codex, 54% accepted); Smart-Cleaner-for-Android has 41 of 277 in other ASF categories (all Codex, 95% accepted).
- **Self-merge:** operators merge their own agent's work in 81% (Codex), 95% (Cursor) and 84% (Claude Code) of merged cases. Of 306 self-merged operator fixes, 209 were merged within an hour and 97% of these carry no human text.
- **A merged fix that does nothing (p. 20):** katspaugh/wavesurfer.js PR 4118 (Codex), merged 4 minutes after opening with no review. "The diff compares a new buffer field with the decoded audio but never assigns that field, so each render from decoded audio recomputes the frequencies." This is a claimed cache that never caches. They found it by reading the diff, not by measuring.
- **Time (4.2):** merged fixes close in a median of 1.2 hours (IQR 0.1-16), rejected in 24.3 hours (IQR 1.6-175). 37% of rejections are direct (within 24 h, no human text). 26% are prolonged. Devin closes 37 with its own inactivity template.
- **Stated reasons (4.3):** no stated reason in 61% of the 480 rejection threads, and in 86% of direct rejections. Only 3% of rejection threads ask for a measurement (13 rejections). A human engages substantively in 34%.
- **Re-executed rejected claims (pp. 22-24, Fig. 4):**
  - Of 23: reproduced 6 (26%), partly 4 (17%), not at all 13 (57%).
  - Median speed-up 1.02x (IQR 0.86-2.20x), "measured on the changed path rather than at production scale".
  - "where a claim gave a number, the measurement fell short of it in all but two of the 16 fixes" (p. 22). So 16 of the 23 claims carry a number. (This 16 is a different count from the 16 fixes with a constructed workload; the paper does not say how the two sets overlap.)
  - Tests the fix touched passed on the head in 13 cases (57%). In several cases the added tests also pass on the base.
  - The 13 failures: six run slower, five show no measurable change (0.97-1.02x), one crashes on the head, one does not contain the claimed change.
  - Slower examples: rsbuild dedupeNestedPaths claimed 2-7x, measured 0.40x at 1,000 paths; opteryx LIMIT push-down 80x slower on a 1,000-row query; a Blender add-on parent-child cache 57x slower, "and the PR's own profile used the same branch for both the before and the after run"; dragonfly claims a 98% CPU reduction and measured 0.55x; taiga-ui still instantiates all 1,110 nodes and renders 18% slower; cal.com .tz() is 25% slower and returns half the time slots for one time zone.
  - Claimed change missing from the diff: softmaple (chunking described in the PR body is not in the diff; build output byte-identical to the base); cosh (head does not contain the ASN-first reordering, "so the 1.95x we measured is not the claimed change").
  - Two of the ten reproduced or partly reproduced fixes break behaviour: vibetunnel (75% fewer WebSocket updates on the PR's bursty stream, but the debounce never fires on a steady stream and an existing test fails); browser-use (1.19x faster but finds 1,334 of 2,000 interactive elements).
  - Reproduced examples are measured in mechanism units, not only time: kibo re-render count falls 37x; sift allocations fall 8x (218 to 27 per op); sktime serialized size shrinks 2.8x; awesome-digital-history removes a loop of 20,000 pushState calls in ten seconds.

### 5. RQ2: factors (pp. 24-30)
- Coded content does not separate outcomes: root cause p = 0.44, category p = 0.25, test co-change 35% merged vs 37% rejected (p = 0.49).
- An attached measurement is slightly **more** common among rejected fixes (20% vs 15%, p = 0.024), and a numeric claim too (35% vs 28%). The effect follows the agent mix and is not significant in M4.
- Merged fixes are smaller (median 90 vs 159 changed lines, p < 0.001).
- **Table 8 (pseudo R2):** M0 0.053; M1 0.119; M2 0.144; M3 0.145 (F3 block p = 0.59); M4 0.232. With track record added: 0.246.
- In M4: pre-opening merge rate OR 13.7 from 0 to 1 (95% CI 6.3-30.0); association NONE OR 0.10, MEMBER 2.2, OWNER 3.0; deleted-line share OR 10.5 (95% CI 4.4-25.2).
- **Description style (5.2):** pooled, rejected fixes are wordier (median 271 vs 97 words). Within each agent there is no difference. The pooled gap is the agents' templates (Codex about 40 words, Copilot and Devin 250-400 words).
- **Deleted-line share (5.3):** 0.26 merged vs 0.15 rejected pooled; Copilot 0.20 vs 0.10; Codex 0.33 vs 0.21; Devin 0.28 vs 0.20 (all p <= 0.001). Higher in merged fixes in 50 of 74 repositories with both outcomes.
- **Blind pairs:** the Claude Opus judge picked the merged fix as the one it would merge in 33 of 40 pairs (binomial p = 4 x 10^-5). It rated the rejected description as overclaiming twice as often (14 vs 7).
- **Repository history (5.4):** acceptance 33% where the repository had merged at most 40% of its decided agent PRs, 57% in the middle band, 84% above 90% (n = 165, 521, 255). Track record: 37% never seen, 31% seen but none merged, 51% after 1-4 merged, 58% after 5-19, 70% after 20 or more.
- They say clearly: "These are associations in observational data, not measured causes of any decision" (p. 24).

### 6. RQ3: content and reach (pp. 30-35)
- **Root causes (Table 10, 1,262 fixes):** RC 27%, RDP 17%, GIC 16%, ISC 11%, IAU 10%, IS 7%, IDS 7%, II 3%, unclear 2%. RC + RDP = 44%.
- **Resolutions:** caching or memoization is the primary resolution of 20% of fixes; concurrency change 10%; removing redundant work 8%; API replacement 8%; resource release or bounding 7%; early exit, batching, lazy evaluation, allocation reduction and algorithm change 6% each; data-structure change and I/O or query tuning 5% each.
- **Cause to resolution:** repeated computation is resolved by caching in 67%; inefficient synchronization by a concurrency change in 84%; inefficient API usage by API replacement in 63%; inefficient data structure by a data-structure change in 57%; special cases by resource release or bounding in 52%.
- Lazy or deferred evaluation is accepted 40% vs 57% overall (p = 0.004). Allocation reduction is accepted most (69%).
- They note Opu et al.'s finding (acceptance varies with optimization type) "does not survive except for lazy evaluation" under their hand-coded resolutions (p. 32).
- **Scope:** 46% architectural-level (582 of 1,259). A raw file count would give 57%. Zhao et al. 2023 found 27% for human fixes.
- **Reach:** architectural-level fixes touch a median of 7 functions (IQR 4-13) across 4 files (2-7), 9 hunks, 151 production lines; 1.7 functions per file vs 2.0 for functional-level (p = 0.42).
- **Patterns (Table 11):** change propagation n=170; new shared abstraction n=174 (258 lines, deleted share 0.10, new file in 63%); optimization clone n=124 (deleted share 0.40); parallel optimization n=78.
- Example (Fig. 10): gitbutler PR 10222, Copilot adds a 30-second cache service; maintainer closes it within 90 minutes: "the query system has caching built in".

### 7. RQ4: tests and delivery (pp. 35-40)
- **Test changes (Table 12):** 472 of 1,259 fixes (37%) change a test file; Copilot 47%, Codex 31%, Devin 29%, Other 37%. 82 fixes (7%) touch a file named as benchmark or performance code.
- **What tests check:** among the 472, tests assert functional behaviour in 51% and a performance quantity in 20%; 30% include an adaptation; 25% a regression guard; 11% a benchmark without an assertion.
- **Across all 1,259:** 11% carry a performance test or benchmark (140 fixes), 16% functional tests only, 10% adaptation only, 63% no test. Of the 140: 66 sized workload, 49 toy, 23 parameterized, 2 none; 91 run in CI.
- **Acceptance by test kind:** 51% performance test, 54% functional only, 60% adaptation only, 58% no test (p = 0.53). With a test change 55%, without 58% (p = 0.49).
- **Fig. 12:** rsbuild PR 6060 adds a test with a 100 ms bound for 100 paths. The unfixed code takes about 41 µs per call, so the bound is more than 2,000 times above the real cost and the test passes on both trees.
- **Merged re-execution (7.3, Fig. 13, Table 13):**
  - 18 deliver, 3 below the claim, 9 do not deliver. Of the 9: six show no gain of at least 5%, three are slower.
  - Median base/head ratio 1.8x.
  - Ten fixes claim a number. The measurement reaches it in four (frostwire 1157, 1181, 1183, color 110), falls short in three (frostwire 1075, 1171, rbac 42), and shows no gain or a loss in three (translate 5767 claims 2.8x, rsbuild 6022 claims 4%, whatsapp-rust 47 claims 1.25x and allocates about 10% more).
  - Workload size matters: eight fixes are slower than the base at one of the three sizes, and five of the eighteen that deliver gain only at the larger sizes. jdereg/java-util PR 127: binary search is 9% slower at the PR's own four keys and 4.8x faster on 600.
  - PR's own tests pass unchanged on the base in 17 of the 28 fixes where they run there. Only 2 of 30 fail on the base for a performance reason. In four fixes the PR's tests fail on the merged head itself.
  - PR's tests execute every performance-relevant changed line in 10 of 30 (median diff coverage 0.89). Generated tests reach full coverage in 28.
  - 8 of the 10 fully covered fixes fail the delivery criterion against 4 of the 20 partly covered ones (p = 0.004). They explain it by diff size: fully covered fixes are mostly one- to five-line micro-optimizations "whose gain disappears under the JIT or inside untouched work".
  - Behaviour: generated-test outputs differ in 24 of 30. In 10 the difference is intended or harmless. In 14 the fix "introduces a functional change its description does not mention", and in 10 of those the head fails or returns a different result on inputs within intended use. Examples: java-util binary search misses a key inserted in descending order; numbagg covariance (PR 397) relative error grows to 0.13 at an offset of 10^6; a rate limiter lets a throttled client through once more than 1,024 clients are active.
  - Performance assertion vs delivery: 3 of 9 with an assertion deliver, 15 of 21 without (Fisher p = 0.10). They do not read this as evidence either way.
  - "The two arms are not comparable, so we report them side by side and draw no conclusion from their difference" (p. 39).

### 8. Discussion (pp. 41-43)
- For maintainers: a re-runnable measurement would put fix-specific evidence into the decision.
- For researchers: the pilot protocol "costs one language container and at most thirty minutes per fix and resolved the large claims in 19 of the 23 fixes we ran (6 reproduced, 13 failed)" (p. 41). The merged-arm protocol "surfaces failure modes the pilot cannot".
- "an evaluation that reports one number on one workload can call a fix delivered when it regresses at the PR's own scale or changes behavior its description does not mention" (p. 41).
- For AIDev users: "a changed test is weak evidence that the claimed benefit was verified" (p. 41).
- 8.2 Approval funnel against human PRs (Table 14): in five repositories (airbyte, cal.com, crewAI, liam, onlook; PRs opened January-June 2025; 1,059 agent and 953 human PRs) agent PRs are merged 41% vs 80% for humans. Third-party approval 35% vs 53%. Once approved, 95% vs 96% are merged. A paired set built **on AIDev v3** (247 agent and 128 human performance fixes; 358 of 375 closed) shows the same funnel: merged 40% vs 79%.

### 9. Threats to validity (pp. 44-45)
- **Construct:**
  - Labels come from LLM coding then author coding.
  - "The blind-pair judge and the re-execution agent are Claude Opus models, and 60 of the 1,262 fixes come from Claude Code, so a same-vendor bias in judging that agent's fixes cannot be ruled out for those two instruments."
  - The judge may read a cleaner fix than the maintainer first saw (head can include review changes) and the PRs may be in its training data.
  - Coders were not blind to the outcome (the PR page shows it).
  - The text filter misses "roughly a tenth of the population" and "every population share is conditioned on the filter".
  - Function counts are a lower bound. A few non-code files are counted as production files.
- **Internal:** the pre-opening merge rate reflects the same maintainers' habits, so it is not an independent cause. For operator accounts it partly measures the operator's own habit. NONE association and empty track record are partly collinear. Devin's inactivity template makes the closed-by field unreliable.
- **Conclusion:** many significance tests, so single differences may be chance. The robustness checks are dependent checks on one dataset, not replications. Subgroup results are exploratory. Dropping mochi (91 consensus fixes) and Smart-Cleaner-for-Android (45) moves pooled acceptance to 55%. Isolated content differences (lazy evaluation and file-count gradient at p = 0.004, architectural scope at p = 0.044) "would weaken under any correction".
- **External (the part about re-execution, p. 45):**
  - AIDev v4 covers six agents, repositories over 100 stars, up to October 2025; the 157 open fixes may since have closed.
  - "The re-execution pilot has 23 fixes, and for 16 of them the executing agent constructed a workload on the changed path rather than running one the PR named. It shows that non-reproduction is common among rejected fixes with an attached measurement, and how it arises, but gives no population rate."
  - The merged arm "was selected by judgment" for fixes a deterministic in-process harness can drive, "which favors small, self-contained fixes, whose gains most easily vanish under a JIT or inside untouched work, so its non-delivery rate (9 of 30) may overstate the population's."
- **Reliability:** a re-run of the model labelling, the pair judge or the executing agent may not give the same output. They release data, codebooks, model outputs, container results and scripts (link "upon acceptance").

### 10. Conclusion and future work (pp. 45-46)
Four limits: (1) associations in one snapshot; (2) the two re-execution arms are small, use different protocols, and the merged arm was selected by feasibility; "running both under the three-size protocol of Section 7.3 on a random sample would give comparable delivery rates and show whether an agent-chosen workload understates them"; (3) the funnel rests on five repositories and one paired set; (4) open fixes and newer agents are outside the snapshot.

## Key results (with numbers) and what they mean
- 57% of closed fixes merged; 61% of rejections give no reason; 3% of rejection threads ask for a measurement -> maintainers almost never check the performance claim in the open.
- Rejected arm: 6 reproduced, 4 partly, 13 not, of 23 -> more than half of the claims failed, but on three runs and mostly agent-written workloads. It is a pilot, and they say it gives no population rate.
- Merged arm: 18 deliver, 3 below the claim, 9 no gain or regress, of 30 -> even merged fixes fail to deliver in about a third of this hand-picked sample. The sample favours small fixes, so 9 of 30 may be too high for the population.
- 14 of 30 merged fixes change behaviour without saying so; 10 of them give a wrong result or fail on normal inputs -> "faster" is not enough, the output must be compared too.
- 8 of 30 merged fixes are slower than the base at one of three sizes -> one workload size can give the wrong verdict in either direction.
- PR tests pass on the unfixed code in 17 of 28 -> the tests agents add mostly cannot detect whether the optimization is there.
- Two rejected fixes do not contain the change the PR text describes (softmaple, cosh), and one merged-by-owner fix never assigns the cache it adds (wavesurfer.js) -> the claimed mechanism can be absent even when a timing number exists. This is the closest the paper comes to a mechanism check, and it was done by reading diffs.
- Pre-opening merge rate OR 13.7; deleted-line share OR 10.5; coded content, tests and measurements not significant -> a merge is a weak label for "the fix works".
- Caching is the top resolution (20% of all fixes; 67% of repeated-computation fixes) -> "cache the result" is the most common mechanism claim an agent makes.

## Tables and figures
- **Fig. 1 (p. 5):** anatomy of one agent performance fix (cal.com PR 21371) and the fields coded from it.
- **Fig. 2 (p. 8):** pipeline 71,677 -> 7,660 -> 1,613 -> 1,262, and the subset each RQ uses.
- **Table 1 (p. 9):** the analysis sets. Read: "rejected, with a measurement, re-executed 30 -> 23" and "merged, with a test change, re-executed 30".
- **Tables 2-5 (pp. 11, 13, 16, 18):** coding schemes.
- **Table 6 (p. 19) and Table 7 (p. 20):** acceptance by agent and category, and by category within agent.
- **Fig. 3 (p. 21):** time to decision; how rejections happen by agent.
- **Fig. 4 (p. 23):** claimed (open diamond) vs measured (filled) improvement for the 23 rejected fixes, log scale from 10^-2 to 10^4. Read: most measured points sit at or left of 1 (no change or slower) while the claims sit to the right. The seven fixes that could not run are not shown.
- **Table 8 (p. 25):** nested models. Read the jump from M3 (0.145) to M4 (0.232): repository history adds the most.
- **Fig. 6 (p. 27), Fig. 7 (p. 27):** deleted-line share by outcome; an example of "replaces code" vs "adds machinery".
- **Fig. 8, Table 9 (p. 29):** acceptance by merge rate and by track record.
- **Table 10 (p. 31):** root causes by agent.
- **Fig. 9 (p. 33):** architectural-level share and acceptance by category.
- **Table 11 (p. 35), Fig. 10 (p. 34):** reach by pattern; the gitbutler cache example.
- **Table 12 (p. 36), Fig. 11 (p. 36):** test changes by agent; three kinds of test change.
- **Fig. 12 (p. 38):** a performance test whose bound is about 2,400x above the cost it guards.
- **Fig. 13 (p. 39):** claimed vs measured for the 30 merged fixes. Filled markers = ratio at the primary workload; small open circles = ratio at the PR's own test size; diamonds = claim. frostwire 1183 removes an allocation entirely, so its ratio is unbounded.
- **Table 13 (p. 40):** rejected: 23 run, 6 / 4 / 13. Merged with a performance assertion: 9 run, 3 / 2 / 4. Merged without: 21 run, 15 / 1 / 5. Merged all: 30 run, 18 / 3 / 9.
- **Table 14, Fig. 14 (p. 42):** approval funnel, agent vs human PRs.

## Ideas we can use
- **Three workload sizes (S, M, L).** One size can flip the verdict (java-util PR 127: 9% slower at 4 keys, 4.8x faster at 600). If our build agent writes one workload, we should say which scale it is, or run more than one.
- **Run the PR's tests on the base.** A test that passes on the unfixed code does not guard the improvement. This is cheap and we can report it per PR.
- **Compare outputs on base and head.** They generate tests by slicing the diff. Our "output changed" verdict is the same idea; cite them for how often it happens (14 of 30).
- **Interleaving base-head-head-base.** A simple order that cancels slow drift. Compare with our run order.
- **"Claimed change not in the diff" as a category.** softmaple, cosh and wavesurfer.js show a claim can be false at the code level. Our mechanism check on kernel signals would catch the same class at run time (no fewer syscalls, no fewer faults).
- **Verdict thresholds as explicit "operational choices".** They state Eq. 2 and the 5% / p / δ rule openly. We should state ours the same way.
- **Their open question is our entry point:** whether "an agent-chosen workload understates" delivery (p. 46). Our build agent never sees the claim, which removes one bias their pilot has.

## Weaknesses and things glossed over
- **The rejected arm is very light.** Three repetitions per tree, no significance test, no confidence interval, container with 2 CPUs, no description of the host, no noise control. A ratio of 0.97-1.02x is called "no change within run-to-run noise" without a measured noise level. There is no base-against-base (A/A) control in either arm.
- **16 of 23 workloads were written by the LLM agent**, and the agent saw the PR text and the claimed numbers. It did not see the outcome, but all 30 drawn fixes were rejected, so blindness to outcome means little inside this arm. A workload "on the changed path" is a microbenchmark and may not reflect the PR's claimed scale; the authors admit this ("rather than at production scale").
- **"Reproduced" needs only half of the claimed gain** (Eq. 2). A claim of 10x counts as reproduced at 5.5x. A claim without a number needs only 1.2x. These thresholds are arbitrary and the authors say so.
- **The merged arm is hand-picked.** Purposive sample, only fixes with a test change, only in-process deterministic code, no database, network, UI or GPU, no C#, no Android. So I/O, concurrency and database fixes are mostly excluded, which are exactly the cases where kernel behaviour matters. Results cannot be generalized, and the authors say the non-delivery rate may be overstated.
- **The "controlled experiment environment" is not described.** No machine, no CPU pinning, no frequency scaling settings, no cloud vs bare metal. With 12 forks this matters less than in the pilot, but it cannot be checked.
- **Delivery is judged only at size L.** A fix that regresses at the PR's own size can still "deliver".
- **The two arms cannot be compared** (different sampling, repetitions, verdict rule). The abstract still puts "6 of 23" and "18 of 30" close together; a quick reader may compare them. The paper warns against this on pp. 18, 39 and 45.
- **Time only, plus ad hoc counters.** They measure cost per operation and, for some fixes, allocations, re-render counts, message counts or size. There are no hardware counters, no syscall counts, no kernel traces. They never test systematically whether the claimed mechanism happened. Where they find a missing mechanism, it is by reading the diff.
- **Who built the merged-arm harness is unclear.** The paper mentions "executing agents" for RQ4 but does not describe the agent's role, or how generated tests were validated.
- **Generated tests as a behaviour oracle.** "Repair them until they compile" may bias which inputs are tested. The split into 10 harmless and 14 unmentioned functional changes is a manual judgment; no agreement number is given for it.
- **Same-vendor instruments.** The re-execution agent and the judge are Claude Opus; they admit possible bias for the 60 Claude Code fixes.
- **Dataset versions are mixed.** The main set is AIDev v4. The text-filter cross-validation and the human/agent paired set (Section 8.2) are on AIDev v3.
- **Coders were not blind to the outcome.**
- **No multiple-test correction**, many subgroup tests.
- **Replication package is not public yet** ("[upon acceptance]"), so the per-fix workloads and container results cannot be inspected now.
- **Not peer-reviewed** as far as the PDF shows.

## Open questions and future work (theirs, and ours)
- Theirs: a controlled study that submits the same optimization in a "removing" and an "adding" form; both arms under the three-size protocol on a random sample; the funnel in more repositories; a refresh after October 2025.
- Theirs, implied: what an approver weighs at the approval step "is a question for interview work" (p. 43).
- Ours: When a fix "delivers", did it deliver for the claimed reason? Their protocol cannot say. When a fix does not deliver, is the mechanism absent, or present but too small to matter? Kernel and hardware signals can separate these two cases.
- Ours: How many of their "no change within noise" verdicts would survive a proper A/A control and more runs?
- Ours: They exclude database, network and whole-workspace builds. How do I/O and concurrency fixes behave, where syscalls, page faults and futex wait are the direct evidence?

## Link to our paper
- **Introduction (`paper/sections/01-introduction.tex`, lines 7-12):** we write that studies "at most, re-execute a few dozen of them" and that "re-executed claims often do not hold", both citing this paper. Both are supported. To be exact: 53 fixes ran (23 rejected, 30 merged); 60 were drawn. In the rejected arm 13 of 23 were not reproduced; in the merged arm 9 of 30 showed no significant gain or regressed and 3 fell short of the claim. "Often" is fair, but the rejected-arm number comes from a three-run pilot, so do not present it as a rate.
- **Related work (`paper/sections/04-discussion.tex`, line 27):** "Qi et al. re-execute 53 fixes from AIDev". Correct (23 + 30). They use AIDev v4; our draft says we use version 5. Say so if a reviewer could think the samples are the same.
- **Approach:** their delivery criterion (5% median, Mann-Whitney p < 0.05, |δ| >= 0.147, CI reaches the claim) is a ready comparison point for our "faster or not" verdict.
- **Results / cases:** their examples of slower, unchanged, crashing and "change not in the diff" fixes match our verdict classes (not faster, mechanism absent, output changed). We can cite them as prior evidence that each class exists.
- **Threats:** they share our threat that an LLM-written workload may not reflect real use. Cite their own statement of it (p. 45).

## Link to the thesis (tracing, kernel analysis)
- The paper has no kernel tracing, no `perf` counters, no eBPF or LTTng. It is a timing study with some application-level counters (allocations per op, render counts).
- It shows why timing alone is weak: gains "disappear under the JIT or inside untouched work", the verdict changes with workload size, and some fixes are "faster" while broken. A trace-based method can show where the time went on both versions.
- Their excluded cases (live database, network, whole-workspace builds) are the ones where kernel-level signals (syscall counts, block I/O, futex wait, scheduler events) carry the most information.
- The most common claims in their data (caching 20%, concurrency change 10%, I/O or query tuning 5%, allocation reduction 6%, resource bounding 7%) each map to an observable low-level signal. This supports building a claim-to-signal table.

## Quotes for inline citation
- "a passing test cannot show the benefit of such a fix, so a maintainer who receives one must judge the benefit from a measurement, and a reliable measurement takes repetition and control that a PR thread rarely shows" (p. 2)
- "only 6 of the 23 re-executed rejected claims held under our three-run pilot on mostly agent-built workloads" (abstract, p. 1)
- "of the 30 merged fixes, 18 met our delivery criterion, 3 fell short of the claim, 9 showed no significant gain or regressed, and 14 change behavior on untested inputs" (abstract, p. 2)
- "a merge does not show that the fix delivers what it claims" (abstract, p. 2)
- "Only 3% of rejection threads ask for a measurement" (p. 22)
- "A reproduced speed-up does not by itself show the fix is correct" (p. 23)
- "The two arms are not comparable, so we report them side by side and draw no conclusion from their difference." (p. 39)
- "a merge records that a maintainer accepted the fix and not that the fix does what its description says" (p. 40)
- "an evaluation that reports one number on one workload can call a fix delivered when it regresses at the PR's own scale or changes behavior its description does not mention" (p. 41)
- "It shows that non-reproduction is common among rejected fixes with an attached measurement, and how it arises, but gives no population rate." (p. 45)

## Suggested citation sentences
- Qi et al. re-executed 53 agent performance fixes from AIDev and found that 13 of 23 rejected claims were not reproduced and 9 of 30 merged fixes showed no significant gain or regressed \cite{qi2026merged}.
- A merge is a weak sign that a performance fix works: acceptance follows the repository's history with the agent more than the content of the fix \cite{qi2026merged}.
- The tests that agents attach rarely guard the improvement; in a re-execution of merged fixes, the PR's own tests passed on the unfixed code in 17 of 28 cases \cite{qi2026merged}.
- Faster is not enough: 14 of 30 re-executed merged fixes changed behaviour on inputs their tests did not reach \cite{qi2026merged}.
- Prior re-execution measured run time on a workload that, in most pilot cases, the executing agent wrote with the claim in view \cite{qi2026merged}; we hide the claim from the build agent and check the claimed mechanism with kernel and hardware signals.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is the closest prior work. It takes agent performance PRs from AIDev, rebuilds base and head, runs a workload and gives a per-fix verdict on the claim. It also compares outputs of base and head. So two of our four per-PR answers ("faster or not" and "output changed") already exist in this paper, on 53 fixes.
  - What it does not do and we do: it never checks the claimed mechanism with low-level signals. It uses run time (and sometimes allocations or call counts chosen case by case). No hardware counters, no kernel traces, no dedicated cores, no A/A control, no report of hidden costs. Its pilot uses three runs. Its executing agent sees the PR text and the claimed numbers; our build agent does not see the claim.
  - Where it weakens our position (be honest about this): (1) Our novelty cannot be "first to re-execute agent performance PRs" or "first to show claims do not hold". It must be the mechanism check and the measurement rigour. (2) They argue a cheap protocol (one container, at most 30 minutes) "resolved the large claims in 19 of the 23 fixes" (p. 41). A reviewer can ask why kernel tracing is needed when a stopwatch already settles large claims. Our answer has to be the cases a stopwatch cannot settle: small effects, faster for a different reason, and hidden costs. (3) They already found "the claimed change is not in the diff" cases by reading code, which is a cheaper mechanism check than tracing for those cases. (4) Their merged arm is statistically stronger than a single measurement per PR on one machine (12 forks, three sizes, bootstrap CI). If we measure each PR once, they are ahead of us on repetition.
  - Shared weakness: both rely on LLM-built workloads. They name this as a threat and as future work ("show whether an agent-chosen workload understates them", p. 46).

- **Safe to cite for:**
  - Agent performance claims often fail when re-executed. Rejected arm: "the claim reproduced in 6 (26%), partly in 4 (17%), and not at all in 13 (57%)" of 23 (Section 4.3, p. 22). Always add that this is a three-run pilot.
  - Merged fixes do not always deliver. "Eighteen of the 30 merged fixes meet our delivery criterion at the primary workload, three improve but fall short of the claimed gain, nine show no significant gain or regress" (Section 7.3, p. 38).
  - A speed-up can come with a behaviour change. "In the other fourteen the merged fix introduces a functional change its description does not mention" (Section 7.3, p. 40).
  - The verdict depends on the workload size. "Eight fixes are slower than the base at one of the three sizes, and five of the eighteen that deliver gain only at the larger sizes." (Section 7.3, p. 38).
  - Maintainers rarely ask for a measurement. "Only 3% of rejection threads ask for a measurement" (Section 4.3, p. 22); "61%" of rejection threads state no reason (p. 22).
  - Agents' tests rarely check performance. "only 11% of all fixes include a performance test or benchmark" (Section 7.2, p. 37); the PR's own tests "pass unchanged on the base tree in 17 of the 28 fixes in which they run there" (p. 39).

- **Do not cite for:**
  - A population rate of false performance claims. They say the pilot "gives no population rate" (p. 45) and that the merged arm's 9 of 30 "may overstate the population's".
  - "Merged fixes hold more often than rejected ones." They forbid this comparison: the arms differ in sampling, repetitions and verdict rule (pp. 18, 39).
  - Any statement that they verified *why* a fix was faster or slower, or that they used profiling, hardware counters or kernel tracing. They did not. Mechanism findings come from reading diffs and from ad hoc counts.
  - "Agents' performance fixes are worse than human fixes." The only human comparison is acceptance and approval (Section 8.2), and the 27% vs 46% architectural share against Zhao et al., which they say are "two populations". No human fix was re-executed.
  - A causal claim such as "deleting code gets a PR merged". They state the results are "associations in observational data, not measured causes" (p. 24).
  - Numbers about AIDev in general (932,791 PRs; 2.7 million at v4). Cite the AIDev paper for those. Also do not say they used the same AIDev version as we do: they used v4 (with v3 for two side analyses).
  - The claim that performance tests do not help delivery. The 3 of 9 vs 15 of 21 comparison (p = 0.10) is explicitly not read as evidence in either direction (p. 39).
