# A Qualitative Study on Performance Bugs
- **Authors:** Shahed Zaman, Ahmed E. Hassan (SAIL, Queen's University, Canada), Bram Adams (MCIS, École Polytechnique de Montréal, Canada)
- **Venue / year / status:** MSR 2012 (9th IEEE Working Conference on Mining Software Repositories), Zurich, Switzerland. Peer-reviewed. Pages 199-208.
- **PDF:** `related-papers/zaman2012perfbugs.pdf`
- **Cite key:** zaman2012perfbugs
- **BibTeX-style reference:** Shahed Zaman, Bram Adams, and Ahmed E. Hassan. 2012. A Qualitative Study on Performance Bugs. In Proceedings of the 9th IEEE Working Conference on Mining Software Repositories (MSR 2012). IEEE, 199-208.

## In short
The authors read 400 bug reports by hand: 100 performance and 100 non-performance bugs from Mozilla Firefox, and the same from Google Chrome. They tag each report on 19 points in four groups (impact, context, fix, fix validation) and compare performance with non-performance bugs. Performance bugs are discussed more before a fix, are harder to reproduce and more often block a release in Firefox, and are far more often regressions in Chrome. Only about one third of performance bug reports contain any measured number. Some performance regressions are accepted on purpose as a trade-off. Most differences are significant in only one of the two projects.

## Problem and motivation
- Earlier work by the same authors (reference [10], MSR 2011, Firefox only) found with numbers that performance bugs take longer to fix ("at least 32% more on average"), are fixed by more experienced developers and need larger changes.
- Those numbers did not say why. This paper reads the reports, comments and patches to find explanations and practical advice for handling performance bugs.

## Background / key terms (explain each term simply)
- **Performance bug (their use):** "performance problems like high resource utilization or slow response time" (p. 199).
- **Regression bug:** a problem brought back or newly caused by a later change (upgrade, another patch), usually found by a failing test.
- **Release blocking bug:** a bug marked as one that must be fixed before a release ships.
- **WFM (WorksForMe):** a Mozilla closing status meaning the developer could not reproduce the problem. Chrome uses "WontFix" or "Invalid" instead.
- **Qualitative study:** reading and tagging text by hand, instead of computing metrics automatically.
- **Sub-dimension:** one of the 19 tags (for example "Measurement used", "Problem in reproducing").
- **Confidence interval of 10 at 95% confidence:** a sample of about 96 reports gives a percentage that is within plus or minus 10 points of the true value, 95% of the time.
- **Joint confidence interval / comparative error:** the test they use to decide if two percentages differ. If the gap between the two percentages is larger than the combined error, they call it significant.
- **Precision / recall of the heuristic:** precision = of the bugs the keyword search calls "performance", how many really are. Recall = of the real performance bugs, how many the search finds.
- **buildbot / tinderbox:** the continuous integration servers of Chromium and Mozilla. Chromium's buildbot runs automatic performance tests.

## Method and setup
- **Data (Section II.A):** Mozilla Bugzilla from September 9, 1994 to August 15, 2010; the tracker holds 567,595 reports for all Mozilla components, of which they take Core and Firefox. Chrome issue tracker from August 30, 2008 to June 10, 2010 (the MSR Challenge 2011 dump).
- **Finding performance bugs (Section II.B):** tags exist ("perf" keyword in Bugzilla, "performance" label in Chrome) but are optional and often missing. So they search the title and keyword field for "perf", "slow" and "hang", and exclude "perfect", "performing", "performed".
  - Firefox: 7,603 bugs classed as performance (4.14% of 183,660). Chrome: 510 (1.13% of 44,997).
  - Check of the heuristic on samples. Firefox: 95 predicted-performance and 96 predicted-non-performance bugs; precision 100 ± 10%, recall 83.3 ± 10%. Chrome: 81 and 96; precision 90.12 ± 10%, recall 97.33 ± 10%.
- **Sampling (Section II.C):** 100 random reports from each of the four groups. The largest group (Firefox non-performance, 176,057 bugs) needs 96 for a ±10% interval; they use 100 everywhere.
- **Tagging (Section II.D):** "The first author studied each sampled bug report" and tagged it. Tags were added until a stable set of 19 was reached, then grouped into 4 dimensions.
- **Statistics:** percentage per group, compared with the comparative-error test above. The source for the test is an unpublished briefing note (reference [13]). No p-values, no correction for running 19 tests on 2 projects.

## Section-by-section notes

### I. Introduction
- States the four headline findings (repeated in Section III below).

### II. Case study approach
- Fig. 1: pipeline (bug repository -> classification -> random sample of 100 + 100 -> choose dimensions -> analysis).
- Table I: the taxonomy. Impact: Regression, Blocking, WorksForMe after a long time, People talking about switching. Context: Measurement used, Has test cases, Contains stack traces, Has reproducible info, Problem in reproducing, Duplicate bug, Improvement suggestion, Reported by a project member. Fix: Problem discussion in comments, Dependent on other bug, Other bugs depend on this bug, Reporter has some hint on the actual fix, Patch uploaded by. Fix validation: Discussion about the patch (technical / non-technical), Review, Super-review.
- Table II: confusion matrix of the heuristic (see Tables and figures).

### III.A Impact on the stakeholder
- **Regression:** Chrome 22% of performance bugs against 3% of non-performance bugs (significant). Firefox 19% against 13% (not significant).
  - Chrome regressions are mostly reported by project members from the automated build and test cycle, with links to generated graphs. Most Firefox regressions were reported after users were affected.
- **"Not all regressions are unexpected."** Some regressions are known and accepted because of a trade-off. Chrome bug 7992 (closed WontFix), comment 3: recent changes "tilted the tuning toward memory usage instead of speed. If you look at the memory usage, you'll see a corresponding drop where the perf slows down."
- **"Performance improvement may cause regression."** Firefox bug 449826 was filed as a possible speed improvement; "the resulting performance ended up being much slower" and the bug was still open since September 2008.
- **Release blocking:** Firefox 14% against 4% (significant). Chrome 8% against 4% (not significant).
- **Closed as WFM / Fixed / Won't Fix after a long time** (months, often more than a year): Firefox 19% against 6% (significant). Chrome 10% against 9% (not significant). For these bugs nobody recorded what fixed them or why they will not be fixed.
- **Users threatening to switch browser:** Firefox 8% against 1% (significant). Chrome 7% against 2% (not significant). The next paragraph says "7 users threatening to leave Firefox", which does not match 8% of 100. The paper does not explain the difference.
- **Comparison with other browsers:** some Chrome bugs were closed WontFix only because other browsers have the same problem (Chrome bug 441).

### III.B Context of the bug
- **Measurements:** 34% of Firefox and 36% of Chrome performance bug reports or comments contain a measurement (CPU usage, disk I/O, memory usage, time for an operation, profiler output; in Chrome also values from the automated performance tests). No non-performance bug had one.
- **Test case:** Firefox 32% against 16% (significant). Chrome 21% against 16% (not significant). More than 70% of test cases come from the reporter.
- **Stack trace:** the bold heading says 10% of performance and 1% of non-performance bugs contain a stack trace "[Chrome]". The text right under it says that in Chrome the numbers are 13% and 8% with no significant difference. I checked the page image (p. 204): the heading and the text disagree in the paper itself. The 10% and 1% are most likely the Firefox numbers, but the paper does not say so. Do not cite these numbers.
- **Problems reproducing:** Firefox 15% against 6% (significant). Chrome 16% against 8% (not significant). Causes named: missing information, no test case, a specific extension or plugin version, intermittent problems.
- **Reported by a project member (Chrome only):** 58% against 35%. Of the 22% that are performance regressions, more than 86% were reported by a project member.
- **External programs:** 11% of Firefox and 14% of Chrome performance bugs are caused by software outside the project (add-ons, plugins such as Flash, one web page, antivirus).
- **Duplicates:** fewer for performance bugs. Firefox 26% against 40% (significant). Chrome 24% against 32% (not significant).
- No significant difference for "steps to reproduce" or "improvement suggestion".

### III.C The bug fix
- **Discussion before a fix:** 47% of Firefox and 41% of Chrome performance bugs needed a real discussion of the problem in the comments, against 25% of non-performance bugs in both projects. Comments like "it happens to me too" are not counted.
- **Dependencies (Table III, counts out of 100):** Firefox performance bugs: 44 blocking, 42 depends-on. Firefox non-performance: 27 and 15. Both differences significant. Chrome: 2 and 6 against 6 and 4, not significant.
- **"Patches are not always used for fixing a bug."** In Chromium the performance tests compare each metric with an expectation baseline stored in a file (`perf_expectations.json`) with "improve" and "regress" values. The script reports both "performance regression" and "unexpected speedup" (bug 18597, comment 11). Many patches only changed this baseline after a real speedup or an accepted regression. "For accepted regressions, the corresponding bug is no longer a bug, but expected behavior." Some patches exist only for troubleshooting (bug 34926, comment 9).
- No significant difference for "reporter has a hint about the fix" or "patch uploaded by".

### III.D Bug fix validation
- No significant difference between performance and non-performance bugs in patch discussion, review or super-review, in either project.

### IV. Discussion
- Table IV links the earlier numeric findings to the new ones. Longer fix time <- WFM after a long time, problems reproducing, more dependencies, collaborative root-cause analysis. More experienced fixers <- more release blocking, people switching. Larger changes <- no qualitative support found ("N/A").
- A caution on their own earlier result: 19% of Firefox performance bugs were closed after a long time with no trace of a fix, so the average fix time "might have been inflated".
- "Our findings for Firefox and Chrome performance bugs were different in most of the cases."

### V. Threats to validity
- One person (the first author) did all tagging. He "took care to consider all available bug data sources and to double-check findings when in doubt".
- The tag set comes from these two projects and may miss dimensions.
- Two projects, both browsers; results may not transfer.
- Performance bugs are found by a keyword heuristic.

### VI. Related work, VII. Conclusion
- Related work: qualitative studies of bug trackers; work on detecting performance bugs.
- Four recommendations: better "steps to reproduce"; better ways to find the root cause; support for collaborative root-cause analysis; and "The impact of changes on performance should be analyzed, e.g., by linking automated performance test results to commits, such that performance bugs no longer magically (dis)appear."

## Key results (with numbers) and what they mean
- Only 34% (Firefox) and 36% (Chrome) of performance bug reports have a measured number -> about two thirds of performance problems are discussed without any measurement at all. With ±10 points of sampling error.
- Chrome: 22% of performance bugs are regressions against 3% of others -> where automated performance tests run on every build, most performance reports come from those tests. This is partly an effect of how Chrome finds bugs, not only of what performance bugs are.
- Firefox: 15% against 6% have reproduction problems -> performance bugs are harder to reproduce there. In Chrome the same gap (16% against 8%) did not pass the test, so the general claim rests on one project.
- 47% and 41% against 25% need a discussion -> finding the cause of a performance bug is more of a group effort. This is the only fix-related result significant in both projects.
- Firefox: 19% against 6% closed after a long time with no recorded cause -> performance problems appear and disappear without anyone knowing which change did it. This is the motivation for their last recommendation (link performance tests to commits).
- Accepted regressions (Chrome bug 7992) -> "slower" is sometimes a chosen trade-off for less memory. A speed number alone does not tell whether a change is good.
- Firefox bug 449826 -> a change meant to make things faster can make them slower.

## Tables and figures
- **Fig. 1 (p. 200):** the study pipeline.
- **Table I (p. 201):** taxonomy of 4 dimensions and 19 sub-dimensions. Bold marks a significant difference in at least one project.
- **Table II (p. 201):** confusion matrix. Firefox: predicted performance row 95 actual performance, 0 actual non-performance; predicted non-performance row 19 actual performance, 77 actual non-performance. Chrome: 73 and 8; 2 and 94. Read: precision is the first row (95/95, 73/81). Recall is the first column (95/(95+19) = 83.3%, 73/(73+2) = 97.33%).
- **Table III (p. 205):** blocking and depends-on counts (Firefox 44/42 against 27/15; Chrome 2/6 against 6/4).
- **Table IV (p. 206):** mapping of earlier quantitative findings to the qualitative ones.

## Ideas we can use
- **Claims without numbers are normal.** In human bug trackers only about a third of performance reports have a measurement. This is a baseline when we describe how agent PRs state their performance claims.
- **Trade-offs.** The Chrome memory-against-speed case is a clean example of a "hidden cost" that a stopwatch misses. It supports reporting more than one signal per PR.
- **Expectation baselines.** Chromium's `perf_expectations.json` flags both regressions and unexpected speedups. Our A/A control plays a similar role: decide how large a change must be before it counts.
- **Link performance to the commit.** Their last recommendation is what a per-PR check does.

## Weaknesses and things glossed over
- One coder, no second rater, no agreement score.
- 100 reports per group gives ±10 points. Many gaps of 5 to 8 points are "not significant" only because the sample is small, and the paper then reports the significant project in the headline.
- 19 sub-dimensions times 2 projects are tested with no correction for multiple tests. Some "significant" results can be chance.
- The significance test is taken from an unpublished note. No p-values are given.
- The recall figures are computed from two samples of about equal size, as if performance and non-performance bugs were equally common. They are not (4.14% and 1.13%). In the Firefox sample 19 of 96 "non-performance" bugs were really performance bugs. Applied to 176,057 bugs, that is far more missed performance bugs than the 7,603 found, so the real recall would be much lower than 83.3%. This is my own arithmetic, not a statement in the paper. It also means the Firefox "non-performance" comparison group may contain roughly one fifth performance bugs, which would shrink the measured differences.
- Internal inconsistencies: the stack-trace heading against its text (p. 204); "7 users" against 8% (p. 203).
- The abstract states the reproduction and discussion findings without saying that the reproduction result holds only for Firefox.
- Several Chrome results reflect Chrome's process (automated tests, members filing bugs), not the nature of performance bugs.
- Data ends in 2010. Both projects have changed their tooling since.
- No measurement of any kind is done by the authors. Everything is what reporters and developers wrote.

## Open questions and future work (theirs, and ours)
- Theirs: repeat on other open-source systems in the browser domain and in other domains.
- Ours: how often do agent PRs include a measurement, and is that share above or below the one third seen here? When an agent PR trades memory or I/O for speed, does the PR text say so?

## Link to our paper
- The key `zaman2012perfbugs` is in `paper/refs.bib`. I found no `\cite` of it in the `.tex` files under `paper/` when writing this note.
- Natural places: Introduction or Motivation (performance claims are usually made without numbers and are hard to reproduce); Discussion of hidden costs (accepted regressions as trade-offs); Related Work on empirical studies of performance bugs.
- See "Connection to Below the Stopwatch" below for the supported statements.

## Link to the thesis (tracing, kernel analysis)
- The measurements people put in reports are coarse: CPU usage, disk I/O, memory, time for an operation, profiler output. No report-level use of kernel traces is described. Fine-grained tracing is absent from the practice the paper observes.
- Reproduction problems and "fixed out of the blue" bugs are what always-on, low-overhead tracing is meant to help with: capture the evidence when the problem happens, so it does not depend on reproducing it later.
- 11% and 14% of performance bugs came from outside programs (plugins, antivirus). System-wide kernel tracing can attribute time to another process; application-level profilers cannot.

## Quotes for inline citation
- "We found that developers and users face problems in reproducing performance bugs and have to spend more time discussing performance bugs than other kinds of bugs. Sometimes performance regressions are tolerated as a trade-off to improve something else." (abstract, p. 199)
- "34% of the Firefox and 36% of the Chrome performance bugs contain performance measurements." (p. 204)
- "Not all regressions are unexpected." (p. 202)
- "Performance improvement may cause regression." (p. 202)
- "Often, the performance bug was tolerated because of a trade-off with a more essential performance feature." (p. 202)
- "For accepted regressions, the corresponding bug is no longer a bug, but expected behavior." (p. 206)
- "The impact of changes on performance should be analyzed, e.g., by linking automated performance test results to commits, such that performance bugs no longer magically (dis)appear." (p. 208)

## Suggested citation sentences
- In human bug trackers, only about one third of performance bug reports contain any measurement \cite{zaman2012perfbugs}.
- Performance problems are harder to reproduce and need more discussion to diagnose than other bugs \cite{zaman2012perfbugs}.
- A change that is slower is not always wrong: developers sometimes accept a regression as a trade-off, for example for lower memory use \cite{zaman2012perfbugs}. We therefore report hidden costs next to timing.
- Changes meant as optimizations can themselves cause regressions \cite{zaman2012perfbugs}.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It describes how humans report and argue about performance: mostly without numbers, with trouble reproducing, and with fixes that nobody can trace to a change. Our pipeline is an automated answer to that: rebuild both versions, measure, and tie the result to one PR.
  - It reads text only. It does not rebuild or run anything, and it does not check whether any claimed fix made the code faster. We do.
  - It has two points that complicate a simple "faster or not" verdict, and we should be honest about them. First, regressions are sometimes accepted on purpose (memory against speed). So our verdict "not faster" or "hidden cost" is a fact about the measurement, not a judgment that the PR is bad. Second, the paper shows that reproducing performance problems is hard even for the project's own developers. A build agent with no access to the claim may fail to reproduce the setting where the PR matters.
  - Nothing in it contradicts our method. It also gives no evidence for it: it contains no measurements.
- **Safe to cite for:**
  - Only about a third of performance bug reports include a measurement: "34% of the Firefox and 36% of the Chrome performance bugs contain performance measurements" (Section III.B, p. 204). Say "in Firefox and Chrome bug reports", with a ±10 point sampling error.
  - Performance bugs need more discussion to resolve: 47% (Firefox) and 41% (Chrome) against 25% (Section III.C, p. 205).
  - Reproduction is harder for performance bugs in Firefox: 15% against 6% (Section III.B, p. 204). Name the project; the Chrome difference was not significant.
  - Regressions can be accepted trade-offs: "Sometimes performance regressions are tolerated as a trade-off to improve something else" (abstract, p. 199; example Chrome bug 7992, p. 202).
  - An intended optimization can make things slower: "Performance improvement may cause regression" (Section III.A, p. 202; Firefox bug 449826). This is one example, not a rate.
  - The call to connect performance results to individual changes: "by linking automated performance test results to commits" (Conclusion, p. 208).
- **Do not cite for:**
  - "Performance bugs take longer to fix / need more experienced developers / larger patches." Those results are from their earlier paper (reference [10], MSR 2011), which this paper only summarizes.
  - Any rate of wrong or unverified performance claims. The paper does not check claims.
  - "Performance bugs are harder to reproduce" as a general fact across projects. It is significant in Firefox only.
  - "Performance bugs are mostly regressions." 22% in Chrome and 19% in Firefox; only the Chrome gap to non-performance bugs is significant.
  - The stack-trace numbers (10% against 1%); the paper is inconsistent about which project they belong to.
  - Root causes or fix patterns of performance bugs. That is jin2012perfbugs, not this paper.
  - Anything about tracing, profilers' accuracy, or measurement method.
  - Anything about AI agents or pull requests. The data are 2010-era bug reports.
