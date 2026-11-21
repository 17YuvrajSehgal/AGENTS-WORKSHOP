# The LTTng tracer: A low impact performance and behavior monitor for GNU/Linux
- **Authors:** Mathieu Desnoyers, Michel R. Dagenais (École Polytechnique de Montréal)
- **Venue / year / status:** Proceedings of the Linux Symposium (Ottawa Linux Symposium, OLS), Volume One, July 19-22, 2006, Ottawa, Canada, pp. 209-224. The proceedings list a review committee (mostly industry kernel developers). It is a practitioner symposium paper, not a top research venue.
- **PDF:** related-papers/4-tracing/desnoyers2006_lttng.pdf
- **Cite key suggestion:** desnoyers2006
- **BibTeX-style reference:** Mathieu Desnoyers and Michel R. Dagenais. 2006. The LTTng tracer: A low impact performance and behavior monitor for GNU/Linux. In Proceedings of the Linux Symposium, Vol. 1. Ottawa, Canada, 209-224.

## In short
The paper presents the first design of LTTng, a Linux tracer that records kernel and user-space events with low cost. Its main ideas are per-CPU buffers, lock-free writing with atomic compare-and-exchange, and timestamps read straight from the CPU cycle counter (TSC). The authors measure the cost of one probe (about 288 cycles, 96 ns, on a 3 GHz Pentium 4) and the CPU share of tracing under four loads. On busy but normal loads, tracing used 1.54% to 2.28% of CPU. All numbers come from one old uniprocessor machine and an early LTTng version (0.5.41), so they do not describe modern LTTng 2.x.

## Problem and motivation
- Performance of modern systems depends on many things at once: I/O, drivers, interrupts, lock contention, scheduling, memory. The authors argue that only a whole-system tracer can see all of them together.
- Such a tracer must not change the behavior it observes. `printk`/`printf` are too slow and cannot be used in some code paths, such as NMI (non-maskable interrupt) handlers.
- Timestamps must be precise and monotonic (never go backwards) across many CPU types.
- Earlier LTT had fixed-size types, a monolithic tracer and viewer that were hard to extend, and used NTP-corrected time, which is not monotonic.

## Background / key terms
- **Tracer:** a tool that records a time-stamped list of events (for example "task A switched out, task B switched in") while the system runs, for later study.
- **Post-processing vs pre-processing:** post-processing tools (LTT, K42, LTTng) save raw events and analyse them later. Pre-processing tools (SystemTap, DTrace, Kerninst) compute summaries such as "syscalls per second" on the live machine. The authors prefer raw events because any question can be asked later.
- **Static vs dynamic instrumentation:** static means trace calls are compiled into the code. Dynamic means the tool patches a breakpoint into running code (like gdb). The authors say dynamic probes cost a breakpoint interrupt and are too intrusive for their goals.
- **NMI (non-maskable interrupt):** an interrupt that cannot be turned off. Code inside it cannot take normal locks. A tracer that works in NMI context must be lock-free.
- **Reentrancy:** the trace function can be interrupted by another call of itself (for example an interrupt arrives during tracing) and still work correctly.
- **Compare-and-exchange (CAS):** an atomic CPU instruction that writes a new value only if the old value is still what you expect. It lets many writers reserve buffer space without a lock.
- **Per-CPU buffers:** each CPU writes into its own buffer. This avoids sharing cache lines between CPUs ("false sharing").
- **RCU list:** a data structure that readers can walk without locks. LTTng keeps the list of active traces in one.
- **Flight recorder mode:** buffers are overwritten in a circle, so the tracer keeps only the latest events and never fails for lack of space.
- **TSC (time stamp counter):** a CPU register that counts cycles. LTTng reads it directly and converts cycles to nanoseconds later.
- **RelayFS:** a 2006 kernel mechanism to move large buffers from kernel to user space.
- **LTTV:** the graphical viewer and analysis tool that came with LTTng in 2006.

## Method and setup
- **Hardware:** 3 GHz uniprocessor Intel Pentium 4, hyper-threading disabled. CPU clock calibration 3,000.607 MHz. Motherboard Intel D915-GAG, timer crystal TXC HC-49S with ±30 PPM precision (used for the time-precision test).
- **OS/kernel:** Linux 2.6 era (RelayFS merged in 2.6.14). Exact kernel version: not stated.
- **Software:** LTTng 0.5.41.
- **Microbenchmarks:** 20,000 hits of a probe that writes 4 bytes plus a 20-byte event header. Each hit is surrounded by two TSC reads; the 100.0-cycle average cost of these reads is subtracted.
- **Macrobenchmarks (kernel):** four loads: Mozilla browsing (small), `find` (medium), `find` + `gcc` (high), `find` + `gcc` + ping flood (very high).
- **Macrobenchmark (user space):** gcc compiled with `-finstrument-functions`, compiling a 6.9 KiB C file into a 15 KiB object at -O2, compared with gprof.
- **Metrics:** cycles per probe; CPU % for load, probes and the lttd daemon; data rate (MiB/s); events/s; object code size; NMI timer interval jitter.
- **How tracing CPU % was computed:** probe time = average probe cost (288.5 cycles) × number of probe hits. lttd time = CPU time of the lttd process from the LTTV analysis. Load = wall time minus time in system-call mode of the idle process. So probe overhead is estimated, not measured as a slowdown.
- **Repetitions / statistics:** number of repeated runs not stated. Only min / average / max for probes. No confidence intervals.

## Section-by-section notes
### 1. Tracing goals (p. 209-210)
Low disturbance, architecture independence, full reentrancy, scalability, precision, extensibility, modularity, ease of use. Precise timestamps across CPUs from MHz to GHz.

### 2. Existing solutions (p. 210)
Two classes: post-processing (LTT, K42, IrixView, Tornado) and pre-processing (SystemTap, Kerninst, DTrace, IBM PEM). The authors reject dynamic probes because of breakpoint cost, and note that pre-processed data can still be logged into a tracer.

### 3. Previous works (p. 211)
LTT (cross-platform, but fixed type sizes, monolithic, non-monotonic NTP time). RelayFS (kernel to user data relay). K42 (lock-free tracing with compare-and-exchange; LTTng borrows this). PEM (shared XML event description ideas).

### 4. The LTTng approach (p. 211-218)
- **4.1 Control:** user tool `lttctl`, daemon `lttd` that writes buffers to disk, kernel modules (`ltt-core`, `ltt-heartbeat` for 32-bit cycle counter overflow, `ltt-facilities` for event type lists, `ltt-statedump` for the initial process/file state), and built-in `ltt-base`. Control goes through a netlink socket.
- **4.2 Data flow:** events go into RelayFS circular buffers; full sub-buffers go to `lttd`. A user-space fast path (`libltt-usertrace-fast`) exists.
- **4.3 Instrumentation:** events are described in XML; a code generator (`genevent`) creates the tracing functions. Supports host-size integers, floats, enums, strings, nested arrays, structures, unions.
- **4.4 Event type registration:** event types are grouped into "facilities"; user space cannot register names that conflict with kernel facilities. Type sizes are stored so 32-bit and 64-bit traces can be read.
- **4.5.1 Reentrancy:** writing an event is: compute size, reserve space with a CAS loop (timestamp taken inside the loop so timestamps grow with buffer offset), copy data, commit. A sub-buffer is readable when reserved bytes equal committed bytes. If buffer is full in normal mode, the event is dropped and a lost-event counter goes up. Flight recorder mode never fails.
- **4.5.2 Scalability:** per-CPU data and lock-free writes. On a 3 GHz Pentium 4: CAS 29 cycles without LOCK prefix, 112 with; atomic increment 7 and 93; spinlock with interrupts disabled 214 cycles. LTTng needs only non-locked versions (per-CPU), so 43 cycles vs 214, "five times faster".
- **4.5.3 Time precision:** kernel time uses integer scaling made for scheduling, not for precise timestamps. LTTng reads the TSC and uses `cpu_khz` for calibration. A heartbeat timer extends 32-bit counters to 64 bits.
- **4.5.4 User-space tracing:** slow path is a system call per event (no library needed). Fast path is a per-thread companion process writing shared-memory buffers to disk, so trace writing is charged to another process.

### 5. LTTV viewer (p. 218-219)
Plugin-based viewer written in C with GTK. Rebuilds kernel state over time, keeps statistics, has a logical-expression event filter, handles multi-GB traces.

### 6. Results (p. 219-222)
- **Table 1 (microbenchmarks):** kernel tracing disabled: 0 cycles average (max 338). Kernel tracing active: min 278, average 288.5, max 6,997 cycles. User-space fast library: average 297.0 (max 88,913). User-space through system call: average 1,042.2 (max 329,062). The key number is 288.5 cycles = 96.15 ns per probe.
- **Latency impact:** interrupt entry/exit probes add twice the probe time to low-priority interrupt latency: 577 cycles (192.29 ns). Scheduler instrumentation adds the same 577 cycles to a task switch. A detail (`preempt_enable_no_resched()`) can make the scheduler miss a timer interrupt.
- **Table 2 (kernel macrobenchmarks):** see below. Busy loads: tracing CPU 1.54% to 2.28%. Ping flood: probes 8.5% plus lttd 0.96%.
- **Table 3 (user space, gcc function entry/exit):** not instrumented 0.446 s; gprof 0.774 s (1.73×); LTTng null output 1.553 s (3.22×, 153.25 MiB/s, 238 MiB of trace); LTTng disk output 3.197 s (74.44 MiB/s). LTTng is 2× slower than gprof with /dev/null output and 4.13× with SATA disk output.
- **Table 4 (object size):** 2,288 to 2,432 bytes per instrumentation site; size varies at most 3.3% from the average.
- **Table 5 / Figure 7 (time precision):** NMI watchdog timer intervals traced: average 3,999,339 ns, min 3,994,844, max 4,004,468, standard deviation 52 ns, max deviation 5,075 ns. 52 ns per 4 ms means 13 µs per second, so 13 PPM frequency error, within the 30 PPM crystal spec.

### 7. Conclusion (p. 222-223)
"About 2% of CPU time on a heavy workload". Lock-free, works in NMI context. Future: time synchronisation between cluster nodes, L1 cache impact profiling.

## Key results (with numbers) and what they mean
- **288.5 cycles (96 ns) per kernel event** -> on that 2006 CPU, each recorded event costs about 0.1 µs. Total cost grows with the number of events, not with the run length.
- **1.54% to 2.28% CPU on busy loads** -> for normal workloads the tracer is cheap. But this is probe-time estimate plus lttd CPU, not a measured slowdown of the workload.
- **9.46% CPU (8.5% probes + 0.96% lttd) under ping flood** -> the cost depends strongly on event rate. A syscall-heavy load (884,545 events/s) costs about four times more than a normal busy load. The "about 2%" headline leaves this case out.
- **577 cycles added to each scheduler switch and interrupt** -> tracing slightly delays scheduling. For latency-sensitive work, this can matter.
- **Writing the trace to disk doubled the user-space trace time (1.553 s -> 3.197 s)** -> trace I/O can become the bottleneck. This is the same effect that the DepGraph paper later saw (42% overhead on an I/O benchmark).
- **±5 µs worst case, 52 ns standard deviation for timestamps** -> TSC timestamps are precise enough to order kernel events and measure µs-level waits.

## Tables and figures
- **Figure 1-5:** architecture diagrams (control, data flow, instrumentation, registration, tracing paths). They show 2006 components (`lttctl`, `lttd`, RelayFS, `ltt-facilities`), which are gone in modern LTTng.
- **Figure 6:** one instrumentation site: inputs are call-site data and trace control from `ltt-base`; output is a write to per-CPU RelayFS buffers.
- **Table 1:** probe cost per hit. Read the "average" column. The max values in user space (88,913 and 329,062 cycles) are interrupts and scheduling noise, not tracer cost.
- **Table 2:** columns are load CPU %, probes CPU %, lttd CPU %, data rate (MiB/s), events/s:

  | Load | Test | load % | probes % | lttd % | MiB/s | events/s |
  |---|---|---|---|---|---|---|
  | Small | mozilla | 1.15 | 0.053 | 0.27 | 0.19 | 5,476 |
  | Medium | find | 15.38 | 1.150 | 0.39 | 2.28 | 120,282 |
  | High | find + gcc | 63.79 | 1.720 | 0.56 | 3.24 | 179,255 |
  | Very high | find + gcc + ping flood | 98.60 | 8.500 | 0.96 | 16.17 | 884,545 |

  How to read: tracing cost = probes + lttd. It rises with events/s, not with load %.
- **Table 3:** user-space function tracing cost vs gprof (see above).
- **Table 5 / Figure 7:** traced NMI timer intervals around 4 ms; the flat band shows stable timestamps.

## Ideas we can use
- Report tracing cost as a function of **event rate**, not only as one percentage. Our ~7% CPU on the coding task can be explained the same way: Claude Code plus test runs produce many syscalls and scheduler events.
- Separate the cost into **probe cost** (inside the traced tasks) and **consumer daemon cost** (lttd, today `lttng-consumerd`). If the consumer runs outside the agent's cgroup, its CPU is not charged to the agent's quota. Worth stating in our Study Design.
- Use the TSC-based timestamp argument to justify µs-level wait splits.
- Flight recorder mode is a way to trace long runs cheaply (keep only the last window, for example around an OOM kill).

## Weaknesses and things glossed over
- **Very old hardware:** one 3 GHz uniprocessor Pentium 4 with hyper-threading off. No multi-core measurements, even though scalability is a stated goal. Numbers do not transfer to modern multi-core CPUs or to cloud VMs.
- **Old software:** LTTng 0.5.41 with RelayFS and kernel patches. Modern LTTng 2.x (we use 2.15) has a different architecture (session daemon, consumer daemon, its own ring buffer, CTF format). This is from general knowledge, not from the paper.
- **Overhead is estimated, not measured:** probe CPU % = average probe cost × hits. No end-to-end runtime comparison with and without tracing for the kernel loads.
- **Headline "about 2%"** leaves out the ping-flood case (about 9.5%).
- No repetitions, no variance, no confidence intervals.
- Workloads are small and informal (Mozilla browsing, `find`, `gcc`, ping flood).
- The paper notes a possible missed timer interrupt from `preempt_enable_no_resched()` but does not measure how often.
- L1 cache impact is mentioned but "planned", not measured.

## Open questions and future work (theirs, and ours)
- Theirs: cluster-wide trace analysis with time synchronisation; L1 cache profiling of instrumentation; network output for traces.
- Ours: what is the per-event cost of LTTng 2.15 on our Intel and AMD GCE VMs? Does the consumer daemon's disk writing compete with the agent under `io.max` limits? Does tracing cost change when the agent is CPU-throttled by `cpu.max` (probes run inside the throttled task's time)?

## Link to our paper
- **Agree / extend (Study Design, Threats):** our measured tracing cost (~7% CPU, no visible wall-time change, also under limits) fits their finding that cost scales with event rate. Our 7% is between their busy case (2.3%) and their ping-flood case (9.5%). Our workload is syscall-heavy, so this is expected.
- **Extend:** we measure cost under cgroup limits and compare trace CPU to `cpu.stat` (agreement within 1.5%). This paper has no such validation. We can cite it as the origin of the tool and say our overhead check is done on modern hardware.
- Use in **Related Work** as the original LTTng reference, and in **Study Design** when we say why LTTng (low overhead, precise per-CPU timestamps, full kernel view).
- Do not use its numbers as current overhead evidence. Say clearly that the 2006 numbers are from a Pentium 4.

## Link to the thesis (tracing, kernel analysis)
- Explains why LTTng timestamps are trustworthy for wait analysis: per-CPU buffers plus TSC timestamps taken inside the reservation loop, so events in one buffer are ordered.
- The "lost events" counter matters for us: if buffers fill during a burst (for example `pytest` spawning many processes), events can be dropped and thread states can become wrong. We should check and report lost-event counts per run.
- Per-event cost × event count is a simple model we can fit on our own data (events/s vs trace CPU %) to show tracing cost per run phase (start-up, model wait, tool time).
- Flight recorder mode could support a cheaper "always-on" agent monitor that dumps a snapshot only when an OOM kill or throttle storm happens.

## Quotes for inline citation
- "LTTng allows tracepoints in NMI code, multiple simultaneous traces and a flight recorder mode." (p. 209)
- "A low impact, high performance, tracing system may therefore be the only tool capable of collecting the information produced by instrumenting the whole system, while not changing significantly the studied system behavior and performance." (p. 209-210)
- "LTTng uses the CPU timestamp counter and its most accurate calibration." (p. 217)
- "The key result in Table 1 is the average 288.5 cycles (96.15ns) spent in a probe." (p. 219)
- "The total cpu time used by tracing on a busy system (medium and high load scenarios) goes from 1.54 to 2.28%." (p. 220)
- "LTTng is a low disturbance tracer that uses about 2% of CPU time on a heavy workload." (p. 222)

## Suggested citation sentences
- We trace the kernel with LTTng \cite{desnoyers2006}, which writes events into per-CPU, lock-free buffers with cycle-counter timestamps, so it can record every scheduler event and system call with low cost.
- The original LTTng paper reported 1.5% to 2.3% CPU for tracing on busy loads, and more on syscall-heavy loads \cite{desnoyers2006}. Because those numbers come from a 2006 single-core machine, we measure the cost of LTTng 2.15 again on our VMs (Section X).
