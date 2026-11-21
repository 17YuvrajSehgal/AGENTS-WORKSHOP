# Below the Stopwatch: artifact

Code and data for the paper *Below the Stopwatch: Checking the Performance
Claims of Coding Agents in the Kernel* (AGENT 2027 workshop at ICSE 2027),
by Yuvraj Sehgal, Sneh Patel, Mahsa Panahandeh and Naser Ezzati-Jivan.

The paper presents **Below**, a pipeline that takes performance pull requests
(PRs) written by coding agents, extracts the mechanism each PR claims, rebuilds
the code before and after the PR with a build agent that never sees the claim,
and measures both versions with timing runs, hardware counters and LTTng kernel
traces.

This artifact lets you:

1. **Reproduce every number in the paper** from the included data, on any
   machine with Python 3.11+, in about a minute. No VM, no tracing, no model.
2. **Inspect every measured PR**: its workload, its harness checks, its coverage
   and all its measured signals.
3. **Rerun the pipeline** on new PRs with the included code (needs a Linux VM
   with a performance-monitoring unit, LTTng, and a Claude Code account).

## 1. Reproduce the paper's numbers

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.lock.txt

python analysis/paper_numbers.py                        # dataset, labelling, claims  -> paper/numbers.tex
python analysis/p7_results.py data/p7_paper/fetched    # funnel, Table II, Fig. 2     -> paper/results.tex
python analysis/p7_cases.py                             # case studies                 -> paper/cases.tex
python analysis/p7_extra.py                             # A/A test, specificity, Table III -> paper/extra.tex
python analysis/verify_paper.py                         # checks all of the above is current
```

Every number in the paper is a LaTeX macro written by these scripts; no number
is typed by hand. `verify_paper.py` regenerates the four macro files, fails if
any of them changes, and fails if the paper uses a macro no script defines.
The artifact builder ran this check on the artifact itself.

To rebuild the PDF: `cd paper && latexmk -pdf main.tex` (IEEEtran class).

| Paper element | Script | Main inputs |
|---|---|---|
| Dataset and labelling numbers (Sec. II-A) | `analysis/paper_numbers.py` | `data/p1_*`, `data/p1_classify/`, `data/p2_classify/summary.json`, `data/p2_haiku_agree/` |
| Table I, RQ1 (claims, evidence) | `analysis/paper_numbers.py` | `data/p5_claims/all_v1/claims_pr.parquet`, `claims_mech.parquet` |
| Control programs (Sec. II-C) | `analysis/paper_numbers.py` | `data/p7_paper/vm_controls/` |
| RQ2 funnel | `analysis/p7_results.py` | every `verdict.json` under `data/p7_paper/fetched/` |
| Table II, Fig. 2, RQ3 counts | `analysis/p7_results.py` | every `measure.json`, `data/p7_paper/review.json` |
| A/A false-positive test, specificity, output split, Table III | `analysis/p7_extra.py` | as above |
| Case studies | `analysis/p7_cases.py` | four `measure.json` files |

## 2. What is in the data

```
data/
  aidev-v5-manifest.json      AIDev v5: Hugging Face commit and sha256 of every file used
  p1_counts.json, p1_keyword_stats.json, p1_template_lines.csv, p1_pr_meta.jsonl
                              keyword filter (Sec. II-A)
  p1_classify/                pilot sample of 2,000 candidates: model input, labels, raw answers
  p2_classify/                stratified labelling: labels, fixed random order, targets, summary
  p2_haiku_agree/             agreement between two models on 66 PRs
  p5_claims/                  claim extraction (codebook v1): per PR and per mechanism, raw answers
  p7_paper/
    fetched/<vm>/<order>_<pr id>/   one folder per build job (150 jobs, 91 measured)
      verdict.json            job, build agent outcome, harness checks, cost
      check.json              independent harness check (run times, coverage, network-free run, output hash)
      coverage.json           changed-line coverage of the workload on base and head
      workload.py             the workload the blind build agent wrote
      measure.json            every measured signal for base, head and base again
      env.json                machine and environment snapshot
    vm_controls/              control-program results for each of the three machines
    per_pr_verdicts.json      per-PR verdicts (faster/slower, mechanism held, hidden costs)
    review.json               manual review decision and reason for every measured PR
labels/                       codebooks (frozen versions with sha256) and the human-labelling sheets
harness/                      VM setup, control programs, build agent, measurement harness, fleet worker
analysis/                     every script, from download to paper numbers
paper/                        LaTeX sources, generated macro files, figures
```

In `measure.json`, each variant (`base`, `head`, `base_aa`) maps a signal to a
list of runs. Timing signals (`wall_s`, `user_s`, `sys_s`, `maxrss_kb`) have 10
runs; hardware counters (`instructions`, `cycles`, cache events, `pcnt_running:*`
to show no multiplexing) have 5; trace signals have 5: `sc:<name>` is a system
call count, `ev:<name>` a kernel event count, plus `offcpu_ns_main`, `futex_ns`,
`bytes_read`, `threads`, `forks` and others. `discarded` and `discarded_packets`
must be 0.

## 3. Rerun the pipeline

The order of scripts, from the AIDev download to the paper, is in
`analysis/` (prefixes `p1_` to `p7_`). The measurement side:

- `harness/vm/setup_lttng.sh`, `enable_full_probes.sh`: LTTng 2.16 from source
  on Ubuntu kernel 7.0 (we used Google Cloud C4 VMs with the performance-monitoring
  unit enabled), including the missing kernel probes.
- `harness/controls/`: the twelve control-program pairs and their checks.
- `harness/pilot/setup_pr.sh`, `measure_pr.py`: check out base (merge base) and
  head, install both, and measure one PR.
- `harness/agent/`: the blind build agent (`run_agent.py`, its instructions in
  `BUILD_AGENT.md`), the independent check (`check.py`) and the fleet worker
  (`worker.py`). `analysis/fetch_results.sh` collects results from the VMs
  (set your own cloud project in it).

A rerun of the build agent will not give identical workloads: it is a language
model. The measurements of a given workload are near-deterministic for kernel
and counter signals and noisy for timing, which is why the harness runs an A/A
control.

## 4. Not included, and why

| Item | Why | How to get it |
|---|---|---|
| Raw AIDev v5 parquet files (15 GB) | public and large | `analysis/p1_download.py` downloads the exact commit in `data/aidev-v5-manifest.json` and checks every sha256 |
| `data/p1_candidates.parquet`, `data/p2_classify/inputs.jsonl` | derived from AIDev, over 100 MB | `analysis/p1_keyword_filter.py`; `analysis/p2_classify.py prepare` |
| Raw LTTng traces (several GB per PR) | size | kept by the authors; available on request |
| Answer key of the human-labelling sheets | the human check is not done yet; labellers must not see the model labels | released after the check |
| PDFs of related papers | copyright | see the paper's references |

Third-party PR descriptions in the data sometimes contain pre-signed cloud
links with temporary access keys (all long expired). The artifact builder cut
these links down to their path.

## 5. Licences

- Code (`analysis/`, `harness/`, workloads): MIT, see `LICENSE`.
- Data derived from AIDev: CC BY 4.0, like AIDev itself. PR text and code
  quoted from GitHub repositories keep their original licences, as the AIDev
  README explains (`data/aidev-readme-b8dc67d.md`).

## 6. Use of AI

Claude models labelled the PRs and extracted the claims, and a Claude Code
build agent wrote the workloads; their raw answers are included. Claude also
helped write the analysis code. All numbers are computed by the scripts above.
