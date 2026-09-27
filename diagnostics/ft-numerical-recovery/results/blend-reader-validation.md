# BLEND reader correction

Input: `/home/jspitz/NetLib/blend.mps`, SHA-256
`c8bb193f8af5dcff735a3b8db62077db93625e93cfb26e2b01f83ca3039cbf7d`.
Validation used Julia 1.13.0 on Linux aarch64, one Julia/BLAS thread and a
24 GiB virtual-memory ceiling. The input file was not modified.

The reader first rejected the descriptive text following `NAME BLEND`.
After accepting that header, it rejected the initial blank RHS set name at
line 355 as an invalid continuation. Both failures were reproduced before
their respective fixes with independent regression tests.

The reader now ignores descriptive text on the initial NAME header. An initial
blank fixed RHS, RANGES or BOUNDS name represents an unnamed set; subsequent
blanks retain the existing continuation behavior. Unnamed sets can be selected
explicitly with an empty string. Initial blank column names remain errors.

Validation results:

- Parser and model-construction suites: 1,667 assertions passed with
  `--compile=min` (`test/mps_parser_tests.jl`, `test/mps_build_tests.jl`).
- Normal compilation: 560 parser assertions, 84 allocation/token-lifetime
  assertions (`test/mps_allocation_tests.jl`) and 13 public-reader assertions
  passed. Automatic reading and explicit fixed reading with `rhs_name=""`
  produced identical model fields: 74 constraints and 83 variables.
- The existing `reproduce/validate-small-models.jl` script solved BLEND with
  legacy dual, steepest-edge pricing, native refactorization and interval 80,
  once each with PFI, Bartels-Golub, Forrest-Tomlin and Suhl-Suhl. All four
  returned OPTIMAL after 83 iterations, with objective
  `-30.812149845828216`. All original-primal feasibility and objective-agreement
  checks passed (11 assertions). These runs used `--compile=min`; their times
  are not performance measurements.
- Independent read-only code review found no blockers; `git diff --check` passed.

This corrects the reader limitation recorded in the earlier small-model
validation. It does not change the pending Windows runtime acceptance check.
