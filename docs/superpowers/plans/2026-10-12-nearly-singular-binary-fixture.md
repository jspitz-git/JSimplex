# S6-O: qualify a binary triangular nearly singular fixture

> Use superpowers:executing-plans inline, sequentially. Diagnostic qualification
> first; no permanent edit until a separate focused RED/GREEN implementation plan.

S6-N reproduced the original Float64 equality failure: y=[-1,1+2^-47] and gap=-1/16
are consistent with unchanged original primal/complementarity tolerances. Preserve
its source and evidence, do not rerun the accepted census or loosen equality.

Proposed small fixture: A=[s s;0 d], s=2^-20,d=2^-43, row bounds[-1,-2]..[1,2],
free columns, c=[0,-1]. It keeps determinant2^-63, strict objective -2^44, and the
a strict optimal corner[-2^44-2^20,2^44] at rows[-1,2]. Its infinity norm
condition number is2^24+2; nearly singular in Float32. Two bounded rows and
invertibility still exclude a recession ray. Binary triangular structure removes
the subtraction of nearly equal matrix entries in factorization. This is a new
fixture hypothesis, NOT yet numerically qualified and NOT equivalent feasible set
to the old matrix/box. The original cancellation stress case remains in S6-N.

- [ ] Reconcile intended no-recession test contract and exact proof. Verify the
  condition number formula and document the changed feasible set/unique optimal
  corner versus non-unique optimal edge (objective depends only on x2).
- [ ] One bounded four-type qualification, unchanged default public solve and
  all original status/publication/exact objective assertions; substitute ONLY the
  proposed matrix and second-row bounds in a diagnostic extracted testset. Record
  exact returned point/objective, original certificates, options and model/global
  preservation. No tolerance/precision changes or repeated accepted runs.
- [ ] Check Float32 failure publication, floating native/backend sensitivity and
  rational strict optimum. A local pass is not proof of every BLAS/platform path.
- [ ] Decide whether a permanent test repair is supported. Preserve cancellation
  coverage evidence and do not claim this fixture verifies arbitrary nearly
  singular factorization accuracy. If accepted, write a separate RED/GREEN plan
  adding exact structural/margin checks first, retaining all original equality/
  status assertions and leaving neighboring testsets unchanged. Review once before
  integration. If not supported, preserve rejection and select another open family.

Use one guarded Julia; separate fresh boot/start_ticks/command and prior runner/
child/driver absence before launch/pinned edits. Preserve raw failures, environments
and user files; no large inputs or accepted corpus/reference repeats; CI disabled.
