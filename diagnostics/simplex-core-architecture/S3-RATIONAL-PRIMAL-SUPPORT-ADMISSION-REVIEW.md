# Independent S3-G source/design review

**S3-G ACCEPTED.** No findings. This accepts rejection of the proposed support-only Rational{BigInt} primal update under the required ownership contract, the scoped continuation edits, and the inspected single-use publication procedure. It does not admit an optimization, numerical launch, production integration, or broader S3 completion. Publication has not been executed by this reviewer.

## Source and ownership decision

Installed `gmp.jl:63–73` defines mutable BigInt. The immutable Rational fields in `rational.jl:9–17` therefore contain mutable owners. The generated `+`, `-` and `*` entries in `gmp.jl:1093–1099` construct `unsafe_rational(BigInt(), BigInt())`; finite `sub!` and `mul!` pass those destinations to GMP, and `sync_rational!` at 979–986 updates and returns their fields. There is no zero shortcut returning an operand in these outer methods. Omitting a successful subtraction of a zero product consequently retains the old numerator and denominator objects where the dense source creates replacements.

The report's retained-field `===` oracle is a valid source-derived discriminator, provided the selected basic entry is not overwritten again by the final entering addition or repeated indices. The ordinary unique basis with a separate entering index supplies that prospective case. This oracle was not run. The rejection follows the plan's explicit ownership-preservation requirement; it is not evidence of a failed solver trajectory, a supported arbitrary-mutation callback API, or impossibility of a future design with a different accepted contract.

Actual sharing mechanisms exist in recompute (`src/simplex.jl:465–471`) and staged primal copies (`src/simplex_pivot.jl:47–49,80`). Array ownership does not recursively detach Rational fields. The report correctly distinguishes those mechanisms from proof that every alias survives at a particular pivot. Cache fields in `HypersparseWorkspace` and `IndexedVector` contain buffer identity, support and validity information, not an element-ownership certificate. Observer absence alone cannot supply one.

The installed `mul!` infinity/zero branch at `gmp.jl:1059–1069` throws DivideError. The ordinary caller checks finite direction and steps (`src/dual_simplex.jl:1267,1419`); the direct helper has no such guard. This distinction and prefix-write failure behavior are preserved. The review makes no dispatch, loader, allocation-event or runtime execution claim from the installed source hashes.

## Admission, order and five review classes

The attempted admission is bounded and ordered: exact type/policy/finite step, existing matching cache and six owners, row_solution identity/dimensions/validity, array and basis-order restrictions, then the indispensable omitted-write ownership condition. That last condition is unproved by current metadata, so the accepted outcome is rejection, not an implementable positive predicate. No always-false runtime check is added.

All five required classes have adequate rejection/fallback decisions and prospective oracles. Direct array overlap, repeated indices and an entering index already basic retain dense sequential writes and the final addition (`src/dual_simplex.jl:593–600`); the Basis constructor does not certify uniqueness. Missing, invalid or mismatched support cannot invoke the mutating accessor as an admission query: `_pipeline_vector!` may construct a cache, rebuild O(m), or compact O(s). Valid indices may contain cancelled zeros. Observer events receive workspace state, bound flips may emit events before the consumer, and recovery writes invalidate directions. No callback-neutrality or ownership proof is inferred from the ordinary local direction-preservation path. Full support and every other scalar type remain dense. No reordering, tolerance change or helper-contract strengthening is proposed.

## Computational work and memory

**No unnecessary NEW production computational work, allocation or retained memory was found.** The src/test/.github diff against master is empty. There are zero added production scans, solves, copies, conversions, repeated checks or retained owners at setup, refactorization, iteration, candidate, recovery or certification frequency. No matrix-nonzero or update-chain scaling changes occur. Documentation-only evidence needs no benchmark; none was run.

The unchanged reached helper visits m basis rows, performs m multiplications and m subtractions, and then one addition. The four BigInt constructor calls per successful finite row and two for the final addition are source counts, not measured allocations, retained bytes or a complete native GMP budget. Bit complexity depends on limb lengths. Hypothetical admission adds a bounded set of scalar/cache/dimension checks, including six owner comparisons; hypothetical indexed execution visits stored support length including cancelled zeros. Re-detaching omitted rows by dense writes would preserve O(m) traversal and scalar work, and an O(m) local scan still cannot certify absence of external references. The report makes no speedup claim and introduces no cache or invalidation obligation.

## Evidence, continuation and publication

All eighteen `source.json` bindings independently match, including both installed scalar files; the fourteen source gates agree with the inspected text and are not runtime tests. Both pre-G continuation snapshots exactly equal their HEAD versions. All six current STATUS/roadmap hashes in F closure, publication and final review resolve to these snapshots. Only those current bindings receive the new mapping; earlier F snapshots and older mappings remain intact.

The two host records agree on boot, refs and all twenty-eight groups/sessions, with empty matching-process lists. A separate read-only review check also found no matching group/session or Julia process. These are timestamped checks, not a continuing host guarantee. HEAD remains `7ddea1bba37e2783871b5d947e261554de88a856`; master remains `d02416c108f06fcd41d58e0a1980b70a51fef9ef` at review. The index is empty and the only tracked worktree edits are STATUS and the original roadmap.

Continuation records the scoped stop, preserves broader open stages and all stopped directions, and authorizes no equivalent ownership inventory. S2-E allowance remains consumed, S6-AQ needs new original evidence, HH reuse remains disabled and CI remains off. The G plan stays unchanged.

The unexecuted `publish.py` explicitly whitelists eight evidence files and requires exact directory membership, accepted independent review and matching bindings before writing separate PASS closure/publication records. It checks initially empty staging, scoped tracked changes, fourteen exact staged names and every staged blob before commit, then exact committed names/blobs before push and both remote refs afterward. Previous snapshot bytes are preserved. This review accepts that inspected procedure, not an unobserved publication result.

No Julia, parser/import/compile or numerical experiment, candidate/driver/launcher, historical auditor rerun or historical artifact rewrite occurred in this review. Existing untracked Manifest.toml and LocalPreferences.toml were not modified. `results/S3-G/review.json` binds this review and the inspected final inputs, excluding its own recursive hash.
