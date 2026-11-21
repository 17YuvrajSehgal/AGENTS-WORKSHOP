# Wait Analysis of Distributed Systems Using Kernel Tracing
- **Authors:** Francis Giraldeau, Michel Dagenais (Polytechnique Montréal)
- **Venue / year / status:** IEEE Transactions on Parallel and Distributed Systems (TPDS), vol. 27, no. 8, pp. 2450-2461, August 2016. Peer-reviewed journal. Received Dec. 2014, accepted Oct. 2015, published online Oct. 2015. DOI 10.1109/TPDS.2015.2488629. Our PDF is the PolyPublie open-access copy of the published version.
- **PDF:** related-papers/4-tracing/giraldeau2016_wait-analysis.pdf
- **Cite key suggestion:** giraldeau2016
- **BibTeX-style reference:** Francis Giraldeau and Michel Dagenais. 2016. Wait Analysis of Distributed Systems Using Kernel Tracing. IEEE Transactions on Parallel and Distributed Systems 27, 8 (Aug. 2016), 2450-2461. https://doi.org/10.1109/TPDS.2015.2488629

## In short
The paper finds why a task waits, using only kernel events (scheduler, interrupts, network packets), with no change to the application. When a thread blocks, the event that wakes it up tells who it was waiting for: another thread, a timer, a disk, or a network packet from another machine. The authors build an execution graph from the trace and walk it backwards from each wake-up to get the "active path" (what really decided the task's elapsed time), even across machines. They test it on a small RPC program and five real systems (Java RMI, CIFS share, Django web app, Erlang, MPI). Tracing cost was 18% in the worst case (tight RPC loop) and about 5% for a typical web request; the analysis runs in linear time.

## Problem and motivation
- Normal profilers (perf sampling, Valgrind) show where CPU time goes. They do not show time spent waiting, and they see only one host.
- Middleware-specific instrumentation (Dapper, Magpie, MPE) works, but each runtime needs its own work, and it ties the tool to one language or framework.
- Syscall tracing is not enough: network sends can happen from interrupt context, kernel threads, and many syscalls, not only `send()`/`recv()`.
- Network-only tracing (tcpeval) sees the wire but not what happens inside each host.
- Goal: explain the elapsed time of a computation in a distributed, multi-language system, using only operating system events.

## Background / key terms
- **Four task states:** running (on a CPU), preempted (ready but not running), interrupted (an interrupt handler runs on top of it), blocked (waiting for an event, CPU given up). Everything except running stops progress.
- **Preemption:** the scheduler takes the CPU away, for example at the end of a time slice. The paper says the cause of preemption is the tasks running on that CPU.
- **Blocking and wake-up:** a blocked task sits on a wait queue. The event that wakes it (the "wake-up event") shows the real cause of the wait. If another task wakes it, that task was the dependency. If an interrupt wakes it, the interrupt type (timer, disk, network) tells the cause.
- **sched_ttwu:** a custom event the authors add with a kprobe on `try_to_wake_up()`. The normal `sched_wakeup` tracepoint ran on the target CPU inside an inter-processor interrupt, which loses who did the wake-up. Their kprobe fires on the waker's side.
- **softirq / ksoftirqd:** deferred interrupt work (packet receive, timers). Under heavy load it moves into the `ksoftirqd` kernel thread.
- **Netfilter hooks:** kernel hooks used here to record TCP packet headers on receive (`inet_sock_local_in`) and send (`inet_sock_local_out`), so a send on one host can be matched to a receive on another.
- **Trace synchronisation:** each host has its own clock. The convex hull method fits a line (offset and drift) between two clocks using many send/receive pairs, so that every receive comes after its send.
- **Execution graph:** a 2-D doubly linked list. Horizontal edges are one task's states over time. Vertical edges are wake-ups or network packets between tasks.
- **Active path:** the task's timeline where every blocked interval is replaced by the work of whatever unblocked it, recursively. It is a form of critical path.
- **Busy wait:** spinning in user space while waiting. The kernel sees it as running, so this method cannot see it.

## Method and setup
- **Steps:** start tracing on every host, run the program, stop tracing, gather traces, synchronise, build the execution graph, compute the active path, show it in a viewer.
- **Events (Table 1):** `sched_ttwu` (kprobe), `sched_switch`, `hrtimer_expire_entry/exit`, `irq_handler_entry/exit`, `softirq_entry/exit` (tracepoints), `inet_sock_local_in/out` (netfilter). Implemented as loadable kernel modules that work with an unmodified kernel.
- **Tracer:** LTTng (2.4). The authors say perf could also be used: "an implementation detail".
- **Algorithm 1 (graph build):** one pass over events. `sched_switch` closes the previous task's interval as running and the next task's as preempted. `sched_ttwu` closes the target's interval as blocked, the source's as running, and adds a vertical wake-up edge. Interrupt entry/exit push and pop a per-CPU placeholder "interrupt task". Packet send adds a vertex and stores the packet; matching receive adds a vertex and a vertical network edge.
- **Algorithm 2 (active path):** walk the task forward. On a blocked edge that has an incoming wake-up, walk backward from the waker until the start of the blocked interval, following network edges and nested blocking recursively. Both algorithms are O(n) in number of events.
- **OS / software:** Ubuntu 14.04, Linux 3.13, LTTng 2.4. Analyzer in Java as Eclipse plug-ins. Code on GitHub.
- **Hardware:** local and VM experiments on Intel i7-4770, 16 GB RAM, 1 TB SSD; VMs with KVM. Bare-metal cluster: 4 nodes, each dual-core AMD Opteron 246, 4 GB RAM, 100 GB disk, dedicated Gigabit Ethernet.
- **Workloads:** `wk-rpc` (their minimal C RPC), Java RMI compute-π example, Samba/CIFS share with `ls`, Django Poll app (Apache + WSGI + PostgreSQL, 3 KVM tiers), Erlang echo server, OpenMPI imbalanced computation with `MPI_Barrier`. For overhead: `netperf` (16 KiB messages), `wk-rpc` tight loop (32-byte messages), `wkdb` (Django Poll).
- **Statistics:** mean differences with 95% confidence intervals and p-values for latency changes; t-tests with t(10) for the optimisation results; R² for daemon CPU vs event rate. Number of repetitions for the latency experiments: not stated. CPU governor set to `performance`.

## Section-by-section notes
### 1. Introduction (p. 2450-2451)
Contributions: kernel instrumentation design; graph model and active path algorithm; experiments on real software by host type, architecture and network conditions; cost evaluation; two optimisations. Not a goal: recovering request flow inside application protocols. If one thread serves many requests at once, user-space instrumentation is still needed.

### 2.1 OS trace of a distributed system (p. 2451-2452)
Defines the four states. Key idea: the wake-up source is the cause of the wait. `select()` example: wake-up from a local writer, from the timer (timeout), or from a network interrupt (remote sender). The analysis does not depend on which syscall blocked. Limitation: busy waiting is invisible; the authors argue network delays are an order of magnitude longer than CPU work, so most programs block. Figure 1 shows `netcat` sending a short string: 8 TCP messages; the active path follows FIN-ACK, SYN-ACK and SYN backward across hosts.

### 2.2 Trace synchronisation (p. 2452-2453)
NTP (millisecond accuracy) is too coarse for µs network latencies. Lamport clocks give order but not durations. Controlled Logical Clock shifts inverted messages but needs prior sync. Chosen: convex hull method (Duda et al.), giving a linear transform f(t) = mt + b per host pair. Transforms are composed along a graph of hosts to one reference host. Long traces (over about one hour) may need sub-intervals because crystal drift is not linear. Figures 2-3 show a three-host example.

### 2.3 Trace analysis (p. 2453-2454)
Execution graph definition, Algorithm 1 and Algorithm 2 (described above). Send vertex is added immediately, before the matching receive is seen, to keep linear time.

### 3. Evaluation (p. 2454-2458)
- **3.1 Host type:** RPC between processes on one host (loopback), two KVM VMs, and two physical machines. Same graph structure in all three. VMs need sync because each VM scales the TSC itself. Difference: locally, a large send may be preempted by the receiver instead of blocking. Shared memory (for example OpenMPI on one host) changes local behavior; waits via `futex()` are still captured.
- **3.2 Network conditions (Fig. 4):** `tc` adds 0 ms, 10 ms, 100 ms latency to `wk-rpc` between VMs. Network share of the active path grows with latency. DNS lookups at the start appear as unresolved network wait, because the DNS server is not traced. Bandwidth test (Apache + `wget`): almost all wait is network delay, even without a limit.
- **3.3 Asynchronous processing (Fig. 5):** client busy-loops 0%, 50%, 100% of the server time before reading. The blocking window shrinks; at 100% the client never blocks and the server disappears from the active path. Event loop with `poll()` and 16 ms timeouts (like a 60 Hz GUI): only the last blocking interval is linked to the server; the earlier three are timer timeouts. So the analysis under-states the real wait for the resource in event loops. Listed as future work.
- **3.4 Use cases:** Java RMI (client waits twice for the registry, three times for the compute server). CIFS: `ls` waits in `newstat()` and `getdents()` because the VFS sends packets; the `cifsd` daemon receives answers and wakes the client, visible only because tracing is system-wide. Django Poll: control moves often between Apache worker and PostgreSQL; PostgreSQL blocks in `fdatasync()` at the end. Erlang: works; the last of 10 round trips does not reach the server because the client was preempted just before blocking (smaller blocking window). MPI: OpenMPI barrier busy-waits with non-blocking `poll()`, so it looks like normal running; `mpi_yield_when_idle` only adds `sched_yield`. OpenMP with `OMP_WAIT_POLICY=PASSIVE` blocks, so the imbalance becomes visible.
- **3.5 Analysis cost (Fig. 11-13):** total tracing cost about 200 ns per event. `netperf`: 424 Mbit/s with and without tracing. `wk-rpc` tight loop: latency +18.3%, 155.9 µs to 190.8 µs (mean difference 34.9 µs, 95% CI 34.7 to 35.1, p < 0.01); mostly a constant shift; a small second mode about 5 µs below the main one, unexplained. `wkdb`: +5.1%, 116.3 ms to 122.5 ms (mean difference 6.3 ms, 95% CI 4.8 to 7.7, p < 0.01). Consumer daemon CPU: 0.8% to 8.2% of one CPU, proportional to event rate (R² = 0.91). Interrupt events are the most frequent in all three workloads (about 58-65% in Fig. 12). Scalability: traces of up to 1,024 HTTP requests (about 500 MB); both algorithms linear; reading the trace is about half of graph build time; graph build is two orders of magnitude slower than path extraction; active path for the largest trace in under 0.5 s.

### 3.6 Analysis optimisations (p. 2459)
- Two-step synchronisation (shift traces to a common origin, coarse sync until hosts are connected with transform precision better than 1%, using weighted quick-union find; expire old unmatched packets): peak memory 319× lower on a 126 MB three-tier trace, processing time +16.8% (95% CI 14.5 to 19.1%, t(10) = 14.1, p < 0.01).
- Fast integer timestamp transform (Algorithm 3, scaled slope with c = 2^30, bit shifts): 2^25 timestamps in 65 ms vs 10.1 s with Java BigDecimal, 155× faster; trace reading time −20.8% (95% CI 16.4 to 25.3%, t(10) = 9.2, p < 0.01).

### 4. Future work (p. 2460)
Reduce interrupt events (carry interrupt context per event instead of entry/exit events). Constant-memory analysis (build a tree of blocking intervals bottom-up and delete resolved vertices). Cache-cold reading was only 2% slower, so analysis is CPU-bound and could be parallel. Link the active path to source code with user-space tracing, call stacks, and performance counters.

### 5. Related work (p. 2460)
Hollingsworth critical path (CPU only, no I/O wait). Panappticon (Android UI, client only). tcpeval (TCP packets only, two hosts, NTP). Request tagging (Magpie, Dapper; server side only). MPE/Jumpshot (MPI only). BorderPatrol (library interposition, fails for static binaries). vPath (hypervisor, needs VMs). Syscall-based methods make wrong assumptions in the general case.

### 6. Conclusion (p. 2460)
Blocking marks a change in control flow; the wake-up source names the wait cause; works across hosts synchronised with convex hull; moderate cost.

## Key results (with numbers) and what they mean
- **About 200 ns per event** -> tracing cost depends on how many events the workload produces, not on how long it runs.
- **+18.3% latency in a tight 32-byte RPC loop (155.9 -> 190.8 µs)** -> the worst case is a workload made almost only of syscalls and packets. Each request had about 35 µs of tracing added.
- **+5.1% latency for a real web request (116.3 -> 122.5 ms)** -> for realistic request work, cost is small. This is closer to our agent case, where most time is model wait.
- **424 Mbit/s with and without tracing** -> bulk network throughput was not affected.
- **Consumer daemon 0.8% to 8.2% of one CPU, R² = 0.91 with event rate** -> again, event rate decides the cost.
- **Interrupts are the most frequent events** -> to cut cost for this analysis, trace fewer interrupt events.
- **Linear analysis time; active path in under 0.5 s for a 500 MB trace** -> the method scales to large traces once the graph is built. Building the graph is the slow part.
- **Event-loop caveat** -> with timeout-based loops, only the last blocking interval is linked to the real cause. Earlier intervals look like timer waits.

## Tables and figures
- **Table 1:** the minimal event list for wait analysis. Useful as a checklist for our LTTng session: scheduler switch, wake-up (with waker), timer, IRQ, softirq, network in/out.
- **Fig. 1:** task states and TCP packets for `netcat`. Shows how the active path jumps between hosts by following packets backward.
- **Fig. 2-3:** host synchronisation graph and composed timestamp transforms.
- **Fig. 4:** active path of `wk-rpc` at natural, 10 ms and 100 ms latency. Pink = unresolved network wait, green = CPU. As latency grows, pink dominates.
- **Fig. 5:** active path with 0%, 50%, 100% asynchronous work, and with an event loop. Shows that overlap hides the dependency.
- **Fig. 6-10:** use-case paths (RMI, CIFS, Django POST across 3 tiers, Erlang, MPI with user-space overlay).
- **Fig. 11:** latency density with and without tracing for `wk-rpc`. Two peaks about 30-35 µs apart: tracing shifts the whole distribution right by a nearly constant amount.
- **Fig. 12:** share of event types (irq, net, sched) per workload. Interrupts are the largest share for `netperf`, `rpc` and `wkdb`.
- **Fig. 13:** analysis time vs number of requests; read, build and extract are all linear.

## Ideas we can use
- **The wake-up source is the cause of the wait.** This is exactly our need for splitting agent time. For Claude Code (a Node.js process): a block woken by a network softirq for the API socket = model wait; a block in `wait4`/pipe read woken by a child process = tool time; a block woken by a disk interrupt = disk wait; preempted/runnable time = CPU wait.
- **Unresolved network wait** (Fig. 4, DNS case) is the same as our model wait: the remote host (the model API) is not traced, so the active path stops at the network edge. We can name model wait as "unresolved remote wait" in their terms.
- **Active path through tool subprocesses:** when the agent blocks on a tool (bash, pytest), the active path follows into the child process and its own waits (CPU throttling, disk, reclaim). This gives a per-tool breakdown that cgroup counters alone cannot give.
- **Event-loop caveat applies to Node.js.** libuv blocks in `epoll_wait` with timers. Like their 16 ms `poll()` example, some blocks end on a timer and are not linked to the real cause. We should state this as a threat to validity for any wake-up-based split.
- **Report overhead with CIs and as an absolute shift**, like Fig. 11. We could show the distribution of local time with and without tracing.

## Weaknesses and things glossed over
- **Preemption cause is too simple for cgroups.** The paper assigns preemption to "the tasks running on the corresponding CPU". Under cgroup v2 `cpu.max` throttling, a runnable task can wait while its CPU is idle, because its cgroup used up its quota. The paper's model would blame the wrong thread or no thread. This is the main gap for our study.
- **Busy waiting is invisible** (they say so). Spinning runtimes (OpenMPI, some JIT or GC threads) look like useful running time.
- **Event loops and async I/O** are only partly handled; listed as future work.
- **Old setup:** Linux 3.13, LTTng 2.4, 2013-era Intel and very old AMD Opteron 246 nodes. Overhead numbers may not hold today.
- **Small and hand-picked workloads:** mostly toy RPC and tutorial apps. No large production system.
- **Number of repetitions** for latency overhead not stated, although CIs are given.
- **Custom kprobe and netfilter modules** are needed; portability to newer kernels is not discussed.
- **No accuracy check** of the active path against ground truth (for example against injected delays with known size), except the qualitative latency test in Fig. 4.
- **Memory:** graph size grows with events; whole graph must fit in memory.
- The small second mode in Fig. 11 is left unexplained.

## Open questions and future work (theirs, and ours)
- Theirs: fewer interrupt events; constant-memory analysis; parallel trace processing; linking the active path to source code via user-space traces, stacks, counters; better handling of event loops; resolving DNS waits when the DNS server is traced.
- Ours:
  - Can we add a "throttled" state to the execution graph, from cgroup throttling (for example `cpu.stat` `nr_throttled` changes, or CFS bandwidth events), so CPU wait is split into "quota" vs "busy core"?
  - For memory limits, can we follow reclaim and OOM-kill events into the active path (for example the agent blocked in direct reclaim, or a test killed by the OOM killer)?
  - How much of the agent's active path is model wait vs tool vs own work, and does the active path differ from our simple wall-time split?

## Link to our paper
- **Agree (Study Design):** our "running / waiting for CPU / sleeping (disk, reclaim, other)" split follows this paper's four task states and wake-up-source reasoning. Cite it as the basis of our wait analysis ("following kernel wait analysis").
- **Extend (Study Design, RQ on breaking points):** we add the cgroup quota as a cause of CPU wait, which this paper does not model. Our "waiting for CPU (quota or busy core)" split is a direct extension.
- **Agree (RQ1, model wait hides machine cost):** their Fig. 4 shows that when network latency grows, the network part dominates the active path. This is the same reason our wall slowdown = 1 + f(s−1): the model wait part of the path is not affected by local limits.
- **Threats:** event-loop caveat for Node.js; busy waiting invisible; tracing overhead depends on event rate (their 5% to 18% vs our ~7% CPU).
- **Related Work:** a main citation for kernel-trace-based critical path / wait analysis.

## Link to the thesis (tracing, kernel analysis)
- **Critical path through model wait vs tool time:** build the execution graph from our LTTng traces for the main Claude Code thread(s). Blocked intervals woken by network softirq on the API socket = model wait (unresolved remote). Blocked intervals woken by a child exit or pipe write = tool time; the path then recurses into the tool's process tree. Remaining running intervals = agent's own work. Comparing this active path with our event-stream split would validate our phase split from the kernel side.
- **Waiting dependency graph for CPU-quota throttling:** add a vertex type "cgroup quota" for intervals where a task is runnable but its cgroup is throttled. Then CPU wait can be split into "quota" (machine limit) and "contention" (another thread on the same core). This is new and fits a thesis contribution.
- **Wake-up source events in LTTng 2.15:** the paper needed a kprobe because `sched_wakeup` lost the waker. Newer kernels have a `sched_waking` tracepoint fired on the waker side (general knowledge, not from this paper). We should check that our full-profile traces contain it and use it.
- **Memory pressure:** extend the graph with reclaim (blocked in direct reclaim, woken by kswapd or by reclaim completion) and OOM kill events, so silent kills inside tests show up as broken edges in the tool's path.
- **Overhead model:** fit "trace CPU % vs events/s" on our runs, as they did with R² = 0.91 for the consumer daemon.
- **Scalability:** their linear algorithm and "graph build dominates" result suggest we can run this on all 2,114 runs if we stream per run.

## Quotes for inline citation
- "Such wait dependencies are invisible to instruction profilers." (p. 2450, abstract)
- "All states other than running prevent the program from making progress and should be reduced whenever possible." (p. 2451)
- "The key idea is that the event unblocking the task (thereafter referred as the wake-up event) indicates the cause of the wait, which is unknown a priori and is non-deterministic in general." (p. 2451)
- "Busy wait in user-space is not visible from the operating system." (p. 2451)
- "We define the active path of execution as the execution path where all blocking edges are substituted by their corresponding subtask." (p. 2454)
- "The total tracing cost is proportional to the number of events produced and is about 200 ns per event." (p. 2457)
- "We found that the worst case tracing overhead for a distributed application is 18 percent and that the typical average overhead is about 5 percent." (p. 2450, abstract)

## Suggested citation sentences
- Following kernel wait analysis \cite{giraldeau2016}, we split each thread's time into running, waiting for a CPU, and sleeping, and we use the wake-up source to tell why a thread slept.
- Wait analysis assigns CPU waiting to the threads that hold the CPU \cite{giraldeau2016}; under a cgroup CPU quota a thread can also wait while its core is idle, so we add the quota as a separate cause.
- Earlier work measured kernel tracing costs of about 5% for web requests and up to 18% for tight RPC loops \cite{giraldeau2016}; on the agent workload we measure about 7% CPU and no visible change in wall time.
