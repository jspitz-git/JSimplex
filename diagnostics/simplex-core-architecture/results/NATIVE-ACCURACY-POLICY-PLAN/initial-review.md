# Initial independent source/design review

Decision: changes requested; not numerical admission. Both findings were reported to the author before edits.

1. Important R1: PIVOT_TOLERANCE=1 is full partial pivoting for an UNSYMMETRIC strategy. AUTO may choose SYMMETRIC, whose diagonal acceptance uses the unchanged SYM_PIVOT_TOLERANCE. Record the actual strategy and qualify the interpretation; do not force strategy or add an arm. Bound header lines 614–626 and 1101–1133 support this distinction.
2. Important R2: remove the optional overlay/loading ambiguity. The component only needs SparseArrays, LinearAlgebra and TOML under the ordinary project, without importing JSimplex or constructing an overlay. Preparation must pin the runtime, project and environment.

Independent checks verified all 19 original source bindings, all 514 baseline hashes, HEAD/master, 132 cost windows, 141 fresh LU, 9 lu! attempts, 3 copies, 4245 FTRAN + 2133 BTRAN entries, 405504 cost output elements and 12 final snapshots. Lifecycle output storage adds 1344 Float64 entries before metadata/headers.

The inspected wrapper copies constructor controls and CSC buffers, sizes W to n or 5n, gives copy(F) independent control/workspace/Info/lock but shared native/CSC owners, and permits lu! to mutate candidate storage before a singular exception. Independent T construction is therefore essential and correctly prescribed. Production copy shares all of F and fresh refactorization uses default lu; neither behavior is changed or qualified by this component plan.

There are no production-code changes and no newly introduced per-iteration, recovery or certification costs. No unnecessary new production work or retained memory was found. Planned R costs are real: 32n extra workspace payload bytes per factor/workspace, residual work and up to two correction solves per solve entry. The diagnostic retains 3244032 bytes of output element payload plus headers/lifecycle data and discloses its timing/GC effects. No speedup or native allocation-balance conclusion is justified. No numerical execution or old auditor replay occurred.
