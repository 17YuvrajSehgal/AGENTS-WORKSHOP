# Multi-scale navigation of large trace data: A survey
- **Authors:** Naser Ezzati-Jivan, Michel R. Dagenais (Department of Computer and Software Engineering, Ecole Polytechnique Montreal, Montreal, Canada)
- **Venue / year / status:** Concurrency and Computation: Practice and Experience (Wiley), vol. 29, no. 10, pages 1-20, 2017. DOI 10.1002/cpe.4068. Journal article, peer-reviewed. The PDF we have is the **accepted version** ("Version finale avant publication / Accepted version") from PolyPublie, the open-access repository of Polytechnique Montréal (https://publications.polymtl.ca/2980/). Its layout and page numbers differ from the publisher's version. The cover page marks it "Refereed" and "All rights reserved".
- **PDF:** `related-papers/ezzatijivan2017multiscale.pdf`
- **Cite key:** ezzatijivan2017multiscale
- **BibTeX-style reference:** Naser Ezzati-Jivan and Michel R. Dagenais. 2017. Multi-scale navigation of large trace data: A survey. Concurrency and Computation: Practice and Experience 29, 10 (2017), 1-20. https://doi.org/10.1002/cpe.4068
- **Page references in this note:** the repository copy has 21 PDF pages (1 cover page, then the article) and no printed page numbers. "PDF p. N" below means page N of this file. Do not use these numbers as journal page numbers.
- **Reminder from the task brief:** one of the authors of this survey is a co-author of our paper. Every statement below was checked against the text.

## In short
This is a survey, not an experiment. It organises the literature on how to make very large execution traces (with a focus on operating system kernel traces) usable by a human analyst. It has three parts: (1) trace abstraction, split into four kinds (content-based, metric-based, visual, resource); (2) ways to show hierarchical trace data at several levels of detail (space filling, focus+context, multiple levels, multiple views), with a review of eleven trace visualization tools; (3) data structures that store abstract events so that any time range can be queried fast. The main conclusion: most trace tools work at one level of representation, semantic zooming across levels is rarely used for traces, and links between events at different levels are mostly missing.

## Problem and motivation
- Dynamic analysis through traces gives precise data, but two problems block its use (Section 1, PDF p. 2):
  - size: tracing "may generate very large trace logs (thousands of megabytes), even when run for only a few seconds";
  - low level: trace data is system-dependent and "requires a deep knowledge of the domain and system related tools".
- Many surveys cover trace abstraction or trace visualization. Few discuss multi-level (multi-scale) visualization, where the analyst starts with an overview and zooms into detail, as in online maps. The paper fills this gap.
- Questions it sets for a multi-level tool (PDF p. 3): how to generate a hierarchy of abstract events, how to organise them, and how to show and link events across levels.

## Background / key terms (explain each term simply)
- **Static analysis:** understanding a program from its source code and documents, without running it.
- **Dynamic analysis:** understanding a program from data recorded while it runs (logs, trace events).
- **Execution trace:** a time-ordered list of events recorded during a run.
- **Kernel trace:** a trace of operating system events (system calls, scheduling, interrupts, disk, memory). Two features set it apart from an application trace (PDF p. 3): the events of one process are interrupted by other processes because of preemption and scheduling, and one trace mixes events from many kernel parts.
- **Trace abstraction:** turning many low-level events into fewer, higher-level items.
- **Selective tracing:** record only chosen modules or processes.
- **Sampling:** keep only some of the events.
- **Filtering:** remove events that are not needed for the question.
- **Compression:** store events in less space. Lossy compression drops data; lossless keeps all of it.
- **Generalization:** treat several specific events as one general event (for example `read`, `readv`, `pread64` as "read").
- **Aggregation / synthetic event:** group related events into one compound event (for example a system-call entry and exit become one "file read").
- **Stateful pattern matching:** patterns share common state (for example which process is running) instead of each pattern recomputing it.
- **Metric-based abstraction:** compute numbers from events (CPU use per process, bytes read, number of failed connections) instead of keeping the events.
- **Visual abstraction:** simplify what is drawn (colors, labels, one dot for many events), without changing the data.
- **Resource abstraction:** group or order the things events refer to (processes, files, CPUs) in a hierarchy.
- **LOD (level of detail):** how much detail is shown at a given zoom.
- **Semantic zooming:** zooming in shows a different, more detailed kind of object, not only a larger picture.
- **Space filling / treemap:** every node of a hierarchy gets a rectangle sized by a property; the whole screen is used.
- **Focus+context:** one part is shown enlarged while the whole stays visible (for example a hyperbolic tree).
- **Overview + detail:** an overview pane and a detail pane side by side.
- **Multiple (coordinated) views:** several views of the same trace; selecting something in one view highlights it in the others.
- **Checkpoint / snapshot:** stored intermediate analysis state at regular points in the trace, so a query does not start from the beginning.
- **State history tree:** a disk-based tree of intervals (key, value, time range) used to store how system state changes over time.
- **Segment tree, interval tree, R-tree:** general data structures for storing and querying intervals or boxes.
- **OLAP / data cube:** a database style of analysis where data is pre-aggregated along several dimensions.

## Method and setup
- **Type of work:** literature survey with a taxonomy. No experiments, no benchmark, no user study.
- **How the literature was chosen:** the paper does not say. There is no search protocol, no list of sources searched, no inclusion or exclusion rules, and no count of reviewed papers. The reference list has 108 entries.
- **Scope stated by the authors:** the techniques are generic, "our focus will be more on the area of operating system (kernel) trace data and analysis, when this distinction is relevant" (PDF p. 3).
- **Structure:** Section 2 abstraction techniques; Section 3 visualization techniques and tools; Section 4 data structures; Section 5 discussion; Section 6 conclusion. Fig. 1 shows this taxonomy.
- **Workloads, repetitions, statistics:** not applicable.

## Section-by-section notes

### 1. Introduction (PDF p. 2-3)
- Software comprehension uses static or dynamic analysis. Static analysis is weak when documents are outdated or for rare timing bugs in distributed systems.
- Dynamic data usually comes from instrumentation (hooks at function entry and exit). Sampling tools that add no instrumentation also exist; VTune and HPCToolkit are named.
- Tracing covers levels "from (kernel) system calls [...] to high-level architectural levels", "leading to the detection of more faults, (performance) problems, bugs and malwares than static analysis [14]". The comparison with static analysis is supported by a citation, not by this paper.
- Ways to cope with size and complexity: reduce, compress, filter, generate high-level information, visualize. Even after that, the result can be large, so the data should be organised at several levels of detail with navigation between them.

### 2. Multi-level trace abstraction techniques (PDF p. 3-8)
- Four categories: content-based (data-based), metric-based, visual, resource.
- **2.1 Content-based abstraction.**
  - *Trace size reduction:* selective tracing, sampling, filtering, compression (the paper's own list also names generalization and aggregation here).
    - Selective tracing: the LTTng Linux kernel tracer "can be configured to trace only the requested modules, say network, file system, etc, instead of tracing the whole operating system".
    - Sampling: "Since sampling filters trace events in an arbitrary manner, it may lose information and not preserve the actual system behavior."
    - Filtering: by timestamp, event type, arguments, function or process name, priority. Fadel et al. [11] filter kernel traces "to remove memory management events (out of analysis scope events) and page faults (noises)".
    - Compression: it "is more a storage reduction technique rather than an analysis simplification technique" and is not usable for online analysis.
  - *Event generalization:* in Linux "the read, readv and pread64 system calls [...] may be used to read a file. However, from a higher level perspective, all of them can be seen as a single read operation." All file open/read/write/close events can become one "file operation" event at higher levels. PAPI is given as an example that abstracts hardware-specific events into general and derived events.
  - *Event grouping and aggregation:* called "one of the critical steps for enabling multi-scale analysis". Example (Fig. 2): a "file read" event built from the read system-call entry and exit and the file-system events between them. Successive aggregation gives a hierarchy; the top level is an overview of the whole trace.
    - Limits of earlier work: Fadel et al. [11] and the work cited as [12] use disjoint patterns and do not scale to large traces. Matni et al. [17] use automata to detect faults such as "escaping a chroot jail" and "SYN flood attacks"; their analyzer does not share state between patterns. Because the scheduler interleaves processes, events must first be split per process before pattern matching.
    - The authors' own earlier work [10, 18]: a stateful synthetic event generator for kernel traces. Sharing common information "simplifies the patterns, reduces the storage space [...], increases the overall computation efficiency". Fig. 3 (from [18]) compares the two approaches.
    - Pattern mining: LaRosa et al. [7] mine kernel traces (LTT and dTrace) with frequent itemsets over time windows to find excessive inter-process communication. Limit: it cannot find patterns that occur rarely.
- **2.2 Metric-based abstraction.** Instead of compound events, compute measures such as CPU load, I/O throughput, failed and successful network connections. Bligh et al. [50] use kernel-trace statistics to debug intermittent problems such as inefficient cache use and poor latency. Cohen et al. [52] relate many metrics to problem intervals but "do not consider scalability issues". Ezzati et al. [53] give a framework to extract statistics from kernel traces. Examples listed (PDF p. 6): CPU used per process; bytes read or written per file or network operation and number of accesses to a file; number of fork operations per process; disk areas most used, latency of disk operations, distribution of seek distances; network I/O throughput and failed connections; memory use of a process and pages used.
  - How it works: for each metric, a pattern of events plus an aggregation function is registered. Example: process I/O throughput = all file read and write events with SUM.
  - Most visualization tools support it (Vampir, Jumpshot, TuningFork are named) and show the result as histograms or counts, usually as the top-level overview.
- **2.3 Visual abstraction.** Works on what is drawn, not on the data. Colors for states (waiting, system call, user space) in Trace Compass and LTTV; rectangles for states; arrows for communication; in LTTV and Trace Compass "when there is more than one trace event in an area smaller than a pixel, a black dot is shown instead". Annotations and labels (Ovation, the Google Chrome tracing tool, Trace Compass).
- **2.4 Resource abstraction.** A trace event involves several resources: a "file open" event carries the process, the file, the CPU and the returned file descriptor. Techniques: grouping, filtering, hierarchical organisation. Montplaisir et al. [61] build an "attribute tree" of resources dynamically from the trace (Fig. 4), which avoids defining resources that never appear. [53, 62] define one hierarchy per resource type and build cubes for OLAP-style analysis. Schnorr et al. [25] group threads by process, machine, cluster.
- **2.5 Applications.** System comprehension, security problem detection, performance degradation investigation, comparison of executions, monitoring. Problems that can be found by looking for patterns: "inefficient CPU scheduling, network attack attempts, slow disk accesses, lock contention, inappropriate latency, non-optimal memory and cache utilization, and uncontrolled sensitive file modifications [50, 17, 8]".

### 3. Multi-level trace visualization (PDF p. 8-13)
- **3.1 Hierarchy visualization techniques (four groups).**
  - *Space filling:* radial methods and treemaps. The treemap was first used for the directory structure of an 80MB hard disk; later for traces in Triva, Gammatella and LogView. Fig. 5 shows one million items. Weak points: focus on leaf nodes, users may lose the global picture, small areas are hard to see.
  - *Focus+context:* magnifier, tree explorers, hyperbolic browser. Weak points: redraw cost, cannot show non-hierarchical relations.
  - *Multiple levels:* separate views per level, as in online maps; supports semantic zooming. In non-semantic zooming ("as used in many visualization tools", TuningFork, Jumpshot, Trace Compass and the Chrome tracing environment are named) objects only get larger. Special case overview + details (Jumpshot, Vampir, Trace Compass; Fig. 7). Judgment: the method "is not exploited much in trace visualization tools. It deserves more consideration".
  - *Multiple views:* the most common in trace tools (Zinsight, TraceVis, Vampir, LTTV, Trace Compass). Views are coordinated by timestamp or by resource. Weak point: the user must follow several views at once.
  - *Data correspondence (linking levels):* structure-based linking (timestamps, resources) or content-based linking (for example an "HTTP connection" abstract event linked to its socket create, send, receive and close events). Links are built statically during aggregation or dynamically by matching. Visual links: VisLink [81], links across application windows [82], context-preserving links [83]. For very large traces, drawing links "may cost too much, and should be studied carefully".
- **3.2 Visualization tools.** Reviewed in text: Vampir, Jumpshot, a paragraph on HPC tools (Allinea MAP, Intel VTune, HPCToolkit's hpctraceviewer, TAU, Scalasca) and HPC visualization research, AVID, Shimba, Jinsight, Ovation, Zinsight, TuningFork, Tracevis, Triva, LTTV, Trace Compass. Selected judgments:
  - Vampir: multiple synchronized views; "the metrics used for representing the system behavior are too low level".
  - Jumpshot: uses the SLOG2 hierarchical format; views are linked only by timestamps.
  - AVID: needs a manually defined architecture model; scalability problems even with sampling.
  - Zinsight: supports abstraction and linked views but cannot show traces "unless they completely fit in main memory".
  - LTTV (developed at the Dorsal lab; shows LTTng kernel traces): statistics view, control flow view, event view; physical zooming, scrolling, filtering. "However, it does not support multi-level trace abstraction and linked events. The same limitation applies to Trace Compass", described as a full-featured Eclipse-based LTTng trace viewer with more views and visual abstraction mechanisms.
  - Table 1 summarises eleven tools (see Tables and figures).

### 4. Hierarchical organization of trace data (PDF p. 12, 14-16)
- Interactive tools must answer queries at any point of a large trace without reprocessing it from the start. Two directions: horizontal analysis (moving along time) and vertical analysis (moving between levels).
- **Checkpoints:** split the trace (example given: one checkpoint per 100K events), store aggregated data at each, and at query time replay only from the nearest earlier checkpoint. Used in LTTV and at first in Trace Compass. LTTngTop [54] indexes LTTng kernel traces this way and is described as "a more detailed and efficient version of the Linux TOP command". Limits: needs the original trace, snapshots are redundant, does not scale to long durations, some tools kept snapshots in memory.
- **Dynamic checkpoints** (Ezzati et al. [53]): a different interval per metric. Works for offline traces and "was tested for very large traces", but stored data grows linearly with trace size. The cube data model [62] targets live streams of arbitrary size.
- **State history tree** (Montplaisir et al. [97, 98]): stores intervals on disk; queries traverse only the relevant branches, with no access to the original trace. The tree can be large; the partial history tree "reduces the state history tree size by more than a hundredfold for a small increase in query time" but needs the original trace again.
- **SLOG / SLOG2** (Chan et al. [87]): intervals in an R-tree-like structure, used by Jumpshot; "nearly constant access time" is reported by its authors. Weak point: fixed equal time spans per level, so unevenly distributed events give uneven access times; no links between objects.
- **General interval structures:** segment tree (query O(log n + k), storage and build O(n log n), hard to store on disk when it exceeds memory); interval tree; Relational Interval Tree on top of a relational database (Montplaisir et al. tried databases and "incurred a considerable overhead in both storage space and access time"); R-tree and variants (R+-tree, R*-tree, SS-tree, SR-tree), which "do not work well for sequences of long intervals with significant overlap". Trace tools typically use custom formats such as SLOG and the State History Tree.
- The review is limited to abstract events in interval form and to explore, zoom and pan. A call-graph view would need a graph structure.

### 5. Discussion (PDF p. 16-17)
- Abstraction: metric-based abstraction "is widely used in trace visualization tools" and usually feeds the top-level view. Tools combine the four methods.
- Visualization: space-time (Gantt-like) views do not scale in number of resources or timeline items. Multiple synchronized views help but add complexity. Semantic zooming over multiple levels "is seldom used in the context of trace data, even though it proved very valuable in spatial applications". No single technique is best; Table 2 gives a use-case per technique. One cited example handles "700k nodes amongst 13 levels" with a multi-level treemap [105].
- Linking: establishing links between related events at different levels is "sometimes neglected". "Most existing trace analysis and visualization tools do not consider the linking between events in different levels. It should be an important focus for future work".
- Data model: R-tree, Quadtree and custom methods (SLOG, State History Tree) can index abstract data at several levels, but they support only one hierarchy and do not manage links or non-hierarchical relations (example: file operations and disk block operations).

### 6. Conclusion (PDF p. 17-18)
- Restates the four visualization methods and that multiple levels with semantic zooming "is not much used in trace tools and deserves to be investigated in future work".
- Studying each abstraction level alone is limiting; users need to pull more detail on demand for a region of interest, which needs links between abstract events and the underlying data.
- Acknowledgement: NSERC, Ericsson Software Research, Defence Research and Development Canada (DRDC).

## Key results (with numbers) and what they mean
This is a survey, so there are few numbers and none are the authors' new measurements.
- Traces of "thousands of megabytes" for a few seconds of run (Section 1; stated without a citation) -> raw kernel traces cannot be read event by event. Some reduction step is needed before any conclusion.
- Four abstraction types and four visualization types (Fig. 1) -> a vocabulary to describe what any trace analysis step does to the data.
- Table 1: of eleven tools, ten have metric-based abstraction (all except AVID and Shimba... see the table rows below: nine have a check mark) -> see the exact rows; the point is that statistics computed from events are the most common form of abstraction in tools. The text says the same in words (Section 5).
- Fig. 3 (from the authors' earlier paper [18]): pattern evaluation time against trace size, 25 MB to 10,000 MB. The stateful approach is faster at every large size. At 10,000 MB the chart shows roughly 950,000 ms (stateful) against roughly 1,480,000 ms (stateless). These two values are read from the chart by eye; the paper gives no table. -> sharing state between patterns saves about a third of the time at the largest size, by this chart.
- Partial history tree: more than a hundredfold smaller (reported from [97]) -> storing less state is possible if the raw trace stays available.
- Segment tree costs O(log n + k) per query, O(n log n) storage -> good in memory, poor on disk for very large traces.

Correction to the Table 1 bullet above, to be exact: metric-based abstraction has a check mark for Vampir, Jumpshot, Jinsight, Ovation, Zinsight, TuningFork, Tracevis, Triva and LTTV. That is 9 of 11. AVID and Shimba have none.

## Tables and figures
- **Fig. 1 (PDF p. 4):** taxonomy. "Trace Logs" enter "Trace Abstraction" (Data, Metric, Resource, Visual abstraction). "Data Organization" connects it to "Multilevel Trace Visualization" (Focus+Context, Multiple Levels, Multiple Views, Space Filling).
- **Fig. 2 (PDF p. 5, source [11]):** state diagram that recovers a "file read" event: within a process, `syscall_entry (sys_readlink)` leads to state SYSCALL_READ_LINK, `syscall_exit` leads to USER_MODE_READ_LINK. The caption says "file read" while the diagram's states are named after readlink.
- **Fig. 3 (PDF p. 5, from [18]):** "Pattern Evaluation Time Comparisons". x-axis trace sizes (MB): 25, 75, 150, 500, 1000, 2000, 5000, 10000. y-axis execution time (ms) up to 1,600,000. Two lines: Stateful Approach (lower) and Stateless Approach (higher). Read: the gap grows with trace size.
- **Fig. 4 (PDF p. 7):** hierarchy of resources extracted from trace events.
- **Figs. 5, 6 (PDF p. 8-9):** treemap of one million items; hyperbolic browser. Both from wikipedia.org.
- **Fig. 7 (PDF p. 9):** overview + detail in the Trace Compass LTTng viewer.
- **Figs. 8, 9 (PDF p. 10):** context-preserving visual links; links between related items.
- **Figs. 10-14 (PDF p. 15-16):** segment and interval tree, segments against intervals, R-tree, R+-tree, R*-tree. Mostly from wikipedia.org.
- **Table 1 (PDF p. 13), checked on the page image.** Columns: Multiple Levels | data abstraction | metric-based | visual | resource | space filling | multiple levels | multiple views | context + focus.
  - Vampir: yes | filtering + aggregation | yes | yes | yes | - | yes | yes | -
  - AVID: manual | sampling | - | animation | manual | - | - | yes | -
  - Jumpshot: yes | yes | yes | yes | mountain range | - | yes | yes | -
  - Shimba: static analysis | selective tracing and abstraction | - | aggregation of sequence diagram | - | - | - | - | -
  - Jinsight: yes | repetition detection | yes | yes | - | - | yes | yes | -
  - Ovation: yes | repetition detection | yes | yes | - | - | - | yes | execution patterns
  - Zinsight: yes | repetition detection | yes | annotation | yes | - | yes | event flow | event type statistics
  - TuningFork: yes | - | yes | color | - | - | - | yes | -
  - Tracevis: yes | filtering | yes | annotation | - | - | yes | yes | -
  - Triva: yes | - | yes | color | yes | treemap | - | - | -
  - LTTV: - | - | yes | color | yes | - | yes | yes | -
  - Read: the first "Multiple Levels" column (a feature) and the later "multiple levels" column (a visualization type) are different things. LTTV has no mark in the first and a mark in the second. Trace Compass is discussed in the text but has no row.
- **Table 2 (PDF p. 18):** technique | main feature | weakness | use-case.
  - multiple views: different aspects in different views | hard to follow all views together | unrelated aspects: statistics view, execution states, function calls, individual events.
  - multiple levels: related behaviours at different levels with zooming between them | users have to relate the different zoom states | system functions and operations at several levels (user space level to kernel level).
  - focus + context: whole view at once with focus on a selected area | not for very large data or for semi-structured or unstructured data | tree hierarchies, such as active processes and their parent/child relations.
  - space filling: splits the screen between all nodes by their properties | hard to follow the global relationship | statistics and their proportions, such as CPU usage of different processes.

## Ideas we can use
- **Name our reduction step.** When we turn an LTTng kernel trace into "number of read syscalls", "page faults", "time waiting on futex", we are doing what the survey calls metric-based abstraction: a set of events plus an aggregation function per metric. Citing the survey gives this step an established name.
- **Generalization of syscalls.** The read / readv / pread64 example is the same decision we face when a claim says "read the file once": the signal should be the family of read calls, not one syscall name.
- **Per-process split first.** The survey's point that scheduler interleaving mixes processes in a kernel trace is why our signals must be computed per process or thread of the workload, not over the whole trace.
- **Filtering changes the answer.** Other work treats page faults and memory events as noise and filters them out. For us they are a signal. We should state which events we keep.
- **Kernel-trace statistics list (Section 2.2)** is a ready checklist of signals: CPU per process, bytes read or written, number of file accesses, forks, disk latency, network throughput, memory pages.

## Weaknesses and things glossed over
- No survey method is given: no search strategy, no selection criteria, no count of papers. Coverage cannot be judged or repeated.
- No evaluation. The tool judgments (for example "too low level", "does not scale well") are the authors' assessments or come from cited papers. No tool was tested on a common trace.
- Several key citations are the authors' own or their lab's work ([10], [18], [43], [53], [61], [62], [97], [98]), and the only performance figure (Fig. 3) is from their own earlier paper. That is normal for a survey by active researchers, but the comparison "stateful is better" is not independent evidence.
- Fig. 3 has no description of the machine, the patterns or the number of runs in this paper.
- The focus is help for a human analyst (visualization, navigation). Automated analysis and trace comparison are named as applications in Section 2.5 but not surveyed.
- Nothing on tracing overhead, on the accuracy of metrics computed from traces, or on lost events.
- Tool coverage reflects the period before 2016-2017. eBPF and `perf` are not discussed; ftrace is not discussed. Hardware counters appear only through PAPI and a list of HPC tools.
- Small inconsistencies: Table 1 has no Trace Compass row; the LTTV row is blank for "Multiple Levels" but marked for the "multiple levels" visualization type; Fig. 2 is captioned "file read" but shows readlink states; the visualization categories are named "context+focus" in one place and "Focus+Context" elsewhere; the name of the author of [12] is spelled two ways; "directed acyclic graphs (DCA)"; "VizLink" against "VisLink".
- The statement that tracing leads "to the detection of more faults, (performance) problems, bugs and malwares than static analysis" rests on one citation ([14], a malware-analysis survey).
- Several figures are taken from wikipedia.org.
- We have the accepted version. Wording, numbering of figures and pages can differ from the published article.

## Open questions and future work (theirs, and ours)
- Theirs: use multiple levels with semantic zooming in trace tools; model and store links between events at different levels, including non-hierarchical relations; study the cost of drawing links for very large traces; data structures that support more than one hierarchy.
- Ours: which abstraction level is the right one to test a claimed mechanism (single syscalls, generalized "read", or a per-process metric)? How stable are metric-based signals across repeated runs of the same version (our A/A control answers this)?

## Link to our paper
- The key `ezzatijivan2017multiscale` is in `paper/refs.bib`. I found no `\cite` of it in the `.tex` files under `paper/` when writing this note.
- Natural places: Background on kernel tracing (why raw traces are reduced to metrics); Method, where we describe how LTTng events become per-run signals; Related Work on trace analysis.
- Because one author is also our co-author, quote exactly and cite it as a survey. Do not present any tool comparison in it as a measured result.
- See "Connection to Below the Stopwatch" below.

## Link to the thesis (tracing, kernel analysis)
- This is a direct reference for the thesis area. It gives the taxonomy for everything done to a kernel trace after collection: reduce, generalize, aggregate, compute metrics, organise resources, store for fast queries, display.
- LTTng, LTTV, LTTngTop, Trace Compass and the State History Tree are all discussed, with their limits (checkpoints need the raw trace; full history trees are large; no multi-level abstraction or linked events in LTTV and Trace Compass at that time).
- The stateful synthetic event generator ([10], [18]) is the model for writing analyses that share process and scheduling state.
- The stated gap (links between abstract events and raw events, across levels) is still a useful design question for any trace-analysis tool, including one driven by an LLM agent that must go from a high-level finding down to the events that support it.

## Quotes for inline citation
- "Tracing can produce precise and comprehensive information from various system levels, from (kernel) system calls [10, 11, 12] to high-level architectural levels [13]" (Section 1, PDF p. 2)
- "Tracing a software module or an operating system may generate very large trace logs (thousands of megabytes), even when run for only a few seconds." (Section 1, PDF p. 2)
- "The second challenge is the low-level and system-dependent specificity of the trace data. Their comprehension thus requires a deep knowledge of the domain and system related tools" (Section 1, PDF p. 2)
- "there is mostly a discontinuity between the execution of events for a process, because of preemption and CPU scheduling policies." (Section 1, PDF p. 3)
- "the read, readv and pread64 system calls in Linux may be used to read a file. However, from a higher level perspective, all of them can be seen as a single read operation." (Section 2.1, PDF p. 4)
- "another method is to extract some measures and aggregated values from trace events, based on some predefined metrics." (Section 2.2, PDF p. 6)
- "most trace visualization tools operate at a single level of representation, which is not adequate to support multi-level analysis." (Abstract, PDF p. 2)
- "Most existing trace analysis and visualization tools do not consider the linking between events in different levels." (Section 5, PDF p. 17)

## Suggested citation sentences
- Kernel traces are precise but very large and low-level, so they are usually reduced before analysis \cite{ezzatijivan2017multiscale}.
- We reduce each trace to a small set of per-process metrics, a step known as metric-based trace abstraction \cite{ezzatijivan2017multiscale}.
- Following the common practice of generalizing related system calls into one operation \cite{ezzatijivan2017multiscale}, we count all calls of the read family together when a PR claims to read less.
- Because the scheduler interleaves processes in a kernel trace \cite{ezzatijivan2017multiscale}, we compute every signal only over the threads of the workload.

## Connection to "Below the Stopwatch"

- **How it relates:**
  - It supplies the background and the terms for our tracing step. Our mechanism signals (fewer `read` syscalls, fewer page faults, less futex wait) are metrics computed from LTTng kernel events, which the survey classes as metric-based abstraction, with generalization of related syscalls.
  - It is about making traces understandable for a human through abstraction and visualization. It does not use traces to test a claim, does not compare two versions of a program, and has no measurement protocol (no repetitions, no A/A control, no hardware counters beyond a mention of PAPI). Those are our additions.
  - Nothing in it contradicts our approach. Two points call for care. First, it reminds the reader that reduction steps lose information (sampling "may lose information and not preserve the actual system behavior"; filtering removes whole event classes), so a signal computed after reduction is only as good as the events we chose to keep. Second, it gives no evidence on how accurate or how costly trace-derived metrics are; we cannot lean on it for the validity of our signals.
  - It notes that understanding kernel traces "requires a deep knowledge of the domain". That fits our choice to fix the mapping from mechanism to signal in advance, not to let the reader interpret raw traces.
- **Safe to cite for:**
  - Tracing gives precise data down to kernel system calls: "Tracing can produce precise and comprehensive information from various system levels, from (kernel) system calls [...] to high-level architectural levels" (Section 1, PDF p. 2).
  - Traces are large and low-level, so they need reduction: "may generate very large trace logs (thousands of megabytes), even when run for only a few seconds" and "the low-level and system-dependent specificity of the trace data" (Section 1, PDF p. 2).
  - Computing metrics from trace events is an established abstraction method: "extract some measures and aggregated values from trace events, based on some predefined metrics" (Section 2.2, PDF p. 6); it "is widely used in trace visualization tools" (Section 5, PDF p. 16).
  - Related system calls can be treated as one operation: read, readv and pread64 "can be seen as a single read operation" (Section 2.1, PDF p. 4).
  - Kernel traces interleave processes and mix kernel subsystems: "there is mostly a discontinuity between the execution of events for a process, because of preemption and CPU scheduling policies" and "kernel traces usually contain events from different modules (disk blocks, memory, file system, processes, interrupts, etc.)" (Section 1, PDF p. 3).
  - Kernel-trace patterns can reveal performance problems such as "slow disk accesses, lock contention, inappropriate latency, non-optimal memory and cache utilization" (Section 2.5, PDF p. 8). This is the survey reporting other work ([50, 17, 8]); cite it as "surveyed in".
- **Do not cite for:**
  - LTTng's overhead or accuracy. The survey says nothing about either. Use desnoyers2006lttng for the tracer.
  - Any measured comparison of tools. Table 1 is a feature checklist made by the authors, not a benchmark.
  - "Tracing finds more problems than static analysis" as a finding of this paper. It is a one-line statement backed by a citation to another survey.
  - The stateful against stateless timing (Fig. 3) as a result of this paper. It comes from the authors' earlier work [18]; cite that paper if the result is needed.
  - Statements about what Trace Compass can do today. The survey describes the tools as of its writing.
  - eBPF, `perf`, ftrace or hardware performance counters as analysis methods. They are not covered (PAPI and some HPC tools are only named).
  - Using traces to verify performance claims, to compare program versions, or for A/A controls. None of this is in the survey.
  - Journal page numbers. Our PDF is the accepted repository copy.
