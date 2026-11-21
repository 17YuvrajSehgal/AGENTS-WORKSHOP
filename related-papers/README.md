# Related papers

Every entry here was looked up, not typed from memory.

- arXiv papers: title, authors and id come from the arXiv API.
- Other papers: title, authors, venue, pages and DOI come from Crossref (the publishers' records).
- The raw answers of both services are in `_lookup.jsonl`.
- Each downloaded PDF was opened and its first-page title was checked against the entry.
- The BibTeX entries are in `paper/refs.bib` under the same keys.

"Cited" = already cited in the paper. The others are ready to cite.

## Agent pull requests (closest work)

| key | paper | file | cited |
|---|---|---|---|
| `li2026aidev` | Li, Zhang, Hassan. AIDev: Studying AI Coding Agents on GitHub. arXiv:2602.09185 | `li2026aidev_2602.09185.pdf` | yes |
| `li2025teammates` | Li, Zhang, Hassan. The Rise of AI Teammates in SE 3.0. arXiv:2507.15003 | `li2025teammates_2507.15003.pdf` | no (in bib) |
| `qi2026merged` | Qi et al. Merged, Not Measured. arXiv:2609.37985 | `qi2026merged_2609.37985.pdf` | yes |
| `peng2026validation` | Peng et al. How Do Coding Agents Optimize Software and Report Performance Validation? arXiv:2610.03969 | `peng2026validation_2610.03969.pdf` | yes |
| `peng2025optimization` | Peng et al. How Do Agents Perform Code Optimization? arXiv:2512.21757 | `peng2025optimization_2512.21757.pdf` | yes |
| `opu2025bertopic` | Opu et al. How Do Agentic AI Systems Address Performance Optimizations? arXiv:2512.24630 | `opu2025bertopic_2512.24630.pdf` | yes |
| `dovhoshliubnyi2026mutation` | Dovhoshliubnyi et al. What Do AI Agents Actually Change? arXiv:2607.05666 | `dovhoshliubnyi2026mutation_2607.05666.pdf` | yes |
| `gong2026inconsistency` | Gong et al. Analyzing Message-Code Inconsistency in AI Coding Agent-Authored Pull Requests. arXiv:2601.04886 (MSR 2026 Mining Challenge) | `gong2026inconsistency_2601.04886.pdf` | no |
| `watanabe2025agentic` | Watanabe et al. On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub. arXiv:2509.14745 | `watanabe2025agentic_2509.14745.pdf` | no |

## Benchmarks: can models and agents make code faster?

| key | paper | file | cited |
|---|---|---|---|
| `ma2025swefficiency` | Ma et al. SWE-fficiency. arXiv:2511.06090 | `ma2025swefficiency_2511.06090.pdf` | yes |
| `sehgal2026formulacode` | Sehgal et al. FormulaCode. arXiv:2603.16011 | `sehgal2026formulacode_2603.16011.pdf` | yes |
| `chen2026benchmarks` | Chen et al. Are Performance-Optimization Benchmarks Reliably Measuring Coding Agents? arXiv:2607.01211 | `chen2026benchmarks_2607.01211.pdf` | yes |
| `shypula2024pie` | Shypula et al. Learning Performance-Improving Code Edits. arXiv:2302.07867 (ICLR 2024) | `shypula2024pie_2302.07867.pdf` | no |
| `he2025sweperf` | He et al. SWE-Perf. arXiv:2507.12415 | `he2025sweperf_2507.12415.pdf` | no |
| `shetty2025gso` | Shetty et al. GSO. arXiv:2505.23671 | `shetty2025gso_2505.23671.pdf` | no |
| `garg2025perfbench` | Garg et al. PerfBench. arXiv:2509.24091 | `garg2025perfbench_2509.24091.pdf` | no |
| `huang2024effibench` | Huang et al. EffiBench. arXiv:2402.02037 (NeurIPS 2024) | `huang2024effibench_2402.02037.pdf` | no |
| `jimenez2024swebench` | Jimenez et al. SWE-bench. arXiv:2310.06770 (ICLR 2024) | `jimenez2024swebench_2310.06770.pdf` | no |

## How to measure performance correctly

| key | paper | file | cited |
|---|---|---|---|
| `mytkowicz2009wrong` | Mytkowicz et al. Producing Wrong Data Without Doing Anything Obviously Wrong! ASPLOS 2009. doi:10.1145/1508244.1508275 | `mytkowicz2009wrong.pdf` | no |
| `kalibera2013rigorous` | Kalibera, Jones. Rigorous Benchmarking in Reasonable Time. ISMM 2013. doi:10.1145/2464157.2464160 | `kalibera2013rigorous.pdf` (Kent repository copy) | no |
| `curtsinger2013stabilizer` | Curtsinger, Berger. STABILIZER. ASPLOS 2013. doi:10.1145/2451116.2451141 | `curtsinger2013stabilizer.pdf` | no |
| `georges2007rigorous` | Georges, Buytaert, Eeckhout. Statistically Rigorous Java Performance Evaluation. OOPSLA 2007. doi:10.1145/1297027.1297033 | `georges2007rigorous.pdf` | no |
| `laaber2019cloud` | Laaber, Scheuner, Leitner. Software Microbenchmarking in the Cloud. How Bad Is It Really? EMSE 24(4), 2019. doi:10.1007/s10664-019-09681-1 | `laaber2019cloud.pdf` | no |

## Kernel tracing

| key | paper | file | cited |
|---|---|---|---|
| `desnoyers2006lttng` | Desnoyers, Dagenais. The LTTng Tracer. Ottawa Linux Symposium 2006 | `desnoyers2006lttng.pdf` | yes |
| `giraldeau2016wait` | Giraldeau, Dagenais. Wait Analysis of Distributed Systems Using Kernel Tracing. IEEE TPDS 27(8), 2016. doi:10.1109/TPDS.2015.2488629 | `giraldeau2016wait.pdf` | no |
| `ezzatijivan2017multiscale` | Ezzati-Jivan, Dagenais. Multi-Scale Navigation of Large Trace Data: A Survey. CCPE 29(10), 2017. doi:10.1002/cpe.4068 | `ezzatijivan2017multiscale.pdf` | no |

## Performance bugs and regressions (human-written code)

| key | paper | file | cited |
|---|---|---|---|
| `jin2012perfbugs` | Jin et al. Understanding and Detecting Real-World Performance Bugs. PLDI 2012. doi:10.1145/2254064.2254075 | `jin2012perfbugs.pdf` | no |
| `zaman2012perfbugs` | Zaman, Adams, Hassan. A Qualitative Study on Performance Bugs. MSR 2012. doi:10.1109/MSR.2012.6224281 | `zaman2012perfbugs.pdf` | no |
| `chen2017regression` | Chen, Shang. An Exploratory Study of Performance Regression Introducing Code Changes. ICSME 2017. doi:10.1109/ICSME.2017.13 | `chen2017regression.pdf` | no |

## Rule for citing

Only write a claim about one of these papers after reading that claim in its PDF or abstract.
All 29 papers are downloaded. Seven were added by hand from the library (2026-11-21) and renamed to their keys.
