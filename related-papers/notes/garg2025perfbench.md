# PerfBench: Can Agents Resolve Real-World Performance Bugs?
- **Authors:** Spandan Garg (corresponding author), Roshanak Zilouchian Moghaddam, Neel Sundaresan (Microsoft Corporation, Redmond, WA, USA; a footnote says the last two did the work while at Microsoft)
- **Venue / year / status:** arXiv:2509.24091v3 [cs.SE], 2 Dec 2025. 8 pages, ACM format. The PDF still has the template placeholder "Conference'17, July 2017, Washington, DC, USA" and a placeholder DOI, so the paper itself does not state its venue. Another paper in this folder (chen2026benchmarks, reference [49]) lists it as "Proceedings of the 2026 International Workshop on Agentic Engineering, AGENT '26, ACM, Apr. 2026, pp. 165-172". Confirm that from the publisher before using it.
- **PDF:** related-papers/garg2025perfbench_2509.24091.pdf
- **Cite key:** garg2025perfbench
- **BibTeX-style reference:** Spandan Garg, Roshanak Zilouchian Moghaddam, and Neel Sundaresan. 2025. PerfBench: Can Agents Resolve Real-World Performance Bugs? arXiv:2509.24091v3. (Venue line in the PDF is a template placeholder.)

## In short
PerfBench is a benchmark of 81 real performance bugs from 32 open-source .NET (C#) repositories on GitHub. Each task gives an agent the repository before the fix and the GitHub issue text. The agent must fix the performance problem and also write its own benchmark with the BenchmarkDotNet framework. The harness then runs that agent-written benchmark and the repository's unit tests to decide success. The stock OpenHands agent succeeds on 1.2% (GPT-4.1) and 3.7% (Claude Sonnet 4) of tasks. A modified agent that is told to write a benchmark first, and that gets the benchmark output shortened to its summary table, reaches 14.8% and 19.7%.

## Problem and motivation
- A performance bug wastes time or memory without breaking any function. No test fails, so it is hard to notice and hard to check.
- Agent benchmarks such as SWE-bench "focus exclusively on functional correctness". Nobody knows how well agents handle performance bugs.
- Checking a performance fix needs benchmarking infrastructure, not only unit tests.
- Earlier performance-repair work (the authors' own DeepDev-PERF, RAPGen, PerfLens) works on isolated methods or snippets, not on whole repositories.

## Background / key terms (explain each term simply)
- **Performance bug:** code that is correct but slower or more memory-hungry than it should be.
- **.NET / C#:** Microsoft's runtime and its main language. Memory is managed by a garbage collector.
- **BenchmarkDotNet:** the standard .NET micro-benchmark framework. It runs a method many times and prints a table with mean time, standard deviation, median, quartiles, iteration count, garbage collections and bytes allocated.
- **MemoryDiagnoser:** a BenchmarkDotNet option that adds allocation and garbage-collection columns.
- **Allocation:** asking the runtime for memory for a new object. Many short-lived allocations cost time in the garbage collector.
- **Gen 0:** the youngest garbage-collection generation. The "Gen 0" column counts those collections per 1,000 operations in BenchmarkDotNet output (the paper shows the column but does not explain it).
- **OpenHands:** an open-source coding agent (formerly OpenDevin).
- **Gold patch / developer fix:** the fix the human developer committed.
- **Step:** one agent action. The limit is 100 steps per task.
- **Success rate:** see Metrics below. It is the headline number.

## Method and setup
- **Collection (Sec. 3.1):**
  1. About 1,200 .NET repositories on GitHub with more than 10 stars.
  2. Commits whose message has a performance keyword (Table 1: "perf", "optimize", "latency", "alloc", "leak", "gc", "cache miss", "hot path", "hang", "high cpu" and others).
  3. Keep commits that reference an issue and change at least one `.cs` file.
  4. Build a Docker image with the right .NET version and check that both the buggy and the fixed version compile with `dotnet build`.
  5. "two experienced .NET developers independently reviewed each issue description and associated fix" to confirm a real performance bug and improvement.
  - Result: 81 tasks from 32 repositories.
- **Task (Sec. 3.3):** the full repository at the commit before the fix, in Docker. The `.git` folder is deleted so the agent cannot look up the fix. The agent gets the issue text.
- **Harness (Sec. 4.1):** takes the agent's code changes and the agent's BenchmarkDotNet tests. "We then execute the agent-written BenchmarkDotNet tests before and after the changes suggested by the agent and developer along with executing unit tests present within the repo."
- **Metrics (Sec. 4.2):**
  - Success rate: "Percentage of tasks where the agent produces a fix that improves performance on at least one benchmark without causing regressions to other benchmarks, as well as passing all existing unit tests in the repo."
  - Performance improvement: read from the BenchmarkDotNet summary table (time or memory).
  - Token usage, steps taken, dollar cost.
- **Agents (Sec. 4.3-4.4):**
  - OpenHands baseline: default bug-fixing prompt, changed only to say C# in place of Python.
  - OpenHands-Perf-Agent: (1) prompt steps changed from "reproduce the error" to "create benchmark tests with BenchmarkDotNet + MemoryDiagnoser", "re-run your benchmark and confirm that the performance has improved", "run any unit tests", and output a markdown with benchmark tables (Fig. 4). (2) Output processing: if the benchmark ran, keep only the summary table; if it failed, keep the full output. This cuts benchmark-output tokens "by >90%"; raw output is "often exceeding 10k tokens for a single execution".
- **Models:** GPT-4.1 and Claude Sonnet 4. Max 100 steps. Isolated Docker containers.
- **Not stated:** the machine the evaluation ran on; how many times each agent ran each task; how big an improvement counts as "improves"; how big a slowdown counts as a "regression"; any statistical test or noise threshold; whether the benchmark was run once or several times by the harness.

## Section-by-section notes

### 1. Introduction
- Claims the baseline OpenHands agent "achieves only 3% success rate on PerfBench with GPT-4.1". Table 4 gives 1.2% for GPT-4.1 and 3.7% for Claude Sonnet 4. The introduction does not match the table.
- Three contributions: the benchmark (public at https://github.com/glGarg/PerfBench), the collection and evaluation framework with agent-generated benchmarks, and the performance-aware agent.
- A point on collection: because the agent writes the benchmark, they can collect fix commits that contain no performance test, "unlike how functional bugs are typically collected for benchmarks like SWEBench".

### 2. Background and related work
- Performance bugs are harder to detect and fix than functional bugs and can stay hidden a long time (cited, not measured here).
- Traditional program repair (GenProg, PAR, CapGen, VarFix) uses tests as the specification, which does not work for performance.
- "Limited work exists in applying LLMs to performance optimization." Profilers and BenchmarkDotNet exist, "but require significant expertise to interpret results".

### 3. PerfBench construction
- **Table 2 statistics over the 81 tasks:** files per repository mean 1,227, median 782, max 5,595. Words per problem statement mean 121.6, median 79, max 1,006. Modified `.cs` files per fix commit mean 3.4, median 2, max 22. Lines changed per fix commit mean 103.7, median 60, max 931.
- **Table 3 taxonomy (counts):**
  - Memory management 33 (excessive allocations 18, memory leaks 15).
  - Concurrency and threading 14 (deadlocks and infinite loops 5, async/await issues 5, incorrect parallelism 4).
  - Inefficient algorithms and data structures 14 (algorithmic inefficiency 9, .NET collection issues 4, other data structure misuse 1).
  - I/O and serialization 12 (serialization inefficiency 10, network I/O 2).
  - Build and analysis tools 8 (test performance 4, build performance 4).
- Memory is "more than 40%" of the tasks (33/81). Concurrency and algorithms are about 17% each.
- Fig. 2 example task: codebude/QRCoder, .NET 8.0, an out-of-memory crash in `BinaryStringToBitBlockList`. Note that this "performance bug" is a crash, and the taxonomy also has deadlocks and infinite loops. Several tasks are closer to functional failures with a resource cause than to "slow but correct".

### 4. Experimental setup
- See Method above.

### 5. Benchmark results
- **Table 4:**

  | Agent | Model | Success | Avg steps | Avg tokens | Avg cost ($) |
  |---|---|---|---|---|---|
  | OpenHands baseline | GPT-4.1 | 1.2% (1/81) | 47.2 | 1.3M | 15.42 |
  | OpenHands baseline | Claude Sonnet 4 | 3.7% (3/81) | 62.3 | 2.6M | 7.92 |
  | OpenHands-Perf-Agent | GPT-4.1 | 14.8% (12/81) | 84.3 | 1.9M | 23.08 |
  | OpenHands-Perf-Agent | Claude Sonnet 4 | 19.7% (16/81) | 49.0 | 1.7M | 5.03 |

- The text compares this to ">60%" for OpenHands on SWE-bench Verified (cited from the OpenHands paper).
- **5.2 Size of the improvements (Fig. 5, successful Perf-Agent fixes):** memory allocation reductions are "typically" above 20%, some in the range of KBs and MBs. CPU time improvements are "typically in the range from 0 to 40%", in absolute terms microseconds or milliseconds. The biggest CPU gains are algorithmic fixes.
- The authors defend the small numbers: they come from isolated micro-benchmarks of one code path and "don't directly reflect usage of the application by an end-user".
- **5.3 Table 5, by category, Claude Sonnet 4:**

  | Category | Total | Baseline | Perf-Agent |
  |---|---|---|---|
  | Memory management | 33 | 6.0% (2/33) | 18.2% (6/33) |
  | Concurrency & threading | 14 | 0% (0/14) | 14.3% (2/14) |
  | Inefficient algorithms | 14 | 7.1% (1/14) | 21.4% (3/14) |
  | I/O & serialization | 12 | 0% (0/12) | 33.3% (4/12) |
  | Build & analysis tools | 8 | 0% (0/8) | 12.5% (1/8) |
  | Total | 81 | 3.7% (3/81) | 19.7% (16/81) |

  The table prints "9" as the total for Build & analysis tools, but the fractions use 8 and Table 3 says 8. It is a typo.

### 6. Limitations
- **Performance against correctness:** the harness checks for a measured gain, not for the right fix. An agent "may achieve performance gains through alternative optimizations that differ from the developer's intended solution, yet still receive full credit".
- **Dependency on benchmarking:** "Our evaluation relies entirely on agent-generated benchmarks, creating a potential weakness where poorly designed benchmarks may fail to capture the true performance characteristics of the issue." They only mention false negatives (a good fix scored as a failure). They argue that writing benchmarks in .NET "is a relatively easy task for today's LLMs". No evidence is given.
- **Language:** only .NET and C#.
- **Metrics:** only execution time and memory allocation. Not "network usage, disk I/O usage, or end user-perceived latency".

### 7. Conclusion
- Says agents get "<4% success rates" at baseline and "up to 20%" with the Perf-Agent, "a 5x improvement".
- Calls PerfBench "the first benchmark for evaluating language model agents on real-world performance bug fixing tasks in .NET".

## Key results (with numbers) and what they mean
- Baseline 1/81 and 3/81 -> an agent told only "fix this issue" almost never produces a fix that passes the performance check. But the baseline prompt never asks for a benchmark, and success requires an agent-written benchmark. So part of this near-zero is "did not write a benchmark", not "could not fix the bug". The paper does not separate the two.
- Perf-Agent 12/81 and 16/81 -> telling the agent to benchmark, and trimming benchmark output, gives most of the gain. Even then about four out of five tasks fail.
- 16 successes spread over five categories (6, 2, 3, 4, 1) -> category comparisons rest on one to six tasks. "I/O is easiest (33%)" is 4 of 12.
- Memory improvements above 20%, CPU improvements 0 to 40% and in microseconds -> the accepted fixes are small micro-benchmark gains. A CPU "improvement" near 0% on a microsecond benchmark is the size of normal run-to-run noise, and the paper states no threshold.
- Cost: $5.03 to $23.08 per task on average -> evaluating agents on performance is expensive because benchmark output is long.

## Tables and figures
- **Fig. 1 (p. 3):** distribution of the 32 repositories. Read: tasks are not concentrated in a few repositories (no numbers in the text layer).
- **Fig. 2 (p. 3):** one task's metadata and issue text.
- **Table 1 (p. 4):** keyword list in five groups.
- **Table 2 (p. 4):** repository, issue and fix size statistics.
- **Table 3 (p. 4):** taxonomy with counts, sums to 81.
- **Fig. 3 (p. 6):** a sample BenchmarkDotNet output (v0.13.12, Windows 11, Intel Core i9-12900K, .NET 8.0) with two example methods. This is an illustration of the format. The paper does not say it is the evaluation machine.
- **Fig. 4 (p. 7):** prompt diff between baseline and Perf-Agent.
- **Table 4 (p. 6):** main results.
- **Table 5 (p. 6):** results by category for Claude Sonnet 4.
- **Fig. 5 (p. 7):** box plots of CPU and memory improvement, relative (%) and absolute (microseconds on a log axis from 10^-1 to 10^3; bytes on a log axis from 2^0 to 2^20). Read: memory gains are larger and more consistent than CPU gains. The text does not say which model's runs are plotted or how many benchmark tests.

## Ideas we can use
- The closest design to our "build agent writes the workload" step. They show an agent can write a runnable micro-benchmark for a real repository. We differ in one key way: in PerfBench the agent that writes the fix also writes the benchmark and knows what it is trying to show. Our build agent never sees the claim.
- Their limitation text gives us the sentence for why blinding matters: agent-written benchmarks "may fail to capture the true performance characteristics of the issue".
- Their success rule is a simple template: better on at least one benchmark, no regression on others, unit tests pass. Our "hidden costs" and "output changed" verdicts cover the same ground with measured signals.
- Their taxonomy maps well to kernel and hardware signals: excessive allocations -> page faults, `brk`/`mmap` calls, instructions; deadlocks and async issues -> futex wait, context switches; serialization and network I/O -> `read`/`write`/`sendto` counts and bytes. It is a second source, next to AIDev patterns, for a claim-to-signal table.
- Output trimming (keep the summary table, drop the rest) is a practical trick for our own agents when they read `perf stat` or trace output.
- Memory gains were more robust than CPU time gains in their data. Count-based signals (bytes allocated) are steadier than time. This is in line with our mechanism-signal idea.

## Weaknesses and things glossed over
- The agent grades its own work. The benchmark that decides success is written by the same agent that wrote the fix, after it was told to "confirm that the performance has improved". The paper only discusses false negatives. A benchmark shaped to flatter the fix (false positive) is not discussed.
- No noise handling is described: no threshold, no statistical test, no repeat count, no statement of the hardware. "Improves performance on at least one benchmark" could be satisfied by noise, more so with CPU gains "from 0 to 40%" in microseconds.
- The abstract says the harness "validates fixes by comparing execution metrics collected for developer fix and agent fix". The success metric in Sec. 4.2 does not use the developer fix at all. The developer fix is run on the agent's benchmark (Sec. 4.1), but the paper never reports those numbers or says how they enter the verdict.
- The paper never checks that the 81 developer fixes show a measurable gain under any benchmark. Task validity rests on two reviewers reading the issue and the fix. No agreement number is given.
- Numbers disagree inside the paper: abstract "~3%" baseline; introduction "3% ... with GPT-4.1" (table: 1.2%); results text "15-20%" (table: 14.8% and 19.7%); "5x improvement" (3.7% to 19.7% is 5.3x for Sonnet; 1.2% to 14.8% is about 12x for GPT-4.1, so "up to 5x" is not right); 16/81 is 19.75%, printed as 19.7% and "~20%".
- Table 5 prints total 9 for Build & analysis tools; it is 8.
- Cost column is odd: baseline GPT-4.1 uses 1.3M tokens for $15.42, baseline Sonnet 4 uses 2.6M tokens for $7.92. The paper does not explain (caching or price differences are possible, but it does not say).
- One run per configuration as far as the paper shows. No variance, no confidence intervals, on a benchmark where 16 successes is the best result.
- The two changes in the Perf-Agent (prompt and output trimming) are not ablated. We do not know which one helps.
- The baseline is handicapped by design: it is not told a benchmark is needed. So "agents struggle with performance" is partly "agents were not told how they would be graded".
- Some tasks are crashes, deadlocks or infinite loops. These are not typical "slow but correct" bugs.
- Commit selection by keyword and by "references an issue" favours well-described bugs. The agent gets the human's issue text, sometimes with a stack trace pointing at the function (Fig. 2).
- Micro-benchmarks only. No end-to-end workload, no I/O or network measurement (admitted).
- Sec. 5.2 calls the time metric "CPU utilization". It is benchmark execution time.
- "First benchmark" is limited by the authors to .NET.

## Open questions and future work (theirs, and ours)
- Theirs: other languages and frameworks; "more sophisticated evaluation methodologies"; "broader metric coverage" (network, disk I/O, user-perceived latency).
- Ours: how often does an agent-written benchmark exercise the changed code path at all? A kernel trace or coverage check could answer this. Would their 16 "successes" survive an A/A control and a blind benchmark writer? Does the size of a micro-benchmark gain predict any change in syscalls or page faults under a realistic workload?

## Link to our paper
- **Related work:** benchmarks for agents on performance tasks. PerfBench is the one where the agent writes the benchmark. We cite it as prior art for agent-written workloads and say what we change: the workload writer is blind to the claim, and the verdict uses kernel and hardware signals with an A/A control.
- **Method (build agent):** cite for feasibility of agent-written benchmarks on real repositories, and for the output-trimming idea if we use it.
- **Threats:** our build agent's workload may also miss the changed code path. PerfBench admits the same risk. We should say how we detect it.
- **Discussion:** their limitation "Focus on CPU and Memory" names network and disk I/O as missing. Those are signals our kernel traces see.

## Link to the thesis (tracing, kernel analysis)
- No kernel tracing or hardware counters. All measurement is in-process, through BenchmarkDotNet (time, allocations, GC counts).
- The paper states the gap itself: profilers exist, but "these bugs require significant manual analysis to translate findings into fixes", and the evaluation does not capture disk or network I/O. Kernel-level tracing covers those dimensions.
- The taxonomy (allocations, leaks, deadlocks, async, serialization, network I/O) is a useful list of bug classes to pair with kernel signals in thesis work on agents that use traces.

## Quotes for inline citation
- "Performance bugs are inefficiencies in software that waste computational resources without causing functional failures, making them particularly challenging to detect and fix." (Abstract, p. 1)
- "existing benchmarks primarily focus on functional correctness and fail to evaluate agents' abilities to identify and resolve non-functional issues like performance bugs" (Abstract, p. 1)
- "Validating performance improvements also requires infrastructure for benchmarking and comparison between benchmarks, unlike functional fixes that can simply be verified through unit tests." (Sec. 1, p. 1)
- "Success Rate (%): Percentage of tasks where the agent produces a fix that improves performance on at least one benchmark without causing regressions to other benchmarks, as well as passing all existing unit tests in the repo." (Sec. 4.2, p. 5)
- "Our evaluation relies entirely on agent-generated benchmarks, creating a potential weakness where poorly designed benchmarks may fail to capture the true performance characteristics of the issue." (Sec. 6, p. 7)
- "An agent may achieve performance gains through alternative optimizations that differ from the developer's intended solution, yet still receive full credit in our evaluation." (Sec. 6, p. 7)
- "Our evaluation primarily considers improvements in execution time and memory allocation without capturing other important performance dimensions such as network usage, disk I/O usage, or end user-perceived latency." (Sec. 6, p. 7)

## Suggested citation sentences
- PerfBench lets the agent write its own BenchmarkDotNet tests and accepts a fix when at least one of them improves \cite{garg2025perfbench}; the authors note that such agent-written benchmarks ``may fail to capture the true performance characteristics of the issue''. In our pipeline the agent that writes the workload never sees the claim.
- On 81 real .NET performance bugs, an OpenHands agent with performance-specific instructions succeeded on at most 16 tasks (19.7\%) \cite{garg2025perfbench}.
- PerfBench measures execution time and memory allocation only and does not capture disk or network I/O \cite{garg2025perfbench}; kernel-level signals cover these.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It is the nearest prior design to our build agent: an agent writes the workload that is used to judge a performance change in a real repository. It shows this is workable. We build on that idea.
  - It does not separate the roles. The same agent writes fix and benchmark, and knows the goal. It has no A/A control, no stated noise threshold, no hardware counters and no kernel traces, and it does not check any stated mechanism. It also studies agents fixing known human-reported bugs in a benchmark, not agent PRs in the wild and their claims. We do all of these.
  - It studies whether agents can fix performance bugs. We study whether agents' performance claims are true. The two fit together: their low success rates make it plausible that claims in real PRs deserve checking, but they do not show it.
  - A point against us: their own limitation applies to any agent-written workload, ours too. A workload that does not exercise the changed path gives a false "not faster" or "mechanism did not happen". Blinding the build agent removes the bias toward flattering the fix, but it makes this miss more likely, because the agent does not know what to stress. We need a check for that (for example, confirm the changed lines run under the workload).
- **Safe to cite for:**
  - Performance bugs do not cause functional failures, so they are hard to detect and tests do not catch them. "waste computational resources without causing functional failures, making them particularly challenging to detect and fix" (Abstract, p. 1).
  - Checking a performance fix needs more than unit tests. "Validating performance improvements also requires infrastructure for benchmarking ... unlike functional fixes that can simply be verified through unit tests" (Sec. 1, p. 1).
  - An evaluation design where the agent writes its own benchmark exists and has a known weakness. "Our evaluation relies entirely on agent-generated benchmarks, creating a potential weakness where poorly designed benchmarks may fail to capture the true performance characteristics of the issue" (Sec. 6, p. 7).
  - Agents do poorly on real performance bugs in this benchmark: 1/81 and 3/81 for baseline OpenHands, 12/81 and 16/81 for the performance-aware variant (Table 4, p. 6). Give the fractions.
  - A measured gain does not prove the right fix or the intended mechanism. "may achieve performance gains through alternative optimizations that differ from the developer's intended solution, yet still receive full credit" (Sec. 6, p. 7).
  - Existing agent performance evaluation looks at time and allocation only. "without capturing other important performance dimensions such as network usage, disk I/O usage, or end user-perceived latency" (Sec. 6, p. 7).
- **Do not cite for:**
  - That agents make false or exaggerated performance claims. The paper does not look at claims.
  - That agent-written benchmarks are reliable or valid. The paper asserts that writing them is "relatively easy" for LLMs and gives no evidence.
  - That agent-written benchmarks are biased in the agent's favour. The paper does not study or mention this. It is our concern, not their finding.
  - "Baseline agents achieve 3%" as one number. It is 1.2% (GPT-4.1) and 3.7% (Claude Sonnet 4).
  - "A 5x improvement" without saying it is the Claude Sonnet 4 pair (3/81 to 16/81).
  - Any statement about languages other than C#/.NET, or about Linux. The only environment shown is a sample output from Windows 11.
  - Kernel-level, syscall-level or hardware-counter behaviour of the fixes. None is measured.
  - Statistically validated speedups. No test, threshold or repeat count is described.
  - Per-category difficulty rankings as findings. They rest on 1 to 6 successes per category.
  - The AGENT '26 venue, until confirmed outside this PDF.
