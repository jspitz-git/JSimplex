# S4-AB independent result, numerical, work and memory review

ACCEPTED S4-AB bounded qualification.

This accepts the frozen bounded component qualification and its report. It supports the subsequent concrete permanent-test/source integration subplan, not automatic production promotion, a new qualification run, or an end-to-end performance claim. No unresolved findings were found within this scope. No Julia, numerical driver, launcher, auditor, preparation, postcheck, or publication script was executed in this review. Independent offline Python reads, hashes, source reconstruction, raw-statistic calculations, Git reads and host process inspection were used.

## Source, mathematics and numerical contract

The independent whole-file comparison reproduces exactly the two related edits: initialize `nonzeros` to integer zero and add the existing singleton-loop row length to it. The inverse reproduces production source byte for byte. Independently extracting the original constructor and rebuilding the candidate constructor/refactor methods reproduces both diagnostic files exactly. The executed methods have only two new private names and one redirected constructor call; the existing module and production methods are not replaced.

The sparse constructor first empties all H retained row and column dictionaries, then scatters only current rows 1:n. Thus every row n+1:H is empty at the count, and the original sum over all H equals the candidate sum over n active rows. Singleton insertion order remains 1:n. Dense bypass branches precede the affected reset/count block and remain identical. No scalar arithmetic, pivot threshold, fill/update order, coefficient test, safeguard, precision, exception handler, or ownership/copy code changes. This reasoning applies to Dict/OrderedDict and the stated ordinary length semantics; arbitrary custom dictionary side effects or throwing length implementations are outside the admitted contract.

The raw evidence contains exactly four work cases, 24 lifecycles and 12 cost cases. I independently checked the expected predicate names and literal Boolean values: 24 work, 456 lifecycle and 168 cost predicates, all true, totaling 648. The top-level error list is empty; both success and ambient-restoration flags are literal true. The recorded module path and Julia 1.13.0 match the admitted driver.

For each work case n=3 or 8 and H=n or 64, the raw reference row-read vector is exactly [2]*n+[1]*(H-n), and the candidate vector is [1]*n+[0]*(H-n). These independently reproduce H removed dictionary queries. Both expected SingularException(1) predicates and both clear/owner-retention predicates pass in every case. The helper catches all exceptions but only the specified exception can satisfy its failure predicate; an unrelated exception cannot produce acceptance. Its original exception text is not preserved, a diagnostic limitation accurately disclosed in the report. Only row dictionary owners are checked for identity here; column contents are checked empty, not column owner identities.

The 24 lifecycles have the full four-type × two-dictionary × three-representation product. All four stages are 24→6→6→24, candidate capacity stays 24, and observed workspace graph sizes match by side at all stages. The predicates compare dimensions, sparse-pivot counts, permutations, packed lower/upper factors, diagonal and dense-core factors/pivots using isequal. Known-ones forward and transpose solves use exact Rational equality or componentwise absolute 64eps(T). Every live workspace/row-owner predicate, saved-factor solve and input-preservation predicate passes.

These are selected signatures and selected right-hand sides, not exhaustive factor-state, alias, conditioning, full-solver or certificate validation. Saved-factor solves after refactors provide bounded copy-survival evidence; they do not exhaustively inspect all nested buffer aliases. BigFloat precision and rounding are checked unchanged but their values are not serialized, so no multi-precision sweep follows. Other failure modes and recovery paths are unchanged by the source inverse but are not newly exercised by these fixtures.

## Work, allocation and retained memory

I found no unnecessary added production work, allocation or retained-memory cost. The affected frequency is sparse construction/refactorization, including any call reached from recovery; this is not new per-pivot, per-candidate, solve or certification work. The candidate removes one H-row dictionary-length traversal and reuses the n existing length reads. It introduces integer accumulation in that existing loop, without a new scan, solve, copy, conversion, invariant check, cache, scratch buffer or field. Both full H-dictionary clear passes remain. Consequently the high-water reset cost and retained-capacity scaling are unchanged; this is not a retention or asymptotic-reset improvement. There is no update-chain-length dependence added.

Driver source entries reconcile independently: work has 8 constructor attempts plus 8 workspace creations/resets; lifecycle has 48 constructors, 48 copies, 144 refactors and 480 direct solves; cost has 24 constructors, 48 setup refactors, 960 timed-window refactors and 48 direct solves. Totals are 80 constructors/attempts, 1152 refactors, 48 copies and 528 direct solves. These are explicit entries, not complete PREforward, helper/import/native or machine-operation budgets. Signature copies, graph walks, input deepcopies and known-solution vectors are outside timed windows; their effect on GC scheduling is not proved absent.

Observed final backend graph sizes are equal in all 12 cost pairs. Allocation-event side medians are equal for every case. Rational bytes differ slightly and have been retained in the report and JSON; no allocation saving is inferred from integer-only source changes or these differences. Summarysize is reachable-graph accounting, not RSS/peak/native-memory release proof. Production code, tests, tracked environment and CI files have no diff from master; existing untracked environment files remain outside publication and pinned unchanged for this attempt.

## Independent whole-refactor statistics

I checked every one of the 240 windows for exact pair/side/phase/repetition schedule, finite nonnegative metrics and positive elapsed time. The 168 measured windows all have zero compile and recompile time. Each window contains four complete refactors; setup, two shape-establishing refactors per side and three warm pairs are separate from seven measured pairs. Alternating pair order is preserved. Timing uses OrderedDict; Dict has correctness coverage only. Exact pair factor signatures and terminal solves reduce trajectory ambiguity without expanding the scope to solver performance.

All 12 paired medians/ranges, side medians for time/bytes/events and total measured GC times were recomputed independently and equal audit.json exactly. result-review.json also records per-side measured minima, maxima and totals plus every measured paired ratio. The table below gives paired C/R medians and side median microseconds/refactor, which are different statistics.

| Type | Case | Paired C/R median | R / C median µs per refactor |
| --- | --- | ---: | ---: |
| Float32 | sparse | 1.000000000 | 3.325 / 3.275 |
| Float32 | retained | 0.932735426 | 5.575 / 5.2 |
| Float32 | dense | 0.994845361 | 4.825 / 4.825 |
| Float64 | sparse | 1.007633588 | 3.275 / 3.275 |
| Float64 | retained | 0.950450450 | 5.55 / 5.275 |
| Float64 | dense | 1.000000000 | 4.875 / 4.875 |
| BigFloat | sparse | 1.014432990 | 12.15 / 12.3 |
| BigFloat | retained | 1.001680672 | 14.625 / 14.675 |
| BigFloat | dense | 1.037188820 | 607.325 / 660.075 |
| Rational{BigInt} | sparse | 1.006550218 | 47.625 / 46.1 |
| Rational{BigInt} | retained | 0.987406716 | 49.0752 / 49.45 |
| Rational{BigInt} | dense | 0.923132685 | 2655.3 / 2450.48 |

Retained-capacity Float32 and Float64 have local paired median reductions of about 6.7% and 5.0%. Their low-ratio reference-side timing outliers remain included (minimum ratios 0.638036810 and 0.362098139). Ordinary sparse and arbitrary-precision timings are mixed. Unchanged dense bypass timings also vary and cannot be attributed to the removed count scan. Rational sparse includes ratio 2.819221148; dense BigFloat spans 0.455759079–1.664047653; dense Rational spans 0.155788241–3.414065607. Measured dense BigFloat GC totals are reference 0 and candidate 0.0029655 seconds; dense Rational totals are 0.067304112 and 0.030089106 seconds. No samples or GC outliers were excluded. One process, small fixed fixtures and short windows limit generality; neither equal event counts nor lower operation counts establish a universal speedup. The report's narrow local-benefit claim and explicit absence of a universal/end-to-end speedup claim are supported.

## Admission, preservation, process and publication

The exact accepted manifest SHA-256 is `a0acb394a93db4f636c6a60486b74788035340f5eb060d39d7069760e538d697`. I independently hashed and resolved all 624 inventory files; files/inventory and required-path bindings match, with no external input or tree inventory. The 15-check accepted admission, six-gate audit and seven-gate postcheck are all literal passes. Their hash bindings, allowance bindings, exact commands, reservation, invocation and raw evidence all match. The postcheck is an explicitly unpinned post-exit supplement, not an admission dependency. The launch plan and copied plan remain byte identical and frozen.

One admitted reservation is linked to one successful invocation and terminal exit0, elapsed 27.021221489994787 seconds. All six raw output files match their portable copies byte for byte; raw pins equal launch pins, run.log is empty and launcher.log equals terminal process.json. current.json is a launch-time identity snapshot and its placeholder launch_error/null fields are not terminal failure; terminal status is established separately. The 27 resource samples have minimum available RAM 21820304 KiB and maximum swap use zero; terminal available RAM is 22344924 KiB and swap zero. Inclusive guard time is not a refactor benchmark. Periodic sampling does not establish continuous peak RSS or native allocation behavior.

Runner 165751/start 8101717 and child 165754/start 8101745 have exact recorded commands, shared boot dade7243-9103-4398-bb45-fa28fbc0be72 and consistent current/terminal/invocation identities. Fresh independent /proc inspection checks all 32 previous IDs plus both new IDs against both process group and session IDs, and separately checks Julia process names: no matches. Branch HEAD is e80249a1687be8bde2a9fa4123230e7b8662d99b and primary/master is d02416c108f06fcd41d58e0a1980b70a51fef9ef. No cleanup or numerical repetition was performed.

The continuation map has exactly the two current STATUS/roadmap entries. Their S4-AB before copies equal both recorded hashes and the HEAD blobs. All MA-B review/closure/publication hash entries were independently verified with only those two substitutions; earlier maps are untouched. The current report, STATUS and roadmap accurately make integration conditional on a subsequent concrete subplan and keep broader stages open. This review does not resume automation, enable CI or enable HH reuse.

Static review of the new publication.py finds 41 evidence names plus four external documentation paths: 45 preclosure bindings, 46 nonself staged files after closure, and 47 final paths including publication.json. It requires a separate PASS closure, verifies accepted review and preserved hashes, checks complete untracked inventory, exact staged names/blobs, whitespace, exact committed names/blobs and remote baselines, and uses fail-fast subprocess calls. Its own recursive hash is explicitly excluded while its staged/committed blob is checked before push. I did not execute either phase; this is readiness review, not a claim that closure, commit or push has occurred.

Unresolved findings: none for this bounded qualification. The next step is the concrete permanent work-count regression/source integration subplan and independent review of actual edits. Preserve this qualification and all outliers; no retry, tuning, additional model or production promotion is accepted by this result review.
