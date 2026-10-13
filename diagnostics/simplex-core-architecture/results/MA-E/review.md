# MA-E independent offline review

**Not accepted for execution.** Five findings remain; E1–E3 affect enforceable admission controls, E4 corrects the work ledger, and E5 aligns the refusal contract. Runtime remains **UNEXECUTED**. No Julia/query/parser/import/compile/Pkg, numerical process, launcher/seal/guard, old audit or synthetic script was run. Only fresh read-only hashing, text comparisons and ledger calculations were used.

## E1: Signal every owned session member during cleanup

active_group_members includes both original PGID and the entire child SID, but signal_owned calls only killpg(child.pid). A descendant that moves to another PGID within the same SID is detected yet never receives TERM/KILL. stop_owned then waits indefinitely while that descendant can continue numerical work after the absolute deadline. --compiled-modules=existing does not prove this case impossible. Preserve the unreaped leader and identify/signal owned session members with start-tick/boot identity protection; use bounded cleanup with a preserved explicit failure if closure cannot be established. Do not report clean closure or start another numerical process while members remain.

Evidence: `guard.py:168`. guard.py:155-184; launcher.py:27 waits without an independent timeout. Source-string session detection test covers enumeration only, not termination.

## E2: Reject changed primary/master before sealing

seal.py copies whatever refs() returns into a newly accepted seal. refs() reads HEAD of the diagnostic and primary checkouts; neither seal nor launcher checks primary HEAD or refs/heads/master against host.json refs.master. A changed primary/master before sealing is therefore accepted even though master must remain 6f68e24e8ddac42b948da8fcc2d636c010751194. Require the frozen master and intended primary branch at sealing and launch boundaries, independently of the deliberately current diagnostic publication HEAD. Hashes of a few primary user files do not establish its Git state.

Evidence: `seal.py:13`. seal.py:10-13; control.py refs; launcher.py:11,21,40. host.json contains the frozen master but no executable comparison uses it.

## E3: Include entry validation in the total clock

The 750-second clock starts after initial seal hash checks, all 658MB of inventory checks, refs/host scans, reservation publication and output creation. This contradicts the stated inclusion of pin checks in wall caps and can admit a sequence whose entry-to-final duration exceeds the hard total while all current checks pass. Capture the total start at launcher entry before validation, propagate the same absolute deadline and refuse before spawning if validation consumes it. Report seal preparation separately if it is intentionally outside numerical-attempt timing.

Evidence: `launcher.py:17`. launcher.py:8-17 versus admission.md:22-28. Per-child checks and cost gaps otherwise count against their deadlines.

## E4: Correct qualification row publications to 432

The 24 star cases publish 6*(6+6+30+30)=432 upper rows. The reported456 equals the selected term count 6*(7+7+31+31), not row publications. Correct the ledger without changing fixtures, arithmetic or any call budgets. The cost total91200selected product/subtraction pairs and96000reset assignments remain correct.

Evidence: `admission.md:71`. Independent fresh arithmetic over fixtures.toml, corroborated by the supplementary ledger-calculation.json.

## E5: Clarify the reservation boundary on preflight refusal

The admission says reservation is consumed on refusal or failure, but launcher seal/pin/output/host refusals occur before attempt-reserved.json is created. Such a refusal can be retried without consuming a reservation. Either explicitly define these read-only preflight refusals as outside the single numerical attempt or consume and preserve the attempt before the relevant admitted checks. Preserve no-retry behavior after reservation and never reuse partial output.

Evidence: `admission.md:25`. launcher.py:9-16; guard/resource refusal after reservation does consume it.

## Source, arithmetic and ownership review

The candidate is unchanged from the MA-D canonical whole source. The generic loop is the original ordered arithmetic; the two specialized methods allocate local scratch lazily and publish through ordinary division. The first subtraction reads the borrowed seed directly. Eligibility checks protect invalid or unassigned operands without replacing original exception behavior; incompatible BigFloat rounding falls back. Installed MA BigFloat and Rational implementations retain separate multiply/subtract operations. No new persistent cache, backend scratch, output alias or precision change was found. Existing signed-zero, nonfinite, MPFR flags, mixed precision, exception ordering, partial publication and shared-leaf tests remain. Actual runtime behavior still requires qualification.

Reference source/test files match originals; candidate changes are exactly the three admitted existing files plus the canonical new test. Both final overlay maps contain515 verified files. Both copied dependency graphs explicitly declare MA1.8.1 and local JSimplex path. Wrapper and nested depot settings, runtime binary/libraries/sysimage and installed MA source are pinned. Loading remains ordinary and unexecuted; this is not cache confinement or a complete import-work proof.

## Independent evidence

All1740manifest hashes and resolved paths match over658551443bytes. The files list equals inventory membership; all1739required entries and hashes match. Relevant source/test/.github, overlays, MA-D artifacts, scripts/configs, plans, report, environment protections and runtime/MA dependencies were independently checked for membership. Supplementary ledger-calculation.json was created after the initial pins; it is bound in review.json and should enter a corrected manifest.

The five instrumentation replacements invert uniquely to the canonical reviewed tests. Independently counted assertions are62/31/96/42/78/72=381. There are77comparison pairs,87reference and92candidate standalone upper calls, four explicit scratch calls; total qualification outer entries are59constructors,6copies,12refactors,83fullforward calls and48prefix dense solves. Internal copy/refactor work is additional original work, not claimed absent. Fixture trace publication is432rows.

Cost counts reconcile:48cases,20processes,10alternating pairs (3warm,7measured),960constructors,4800fullforward solves,4800upper/reset calls,96000reset assignments,91200selected product/subtraction pairs and640cold scratch constructions. First-use and repeated windows use the same signatures; no hidden warmup. Encoding, graph sizing, retained output copies and77/30metric pushes sit outside measured windows. Compile/recompile must be zero in steady windows. Cold qualification/growth timings cannot support a warmed speedup claim. The finite oracle independently checks sequential finite arithmetic and exact residuals; runtime regressions cover nonfinite/sign/flag behavior beyond that oracle.

Initial45/46synthetic evidence remains preserved; the only failure is the wrong deadline expectation. Separate corrected46/46 and24admission checks were inspected, not rerun. A source-string session test is not a cleanup proof, as E1 demonstrates.

## Work and memory ruling

No unnecessary NEW production work, allocations or retained memory were found: src/test/Project.toml have no diff against frozen master. The unchanged candidate adds O(K) eligibility and at most one private scratch set per eligible upper call, plus type/rounding guards. No extra basis solve, matrix conversion, full output copy or persistent backend storage is introduced. These correctness costs remain prospectively included in complete-forward timing. Diagnostic pin checks, exact residuals, retained output containers and bounded metric logs are explicit external costs. No benchmark, speedup, native-memory-release or runtime correctness claim is accepted.

The immutable key-file hashes, actual admission-pins SHA256 and detailed findings are in review.json. Correct the findings, preserve this rejected review and original package, refresh bindings, and obtain a fresh offline acceptance before any seal or numerical launch.
