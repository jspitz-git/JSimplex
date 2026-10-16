# Column-block U: Task2 BG adapter preparation

The separate Float64 BlockBG adapter and differential tests are prepared and independently accepted for OFFLINE Task2 source preparation. No Julia query, parser, import, compilation, test, solve, numerical measurement or benchmark was executed. Runtime syntax/dispatch/correctness, allocation and performance/memory gates remain unqualified. Task3 driver/admission and production integration were not started.

## Canonical deliverables

- diagnostics/direct-bg-block-upper/reproduce/block-bg.jl: private BlockBGFactor plus explicit FTRAN/BTRAN, unit RHS, replacement, copy and transactional refactor methods. SHA-256 5b6c7bd442c79459e7607e4301e087921196bbd285ccaaa3774fd5b9c918aa4d.
- block-bg-tests.jl: seven named differential/edge/failure test groups, 115 static @test/@test_throws sites. SHA-256 d6997aa4d277f2d46242e9e78d8c891ef00b518677cf0b835ba66861b7fb2eed. Static sites are not runtime assertion counts; loops and nested Task1 oracles add runtime work still to be admitted.
- fixtures.jl: byte-exact frozen seven-fixture source, SHA-256 835b6e4241705b4c7a6a2625c904999ffe30e90ec99c937d257cbe2a2c289517.
- MEMORY-WORK.md and SOURCE-MAP.md: full owner/work/coexistence ledger and helper-by-helper packed-reference contract map.
- adapter-inverse-reviewed.json: exact whole-source reversible derivation, explicit renames and23 changes, including the independently reviewed alias correction.
- overlay-reviewed.json and adapter-source-bindings-reviewed.json: identical manifest of81 ordinary stage files in task2-stage-reviewed. Frozen Task1 contributes78files;77 are unchanged, one root gains the exact adapter include, and three files are added. Task1 and its original78-file stage remain unchanged.

The packed DIRECT BG comparator uses the accepted policy-aware adapter stage, not actual unmodified master dispatch and not the stopped dynamic-slot candidate. stage-source-map.json proves all numerical helper bodies match the repository sources: four whole triangular helper files are identical; triangular_factorization.jl differs only in three previously accepted policy constructors. Staged direct-factor.jl and factor-export.jl are byte-identical accepted dependencies. No old numerical comparator is rerun.

## Behavior and coverage

Solves traverse each column's live contiguous block prefixes in original arithmetic order, with the last-diagonal fast path and original missing/Hessenberg fallback. No packing/mirror, row-incidence solve scan, full invariant pass or extra basis solve is introduced. Elimination advances source/target ranks in stable column order, uses the existing source entry as a direct predecessor for fill, and reloads handles repaired by block edits. Replacement, exact-zero policy, pivot checks, pure-swap batching, history order and two-slot entering/DSE spike provenance follow the reference. Lower export/normalization and native threshold_one/Markowitz default are unchanged.

Differential tests preserve seven accepted fixtures and both genuine backend arms, initial solves, eight updates for nontrivial fixtures, entering then distinct DSE FTRAN, unit BTRAN, copy/diverge after2 and refactor4/8. Added tests cover dimensions0/1/31/32/33/64, nonidentity q, block-crossing rotation/split/fill/delete, signed zeros, cancellation, missing/Hessenberg/nonfinite values, alias and unsupported-call sentinels, malformed export, checked limits, storage-allocation refusal and saved-copy independence. Update failure tests require refactor before a later solve and make no whole-update rollback claim. Full test oracles/snapshots and exact residual calculations are outside candidate code and future timed windows.

## Work and memory decision

Every U/manager/lower/history/cache owner, all nested vector headers/backing capacity and prepared external destination roots are listed. Source-owned growth/copy/refactor coexistence is explicit. Task1 payload16C+4R+28K+32n+656 and outer pointers8n+24D remain unchanged. Adapter direct construction has nine explicit manager-side vector requests beyond U, excluding unchanged backend/export/normalization/library/boxing work. These are source counts, not measured allocation events or native/process peaks.

Solves scale with visited entries/blocks and history. Update ledger includes row searches/gap movements, split staging33/final33 writes, up to63 old tuple moves for delete+merge, map rotations, metadata growth and capped-row-reserve worst-case Theta(f*d+f^2) copies/repairs. Deterministic clearing and duplicated bounded diagonal metadata reads remain charged. No unexplained new full scan, coefficient mirror or retained owner was found. The historical-model dense96 estimate still has only907.2B margin; fragmentation and growth can erase it. No fixed gate passes from these source estimates and no speedup is claimed.

## Preserved findings and verification

The first adapter generator failed before creating a candidate: its inverse selector also matched the new helper declaration. prepare-adapter.py and prepare-adapter-failure.json preserve that failure. Separate prepare-adapter-2.py used exact indented call sites and passed the whole inverse; no Julia or numerical retry occurred.

Initial review accepted the main numerical/storage design but subsequent strengthened alias coverage exposed two blocking findings. Base.mightalias returns false on empty arrays, so exact destination===work rejection had to be restored. Separately, an offset unsafe_wrap test incorrectly assumed dataids detected arbitrary pointer intervals. The one offline correction restored identity-first rejection and changed the test to source-supported shared-Memory wrapping, adding an explicit alias assertion and empty-work sentinel. No new pointer-range hot-path scan or arbitrary foreign unsafe_wrap support was introduced. Installed Julia sources are read-time bindings only, not launch pins. Initial source/tests/reviews/maps/ledger/stage and every failure are preserved.

Author verification: source-check-reviewed.json40 PASS/36 relevant bindings; review-fix.json9 PASS; stage-source-map.json7 PASS. The original40-check record is preserved and explicitly insufficient for alias coverage; its vacuous adjunct is superseded by nonvacuous checks. Fresh independent gpt-6-astra review accepted the final exact candidate/tests/ledger/stage with no unresolved blocking findings, full81-file stage verification, forward/reverse inverse and the five Review Focus classes. reviewer-final-check.json and reviewer-final-bindings.json bind this acceptance. No test or benchmark ran.

Historical mappings are explicit: tests-first/reviewer-v1 test hashes map only to block-bg-tests.jl.before-coverage-amendment; initial source-check and v2 test hash map only to block-bg-tests.jl.before-alias-review; initial adapter/v1/inverse hashes map only to block-bg.jl.before-alias-review. Initial ledger/map hashes map to their .before-alias-review files. Final reviewed bindings refer to canonical current files; no retroactive acceptance or pin replacement.

Fresh host record found no historical groups/sessions and one foreign Julia, which was untouched. New Task2 diagnostics and ignored stages only; actual src/test, environment, CI, master, STATUS and roadmap remain unchanged. Old scripts/raw/results and unrelated user untracked files are preserved. This source acceptance does not authorize Task3. The next separately requested step is concrete RED/GREEN driver and admission preparation, initially without Julia.
