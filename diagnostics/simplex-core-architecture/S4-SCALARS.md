# S4-D: bounded HH scalar component attribution

Source: current production master3220118, diagnostic base2fb78ef. Production
unchanged. Scalar-components-1 exited0 in43.03s with unchanged independently
reverified pins;360 measured compile0 samples cover40cases and10lifecycle paths.
Correctness checks execute outside timed scopes. Fresh independent review accepted the bounded diagnostic without blockers.

## Method and limits

Types: Float16,Float32,BigFloat256,Rational{BigInt},Rational{Int64}; HH/native and
HH/Markowitz. Dimensions8/32, sparse symmetric2x2 blocks and dense identity plus
rank-one, exactly representable1/16 entries. Three rotating rounds per region,
four refactors/extractions per sample; independent fresh owner per sample with
first inactive-slot allocation included. Warmups/construction are outside timing.
No repeat of prior Float64 measurements, no baseline/candidate or whole-solver
speedup claim. Simple fixtures bound rational growth and do not represent arbitrary
fill/growth. Floating residual bound16eps(T)*max(1,norm(rhs)); rational residuals
are exact. This diagnostic bound does not modify production tolerances.

Native actual factors are generic LinearAlgebra.LU at each input type, including
sparse inputs; these are not Float64 UMFPACK measurements. Markowitz factor types
retain the selected scalar. Sparse/dense labels denote input shapes only.

## Component observations

Below: dense32 median microseconds per call and allocated bytes per4calls.
Full min/median/max, allocation events, GC and all8/32 sparse/dense samples are in
results/S4-D/scalar-components-1-audit.json and the raw portable reference TOML.
Elapsed includes GC. Independently sampled medians must not be added: noise can
make a whole-refactor median smaller than a component median (BigFloat/native
backend739.8us vs whole636.375us here). No speedup inference follows from that.

| Scalar/backend | Backend us | Extraction us | Whole us | Backend bytes | Extraction bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| BigFloat/markowitz | 587.550 | 37.075 | 631.950 | 8808200 | 287712 |
| BigFloat/native | 739.800 | 38.100 | 636.375 | 8832352 | 567264 |
| Float16/markowitz | 11.550 | 12.325 | 19.475 | 3656 | 197664 |
| Float16/native | 8.750 | 8.250 | 14.650 | 9952 | 86048 |
| Float32/markowitz | 15.375 | 13.825 | 25.100 | 5832 | 223456 |
| Float32/native | 12.400 | 9.500 | 18.250 | 18144 | 111200 |
| Rational{BigInt}/markowitz | 2715.275 | 72.625 | 2728.900 | 28526168 | 393888 |
| Rational{BigInt}/native | 2690.400 | 117.125 | 2656.775 | 28569648 | 747936 |
| Rational{Int64}/markowitz | 264.050 | 27.175 | 275.200 | 18888 | 377056 |
| Rational{Int64}/native | 270.550 | 21.475 | 277.850 | 67296 | 261728 |

BigFloat and Rational{BigInt} backend arithmetic dominates this small dense case's
allocation traffic (8.8MB and28.5MB per4calls respectively), while extraction is a
much larger fraction for machine floats. For sparse32 Markowitz, BigFloat backend
allocates270784B versus native8832352B; Rational{BigInt}812304B versus27364704B.
These are bounded mechanism observations, not a recommendation to switch backend
or a cross-solver performance comparison. No avoidable production work has been
proven by attribution alone, and no runtime change is proposed by this subplan.

## Ownership and lifecycle

All40cases check fresh/cycled Julia-visible graphs and independent checkpoint
scratch, shared immutable current base and extraction-output non-aliasing. Each
of10type/backend lifecycle cases changes pattern, shrinks32->8, regrows dense32,
passes through empty and restores sparse32, then attempts a singular refactor.
Live and saved factors remain exactly unchanged after failure and solve the old
matrix correctly; failed refactor workspace is released. Exact snapshots use
value equality, not Serialization hashes. These traces have zero update chains;
existing accepted precision/update tests remain separate evidence.

Graphs measure reachable Julia objects, not native allocations, hidden backing
capacity or process peak. Subgraphs overlap and must not be summed. A freshly
copied checkpoint shares the current base; this graph is not a retained-old-base
lifetime estimate. Separate lifecycle saved factors exercise old-base correctness.
Host peak VM1253368KiB,sampledRSS699792KiB,minavailable22207412KiB,swap0.

## Preserved BigFloat fingerprint defect and scoped ruling

The initial audit had17true gates and one failed cross-backend hash gate for all
four BigFloat shapes. The original40case/360sample report remains untouched.
`Serialization` hashes are representation-dependent on this Julia version:
scalar-hash-probe-1 shows repeated serialization of one object is stable, while
an exactly equal deepcopy has a different hash. All8BigFloat backend fixtures
remain exactly unchanged by factorization; canonical hashes of shape/CSC indices,
precision and exact Rational{BigInt} values agree across the two backends.
The probe uses the unchanged original fixture function, not a new recipe.

Ruling: retain original cost samples and label their BigFloat serialization hashes
unsuitable for canonical input equality. Accept the pure pinned recipe and separate
8case canonical/mutation probe as a bounded supplemental check. The original cost
records do not retroactively gain canonical hashes; no numerical/time rerun is
justified for this reporting defect. The original rejected audit, raw hash values,
probe and final22-gate audit are preserved. Future diagnostic hashes should use
canonical scalar values rather than Serialization for this purpose. Cost if wrong:
limited retrospective hash provenance for BigFloat; claims stay at component
attribution with exact internal value checks, not cross-backend numerical identity.

## Next boundary

Choose S5-A ordinary original-model cleanup initialization for a work census and
explicit eligibility contract. `_initialize_workspace_state` allocates a slack
factor, then `_finish_workspace_initialization!` reconstructs and emits
refactor_initial; cleanup replaces the basis and reconstructs again. This is only
a candidate cold-entry redundancy. Observer-visible slack state, expired deadlines,
exception ownership, prior counters, precision-boost/refinement paths and original
certification must retain existing behavior. No direct-basis reuse is approved.
Reuse the completed old cleanup-entry attribution; no old medium rerun. Broader
S4 manager/update-chain/large-input coverage and S6 still remain open.


## Independent final review

Fresh gpt-6-astra read-only review independently checked case/sample/retention/
lifecycle coverage, metrics,22gates and the scoped BigFloat ruling. Numerical and
ownership claims accepted; no unnecessary production work or retained-memory
increase found because production is unchanged. Snapshots, validation, graph scans,
initialization and explicit GC are outside timed regions. No wider claim accepted.

Final: minor (deferred): hh_scalar_audit.py writes the initial audit via write_text;
an accidental rerun can overwrite it before later exclusive output creation fails.
Do not rerun the auditor on this accepted attempt; committed original audit/raw
reports preserve this evidence. A future auditor revision should use exclusive
creation for all artifacts. No runtime/solver issue and no numerical rerun needed.
