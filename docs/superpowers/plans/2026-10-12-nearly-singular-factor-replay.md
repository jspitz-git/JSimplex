# S6-R: nearly singular handoff factor-component replay

> Execute inline using superpowers:executing-plans. Diagnostic only; no repair.

S6-Q has no eta at original-bound handoff; the refactor event precedes reconstruction
and final row_solution equals the erroneous structural point. This narrows coverage
but does not isolate factorization, FTRAN, bound flips or publication as the cause.
Do not repeat S6-N/O/P censuses or S6-Q solver trace.

- [x] Reconcile accepted captured immutable CSC B=[1 1;1 1+2^-23], basis[1,2],
  states[BASIC,BASIC,AT_LOWER,AT_UPPER], model bounds and scaling. Derive primal
  RHS[-2^20,2^20] with exact offline algebra matching _nonbasic_value/recompute!;
  captured final scratch_row_rhs=[0,-1] belongs to BTRAN and must not be substituted.
  Verify source/runtime/environment/options/policy/thread comparability.
- [x] Inspect current _basis_factorization, copy_basis_factorization, refactorize!,
  _backend_forward_solve!, pipeline dispatch and _maybe_refine_basis_solve!
  contracts. Establish which wrappers are active under saved legacy policy; no
  guessed kernel or factor lifecycle. Record limitations of reconstructing a factor
  rather than retaining opaque runtime state.
- [x] One bounded component driver, no solve(problem) or workspace reconstruction.
  Compare a fresh B factor and the actual relevant identity-base/copy/refactor
  lifecycle; explain any modeled lifecycle differences. Apply the production
  FTRAN and BTRAN APIs with the exact captured/derived RHS, unchanged precision,
  tolerance and backend defaults. These are new component cases, not control
  solver reruns. Preserve mismatches/failures; count calls, do not benchmark.
- [x] Inspect Julia/SparseArrays UMFPACK supported property contracts locally
  BEFORE reading permutations, row scaling, L/U or control metadata. Record owned
  plain values only, never serialize opaque pointers or mutate backend controls.
  Metadata extraction may allocate and should follow recorded solves. Verify exact
  rational factorization identity under the documented permutation/scaling convention
  when supported; mark unavailable rather than infer it from final error.
- [x] Compare returned point to saved S6-Q row_solution and strict rational solution;
  compute exact residual/objective and inverse amplification offline. Distinguish a
  reproduced component endpoint from proof of the hidden runtime factor internals.
  A reproduced rounded solve can be tolerance-valid; do not weaken equality,
  precision/tolerances, safeguards or alter production to manufacture improvement.
- [x] Verify exit/process/source/input/pins, immutable reports and an independent
  final numerical/work review. Only concrete evidence can justify a separate
  RED/GREEN implementation or fixture-contract plan. No full-suite/x64 assertion.

One guarded Julia/BLAS1,heap2GiB,VM8GiB,minRAM6GiB,maxswap1GiB. Prior runner386534,
child386535,driver386526 require fresh separate host absence and boot identity
before pinned edits/new launch. Preserve raw evidence and all user files. No large
inputs/aliases, old accepted experiments or CI re-enablement.

## Outcome

replay-1:12/12,exit0,21gates/613pins; both fresh and -I/copy/refactor reproduce
saved S6-Q primal and raw rho. Exact factor identity residual(2,2)=-2^-72; exact
factor/application objective contributions sum to-1/16. No original runtime/CI
metadata capture or repair. Final independent review accepted without findings; see S6-FACTOR-REPLAY-REVIEW.md. Next separate
row-balanced qualification plan; report S6-FACTOR-REPLAY.md.
