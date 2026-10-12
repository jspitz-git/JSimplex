# S6-M: repair the cross-precision infeasibility fixture

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

Prerequisite: accepted local S6-L qualification of row_lower=4g with unchanged
supplied tolerance t=g-2^-80. If qualification fails, do not begin this edit.
No solver, policy, tolerance, ambient precision, rounding or workflow change.

- [x] Add exact rational margin assertion for kind=:primal before the solve:
  original row lower bound > 2 * stored primal tolerance. Keep old row_lower=g
  initially. Extract the actual constructor and assertion from the test source for
  one RED control (kind=:primal,interval=1); do not solve or repeat S6-K matrix.
  Expect exactly one failed margin assertion, not an import/parser error. Preserve
  raw RED and frozen test source.
- [x] Change only primal construction row_lower=g to4g, with a comment explaining
  independent row/column allowances. Keep every original status assertion and
  dual/zero branch unchanged. Run the same margin control to GREEN and the complete
  cross-precision status testset plus neighboring supplied-option preservation
  testset. These are new-source regression gates, not repetition of old baselines.
- [x] Audit exit, pins, actual source/test hash, exact constructor/assertion diff,
  no production changes, independent public option retention checks and ambient
  globals. Preserve failures. Report limited local platform coverage: robust
  infeasibility does not prove end-to-end last-bit status sensitivity.
- [x] One combined independent final numerical/work/memory review of S6-L/M. If
  accepted, commit only test file and cherry-pick to master preserving user files.
  Fresh absence check, guarded targeted master verification, source/pins/user hashes,
  authorized push and remote verification. Never enable CI or claim full-suite pass.
- [x] Publish reports, STATUS, ledger and a concrete remaining CI-family subplan.

Use the existing one-Julia guard (Julia/BLAS1,heap2GiB,VM8GiB,availableRAM6GiB,
swap1GiB), separate process identity/absence checks before launch or pinned edits.
No forbidden models or aliases; no broad corpus/long baseline reruns. Retain all
raw evidence and old checkouts/environments. A numerical failure of the candidate
must be investigated, not bypassed by permissive statuses or higher precision.

Closed: test2c3e0eb -> master7fea422249442003b53f6f245bb569a5e0cf9bcf; fresh
independent review, master1477 assertions/14gates, source/pins/user hashes and
remote master ref verified. S6-N is the next bounded plan; full S6 remains open.
