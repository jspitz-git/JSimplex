# S6-F: qualify a controlled artificial-row test fixture

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Establish a deterministic test-only row-solve seam before repairing the
roundoff-dependent budget/cancellation oracle. No production change in this plan.
**Architecture:** Wrap an owned factorization in a test-only forwarding adapter,
reconstruct a workspace with that concrete factor type, and inject one bounded
unit-row error after setup. Exercise unmodified production remove_artificials!.
The S6-E AST clone is mechanism evidence only and cannot be the permanent target.
**Tech stack:** Julia test-only adapter, existing guard and independent audits.
**Spec:** architecture design; S6-ARTIFICIAL-ROW.md and S6-D/E raw records.

## Constraints / review focus

No CI enable, production hook, method overwrite on production types, tolerance or
precision change, skipped old assertion, repeated accepted census or cost run.
First inspect existing test adapters and generic factor fallbacks to avoid a new
unnecessary seam. Use the same single-process memory limits and fresh host checks.
No qualification means no permanent test edit. Counterfactual96failure predicates
are not exactCItrajectory proof; actual CI row/backend cause remains unknown.

## Tasks

- [ ] Inspect SimplexWorkspace constructor fields, _pipeline_basis_solve!, factor
  traits, forward/transpose solves, update/refactor/finite checks, copying and
  recovery ownership. List exact methods the adapter must forward. If this requires
  changes to production or hides a safety gate, reject the design and document the
  smallest alternative diagnostic plan; never grow a production API for this test.
- [ ] Build an isolated diagnostic adapter forwarding all ordinary behavior to its
  owned real manager. Arm only after fixture setup. Target exactly the first unit
  BTRAN in artificial removal, not setup/pricing/refinement. Count hits and capture
  input/output; preserve subsequent solves/update/refactor and callback ordering.
  Qualification must prove disabled adapter matches real factor selected state;
  enabled seam changes only its declared row output. Avoid global method overrides.
- [ ] Propose one explicit finite row perturbation and prove independent unchanged
  solve-quality rejects it, while the real correction path can repair it. A fixed
  small rational/integer fixture may reduce dependence on native LU roundoff.
  Record actual matrix/row/error, not a platform-dependent claim from eps alone.
- [ ] Run bounded manager/mode matrix including zero budget, checked/dual exclusion,
  cancellation, exact callback exception, stringent pivot, infeasible original
  export, successful correction and reliable no-correction control. Require all
  old semantic assertions plus actual injection and correction reachability.
  Export checks stay against original model; charge consumed work on failure.
- [ ] Audit source/pins/process and forwarding work. If qualified, write a separate
  permanent test RED/GREEN/integration subplan; otherwise preserve all failures.
  One fresh final review. No claim of x64CIvalidation from local AArch64 evidence.
