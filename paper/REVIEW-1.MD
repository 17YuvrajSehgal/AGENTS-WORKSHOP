**Short answer:** The idea is strong and fits AGENT well. As written, I would score it **weak accept**. My rough guess is a 60 to 70% chance, but I'm not sure, because workshop decisions depend a lot on who reviews it. Two problems could pull it down to borderline: the 41/79 output-change confound, and the claim that kernel signals "check the mechanism" when several of them really just measure "it got faster."

**Deadline first.** The submission deadline is 20 November 2026 (extended), and the page says it is firm with no further extensions. AoE means it closes at 12:00 UTC on Nov 21, which is today. If you have not submitted yet, submit now and fix the rest later. If you already submitted, everything below can go into the rebuttal plan or the camera-ready version (Jan 29).

You wrote "ICPE." I checked against the AGENT 2027 call, because that is where you are submitting. If you meant ICPE (ACM/SPEC), the template and rules are different. Tell me and I'll re-check.

## Requirements check (AGENT 2027)

| Requirement | Status |
|---|---|
| Short papers: up to 5 pages, including references | OK. You use 4, so **you have one free page.** Use it (see below). |
| IEEE conference proceedings template, single-anonymous review | OK. Author names are allowed. |
| AI-generated substantive content (text, figures, or code) must be disclosed in the acknowledgments, naming the tools and what they did | OK. Your disclosure is clear and complete. |
| Original, not under review elsewhere | You must confirm this yourself. |
| Topic fit | Good. Topics include verification, validation, and benchmarking; AgentOps, observability, and runtime monitoring; and empirical studies. |

One thing matters for how you cite: Ahmed E. Hassan is a co-chair, Hao Li is on the PC, David Lo is a co-chair, and Derui Zhu, Zhensu Sun and Yuling Shi are PC members. These are authors of your refs [1], [6] and [18]. They will notice any mistake in how you describe their work.

## Strict reviewer report

**Summary.** The paper checks whether the mechanism an agent claims in a performance PR (cache, fewer reads, less locking) actually shows up in kernel traces and hardware counters. It uses a build agent that never sees the claim. It reports claim statistics for 1,343 PRs and first measurements for 79.

**Strengths**
- The idea is new and easy to say: "faster for the right reason." No prior agent-PR study looks below wall time.
- Good measurement hygiene: an A/A base-again control, no counter multiplexing, PRs dropped when trace events are lost, dedicated cores via systemd (with a good explanation of why isolcpus failed), and control programs for each signal.
- Keeping the build agent blind to the claim is a smart design for avoiding confirmation bias.
- The four case studies are concrete and convincing, especially mlflow and the getdents64 one.

**Major issues**

1. **Output changed in 41 of 79 PRs (52%).** If base and head produce different output, they are doing different work. Then neither the wall-time verdict nor the kernel signals are a fair comparison. This is the first thing a reviewer will attack. You need to:
   - Split Table II by output same versus output changed.
   - Explain what "output differs" means. Is it real behavior change, or timestamps, dict ordering, or float noise? Did base vs base-again ever produce different digests? If yes, the digest is noisy.
   - Note that Qi et al. found the same pattern. Of their 30 re-executed merged fixes, 14 changed behavior on untested inputs. Citing this turns the finding into a confirmation instead of a red flag.

2. **Signal specificity: is "mechanism holds" just "it got faster"?** Your control programs show that each signal *moves* when the mechanism is present (sensitivity). They do not show that the signal stays still when a *different* mechanism caused the speedup (specificity). In Table I, "fewer instructions" is the signal for six mechanisms, and almost any CPU-bound speedup lowers instructions. "Parallelize" uses wall time as its signal, which is circular. So the 27 of 31 "faster and holds" result is partly built in. A strong reviewer will say Table II does not support the main claim.
   - Cheap fix with data you already have: for every PR, test the signals of the mechanisms it did **not** claim too. If unclaimed signals "hold" almost as often as claimed ones, the method does not tell mechanisms apart. If they rarely do, you have strong evidence. One small table, and it fits on your free page.
   - Report results per mechanism. Also report which signal passed, because "any one of its signals" gives several chances to pass.
   - Longer term, give caching a signal that only caching produces. For example, count calls to the cached function with uprobes or CPython USDT probes: `bpftrace -e 'usdt:/path/to/python:python:function__entry { @[str(arg1)] = count(); }'` (this needs a CPython built with `--with-dtrace`).

3. **"Absent" mixes two different causes: the claim is false, or the workload never triggers the right conditions.** Covering 80% of the changed lines does not mean the workload is in the regime where the mechanism matters. A cache needs repeated calls. Streaming needs big files. Pagination needs deep pages. Many of the 25 "absent, no change" PRs may be workload problems. Also, external I/O is stubbed and there is no network, so connection pooling, async I/O and database mechanisms cannot leave a real footprint. Your gemini-notebook example (6 sockets on both versions) may just be the stub, not proof that the claim failed.
   - Report how many claims fall in network or database categories.
   - On a subset, run a second, claim-aware workload and count how often the verdict flips. That measures what blindness costs you.

4. **There is no human validation of the LLM steps.** Agreement between Opus and Haiku (κ = 0.79 on 66 PRs) shows the two models agree with each other, not that they are right. Two models from the same family can share the same errors. Reviewers from the MSR community will push hard on this. You say the human check is "prepared but not yet done." Do at least 100 PRs before camera-ready.

5. **Claude runs almost every step, and Claude Code is also one of the agents you study.** Claude classifies the PRs, extracts the claims, and writes the workloads. Say this openly as a threat, and give a per-agent breakdown. A workshop about agents will expect per-agent results anyway.

6. **The Python interpreter dilutes the signals.** You trace the whole process tree. For a 0.5 s run, interpreter startup and imports produce a large share of the syscalls, openat calls and page faults. A 10% threshold on whole-process counts can hide real effects or create fake ones. Restrict the analysis to the workload region, using userspace markers or a marker syscall at the start and end of the region. Or subtract an import-only run.

7. **False positives from multiple tests.** Complete separation with 5 vs 5 runs has a two-sided chance probability of about 0.008. You test several signals per mechanism and about 7 resources for "hidden costs," so some hits will appear by chance. You already ran base-again, so compute the **A/A false-positive rate for every kernel signal**, not just wall time. This is cheap and very convincing.

8. **The sample flow does not add up.**
   - 91 workloads passed. Your exclusions are 4 non-Python, 4 from manual review and 1 noisy A/A, which totals 88 with 79 analysed. Three PRs are missing, probably lost events.
   - It is not explained how the first 150 of 949 were chosen.
   - Labels: 1,130 + 4,769 = 5,899, not 5,900. With 66 PRs labelled by both models, there are 5,833 unique PRs.
   - It is unclear whether the 2,000-PR sample is part of the 5,900.
   - The "stop rule per agent" is never defined.
   - Add a small flow table or a sentence for each step.

9. **Novelty compared with Qi et al. [6].** Their paper is very close to yours. They re-execute 23 rejected and 30 merged fixes, and their pilot ran on mostly agent-built workloads. They also find failed claims and behavior changes. Right now your related-work section gives them one line. Say clearly what they cannot see and you can: why a fix is faster, not only whether it is. One of their co-authors is on your PC.

**Minor issues**
- "2 was unclassified" should be "2 were unclassified."
- 10.19 / 0.90 = 11.32, but the paper says 11.35×. And 6.32 / 4.32 = 1.46, but the paper says 1.47×. These probably come from unrounded medians. Add a note, or give more digits.
- Fig. 2's x-axis ends at 10, but one PR is at 11.35×. Check that it is actually plotted.
- Two of your four examples come from iPhotron, and up to 15 PRs come from one repository. Report results per repository, or cap each repository's share.
- The abstract says "41 also changed their output." Say what that means for the other results.
- Add explicit RQs. Workshop reviewers find them easier to score.
- [22] is a survey on trace visualization. It is a weak fit for "kernel traces explain where time goes," and it is a self-citation. Add or swap in something closer, such as Fournier and Dagenais, "Analyzing blocking to debug performance problems on multi-core systems," SIGOPS OSR 44(2), 2010. I saw it cited in a reference list during this check, not from the source itself.
- For the measurement design, reviewers expect Georges et al. (OOPSLA 2007). It is a standard citation next to Mytkowicz et al. and Kalibera and Jones in this area.

## Reference check (all 22)

All 22 references are real. One has a wrong author. Several are missing their published venues. One cites the right paper but with numbers the paper does not contain.

| Ref | Status | Problem / fix |
|---|---|---|
| [1] AIDev | Real, ID correct | **Numbers mismatch.** The cited paper reports 932,791 PRs from five agents, plus a subset of 33,596 PRs from 2,807 repositories with over 100 stars. Your 7,685,281 PRs, six agents and AIDev-pop of 361,296 must come from a later release, so cite that dataset version separately (Zenodo/HF commit). Qi et al. did this for v4. Also add MSR '26. Hao Li and Hassan will check this. |
| [2] Opu et al. | Correct | Authors, title and 2512.24630 all match. |
| [3] Peng et al. | Correct | Authors match. It was accepted to MSR '26, so add the venue. |
| [4] Dovhoshliubnyi et al. | Correct | Authors match. Published in Search-Based Software Engineering (SSBSE 2026), so add the venue. |
| [5] Peng et al. | Correct | Authors and 2610.03969 match. |
| [6] Qi et al. | Correct | All 9 authors match, and "53 fixes" = 23 + 30 is accurate. |
| [7] LTTng, OLS 2006 | Correct | Checked from my own knowledge, not online. |
| [8] Laaber et al., EMSE 2019 | Correct | Checked from my own knowledge, not online. |
| [9] Mytkowicz et al. | Correct | ASPLOS '09, pp. 265–276. |
| [10] Gong et al. | Correct | Authors match, MSR '26. |
| [11] PIE | Minor | The arXiv version lists 10 authors, but the ICLR 2024 version adds Yiming Yang between Gardner and Hashemi. You cite it as ICLR 2024, so add Y. Yang. |
| [12] EffiBench | Correct | NeurIPS 2024 confirmed. I checked the arXiv ID from my own knowledge. |
| [13] SWE-Perf | **Wrong author** | **"Y. Zheng" is not an author.** The real list is Xinyi He, Qian Liu, Mingzhe Du, Lin Yan, Zhijie Fan, Yiming Huang, Zejian Yuan, Zejun Ma. Published at ICML 2026. |
| [14] GSO | Correct | Authors match; NeurIPS 2025. Add the venue. |
| [15] PerfBench | **Wrong version** | It was published in Proceedings of the 2026 International Workshop on Agentic Engineering (AGENT '26), pp. 165–172. That is last year's edition of the workshop you are submitting to. You must cite it that way. |
| [16] SWE-fficiency | Correct | Authors and ID match. ICML 2026, so add the venue. |
| [17] FormulaCode | Correct | Authors and 2603.16011 match. PMLR 306, ICML 2026, so add the venue. |
| [18] Chen et al. | Correct | All five authors match. |
| [19] Jin et al., PLDI 2012 | Correct | Checked from my own knowledge, not online. |
| [20] Zaman et al., MSR 2012 | Correct | Checked from my own knowledge, not online. |
| [21] Giraldeau & Dagenais | Correct | TPDS 27(8), 2450–2461. |
| [22] Ezzati-Jivan & Dagenais | Correct metadata, weak fit | CCPE 29(10), article e4068. Add the article number. See the minor issues above about fit. |

For [7], [8], [19] and [20], I'm confident in the details, but I did not fetch them online. Do a quick DOI check before camera-ready.

## What to do with the spare page

In priority order, all using data you already have:
1. Table II split by output same vs output changed.
2. The cross-mechanism specificity table (claimed vs unclaimed signals).
3. A/A false-positive rate for each kernel signal.
4. A sample-flow line, and a per-agent breakdown.

Fix [13], [15] and the AIDev numbers no matter what. These are the kinds of errors that make a reviewer distrust the rest of the paper.