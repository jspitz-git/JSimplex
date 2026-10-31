# Independent revised Task2 GREEN admission

**Accepted** for the exact concrete GREEN command and149-pin manifest SHA256 `d17fbfa45e2e9dd8d1018ed07dad9bda88b7693e421cf7f2603886aabb351c69`. All149 file content hashes and resolved paths match. No Julia or Julia parser ran; no repository files were edited. Acceptance permits this one bounded ordinary test run. It does not assert observed passing tests, native allocation behavior, performance improvement, production integration, or completion of later tasks.

## Prior findings resolved

R1 is resolved by the explicit ownership boundary in WORK-MEMORY and GREEN-ADMISSION: unknown scratch/index/model mutation requires invalidation, discarding the phase and fresh import from an unmodified source. `rebuild_invariants!` is explicitly limited to committed numeric/basis membership and cannot repair poisoned support, RowAccess/model data or an invalid factor. No unnecessary hot-path scan was added to conceal this boundary.

R2 is resolved for this component admission. The test suite now includes an actual native forward solve with an empty saved RHS support and deliberately perturbed finite direction, proving basis-product rows are visited. A separate genuine native solve uses an exact dyadic direction whose second RHS entry is zero, verifies that row2 is absent from saved RHS support, and requires ordinary receipt validation to retain the marked row and positive absolute scale. Finite-input residual overflow and cleanup, pricing overflow and subsequent reuse, nonordered CSC fallback, owner/output/factor-ID/ticket mismatch, ticket wrap, actual factor replacement and fresh import are included.

The original rejected report, initial140-pin manifest/tests/docs, and intermediate147-pin manifest/test are preserved and pinned. The kernel implementation and shared source types are byte-identical to the initially reviewed implementation; only tests and the ownership/admission prose changed.

## Fixture/API inspection

The test-only perturbation wrapper calls the real native solve before changing output[1]; it uses a new wrapper type and adds no production method overwrite. Its SimplexWorkspace and EngineState field generators match the current constructor field layout. Literal perturbations are Float64. The actual replacement calls the existing `_basis_factorization(B, options)` overload and returns the same concrete native PFI type required by the workspace field.

The extreme coefficient exists only in a nonbasic column before construction/import; its basis remains4I. The nonordered CSC fixture swaps paired row/value entries only in a nonbasic column before initialization; LinearProblem reconstructs/copies the raw CSC storage order, and RowAccess detects that order. Neither test mutates the immutable working matrix during an ownership epoch. The exact dyadic canceled-row fixture uses B[2,1]=1/512 and B[2,2]=4 with direction[1]=1 and direction[2]=-1/2048. Inputs, sizes and fixture/import counts remain within the revised48-fixture/import and64-row/128-structural-column cap.

## Numerical, work and memory judgment

No remaining blocking numerical or ownership issue was found for the explicitly private, coherent-input contract. The original complete row-residual criterion remains independently called. The direction kernel preserves ascending basis-coordinate and CSC term order, complete absolute scale, exact-zero support, marked canceled rows and the original zero/pivot/256eps criterion. Finite immutable matrix inputs justify omitting zero direction terms. Nonfinite output, residual or scale is rejected. Factor exceptions count the attempt before forwarding, invalidate evidence and factor state, and remain invalid after numeric membership rebuild; foreign exceptions propagate.

No unnecessary new hot full scan, growing log or retained old factor graph was found. Per solve, the O(m) finite RHS copy/support capture and O(m) finite output capture are explicit; an external RHS check adds O(m), while the exact saved-owner path reuses its support. The retained row check remains O(nnz(B)+m). Sparse pricing visits adjacency terms plus support-prefix maintenance; dense pricing visits all CSC terms and output coordinates. Direction validation visits nonzero direction columns and the union of saved RHS/product rows. Failure-only cleanup and stamp-wrap dense work are disclosed.

Three fixed saved RHS value/index pairs add48m bytes on64bit before headers. Scalar factor IDs do not retain obsolete factor graphs; caller RHS arrays are not retained. Existing Task1 setup/storage remains, including its disclosed inverse-map setup redundancy. No new timing/allocation/native-retention claim is accepted. These require later admitted measurements; this review introduces no extra benchmark.

## Guard and source binding

HEAD remains42d88ae5b486043a8480e75bac8b4224a87b5723. Production src bytes match the loaded master project; all loaded project source and experimental files are pinned. Task1 regression assertion files remain unchanged. The runner and guard sources remain identical to accepted RED, whose observed outcome was6 failures,0 errors,exit1 before implementation. Python source parses by AST inspection only.

The exact command retains existing compiled modules/pkgimages, offline environment, Julia/BLAS1, heap2GiB hint, hard VM8GiB, available RAM6GiB and swap1GiB limits. The common1800s bound includes loading/tests/cleanup. Exclusive output publication, process lock, no-Julia check, parent-death startup gate, exact command/identity binding, deadline supervision, cleanup and postexit pin checks remain. The historical788 base groups are supplemented by RED/current identities, checking both process groups and sessions. Fresh host/process/resource checks remain mandatory immediately before launch; source admission does not replace them.

After the run, inspect actual ordinary test results, marker/exit agreement, all pins, resource/identity closure and preserved output before declaring Task2 GREEN. No public LP solve, benchmark, production/default routing, CI, merge or push is admitted.
