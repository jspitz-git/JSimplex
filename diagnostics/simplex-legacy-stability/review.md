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
