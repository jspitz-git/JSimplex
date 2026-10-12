# AE source and work preflight

517 shared AC source/test/environment/runtime/launcher hashes and all11 AD source
hashes match. No runtime launched yet. AD input file converted to TOML with exact
rational strings, linked by SHA. Driver asserts represented conversion exact.

Dense unit BTRAN uses _unit_transpose_rhs: Vector fallback for PFI, _UnitTransposeRHS
for native Float64 triangular factors (factorization.jl:13,triangular:786). Ordinary
correction BTRAN uses plain vector. forward_solve! is prepared FTRAN; no workspace
pipeline call and hence no extra outer pipeline destination invalidation. Triangular
FTRAN and both BTRAN methods internally invalidate destination; PFI has no prepared
cache. Separate destinations retain prepared FTRAN until one explicit destination
invalidation after all3solves. Record cardinality without copying cache or opaquefactor.
Exactly8 explicit invalidation entry calls; six triangular case cache entries clear,
PFI fallback no-op. Internal triangular invalidations are3/case, counted by source,
not instrumented. Factor initial/refactor kernels and solve entries separated.

Native Float64 factory uses sparse UMFPACK backend; triangular manager wraps base
with identity upper structure and row/work scratch, not another numerical LU.
Fresh setup1factor/case; -I lifecycle1initial plus1refactor/case. Backend refactor
uses existing candidate/spare rules, no externally asserted symbolic reuse. Each
solve entry invokes base solve once; triangular upper/update passes are additional
internal work, not extra basis solve entries. No updates/chains or factor copies.
Prepared triangular FTRAN copies spike/direction and owns2cache slots; actualprepare
counts checked, not presented as zero-allocation. Driver records owned tiny outputs.

Production compensated quality has one entry/case; native products/compensated
accumulation/interval checks inside are not enumerated as extra entry calls. No
fallback forcing or reliable flag overwrite. Actual residual/nothing/finite/reliable
preserved. Global rounding/precision/zero-subnormal and Julia/BLAS1 checked.
Eight cases,24basis solves,8quality entries,8explicit invalidations,8factor setups,
4refactors maximum. No old census/certificate/workspace/publicsolve/adapter calls.
AD deferred wording copy means factor copy; vector copies remain explicitly counted
in source discussion. Accepted AD evidence/report not edited or rerun.
