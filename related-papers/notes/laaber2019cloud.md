# Software Microbenchmarking in the Cloud. How Bad is it Really?

- **Authors:** Christoph Laaber (University of Zurich), Joel Scheuner (Chalmers | University of Gothenburg), Philipp Leitner (Chalmers | University of Gothenburg)
- **Venue / year / status:** Peer-reviewed journal article, Empirical Software Engineering 24(4): 2469-2508, 2019, DOI 10.1007/s10664-019-09681-1. The PDF is the post-peer-review, pre-copyedit version from the Chalmers repository (p. 1 cover). Page numbers below are the manuscript's printed page numbers (PDF page = printed page + 1, because of the cover sheet).
- **PDF:** related-papers/3-variability-method/laaber2019_microbenchmarking-cloud.pdf
- **Cite key suggestion:** laaber2019
- **BibTeX-style reference:** Christoph Laaber, Joel Scheuner, and Philipp Leitner. 2019. Software Microbenchmarking in the Cloud. How Bad is it Really? Empirical Software Engineering 24, 4 (2019), 2469-2508. https://doi.org/10.1007/s10664-019-09681-1

## In short
The authors run 19 real Java (JMH) and Go microbenchmarks on 9 cloud instance types (AWS, GCE, Azure; general, compute and memory families) and one IBM bare-metal server, with 50 instances per type, 10 randomized trials per instance and 50 iterations per trial, giving more than 4.5 million data points. Variability (coefficient of variation) ranges from 0.03% to 100.68% depending on benchmark and environment. With A/A tests (same code vs same code) they show small samples give many false alarms, and with simulated slowdowns they find the smallest slowdown each setup can detect 95% of the time with at most 5% false positives. Running "test" and "control" on the same instances in random interleaved order (trial-based) is much better than on different instances: with 20 instances, 77-83% of setups can detect slowdowns below 10%.

## Problem and motivation
Performance engineering usually assumes bare-metal, controlled machines. Many people cannot afford them, and cloud is attractive (cheap, scalable, parallel). But cloud performance is unpredictable (noisy neighbours, hardware heterogeneity). Question: is using public cloud for performance testing always a bad idea? (pp. 2-3)
- RQ1: How variable are microbenchmark results in different cloud environments?
- RQ2: Which slowdowns can be detected 95% of the time with at most 5% false positives? (p. 3)

## Background / key terms (explain each term simply)
- **Microbenchmark:** a short performance test (often < 1 ms per call) of one small unit, like a method. Like a unit test, but for speed (pp. 2, 5).
- **Invocation / iteration / trial / instance:** one call = invocation. Calls repeated for a fixed time (e.g., 1 s), the mean is one **iteration** = one data point. 50 iterations in a row = one **trial** of a benchmark. 10 trials on the same VM, each with benchmarks in random order. 50 different VMs = **instances** (pp. 3, 10; Fig. 1).
- **JMH:** Java Microbenchmark Harness, uses `@Benchmark` annotations. Go has a benchmark framework in its standard library (`func BenchmarkX(b *testing.B)`) (p. 5).
- **Warm-up iterations:** iterations run and thrown away so the JVM's JIT compiler can reach steady state (p. 10).
- **Coefficient of variation (CV):** SD divided by mean, in %. Same as RSD (p. 13).
- **RCIW:** relative width of a 95% CI, here for the CV itself, from bootstrap with 1,000 resamples. Shows how sure we are about the CV value (p. 13).
- **A/A test:** compare two samples that come from the *same* code in the same environment. Any "significant difference" is a false positive (FP). This measures how often the setup gives false alarms (p. 19).
- **A/B test / minimal-detectable slowdown (MDS):** artificially slow the test group by x% and check if the test finds it. MDS = smallest x found in ≥ 95 of 100 resamples, with A/A FP ≤ 5 of 100 (p. 30).
- **Wilcoxon rank-sum (Mann-Whitney U):** non-parametric test that one group tends to have larger values. They combine it with **Cliff's delta** effect size ≥ 0.33 ("medium") to avoid flagging tiny but significant differences (p. 20).
- **Overlapping confidence intervals:** call it a change only if the two 95% CIs of the mean do not overlap. CIs from **hierarchical bootstrap**: resample instances, then trials, then iterations (p. 20).
- **Instance-based sampling (ibs):** test and control on *different* instances. Like comparing a new release today with old results from a VM that has since been deleted (p. 21).
- **Trial-based sampling (tbs):** test and control on the *same* instances, different trials, in random order. Like a paired design. Based on RMIT (randomized multiple interleaved trials) from Abedi & Brecht 2017 (pp. 3, 23).
- **Bonferroni correction:** divide the significance level by the number of tests to control false alarms across many tests (p. 24).

## Method and setup
- **Projects (Table 1):** Log4j2 (commit 8a10178, 437 benchmarks), RxJava (2162d6d, 977), bleve (0b1034d, 70), etcd (e7e7451, 41). Two Java (JMH), two Go.
- **Benchmark choice:** each project's full suite was run 5 times on an in-house bare-metal server (37.8 min for etcd to 8.75 h for RxJava per trial). Ranked by variability; picked the most stable, 25th percentile, median, 75th percentile and most unstable: 5 per project, 20 total. bleve-1 lost by a configuration error, so 19 benchmarks (p. 7-8; Table 2).
- **Cloud environments (Table 3), all 2 vCPU, Ubuntu 17.04 64-bit, prices summer 2017:**
  - AWS us-east-1: m4.large (GP, 8 GB, $0.10/h), c4.large (CPU, 3.75 GB, $0.10/h), r4.large (Mem, 15.25 GB, $0.133/h).
  - Azure East US: D2s v2 (GP, 8 GB), F2s (CPU, 4 GB), E2s v3 (Mem, 16 GB).
  - GCE us-east1-b: n1-standard-2 (GP, 7.5 GB, $0.095/h), n1-highcpu-2 (CPU, 1.8 GB, $0.0709/h), n1-highmem-2 (Mem, 13 GB, $0.1184/h).
  - IBM Bluemix bare metal, Amsterdam: Xeon E5-2620 v2 2.1 GHz, 16 GB, Ubuntu 16.04. Hyper-threading and Turbo Boost off; frequency scaling could not be disabled ("presumably overridden by IBM") (p. 10).
- **Execution:** 50 instances per type; 10 trials per instance; benchmark order randomized in each trial; 50 iterations per benchmark per trial; JMH 10 warm-up iterations discarded (they note 10 x 1 s may not be enough for some benchmarks). Cloud Workbench for setup. Data July-October 2017 (pp. 10-12).
- **Data:** > 4.5 million data points. Outlier removal: drop points ≥ 10x the median (one order of magnitude). Removed very few (Table 4: e.g., Azure GP 472,636 -> 472,122; AWS CPU 475,000 -> 474,999). About 1% of points removed for log4j2-5 and etcd-2 (p. 12).
- **RQ1 metric:** CV of all data per configuration (190 configurations = 19 x 10), with bootstrap RCIW. Decomposed into: benchmark variability (mean CV per trial), variability between trials (mean CV per instance), total variability (Eq. 5-7).
- **RQ2:**
  - A/A: sample 1, 2, 3, 5, 10, 15, 20 instances and 1, 2, 3, 5 trials for each group, ibs and tbs, 100 random repeats per configuration. Threshold: ≤ 5% FPs. Bonferroni correction over the 100 tests for Wilcoxon (p. 24).
  - MDS: slowdowns 0.1, 0.2, 0.5, 1, 1.5, 2, 5, 10, 50, 100, 1000%. Slowdown simulated by adding x% to every data point of the test group (an "idealized" slowdown). ibs with 1 trial; tbs with 5 trials; 1, 2, 3, 5, 10, 15, 20 instances. 100 resamples each. Bootstrap for CIs uses only 100 iterations (they argue 100 x 100 = 10,000 overall). Compute: about 130 h for A/A and 500 h for detection on a 10-machine private cloud (pp. 20, 30).
- **Artifacts:** dataset, scripts, appendix at figshare DOI 10.6084/m9.figshare.7546703.

## Section-by-section notes

### 1 Introduction (pp. 2-4)
Summary of findings: CV 0.03% to > 100%; both tests give many FPs with small samples; with instance-based sampling and 20 instances only 78-83% of setups detect slowdowns at all; with trial-based sampling all setups detect slowdowns with ≥ 10 instances; Wilcoxon detects smaller slowdowns and is cheaper. "Practitioners can use our study as a blueprint" (p. 4).

### 2 Background (pp. 4-6)
Microbenchmarking with JMH and Go (Listings 1-2); IaaS concepts (instance, type, image, family).

### 3 Approach (pp. 6-12)
They benchmark software on cloud, not the cloud itself. Not about load tests. See Method above.

### 4 Benchmark variability in the cloud (RQ1) (pp. 12-19)
- **Table 5 (p. 14), CV per benchmark and environment:**
  - Very stable everywhere: rxjava-1 0.03-0.27%.
  - Unstable everywhere: log4j2-1 40.8-51.8%, log4j2-5 76.8-88.2%, etcd-5 22.5-43.6% (even 23.73% on bare metal).
  - Stable on some, unstable on others: etcd-2 AWS 4-6%, GCE 67-69%, Azure 90-101% (max 100.68% on Azure GP), bare metal 29.46%. bleve-5 AWS 8-10%, GCE 58-59%, Azure 46-53%. rxjava-5 AWS 2.8-5.6%, Azure GP/CPU 62-64%.
  - Bare metal often lowest (e.g., bleve-3 0.18%, etcd-3 0.14%).
- Causes: very short benchmarks (log4j2-1 averages 4.7 ns) suffer from measurement inaccuracy; some benchmarks are just low quality (etcd-5). log4j2-3 on GCE Mem: similar medians but different tail lengths per instance, which they link to noisy neighbours and IO (logging writes files) (Fig. 3). bleve-5 on Azure: medians fall in two groups because two versions of the same CPU model with different clock speeds were given (hardware heterogeneity, Fig. 4).
- Instance families of one provider barely differ, except Azure Mem which is worse (p. 16).
- **Sources of variability (Fig. 5):** etcd-2 on AWS: all three levels similar, so variability is from the benchmark itself. etcd-2 on Azure: total CV much higher than per-trial or per-instance, so instances differ. log4j2-5 on AWS CPU: tiny within-trial variability, big between-trial variability, whether or not on the same instance (trial-level contention). etcd-4 on GCE Mem: all three contribute.
- RQ1 answer: GCE and Azure "seem to lend themselves much less to performance testing than AWS at the time of study" (p. 19).

### 5 Reliably detecting slowdowns (RQ2) (pp. 19-35)
- **5.3 A/A tests.** Table 6 (bleve-3, CI test, FP %): 1 instance, 1 trial ibs: 43% (bare metal) to 92% (GCE Mem). 20 instances x 5 trials ibs: 0-5%. tbs 3 instances x 5 trials: 0-1% in cloud, 5% on bare metal (its CIs are so narrow that tiny mean shifts look significant).
- Fig. 7 (density of FP rates over 190 configurations): ibs 1x1: only 18/190 (Wilcoxon) and 8/190 (CI) under 5% FPs. ibs 10 instances x 1 trial: Wilcoxon 44/190 ≤ 5%, 54 above 20%; CI 110/190 ≤ 5%, none ≥ 20%. tbs 5x5: 185/190 (97%, Wilcoxon) and 189/190 (CI) ≤ 5%; overall 75 of 19,000 (0.4%, CI) and 106 (0.6%, Wilcoxon) FPs.
- Counter-intuitive: stable environments (AWS, bare metal) sometimes have *more* FPs at mid sample sizes, because unstable environments give wide CIs and weak Wilcoxon power, which hides false alarms (p. 27). Unstable clouds (GCE, Azure) benefit most from tbs, supporting RMIT as best practice.
- Fig. 8 (minimal samples for < 5% FPs): upper bound for ibs: 5,000 samples (20 instances x 5 trials x 50 iterations) for Wilcoxon, 1,000 (20 x 1 x 50) for CI. For tbs: 1,500 (10 x 3 x 50) Wilcoxon, 750 (5 x 3 x 50) CI (pp. 28-29). Log4j2 is the hardest project.
- **5.4 Minimal-detectable slowdowns.**
  - ibs (1 trial): no slowdown detectable in 172/190 (91%) with 1 instance, 162 (85%) with 5, 146 (77%) with 10, 42 (22%) with 20, using Wilcoxon. CI test: 154 (81%), 141 (74%), 71 (37%), 24 (13%). With 20 instances, Wilcoxon finds a slowdown in 148 (78%) and CI in 157 (83%); slowdowns ≤ 10% in 121 (64%) and 95 (50%) (pp. 32-33). AWS detects smaller slowdowns than GCE, Azure, even bare metal (Table 7).
  - tbs (5 trials): with 1 instance, 142 (75%, Wilcoxon) and 117 (62%, CI) find nothing. With 5 instances, 185 (97%) and 189 (99%) find a slowdown. Slowdowns ≤ 10%: 5 instances 150 (79%, Wilcoxon) vs 74 (39%, CI); 10 instances 156 (82%) vs 113 (60%); 20 instances 157 (83%) vs 147 (77%). 1 instance: 34 (17%) vs 43 (22%) (p. 34).
  - Here Wilcoxon is better: it rejects H0 more easily, which costs more A/A FPs but finds smaller real slowdowns.

### 6 Discussion and threats (pp. 36-41)
- Provider: AWS close to bare metal; GCE and Azure worse; instance families do not matter much (p. 36).
- Strategy: tbs better statistically; ibs is easier in CI pipelines and parallelizes, but the provider may change hardware between versions, which makes ibs comparisons unfair (p. 37).
- Required runs: no general rule; for ≤ 10% slowdowns, 20 instances x 5 trials. Tooling should track per-benchmark variability and adapt repetitions (pp. 37-38).
- MDS: a 20-instance x 1-trial ibs setup is a "sanity check"; ≤ 10% needs tbs with ≥ 20 instances x 5 trials for most benchmarks. "always perform A/A testing" (p. 38).
- Wilcoxon vs CI: Wilcoxon more sensitive and cheaper; CIs more conservative; choice depends on whether false alarms or misses are worse (pp. 38-39).
- Threats (pp. 39-40): cloud is a black box; entry-level types only; GCE CPU type has much less memory (1.8 GB) so not directly comparable; short time window (snapshot, not longitudinal); idealized slowdowns; only Java and Go; not about load tests; private clouds may differ; results are a "moving target".
- Future (pp. 40-41): study benchmark properties that cause instability (file writes, network); IDE support for writing good benchmarks; adaptive repetition configuration.

### 7 Related work (pp. 41-43)
Measurement bias (Mytkowicz), Georges et al., Kalibera & Jones, Arif et al. 2017 (virtual vs physical load tests differ, IO the worst). Compared to their own previous work: Leitner & Cito 2016 found AWS fairly unreliable, this study found it stable. log4j2-1 was "very stable" in their earlier study but highly unstable here. They say this is expected because providers change hardware and policies.

### 8 Conclusions (pp. 43)
Cloud microbenchmarking is possible "to some degree", with enough instances/trials and same-instance test and control.

## Key results (with numbers) and what they mean
- CV from 0.03% to 100.68% -> the same environment can be fine for one benchmark and useless for another. Variability must be measured per benchmark, not assumed per cloud.
- 1 instance x 1 trial: FP rate 43-92% for bleve-3 -> a single run before and after a change is mostly noise.
- tbs 5 instances x 5 trials: 97-99% of setups under 5% FPs -> modest sample sizes are enough if test and control share instances and are interleaved.
- tbs 20 instances: 77-83% of setups detect slowdowns ≤ 10% -> about 10% is a realistic detection limit in cloud; smaller effects are often not detectable.
- ibs 20 instances: 13-22% of setups detect nothing at all -> comparing results from different VMs can fail even with many VMs.
- Wilcoxon + medium Cliff's delta: more FPs in A/A, but smaller detectable slowdowns -> a sensitive test needs an A/A check to show its false-alarm rate.

## Tables and figures
- **Fig. 1 (p. 11):** structure: instance types -> instances -> randomized trials -> data points.
- **Table 4 (p. 12):** data points before and after outlier removal. Shows outlier removal was very light.
- **Table 5 (p. 14):** CV per benchmark x environment, with symbols for how wide the CV's own CI is. Read rows to see benchmark quality, columns to see environment quality.
- **Figs. 2-4 (pp. 15-17):** per-instance distributions (beanplots) for etcd-5, log4j2-3, bleve-5. Fig. 4 shows two clusters of instance medians, the signature of hardware heterogeneity.
- **Fig. 5 (p. 18):** three-level CV decomposition. If the bottom (total) bar is much longer than the others, variation comes from differences between instances.
- **Fig. 6 (p. 22):** ibs vs tbs diagram.
- **Table 6 (p. 24):** A/A FP rates for bleve-3.
- **Fig. 7 (p. 26):** density of FP rates for each design. Mass to the left of the 5% line is good.
- **Fig. 8 (p. 28):** minimal instances x trials per configuration for < 5% FPs. Points closer to the bottom-left need fewer runs.
- **Tables 7-8 (pp. 31, 34):** MDS for three example benchmarks per environment. ∞ = nothing detectable.
- **Figs. 9-10 (pp. 32, 35):** histograms of MDS over all 190 configurations for ibs and tbs. "Inf" bar large for ibs, small for tbs.

## Ideas we can use
- **A/A test for our breaking-point rule.** We declare a breaking point when the whole bootstrap CI of the slowdown ratio is above 1.10. We can check its false-alarm rate: split unlimited baseline runs on one VM into two random halves many times, compute the ratio CI, count how often it is fully above 1.10. This is cheap (no new runs) and directly answers "how often would our rule fire with no limit?". Report it in Statistics.
- **Detectable effect size.** Their tbs result (about 10% detectable with 20 instances x 5 trials) gives a reference for why our 10% threshold is reasonable for cloud measurements, and why we do not claim smaller effects.
- **Variance decomposition.** Their three-level CV (within trial, between trials, between instances) maps to ours: within run (agent step times), between runs on one VM, between VMs/disk sets. Showing this for baseline runs would quantify how much the disk-set difference matters.
- **Hierarchical bootstrap.** If we pool runs across VMs anywhere (e.g., cross-machine checks on M1/M2), resample VMs first, then runs. Otherwise CIs are too narrow.
- **Light outlier policy.** Their rule (remove only points ≥ 10x median) is a citable, conservative choice. If we drop failed or timed-out runs, state the rule and count, as they do.
- **Test choice.** We use one-sided rank-sum + Cliff's delta, which is their "Wilcoxon with effect size" design. They used Bonferroni; we use Holm, which is uniformly more powerful with the same family-wise control. Good to state.

## Weaknesses and things glossed over
- **Idealized slowdowns.** Every test data point is multiplied by (1 + x). Real regressions change the shape of the distribution, not just shift it. So MDS values are likely optimistic. They admit this (p. 30).
- **Mixed messages on tests.** A/A says the CI test is better (fewer FPs); MDS says Wilcoxon is better (smaller slowdowns). The abstract and conclusion stress Wilcoxon. Both are true, but the trade-off is not formalized (e.g., no ROC-style analysis).
- **Only 100 bootstrap iterations** per CI, below Kalibera & Jones (1,000) and Hesterberg (10,000). Their argument that 100 x 100 resamples "reaches the 10000" (p. 21) mixes two different things: 100 different CIs each with 100 resamples is not the same as one CI with 10,000 resamples.
- **The 100 A/A or MDS resamples are drawn from the same 50 instances**, so they are not independent experiments. FP rates may be under-estimated.
- **Bonferroni over 100 resampled tests** of the same configuration is unusual: those tests are simulations of repeated experiments, not a family of claims. This makes Wilcoxon more conservative in a way that depends on the number of simulations.
- **CV on long-tailed data** (they say data is long-tailed and multi-modal) is sensitive to outliers.
- **Entry-level 2-vCPU VMs only**, one region per provider, one bare-metal server whose frequency scaling could not be disabled.
- **Text inconsistencies:** threats say "two OSS projects" (p. 40) but there are four; Eq. 7 text says "trials = 50" (p. 17) but trials = 10.
- **Benchmark selection** used variability on their own bare-metal server, and some "stable" picks (log4j2-1) were very unstable in cloud. This shows selection by variability is itself unstable.
- **Snapshot of 2017.** Their own comparison with Leitner & Cito 2016 shows results flip over time (AWS unreliable then, stable now).

## Open questions and future work (theirs, and ours)
- Theirs: which benchmark properties cause instability (file IO, network); IDE tools for good benchmarks; adaptive repetitions per benchmark; load tests and other metrics (memory, IO, locks); bare-metal cloud instances.
- Ours: our "benchmark" is a whole agent run (minutes, many model calls). The main noise source is not the VM but the remote model wait. Their framework (A/A, MDS) could be applied to agent runs to give a "minimal detectable slowdown" for agentic workloads. That would be new.
- Ours: is our 10% threshold above the A/A noise floor on each VM type? Test it as described above.

## Link to our paper
- **Agree (design):** we compare limits only against the unlimited baseline on the same VM and disk set, in random order. This is their trial-based sampling / RMIT, which they show is clearly better than instance-based comparisons. Cite in Study Design.
- **Agree (statistics):** one-sided rank-sum with Cliff's delta is the same family as their "Wilcoxon + medium Cliff's delta". Bootstrap CIs also match. We use 2,000 bootstrap resamples, more than their 100, which is a plus. Holm vs their Bonferroni: Holm is the better choice.
- **Agree (threshold):** our breaking-point threshold of 1.10 (10% slowdown) matches their finding that about 10% is the usual detectable effect in cloud with 20 instances x 5 trials. With 5-15 runs on one VM, we are in their tbs "1 instance x 5-15 trials" range, where only some setups detect < 10%. Our effects at the breaking point are much larger (e.g., x1.8-2.6 wall at 0.25 core), so detection is not the problem, but the *exact* location of the breaking point may shift by one step. Say this in Threats.
- **Gap (A/A test):** they say "always perform A/A testing" (p. 38). We should add an A/A check of our breaking-point rule on baseline runs (no new runs needed). If we already have it, cite them for it.
- **Gap (single VM per comparison):** they show that with only one instance, tbs still has FP problems for many benchmarks (Fig. 7, Table 6 rows with 1 instance). Our comparisons are within one VM per machine type, so our results speak for that VM. The cross-machine checks (M1, M2) help, but each is also one VM. State in Threats: "results on each machine come from one VM instance; the cross-machine agreement (CPU breaking point 0.75 core on all machines) reduces but does not remove this risk."
- **Extend:** they study ns-to-ms microbenchmarks; we study minute-long agent runs whose wall time is mostly remote wait. Their variability sources (benchmark, trial, instance) need a fourth for us: the remote model service. Our replay model separates local from remote time, which is a way to remove that source.
- **Where to cite:** Related Work (performance testing in cloud), Study Design / Statistics (paired same-VM design, Wilcoxon + Cliff's delta, A/A), Threats (one VM per machine, 10% detection limit, moving target).

## Link to the thesis (tracing, kernel analysis)
- They explain variability only from end results (CV patterns, CPU model metadata). Kernel tracing could attribute it: e.g., for log4j2 (IO-heavy), trace block I/O latency; for "trial-level effects" (log4j2-5), trace scheduler run-queue latency and steal time during each trial. Commands: `sudo runqlat-bpfcc 1` (run-queue latency histogram), `sudo biolatency-bpfcc 1`, `mpstat -P ALL 1` (%steal).
- Their "benchmark variability vs trial vs instance" decomposition is a good frame for a thesis chapter: use traces to explain *which* level the variation comes from and *why*.
- They could not disable frequency scaling on bare metal. Tracing `power:cpu_frequency` events (`sudo perf trace -e power:cpu_frequency` or LTTng `power_cpu_frequency`) would show whether it mattered.

## Quotes for inline citation
- "We find that the variability of results differs substantially between benchmarks and instance types (by a coefficient of variation from 0.03% to > 100%)." (p. 1, abstract)
- "However, executing test and control experiments on the same instances (in randomized order) allows us to detect slowdowns of 10% or less with high confidence, using state-of-the-art statistical tests (i.e., Wilcoxon rank-sum and overlapping bootstrapped confidence intervals)." (pp. 1-2, abstract)
- "However, running test and control groups on the same instances, optimally in random order, reduces the number of required repetitions (i.e., number of trials or instances)." (p. 4)
- "That is, always perform A/A testing to validate whether the detected changes between different versions are due to software-performance changes or unreliable environments." (p. 38)
- "A more pressing issue is that you can not be sure that the cloud instances have not been upgraded by the provider between test executions of two versions." (p. 37)
- "Hence, one should not read the outcomes of a cloud benchmarking study as a set-in-stone truth." (p. 42)

## Suggested citation sentences
- We run the baseline and each limited setting on the same VM in random order, a design that detects much smaller slowdowns than comparing runs from different cloud instances \cite{laaber2019}.
- In public clouds, slowdowns of about 10% are usually the smallest that can be detected reliably \cite{laaber2019}; we therefore define a breaking point only when the whole confidence interval of the slowdown is above 1.10.
- Following \cite{laaber2019}, we checked the false-alarm rate of our test with A/A comparisons between random halves of the unlimited runs.
