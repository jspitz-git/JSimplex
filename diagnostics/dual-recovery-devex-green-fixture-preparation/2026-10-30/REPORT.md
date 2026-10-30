# Isolated GREEN fixture preparation correction

**OFFLINE PREPARATION ONLY. No Julia/query/import/parser/compile/numerical process, new seal, numerical admission, attempt or launcher was executed or created.** The failed first GREEN remains NOT ACCEPTED. This correction prepares test inputs and an exact-source dependency check; it does not claim numerical GREEN, cost qualification or production promotion.

## Repair and exact preservation

The first GREEN had5772PASS/0FAIL/1ERROR/0BROKEN: unchanged simplex_numerics_tests.jl:129 tried to read its relative fixtures/solver/netlib/adlittle.mps, which had not been staged. Both preparation and concrete admission overlooked the original dependency. Frozen stage.py copied only wide-bound129; frozen ADMISSION-PREPARATION.md said no other model was admitted. That statement is incomplete for the included unchanged regressions. This separate record explicitly adds the exact existing adlittle input; no frozen statement or manifest is rewritten.

prepared/ contains a self-contained ordinary GREEN tree of91 files: the original green.jl and endpoint.jl, all13 original test/helper files, the74-file candidate project, and two fixture files. All driver/test/candidate bytes match the old accepted preparation; relative includes and the package-source path assertion are unchanged. No source rename, nested module clone, method overwrite, test skip, lowered assertion budget or numerical option/tolerance/precision change occurs. The candidate source remains the same three canonical Task3 substitutions.

The sole new file relative to the equivalent old tree is prepared/tests/fixtures/solver/netlib/adlittle.mps,16500bytes,SHA256fec81e24fa91bc545d97239b108b43e6034f37b4bf2455a3f8c179726b44d44c, copied byteexact from the repository's existing test fixture. The other fixture, generated/wide-bound129.mps, is retained unchanged. It is an existing regression dependency, not a new LP design or replacement numerical witness. No MPS was parsed or solved here.

All255 published files in original Task4 preparation and failed-GREEN evidence remain byte-identical; staging.json records them individually. Original RED/raw/reviews/checks/seals/attempts/failedGREEN and actual src/test/env/CI/master remain frozen and unchanged. Preexisting untracked Manifest/LocalPreferences are preserved.

## Complete bounded input audit

The exact immutable GREEN test graph has15 Julia programs and14 include edges:12 entry includes in original order plus reference.jl and legacy_rebuild_reference.jl. There are exactly two read_mps input call sites:

| Program | Line | Required relative fixture |
|---|---:|---|
| tests/simplex_numerics_tests.jl |129|fixtures/solver/netlib/adlittle.mps|
| tests/partial_pricing_edge_tests.jl |110|fixtures/solver/generated/wide-bound129.mps|

fixture-manifest.json binds every program and both fixture hashes plus original fixture paths/sizes. fixture_check.py verifies source hashes first, traverses literal include dependencies, resolves each input relative to its source, and checks manifest membership, existence, hash, root confinement and no unused/unreachable entries. Unsupported dynamic/multiline include/input syntax or unclassified known IO calls rejects. The exact endpoint open(path,"w") at line105 is explicitly classified as a write-only diagnostic output, not a missing input.

This is a bounded text audit of the15 hash-bound known sources, independently checked by reading them; it is not a general Julia parser, macro evaluator or proof of arbitrary dynamic/package-initialization/FFI/loader dependencies. The implementation does not strip arbitrary Julia syntax and could see tokens inside strings/comments; the exact-source restriction and manual review are mandatory. A changed source needs a new reviewed inventory, not a hash waiver or parser-confidence claim. Production package source loading and stdlib/depot behavior retain the previous limitations. No cache/bootstrap/loader investigation is reopened.

## Offline verification

The new nine-test Python suite first ran against the frozen incomplete staging: exactly one expected failure, missing adlittle; eight rejection controls passed. Its original log is preserved in offline-red.log. With the same test suite and manifest, corrected prepared/ passed9/9 in offline-green.log. Controls reject missing/changed fixture, omitted inventory, dynamic input/include, escaping path, unclassified IO and changed program. These are real filesystem/call-graph checks, not Julia numerical RED/GREEN and not a replacement for the untouched ordinary tests.

The new checker CLI produced fixture-check.json: all15 programs,14edges,twofixtures and one classified output. New source verification17checks/365bindings checks exact91-file tree,98 byteexact preparation copies, all255 frozen publication hashes, unchanged original programs/regressions/candidate, two exact fixture inputs, original12include order, offline tests, no symlinks, no extra numerical reservation and unchanged tracked tree/master. Python syntax checking was AST-only. No old script/test/reviewer/launcher/auditor was rerun.

Fresh host preflight covered all733 previous/current groups AND sessions and exact recorded owner identities, boot781795f4-f7af-4c3b-9ce9-45c7cae76ecb; no Julia/conflicts,available23182052KiB,swap0. HEADa2f2415fcc6c9a018ae8209e28f517da1b23b688, local/remote masterc0fa748ffa61ccb7c1caaf248c40324f60bc737b and diagnostic remote matched. host.json is this new preflight, not a future launch preflight.

## Work and memory

No production execution-frequency, vector/matrix scan, factorization, solve, callback, persistent field or scratch ownership changed. Preparation copies91 files/1237330payload bytes on disk; fixtures total20165B, with16500B additional to the equivalent old tree. These are file payloads, not allocator events, live RAM or native graph bounds. Original and corrected trees deliberately coexist for preservation.

Offline validation is O(total bound source+fixture bytes plus include edges); hashes use1MiB chunks, source-text inspection holds one program at a time, queue/sets scale with15 programs/14edges/twoinputs. SHA/Git scans over255 old files are offline preservation work. There is no numerical hot-path overhead, MPS parser invocation, benchmark or claimed runtime/allocation improvement here. A future run adds only the already-required existing adlittle public regression solve that the failed run never reached; its factor/solve/internal work is not assumed zero or fully budgeted by include markers.

## Next verification boundary

This step creates no new numerical launcher, guard, auditor, concrete seal or admission. Future driver/admission preparation must use the corrected prepared/green.jl and its prepared/overlays/candidate project, bind every executable/dependency and both fixture files, and run the offline fixture checker before launch. The old canonical common/seal/launcher still point to incomplete old staging and a consumed failedGREEN; do not rerun them or substitute this tree without a separately reviewed continuation.

Keep ordinary Test, the exact12includes, full all-green Pass=Total/noFailErrorBroken oracle and46endpoint checks. Do not guess the corrected aggregate count from5772. Preserve failedGREEN accepted=false,absent canonical audit and all old raw evidence. Initial four-process sequence stopped; a new GREEN needs a separately named reservation/outputroot and fresh independent concrete numerical/work-memory admission, then future cost qualification under its own accepted continuation.

Already consumed RED+GREEN time527.9604928489425s, shared1800s unspent1272.0395071510575s. This offline preparation neither spends/resets that numerical budget nor authorizes an automatic fifth process/retry. The separate continuation must account for all consumed time explicitly and state its admitted remaining ceiling; do not bypass failed acceptance via old previous(). Before any future numerical work, fresh full733groupsANDsessions/boot+start_ticks+command/noJulia/refs/resources remains mandatory. Launcher410682/start32720389,guard410703/32720412,child410704/32720428 identities remain historical, not live owners. CI off,HH reuse disabled; broader plan remains open.
