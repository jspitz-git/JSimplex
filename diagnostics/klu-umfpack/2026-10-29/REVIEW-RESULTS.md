# Independent result and work/memory review

Decision: **ACCEPT the recorded fixed-basis comparison and REPORT.md. No unresolved important or critical finding.** Review used the requesting-code-review assignment and AGENTS.md. Only static reads, hashing, and fresh offline Python recomputation were performed; no Julia/native execution, old analysis script rerun, new measurement, or frozen evidence rewrite occurred.

## Evidence binding

The executed driver is `d23e84344289bfd6bed9cf484d826556223e6fd075f6ae6876056adf788cd60b`, exactly the final admission binding. All **57** launch inventory entries were independently rehashed and resolved-path checked with zero differences; the guard's copied manifest equals the launch manifest. All **six** recorded loaded library paths independently match library-pins.toml and their actual file hashes, including KLU 2.3.5 and UMFPACK 6.3.5. This verifies recorded binary identity, not upstream-to-installed reproducible build provenance. The initial Rs-order rejection and both intervening source versions remain preserved and launch-pinned; final admission, not the earlier correction-only acceptance, governs the executed bytes.

SHA-256 bindings of reviewed artifacts:

- `PLAN.md`: `dddb8617c1acbb7ca5290c360f5eb58f630c000b5f1995e664072a30eac8a595`
- `REVIEW-ADMISSION-ORDER-FINAL.md`: `39e426d979d043edf43d610aa12b44366a744f3b6a29fb50dc6f97b3f425e836`
- `results-1.toml`: `188c35f69621704b67e99637ddaf6f47696d59bf9ace5c6e2f822cb4d67f530c`
- `analysis.json`: `5d9f8dca808236cf17fe17fc4b7708d8c1829d925e84409d8491a71baf532560`
- `summary.csv`: `d676a8a4dab16bad221798a8ab238a41d4c61dcf6fdadb56525a25961a1e9802`
- `derived-summary.json`: `9633e37fc4a22fbbec1f6d18b6ee61eae86da1993bfe06e6052df967700de87d`
- `REPORT.md`: `f3e4a6d7b594d0cf02fc501069ae55bcf26a1c0e13a2d18cb836edd0bd175716`
- `launch-pins.json`: `3a664324b4742c9bd230bce073b82132692684ada806f13dbfa74d3759c6d618`
- `comparison-1/guard/process.json`: `22c7d0d061fc0802a994b7537006ea414f3b9b2221b14f71cb8f061ec6c15b8b`
- `comparison-1/guard/resources.jsonl`: `48efb01f36adef9d18fad7718f3155e67c248b6d8a5e6223147a87908b39f993`
- `comparison-1/postflight.json`: `20c1bee2ff0ecae9b76b5f502f23815622cfbb6091cf9ae9415f3c1863ac24a6`

## Independent result checks

Fresh computation directly from results-1.toml agrees exactly with all **36** paired factor/FTRAN/BTRAN median, minimum, maximum and unscaled MAD distributions, all **24** summary rows (including per-call divisors, allocations and native/graph/storage data), and all **12** derived triplet/current/peak/allocation ratios. Absolute arm medians are correctly distinguished from medians of round-matched ratios. The report's percentages and tabulated rounded values agree.

The complete workload is **12 cases, 24 cold qualifications, 48 warm samples, 120 measured samples**, with unique complete round pairs. Literal accounting independently gives **196 factor attempts, 8522 FTRAN and 4272 BTRAN**: 192 main successful builds, two ownership successes and two expected singular attempts. Three cold normal solves plus two known-point solves per factor explain the otherwise easily missed call counts. Recorded Test output is 1009/1009 with exit 0; the 20 offline acceptance checks are corroborated by direct data/source inspection.

Every cold and warm/measured ordinary residual meets its case's unchanged tolerance. Every directed enclosure passes with upper residual no larger than lower allowed threshold. Maximum cold normwise residual is 1.1988967381689757e-14, known-point relative error 1.143004552117688e-9, scaled growth 1.9566103430244413; all storage bounds pass. All 120 measured samples have zero compilation, recompilation and in-window GC in all three stages, and zero GC-counter bytes/events for both solve stages. Output hashes are stable within arms. Source establishes matching owned input bytes, caller-value poisoning and expected singularity tests; cold numerical checks precede all KLU extraction/sorting.

Guard/process records show exit 0 after 25.159995 s; supervisor accepted at 25.368292 s without timeout/kill/abnormal cleanup. The 25 resource samples have minimum available RAM 22,162,376 KiB and zero swap. Last sampled HWM/VM peak are 608,296/1,166,308 KiB, consistent with reported process context. Recorded postflight has no conflicts across all 713 historical/new groups and sessions, no Julia, and unchanged master refs. These are recorded run/closure observations, not a newly executed numerical test.

## Work, memory and numerical interpretation

**No unnecessary new production work or memory cost was found: production code is unchanged. Avoidable cold diagnostic work exists and is honestly excluded from measured kernels.** Per cold factor, UMFPACK performs three property extractions; KLU performs five sort/extract calls for nonempty F and four for empty F, plus F column sorting where needed. Repeated residual/norm/hash scans cost O(nnz+n); residuals and directed 256-bit checks allocate O(n) scratch, with BigFloat objects in cold certification. Invariant norms could be cached, and a combined extraction could reduce cold repetition, but neither is a blocker for this finite diagnostic. All 12 immutable cases are intentionally retained; result rows retain scalar metadata, hashes and control copies, not factors or exported factor matrices.

Each fresh build includes owned O(n+nnz) CSC/index conversion, full symbolic/BTF/order and numeric work. There is no symbolic reuse or update-chain scaling in this experiment. Reused x/y/z buffers sit outside solve windows. Each KLU solve includes an O(n) RHS copy for its destructive API; UMFPACK's three-argument API uses distinct input/output buffers directly. Locks/checks and adapter costs are included. Consequently these are concrete backend API/policy costs, not pure triangular-kernel or production speedups.

Allocation bytes, event counts and retained memory are correctly kept distinct. On the six runtime cases KLU's factor allocation bytes are 0.502–0.566 times UMFPACK's, events 15.46–19.36 times, final native current 1.100–1.208 times, and native peak 0.674–0.812 times. Lower traffic/fill therefore does not imply lower retained memory. Event category attribution is explicitly uninstrumented. KLU current/peak are captured after the five cold solves and before extraction, and include native permanent workspace; UMFPACK uses its documented size-unit reports. These library reports are not allocation/free ledgers. Julia reachable graph sizes omit native pointer payload; RSS and release RSS cannot establish native free.

The Rs scatter through final pivot permutation is preserved. KLU versus UMFPACK ordering, scaling and numerical pivot policies differ despite tolerance-one controls. The one-block explanation matches the pinned kernel/header and controls: whole-block sparse left-looking factorization, empty off-block F, complete native forward/transpose solves with permutations/scaling, without backend substitution. The 256-row sparse and dense controls both report one block/F=0; the coupled control reports 32 blocks and nonempty F. Singleton and BTF-disabled configurations are not separate measured cases and no general performance conclusion follows for them.

Five round pairs in one process are limited evidence, with several ranges crossing one and a large coupled-control outlier. REPORT.md exposes those limitations and appropriately retains UMFPACK as default. No whole-solver speedup, current-master trajectory equivalence, integration/update/recovery/certification qualification, other-precision support, native-free proof, or general backend-selection claim is established. No extra benchmark is needed to accept this documentation-only result review.
