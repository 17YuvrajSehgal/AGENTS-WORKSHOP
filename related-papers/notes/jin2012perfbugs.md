# Understanding and Detecting Real-World Performance Bugs
- **Authors:** Guoliang Jin, Linhai Song, Xiaoming Shi, Joel Scherpelz, Shan Lu (University of Wisconsin-Madison; a footnote says Scherpelz did the work as a graduate student there and now works at NVIDIA)
- **Venue / year / status:** PLDI '12 (ACM SIGPLAN Conference on Programming Language Design and Implementation), June 11-16, 2012, Beijing, China. Peer-reviewed. The PDF pages are numbered 77 to 87 (11 pages); `paper/refs.bib` lists pages 77-88.
- **PDF:** `related-papers/jin2012perfbugs.pdf`
- **Cite key:** jin2012perfbugs
- **BibTeX-style reference:** Guoliang Jin, Linhai Song, Xiaoming Shi, Joel Scherpelz, and Shan Lu. 2012. Understanding and Detecting Real-World Performance Bugs. In Proceedings of the 33rd ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI '12). ACM, 77-88.

## In short
The authors read 109 fixed performance bugs from five open-source suites (Apache, Chrome, GCC, Mozilla, MySQL) and sort them by root cause, by how they were introduced, by what input exposes them, and by how they were fixed. Most bugs fall into a few patterns (inefficient call combinations, calls that do unneeded work, too much locking) and most fixes are small (median 8 lines). They then turn 25 of the patches into static "efficiency rule" checkers and find 332 previously unknown problem sites in the latest versions of Apache, Mozilla and MySQL. The study is manual and qualitative. The authors did not measure the speed of the 109 bugs themselves; the slowdown numbers for those bugs come from the bug reports.

## Problem and motivation
- Performance bugs are common in released software and are hard to diagnose because nothing crashes. Example given: Mozilla developers "have fixed 5-60 performance bugs reported by users every month over the past 10 years" (Section 1.1, p. 77).
- Before this paper there were many empirical studies of functional bugs but, in the authors' words, no comprehensive study of performance bugs. Without one, tool builders did not know what the common root causes, triggers and fixes look like.
- Two questions: (1) what do real performance bugs look like across their life (introduced, exposed, fixed)? (2) can rules taken from old patches find new performance problems?

## Background / key terms (explain each term simply)
- **Performance bug (their definition):** "software defects where relatively simple source-code changes can significantly speed up software, while preserving functionality" (p. 77). So it is about wasted work that a small code change removes, not about a missing big redesign.
- **Functional bug:** a bug that gives wrong output or a crash. Used as the comparison group.
- **Root cause categories (Section 4.1):**
  - *Uncoordinated Functions:* each call is fine alone, but the combination is slow. Example: N database transactions in a loop where one batched transaction would do.
  - *Skippable Function:* a call does work whose result is not needed in this context. Example: drawing a transparent image.
  - *Synchronization Issues:* unneeded locking that makes threads wait for each other.
- **Workload mismatch:** the developer's idea of the typical input is wrong or has become outdated.
- **API misunderstanding:** the developer does not know a hidden cost of a function (for example that `random()` takes a global lock).
- **Always Active bug:** a bug that almost every input triggers (for example in start-up code).
- **Special Feature / Special Scale input:** the bug shows only with an input of a certain kind (feature) or a large enough size (scale).
- **Efficiency rule:** a pair of (condition, transformation). If code matches the condition, applying the transformation makes it faster and keeps behaviour the same.
- **PPP (potential performance problem):** a code site that breaks an efficiency rule and that the authors judged slower than the suggested alternative.
- **Lift:** a correlation measure between two categories. lift(A,B) = P(AB) / (P(A)P(B)). 1 means independent, above 1 means they tend to appear together, below 1 means they tend not to.
- **Chi-square test:** a statistical test for whether two groups (here server bugs and client bugs) fall into a category at different rates.
- **LLVM:** a compiler framework. The authors write checkers that scan LLVM bitcode (the compiler's internal form of the program).

## Method and setup
- **Applications (Table 1, p. 78):** Apache suite (HTTPD in C, TomCat and Ant in Java) 25 bugs; Chromium (C/C++) 10; GCC (C/C++) 10; Mozilla suite (Firefox and Thunderbird; C++, JavaScript) 36; MySQL suite (server and connectors; C/C++/Java/.Net) 28. Total 109.
- **How bugs were found (Section 2.2):** GCC, Mozilla and MySQL have developer tags for performance bugs (`compile-time-hog`, `perf`, `S5`). Apache and Chrome have no tag, so the authors searched with keywords ("slow", "performance", "latency", "throughput", etc.). From these they "randomly sampled 109 fixed bugs that have sufficient documentation".
- **Spread of the sample:** 44 reported after 2008, 38 between 2004 and 2007, 27 before 2004. 41 from server applications, 68 from client applications.
- **Manual study:** more than one year. Each bug studied by at least two people, in several rounds of re-study and cross-checking (Section 2.3). No agreement score is reported.
- **Statistics used:** counts per category (Table 2), lift for correlations, chi-square at the 0.01 level for server against client.
- **Checker experiment (Section 6):** 25 checkers (14 on LLVM for C/C++ rules, 11 Python scripts for Java, JavaScript and C# rules). Run on "an 8-core Intel Xeon machine running Linux version 2.6.18" (Section 6.4). Each checker is run on (1) the original buggy version, (2) the latest version of the same software, (3) for 13 checkers, the latest versions of different software.
- **Validation of PPPs:** "thorough code reviews and unit testings" (Section 1.3). Only two unit-test timings are printed (see below). The paper gives no table of measured slowdowns per PPP.

## Section-by-section notes

### 1. Introduction
- Figure 1: Apache bug 45464. After an API upgrade, `apr_stat(..., APR_DEFAULT)` started to retrieve more information from the file system than needed. The fix changes one parameter to `APR_TYPE`. Impact stated: the httpd server is "10+ times slower in file listing".
- Trends that make the problem worse: single cores are not getting faster, software and workloads get more complex, energy cost.
- Summary of findings and of the checker results (125 PPPs in original versions, 332 in latest versions, 219 of them cross-application).

### 2. Methodology
- See Method above. Section 2.3 "Caveats" is the paper's threats section. Key sentence: "we do not emphasize any quantitative characteristic results" (p. 79). The authors also say that unreported or unfixed problems cannot be studied, and that scientific computing and distributed systems are not covered.

### 3. Case studies (four example bugs)
- **Transparent Draw (Mozilla 66461, Fig. 2):** `nsImage::Draw` did scaling and rendering even for transparent images. It became a problem two years later, when 1x1 transparent GIFs were widely used as spacers. Fix: return early when the image is transparent.
- **Intensive GC (Mozilla 515287, Fig. 3):** Firefox ran a garbage collection after every XMLHttpRequest. Users reported about 10 times more CPU than Safari on pages like Gmail. Fix: remove the GC call.
- **Bookmark All (Mozilla 490742, Fig. 4):** N database transactions to bookmark N tabs; Firefox hung with 20 open tabs. Fix: one aggregated transaction.
- **Slow Fast-Lock (MySQL 38941, Fig. 5):** `fastmutex_lock` called `random()`, which holds a global lock inside glibc. Users' unit test showed it "could be 40 times slower than normal locks". Fix: a random generator without a lock.
- The point of these four: the bugs are about API and function usage (like functional bugs), but several became bugs only after the workload changed, and ordinary functional tests would not expose them.

### 4. Characteristics study (Table 2)
- **4.1 Root causes:** Uncoordinated Functions 42, Skippable Function 34, Synchronization Issues 12, Others 23. Performance is "mostly lost at call sites and function boundaries". Synchronization: 4 of 15 Apache server bugs and 5 of 26 MySQL server bugs. "Others" includes wrong data structures, hardware architecture issues, and design or algorithm issues with long propagation chains (example MySQL 39295: wrongly invalidating the query cache, which costs time only later through cache misses). The "Others" type is said to be especially common in GCC.
- **4.2 How introduced:** Workload Issues 41, API Issues 31, Others 38. "29 out of 109 bugs were not born buggy": they became slow after a workload shift or a code change elsewhere (Fig. 1, Chrome 70153 when GPU acceleration arrived). Some performance bugs are side effects of functional bugs (Mozilla 196994, a busy flag never reset).
- **4.3 How exposed:** Always Active 15, Special Feature 75, Special Scale 71, both Feature and Scale 52. "Judging whether performance bugs have manifested is a unique challenge in performance testing." Many always-active bugs were found by comparing with other software (Chrome against Mozilla against Safari).
- **4.4 How fixed:** Change Call Sequence 47, Change Condition 35, Change A Parameter 13, Others 23. "42 out of 109 bug patches contain five or fewer lines of code changes. The median patch size for all examined bugs is 8 lines of code." 33 of the 47 call-sequence patches use only functions that already existed. MySQL 45475 was fixed by changing a configuration parameter from 64 to 400.
- **4.5 Other characteristics:**
  - *Life time (Mozilla only):* the 36 Mozilla performance bugs took 935 days on average to be discovered and another 140 days to be fixed. 36 randomly sampled Mozilla functional bugs took 252 days to be discovered and 117 days to be fixed.
  - *Location:* over three quarters are inside an input-dependent loop or an input-event handler. About 40% contain a loop whose iteration count grows with input. "about half performance bugs involve I/Os or other time-consuming system calls" (p. 82).
  - *Correlations (lift):* Skippable Function with Change Condition 2.02; Workload Issues with Change A Parameter 1.84; Uncoordinated Functions with API Issues 1.76; Synchronization Issues with Change Condition 0.26.
  - *Server against client:* only Synchronization Issues differ significantly (22% of server bugs, 4.4% of client bugs; chi-square, 0.01 level).

### 5. Lessons
- Compared with functional bugs: performance bugs hide much longer, can appear in old correct code when the software or workload changes, and are not all rare events.
- Testing: regression tests must consider workload changes. Performance tests need inputs with both the right feature and a large scale. "Expressing performance oracles and judging whether performance bugs have occurred are critical challenges in performance testing".
- Diagnosis: "It is difficult to use profiling alone to locate the root cause of a performance bug that has a long propagation chain or wastes computation time at function boundaries, which is very common".
- Annotations: APIs should document performance features (locks inside, complexity, good parameter ranges).

### 6. Rule-based performance-bug detection
- **6.2:** 50 of the 109 patches contain an efficiency rule; 59 do not (too specific or too general). Table 3 lists typical rule conditions: call-sequence conditions (for example "function f1 is called once in each iteration of a loop"), parameter and return conditions, calling-context conditions.
- **6.3:** Apache, MySQL and Mozilla give 40 rule patches; 25 have conditions that are mostly statically checkable. These became the 25 checkers. LLVM checkers do intra-procedural data-flow analysis (inside one function only), which "may lead to false positives and negatives".
- **6.4:** results are sorted into PPPs, bad practices (code likely to become slow later) and false positives. A changed version of each checker also counts good practices (code that follows the rule).
- **6.5 Results (Table 4):**
  - Original buggy versions: 125 PPPs, found by 17 of the 25 checkers. 113 of the 125 are in other files or modules than the original bug. Later fate of the 125: 4 fixed in later versions (after 14 to 31 months), 20 disappeared because the code was removed or rewritten, 101 still in the latest version (12 to 89 months after the original fix).
  - Latest version of the same software: 23 checkers still apply; 113 PPPs (101 inherited, 12 newly introduced).
  - Latest versions of different software: 8 of 13 cross-application checkers found PPPs; 219 in total. The Apache 32546 rule (small read buffer) alone found 135 sites in 36 applications, with buffers of 1 KB to 4 KB.
  - 14 PPPs (from 6 checkers) were confirmed and fixed by developers after the authors reported them.
  - False positives: "the false-positive-vs-PPP rate is 1:4". Sources: no type information in the Python checkers, rules that are hard to express, and rules that need run-time or workload information.
  - Checker speed: each Python checker scans 10 million lines in 90 seconds; one LLVM checker takes 4 to 1270 seconds per application.
  - Unit-test timings printed: reading with a 4 KB buffer against a 40K buffer gives a stable 3 times throughput gain; on a 50 MB file the file operation time goes from 0.87 s to 0.26 s. A Struts fix on a 15K JSP file cuts latency by 0.1 s. In the original Apache 32546 report, developers got an 80 times throughput gain in a WebDav server by going from a 2 KB to a 200 KB buffer.
  - "Whole system testing turns out to be difficult". No PPP found by the checkers is in the always-active category.
- **6.6 Discussion:** copy-paste detectors would miss most PPPs; compilers could not remove any of the rule bugs; tools that infer rules from "what most code does" may fail because violations are not rare (Table 4 shows many violations next to good practices).

### 7. Related work, 8. Conclusions
- Related work covers HPC performance tools, profiling-based diagnosis, performance debugging in distributed systems, performance testing (mostly black-box), and tools for functional correctness.
- Conclusion: one of the first studies of real performance bugs; rule-based detection finds many unknown problems. More material at the authors' web page (URL in the paper).

## Key results (with numbers) and what they mean
- 42 + 34 of 109 bugs are inefficient call combinations or skippable calls -> most wasted time sits at call sites, and the fix is "call less" or "call something cheaper". This is the same family as claims like "batch the writes" or "skip the call when not needed".
- 12 of 109 are synchronization issues, 22% of server bugs -> lock waits are a real and separate class, mostly in servers.
- About half involve I/O or other time-consuming system calls -> for about half of real performance bugs, the waste should be visible at the system-call level. The paper states this as a count from reading code; it does not measure system calls.
- 75 need a special input feature, 71 need large scale, 52 need both, only 15 are always active -> most performance bugs do not show under an arbitrary input. A test that does not hit the right feature and scale will see no difference.
- 29 of 109 were not born buggy -> code can become slow without changing, when the workload changes.
- Median patch 8 lines, 42 patches of 5 lines or fewer -> big speedups can come from very small diffs, so patch size says little about effect size.
- 935 days to discover against 252 for functional bugs (Mozilla, averages) -> performance problems stay unnoticed about 3.7 times longer in this sample. Only averages are given, no medians or spread.
- 332 new PPPs in latest versions, 219 from rules of another application, 1 false positive per 4 PPPs -> the same efficiency mistake repeats across places, developers and projects.
- 101 of 125 sibling PPPs still present 12 to 89 months later -> developers fix the reported site and miss the others.

## Tables and figures
- **Table 1 (p. 78):** suites, languages, bug counts (25, 10, 10, 36, 28; total 109).
- **Table 2 (p. 81):** the main table. Per-application counts for root cause, how introduced, how exposed, how fixed. Read: categories inside one block are not exclusive (the caption says so), so rows can sum to more than 109. Per-application rows, in the order Apache / Chrome / GCC / Mozilla / MySQL / Total:
  - Uncoordinated Functions 12 / 4 / 2 / 15 / 9 / 42. Skippable Function 6 / 4 / 3 / 14 / 7 / 34. Synchronization 5 / 1 / 0 / 1 / 5 / 12. Others 3 / 1 / 5 / 6 / 8 / 23.
  - Workload Issues 13 / 2 / 5 / 14 / 7 / 41. API Issues 6 / 3 / 1 / 13 / 8 / 31. Others 6 / 5 / 4 / 10 / 13 / 38.
  - Always Active 2 / 3 / 0 / 6 / 4 / 15. Special Feature 19 / 6 / 10 / 22 / 18 / 75. Special Scale 17 / 2 / 10 / 23 / 19 / 71. Feature+Scale 13 / 1 / 10 / 15 / 13 / 52.
  - Change Call Sequence 10 / 2 / 3 / 20 / 12 / 47. Change Condition 2 / 7 / 6 / 10 / 10 / 35. Change A Parameter 5 / 0 / 1 / 4 / 3 / 13. Others 9 / 3 / 0 / 4 / 7 / 23.
- **Table 3 (p. 83):** typical conditions in function rules (call sequence, parameter/return, calling context).
- **Table 4 (p. 85):** per-checker results for the three targets. Totals: original version 125 PPP, 29 bad practice, 41 false positives, 252 good practice; latest version of the same software 113, 27, 30, 191; latest version of different software 219, 49, 46, 94. I re-added the PPP columns from the rows and they match the totals. Read: MySQL 14637 (50, 49, 46) and Apache 32546 (135 cross-application) dominate, so the totals depend strongly on two rules.
- **Fig. 1 (p. 77):** Apache 45464 patch.
- **Figs. 2-5 (p. 79):** the four case-study patches. Some text in these figures is garbled in the PDF itself.
- **Fig. 6 (p. 85):** two PPPs the authors found (MySQL `ismbchar` length computation; Struts `indexOf` rescanning) next to the original patches the rules came from.

## Ideas we can use
- **A vocabulary for mechanisms.** Their root causes and fix strategies map onto the claims agents make: "batch the calls" (Uncoordinated Functions, Change Call Sequence), "skip the work" (Skippable Function, Change Condition), "remove the lock" (Synchronization Issues), "change the buffer size or setting" (Change A Parameter). We can name our mechanism classes with reference to these.
- **Mechanism to kernel signal.** Their examples give clean pairs: `apr_stat` parameter -> less file-system metadata work; small read buffer -> fewer `read` calls for the same bytes; N transactions -> fewer commits (fsync/write); `random()` global lock -> less lock wait (futex). The paper names the mechanisms but never checks the signal. That is our step.
- **Workload must hit feature and scale.** Section 4.3 is a direct warning for our build agent's workload: 52 of 109 bugs need both a special feature and a large scale.
- **Small diff, large effect.** Useful when arguing that patch size cannot stand in for measurement.

## Weaknesses and things glossed over
- No measurement of the 109 bugs. Slowdowns ("10+ times", "40X", "10X more CPU") are taken from bug reports and users' own tests. Nothing was re-run under controlled conditions.
- Selection: only fixed bugs "that have sufficient documentation", and for Apache and Chrome only those that match keywords. Well-documented, clear-cut bugs are likely over-represented.
- The category labels are manual. Two people per bug, but no agreement statistic. Categories overlap, so percentages cannot be added.
- The authors themselves say not to lean on the quantities ("we do not emphasize any quantitative characteristic results"). Later papers often quote the fractions anyway.
- Life-time numbers are Mozilla only, averages only, 36 against 36 bugs, no test of significance.
- "About half involve I/Os or other time-consuming system calls" is one sentence with no table and no definition of "time-consuming".
- PPP validation: "confirms that each PPP runs significantly slower" but only two timing examples are printed, no method for the unit tests (repetitions, machine state, variance), and whole-system tests were not done. Only 14 of the 332 were confirmed by developers; other reports were "put on hold due to lack of bug-triggering input information".
- Totals in Table 4 are driven by two rules (MySQL 14637 and Apache 32546).
- The false-positive rate is an average over all checkers; per-checker it ranges widely (for example Mozilla 35294: 5 PPPs and 10 false positives).
- Software from 2012 and before, mostly C/C++ and Java. No Python, Go or Rust projects.

## Open questions and future work (theirs, and ours)
- Theirs: generate efficiency rules automatically; combine static checks with dynamic analysis and workload monitoring; input generators that aim at performance; performance-aware API annotations; performance oracles for testing.
- Ours: do agent-written performance PRs fall into the same few classes? Does the claimed class predict which kernel signal moves? How often does a PR in the "skippable function" class show no change because the workload does not reach the special input?

## Link to our paper
- The key `jin2012perfbugs` is in `paper/refs.bib`. I found no `\cite` of it in the `.tex` files under `paper/` when writing this note.
- Natural places: Background or Related Work, where we say that real performance fixes follow a small set of mechanisms and are usually small patches; and Threats, where we say that a workload may not trigger the changed path.
- See the section "Connection to Below the Stopwatch" below for the exact statements this paper supports.

## Link to the thesis (tracing, kernel analysis)
- The paper says where time is lost (call sites, function boundaries, loops over input, I/O and system calls, lock waits) but uses no tracing at all. Each of its example bugs has a clear low-level signature that `perf`, LTTng or eBPF can observe: syscall counts per operation, futex wait time, CPU time in GC.
- Their remark that profiling alone struggles with long propagation chains (MySQL 39295: a cheap invalidation causes cache misses later) is an argument for causal, trace-based analysis instead of flat profiles.
- The server finding (22% synchronization bugs) points to off-CPU and wait analysis as the right tool for server workloads.

## Quotes for inline citation
- "we refer to performance bugs as software defects where relatively simple source-code changes can significantly speed up software, while preserving functionality." (p. 77)
- "performance testing mainly relies on ineffective black-box random testing and manual input design, which allows the majority of performance bugs to escape" (p. 77)
- "performance is mostly lost at call sites and function boundaries" (p. 80)
- "29 out of 109 bugs were not born buggy." (p. 80)
- "Judging whether performance bugs have manifested is a unique challenge in performance testing." (p. 81)
- "Almost half of the bugs need inputs that have special features and large scales to manifest." (p. 81)
- "42 out of 109 bug patches contain five or fewer lines of code changes. The median patch size for all examined bugs is 8 lines of code." (p. 81)
- "about half performance bugs involve I/Os or other time-consuming system calls." (p. 82)
- "Expressing performance oracles and judging whether performance bugs have occurred are critical challenges in performance testing" (p. 82)

## Suggested citation sentences
- Studies of human-written fixes show that real performance bugs fall into a few recurring mechanisms, such as inefficient call combinations, skippable calls and unnecessary synchronization \cite{jin2012perfbugs}.
- Performance fixes are often very small: in a sample of 109 real bugs the median patch was 8 lines \cite{jin2012perfbugs}, so the size of a PR says little about its effect.
- Most performance bugs need an input with a special feature, a large scale, or both before they show \cite{jin2012perfbugs}; a workload that misses this input will report no change.
- About half of the performance bugs in that sample involve I/O or other time-consuming system calls \cite{jin2012perfbugs}, which is why we look for the claimed mechanism at the system-call level.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It gives the classic taxonomy of performance-fix mechanisms from human-written patches. Our mechanism classes (cache, batch, skip, remove lock, change parameter) can be anchored to its root causes and fix strategies.
  - It stops at reading patches and bug reports. It never checks that the claimed mechanism happened at run time, and it never measures at the kernel or hardware level. We do both, per PR, with an A/A control.
  - It weakens one part of our approach: 75 of 109 bugs need a special input feature and 71 need large scale (52 need both). A workload written by a build agent that never sees the claim may miss the feature or the scale. In that case "not faster" and "mechanism did not happen" can be a workload miss, not a wrong claim. We need to say this in Threats and, where possible, check that the changed code is executed.
  - It also says that judging whether a performance problem has shown up is itself hard (Section 4.3, Section 5). This supports our use of mechanism signals next to timing, but it is a statement of difficulty, not evidence that our signals are right.
- **Safe to cite for:**
  - A definition of performance bugs as defects where "relatively simple source-code changes can significantly speed up software, while preserving functionality" (Section 1.1, p. 77).
  - Real performance bugs cluster in a few mechanisms: Uncoordinated Functions 42, Skippable Function 34, Synchronization Issues 12 of 109 (Section 4.1, Table 2, p. 81). Performance "is mostly lost at call sites and function boundaries" (p. 80).
  - Fixes are small and follow a few strategies: Change Call Sequence 47, Change Condition 35, Change A Parameter 13; "The median patch size for all examined bugs is 8 lines of code" (Section 4.4, p. 81).
  - Many bugs show only under specific inputs: "Almost half of the bugs need inputs that have special features and large scales to manifest" (Section 4.3, p. 81; Table 2: 52 of 109).
  - A large share touch the operating system: "about half performance bugs involve I/Os or other time-consuming system calls" (Section 4.5, p. 82). Cite as their observation from code reading, not as a measurement.
  - Deciding whether a performance problem occurred is hard: "Expressing performance oracles and judging whether performance bugs have occurred are critical challenges in performance testing" (Section 5, p. 82).
- **Do not cite for:**
  - Any claim that performance fixes or developers' performance claims are often wrong. The paper studies fixed bugs and accepts the reported speedups.
  - Any measured effect of the 109 fixes. The numbers (10+ times, 40X, 10X CPU) come from bug reports, not from the authors' experiments.
  - Kernel tracing, hardware counters or system-call measurement. None is used.
  - Exact population rates ("X% of all performance bugs are ..."). The sample is 109 documented, fixed bugs from five suites, and the authors say they do not emphasize quantitative results.
  - "Performance bugs take longer to fix." Their own numbers show the opposite for fix time: 140 days against 117 days is called "a similar amount of time". What is longer is the time to be discovered (935 against 252 days, Mozilla only, averages).
  - Anything about AI agents, pull requests or code review.
  - That static rule checkers are precise in general. The 1:4 false-positive rate is for 25 hand-built checkers on three suites.
