# AGENT 2027 workshop paper: ideas

Written 2026-11-19. Source of the numbers: memory notes, not yet re-checked
against the row files. Every number below must be re-derived before it goes
into a paper.

## The workshop

- AGENT 2027: International Workshop on Agentic Engineering, co-located with
  ICSE 2027 (Dublin, 25 April to 1 May 2027).
- Call: https://conf.researchr.org/home/icse-2027/agent-2027#call-Call-for-Papers
- **Submission deadline: 20 November 2026 AoE. The page says it is firm.**
- Notification: 11 December 2026. Camera-ready: 29 January 2027.
- Full paper: up to 8 pages. Short paper: up to 5 pages (position, emerging
  research, tool, benchmark, or experience). Both limits include references.
  Extra pages cannot be bought.
- IEEE conference template. Submission through HotCRP.
- Review is single-anonymous (our names are on the paper).
- No concurrent submission of the same work to another refereed venue.
- arXiv preprints are allowed.
- AI help with grammar is allowed. Substantive AI-generated text, figures or
  code must be disclosed in the acknowledgments.
- Published by IEEE. One author must register and present in person.

What they ask for: empirical evidence, reusable methods, operational lessons
and open problems on building agents.

Topics that match our work:

- Architecture, orchestration, tool use, memory, protocols
- AgentOps, observability, runtime monitoring, intervention
- Empirical studies, industrial case studies, deployment lessons
- Agentic systems supporting maintenance and operations

## Constraint

About two days are left. There is no time for new experiments. The paper has
to come from data we already have.

## Main idea: a 5-page experience paper

**Working title:** "Instructed Is Not Enforced: What an LLM Agent Skips When
Tool Use Is Optional"

**Claim:** when an agent's result depends on a behaviour, telling the model to
do it in the prompt is not enough. The model skips it at scale. The behaviour
must be built into the structure of the agent.

**Evidence:** the C7 fault localization agent, v1 run, 168 instances
(2026-11-01).

| Behaviour the prompt asked for | What happened in v1 | Structural fix | After |
|---|---|---|---|
| Consult incident history (`recall_incidents`) | 0.32 calls per run | Pre-run it in the setup phase and pass the results as evidence. It is a local BM25 lookup, so no extra model calls. | always present |
| Walk back to callers (`callers_of`) | 1 use in 168 runs | Fold the callers into the return value of `search_symbol`, which the model already called 3.7 times per run | arrives unasked; the separate tool is still never chosen (0.01 calls per run) |
| Record evidence (`note_candidate`) | 37% of runs recorded nothing | Make `evidence` a required field of the submit tool's schema | 0% |
| Submit an answer | Some runs used all 14 turns and never submitted | Reminder at 3 turns left, forced `tool_choice` on the last turn | to be measured |

Extra observation: runs that recorded no evidence were also the failing ones.
0.8 notes per run when the fault was missed, 2.2 when it landed in the top
five.

**The reusable method (the contribution):**

1. List everything the result depends on.
2. For each item ask: "what happens if the model does not do this?"
3. If the answer is "the result is wrong", it must not be an instruction.
   Pre-run it, make it a required schema field, or fold it into a tool the
   model already uses.
4. Log tool-call counts per run from the first pilot. A tool used 0.01 times
   per run cannot be seen by reading transcripts one at a time.

**Why it fits the workshop:**

- Matches "architecture, tool use, memory" and "AgentOps, observability,
  runtime monitoring".
- It is an operational lesson with numbers and a method others can reuse.
- It does not overlap with the C7 paper. None of these numbers and no mention
  of `callers_of` appear in the C7 `.tex` files (checked with grep).

## Optional second case: more tools can hurt

From the ARISE ReAct work on the OB dataset (Phase 2 and 3, June 2026):

- All 16 subsets of 4 evidence tools were tested.
- Only the similar-incident tool (peers) helped: +0.0151 Hit@1, but not
  significant (p = 0.18).
- The trace tool alone was significantly harmful: Δ Hit@1 = −0.018,
  CI [−0.033, −0.006], p = 0.002.
- On OTel and WoL the lift was exactly zero.

Together the two cases say: models skip the tools you need, and extra tools
can hurt. So measure tool use per run and ablate per tool.

Only add this if the result is not being kept for the paused FSE/EMSE paper.
With it, the paper could grow to a full 8-page paper, but 5 pages is safer in
two days.

## Suggested outline (5 pages)

1. Introduction: prompts describe a method, but the model treats steps as
   optional.
2. Setting: a fault localization agent with code-search tools and an incident
   memory. Described generically.
3. What was skipped: the v1 measurements.
4. Structural fixes and what changed.
5. (Optional) The tool ablation case.
6. Lessons and checklist.
7. Threats: one agent, one model family, 168 instances in v1.

## Things to check before committing

- **Data on disk.** A quick search did not find the v1 run files. The v1
  numbers come from a memory note that is 17 days old. The ReAct numbers come
  from a note about 5 months old. Locate the v1 and v2 row files and rebuild
  the table from them first.
- **Anonymity of the C7 submission.** This paper carries our names, and the C7
  paper is under double-anonymous review. Describe the agent generically. Do
  not use the INQUEST name, its headline numbers, or its figures.
- **Evidence strength.** 168 instances is fine for an experience paper but
  not for strong statistical claims. If the seed-42 rows (26,540 runs) log
  tool calls, the "after" side can be much stronger.
- **Supervisor sign-off** on submitting a second paper from the same agent
  while C7 is under review.

## Checked against the data (2026-11-19)

Row files: `industry-c7/data/archive/agent/agent-v1.jsonl` (168 rows) and
`agent-v2.jsonl` (790 rows). Paired result:
`industry-c7/data/results/agent-v1-v2-ablation.json`, made by
`industry-c7/scripts/ablate_agent_versions.py`.

Behaviour, recomputed from the rows:

| | v1 (168 runs) | v2 (790 runs) |
|---|---|---|
| `recall_incidents` calls per run | 0.32 (54 runs) | 0.28, on top of the pre-run recall |
| `callers_of` | 1 run of 168 (0.01 per run) | 9 runs of 790 (0.01 per run) |
| `search_symbol` calls per run | 3.73 | 3.42 |
| runs with zero evidence (168 shared) | 36.9% | 0.0% |
| evidence notes per run (shared) | 1.99 | 5.77 |
| prompt tokens per run (shared) | 84.5k | 91.1k |

The memory note was right. The script's header comment (0.4 calls per run,
1 use in 105 runs) is out of date, from an earlier partial run.

Effect, v2 minus v1, paired on 168 shared instances, 2,000 bootstrap
samples, BH-corrected:

| population | metric | v1 | v2 | delta [95% CI] | q |
|---|---|---|---|---|---|
| all (168) | Acc@1 | 0.619 | 0.696 | +0.077 [+0.012, +0.149] | 0.042 |
| all | Acc@5 | 0.869 | 0.899 | +0.030 [−0.012, +0.071] | 0.197 ns |
| all | MRR | 0.720 | 0.783 | +0.062 [+0.019, +0.108] | 0.010 |
| hard (86) | Acc@1 | 0.430 | 0.570 | +0.140 [+0.047, +0.244] | 0.010 |
| hard | Acc@5 | 0.744 | 0.814 | +0.070 [−0.012, +0.151] | 0.132 ns |
| hard | MRR | 0.553 | 0.674 | +0.121 [+0.053, +0.190] | 0.000 |

Caveat: v1 to v2 bundles four changes (pre-run recall, callers folded in,
required evidence, and backfill instead of blending in the safety net).
There is no per-change ablation. The paper can say "the four fixes together"
but not which one helped.

## Problem: overlap with the C7 paper

The C7 paper (under double-anonymous review) already makes the same core
claim. Its Section 4.1 lists four design principles that "take those
decisions away from the model", and Table "ablation" compares the staged
workflow against an unconstrained loop on 26,537 instances (region Acc@1
+14.1 points). The v1/v2 numbers are not in C7, but the thesis
"structure beats instruction" is.

Two risks:

- **Concurrent submission.** The workshop forbids submitting the same work
  elsewhere. A reviewer could see the workshop paper as the C7 design story
  told again.
- **De-anonymizing C7.** The workshop paper carries our names. If it
  describes the same agent, it reveals the authors of the C7 submission.

Ways around it:

1. **Make it about the design process, not the agent.** The lesson is "how
   we found what the model skips": per-tool call counts, what each count
   told us, and the fix. Present v1 and v2 only, never the final staged
   workflow and never the 26k ablation. Still the same agent, so ask the
   C7 chairs or the workshop chairs first.
2. **Use the ARISE ReAct case instead.** Different system, different data
   (OB, OTel, WoL). Main finding is "more tools can hurt": the trace tool is
   significantly harmful (p = 0.002), and only one of four tools helps. No
   overlap with C7. Weaker as a positive story, but clean.
3. **Skip this deadline.** Wait for the C7 decision, then write the full
   v1 → v2 → workflow story for a later venue.

## Idea 2 (from the professor): AIDev + kernel tracing of agent PRs

### The dataset (read in full: `related-papers/2602.09185v1.pdf`, MSR '26, 5 pages)

- AIDev: 932,791 agent-authored PRs (Codex, Devin, Copilot, Cursor, Claude
  Code), 116,211 repos, cutoff 1 August 2025.
- Curated subset (repositories with more than 100 GitHub stars): 33,596
  PRs, 2,807 repos, with comments, reviews, commits, file-level diffs
  (711,923 rows), linked issues and timelines. ("AIDev-POP" is a name
  other papers use; the AIDev paper does not.)
- `pr_task_type`: GPT-based label in Conventional Commits categories, so a
  `perf` category is expected. Other papers report 340 PRs with it and
  about 1,100 to 1,300 perf PRs when bug-fix and feature PRs are also
  searched. Not yet counted by us.
- The paper is a dataset description only. It has no runtime data, no
  measurements, no evaluation of its GPT labels. Its own research questions
  4.5(4) ask "which Agentic-PRs reach production and persist", but nothing
  about runtime behaviour.
- HF: https://huggingface.co/datasets/hao-li/AIDev,
  Zenodo: https://doi.org/10.5281/zenodo.16899501,
  GitHub: https://github.com/SAILResearch/AI_Teammates_in_SE3

### What already exists (checked 2026-11-19)

At least five papers study agent perf PRs from AIDev:

| paper | executes code? | OS/kernel level? |
|---|---|---|
| arXiv 2512.24630, BERTopic analysis of perf PRs | no | no |
| arXiv 2512.21757, "How Do Agents Perform Code Optimization?" (340 agent vs 88 human perf PRs) | no; agents mostly use static reasoning, not benchmarks | no |
| arXiv 2607.05666, mutation taxonomy (1,254 hunks, 216 PRs) | no | no |
| arXiv 2610.03969, Purdue, 1,130 agent + 1,130 human perf PRs; merged 54.4% vs 73.3%; agents use benchmarks less (46.1% vs 57.2%) | no ("we do not execute the changed code") | no |
| arXiv 2609.37985, "Merged, Not Measured" (1,262 perf fixes, 6 agents) | **yes, 23 rejected + 30 merged**; wall time per op and allocations, containers with 2 CPUs | no |

"Merged, Not Measured" key numbers: only 6 of 23 re-run rejected claims held;
of 30 merged fixes, 18 met the claim, 3 fell short, 9 showed no gain or
regressed, 14 changed behaviour on untested inputs.

**The gap:** nobody looks below wall-clock time. No perf counters, syscalls,
page faults, context switches, I/O or scheduler data. Nobody checks the
*mechanism* a PR claims.

### The research idea

**Working title:** "Below the Stopwatch: Kernel-Level Validation of
Performance Claims in Agent-Authored Pull Requests"

An agent's perf PR usually claims a mechanism, not only a number: "avoids
repeated file reads", "reduces allocations", "batches requests", "caches
the result", "removes a lock". Each mechanism leaves a kernel footprint:
fewer `read`/`openat` syscalls, fewer page faults, fewer context switches,
fewer futex waits, less I/O. So the claim can be checked by its mechanism,
not just by timing.

Research questions:

- **RQ1 (claim to mechanism):** what share of agent perf PRs state a
  mechanism that a kernel trace can check? Map claim types to trace signals
  (I/O claim → `read`/`write`/`openat` counts and bytes; memory claim → page
  faults, RSS; concurrency claim → context switches, futex; CPU claim →
  task-clock, instructions).
- **RQ2 (does the mechanism happen?):** run the before and after commits
  under tracing. Does the claimed signal move the right way?
- **RQ3 (hidden costs):** when wall time improves, did cost move somewhere
  else (user time down but system time up, more syscalls, more memory)?
  When wall time does not change, does the kernel view show why (for
  example, the code was I/O-bound and the change was CPU-only)?

Why it is new: the closest paper ("Merged, Not Measured") has only wall time
and allocations on 53 fixes. A mechanism-level check, and the "hidden cost"
view, are not done anywhere. It also fits the thesis area directly (kernel
tracing + software performance) and the workshop topics "verification and
validation" and "agentic systems supporting maintenance".

### Measurement setup

Per PR: check out the parent commit and the PR head, build both, run the
same workload (the PR's own benchmark or test if present, else a small
written workload), 10+ interleaved runs per side, report medians with
bootstrap CIs.

Commands per run:

```bash
# software counters (work in WSL2 and VMs)
perf stat -e task-clock,context-switches,cpu-migrations,page-faults,major-faults \
  -x, -o stat.csv -- <workload>

# syscall counts and bytes by syscall (eBPF, low overhead)
bpftrace -e 'tracepoint:raw_syscalls:sys_enter /comm == "python3"/ { @[ksym(args->id)] = count(); }' \
  -c '<workload>'
bpftrace -e 'tracepoint:syscalls:sys_exit_read /comm=="python3" && args->ret > 0/ { @bytes = sum(args->ret); }' \
  -c '<workload>'

# off-CPU / scheduler waits
bpftrace -e 'tracepoint:sched:sched_switch /prev_comm=="python3"/ { @[args->prev_state] = count(); }' -c '<workload>'
```

Hardware counters (cycles, instructions, cache-misses) need a machine whose
PMU is visible: bare metal, or a cloud VM with PMU passthrough (for example
GCP C3 with `--performance-monitoring-unit=standard`). WSL2 on the laptop
probably does not expose them.

Clusters are not suitable: no root, so no bpftrace, and perf is usually
restricted.

### Laptop check (2026-11-19)

- WSL kernel 6.6.114.1-microsoft-standard-WSL2, 24 cores.
- `perf`, `bpftrace`, `strace`: not installed.
- `/sys/kernel/btf/vmlinux` exists, so bpftrace should work after
  `sudo apt install bpftrace strace`.
- `perf_event_paranoid` = 2 (needs sudo or a lower value for kernel events).
- `perf` for the WSL kernel is not in apt under that name; the generic
  `linux-tools` binary usually works with a warning, or build it from the
  WSL kernel source.

### Feasibility for the 20 November deadline

- The hard part is not tracing. It is building old commits of random
  GitHub projects and finding a workload. "Merged, Not Measured" needed an
  agent with shell access and still had 7 of 30 pilot fixes fail to run.
- Realistic pilot in about one day: 10 to 20 Python perf PRs (pure Python,
  pip-installable, PR has a test or benchmark), software counters +
  bpftrace syscalls only. That supports a 5-page "emerging research" paper:
  RQ1 on the full perf set (text only, uses an LLM to classify claims) and
  RQ2/RQ3 as a pilot with case studies.
- Honest risk: with ~20 PRs this is a vision paper with early evidence, not
  a study. It is also the stronger long-term idea; it could become a full
  paper (MSR 2027, FSE 2027 IVR, or a thesis chapter) with a cloud VM and an
  agent that builds the PRs automatically.

### Overlap check

No overlap with C7 or ARISE: different data, different question. No
anonymity issue.

## Next steps

1. Find the v1 and v2 agent row files and recompute tool-call counts per run.
2. Check whether the seed-42 rows log tool calls.
3. Decide: one case (5 pages) or two cases.
4. Draft in the IEEE template.
