# S6-P: qualify a balanced binary nearly singular fixture

> Use superpowers:executing-plans inline. Bounded diagnostic spike under standing
> user authorization; no additional confirmation. No permanent test edit yet.

S6-O triangular proposal passes13/13 but presolve removes row2 (all four types:
1row/2columns/2nnz). It changes the feasible set to a nonunique optimal edge and
no longer preserves the original two-row cancellation problem. Retain its evidence;
do not promote merely because equality passes. No need to rerun it.

Propose A=[s s;s s-d], s=2^-20,d=2^-43 from Float32 powers of two, keeping original
row bounds[-1,-1]..[1,1], free columns,c=[0,-1], default options and assertions.
All4coefficients remain nonzero and close in magnitude. Determinant=-2^-63 and
infinity condition number2^25. Strict optimum-2^44 is unique at rows[1,-1],
x=[-2^44+2^20,2^44]. Dual[-2^43,2^43] is stationary with proper row signs.
The maximum coefficient s is binary; unlike old s+d, first complete-pivot choices
can divide by s without introducing a non-dyadic multiplier. This is a hypothesis,
not proof of every backend pivot/scaling/cleanup path. Auto scaling and presolve
must retain the intended problem structure in the observed run.

- [x] Verify exact proof and reversible substitution in original extracted test.
- [x] One four-type qualification with unchanged default public solve/assertions;
  record original certificates, exact residuals, model/globals and phase logs.
  Preserve all failures. Do not repeat S6-N/O or broad accepted corpora.
- [x] Compare observed presolve topology with original2rows/2cols/4nnz. Distinguish
  this from a captured runtime basis or platform proof. Do not claim universal
  equality merely from one local pass.
- [x] If evidence supports repair, write a separate S6-Q RED/GREEN plan using
  actual test-source structural assertion(s), then old assertion-preserving change,
  selected neighboring regression checks and fresh final numerical/work review.
  No solver/tolerance/precision change. If unsupported, reject and preserve it.

Numerical guard/host identity/immutable pins and CI-disabled rules unchanged.
Scope is an input-fixture qualification, not a numerical algorithm repair.

## Outcome

See S6-BINARY-QUALIFICATION.md. No permanent change accepted: S6-O passes but
changes presolve/main numerical route; S6-P preserves topology but fails original
Float64 equality. New point-provenance diagnostic plan is2026-10-12-nearly-singular-point-provenance.md. Final independent review accepted
diagnostic evidence without blockers; see S6-BINARY-QUALIFICATION-REVIEW.md. No RED/GREEN repair starts.
