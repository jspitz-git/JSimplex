# Review record

A separate reviewer performed read-only review of the branch from base `0065da8`, followed by bounded reviews of the evidence-driven repairs. The reviewer did not edit files or run concurrent numerical jobs.

Findings addressed:

- Invalidate rejected primal entering candidates after a fresh factor changes the numerical state, and allow a bounded fresh pricing pass. Fixed in `a9f1d72`.
- Check repriced tableau values after native dual correction before ratio selection or dual-state mutation. Fixed in `a9f1d72`.
- Certifying original primal bounds alone does not establish consistency with stored nonbasic row activities. Added the independent row-activity certificate and cancellation regression before committing `95a41ee`.

The follow-up reviews found no additional concrete issues in:

- Legacy per-bound Harris feasibility, with adaptive aggregation unchanged.
- Signed predicted-point capture, bound flips, original bounds and row consistency, scratch lifetime, cancellation/exception rollback, and policy exclusions.
- Legacy primal transpose-row validation before basis mutation, native correction, finite repricing, pivot agreement, shared pricing rows, one unchanged-basis refresh, and candidate-retry cleanup.

These reviews do not establish that every ill-conditioned LP will solve, or replace the full test and benchmark results in `report.md`.

## Compilation follow-up

A separate read-only review examined the four-file signature simplification and
the new non-hardware regression test. No changed supported Float32/Float64
numerical path or in-tree dispatch ambiguity was found. All eligibility guards
precede callbacks and mutation, and adaptive/staged exclusions remain intact.
The reviewer identified minor differences for unsupported internal invocations;
these are documented in `compilation/report.md`, rather than claiming identical
behavior for arbitrary type instantiations or invalid keyword values.

The review recommends targeted legacy, precision-phase/exception, and direct
BigFloat/Rational validation. Those 14 files pass 776 checks. The direct test
also exercises primal/dual public solves under legacy/adaptive policies. Its
scratch assertions cover selected vectors and cache identity, not exhaustive
mutation of every scratch field. The reviewer found no concrete reason to repeat
unrelated full gates for this bounded compiler change.
