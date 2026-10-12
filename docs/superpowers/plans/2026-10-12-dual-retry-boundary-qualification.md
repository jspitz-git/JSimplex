# S6-I: qualify explicit transactional dual recovery tests

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Determine whether recovery/callback assertions can explicitly test the
transactional retry boundary instead of incidental native-roundoff entry.
**Architecture:** Diagnostic-only redirect of the two recovery testsets' iteration
calls to a uniquely named helper invoking the existing retry with guarded stop,
ordinary dual tolerance, unrefreshed entry and unchanged perturbation argument.
No production modification; retain public duplicate-column safety and accurate
small-pivot tests as independent obligations. Do not call this a public-path fix.
**Evidence:** S6-DUAL-RECOVERY.md; current108original assertions and20pairs accepted.

## Tasks

- [x] Inspect the retry caller contract and existing direct-boundary tests. Establish
  necessary entry state, finite/auto-pricing preparation and ownership obligations.
  A direct call must not silently skip a necessary precondition. If unsafe, reject
  this proposal and document a bounded alternative without changing production.
- [x] Define a unique diagnostic helper with explicit arguments and guards. Confirm
  existing ratio/candidate/quality/recovery work remains production code. Preserve
  original policies and assertion nodes; only calls in the two recovery groups may
  redirect. Keep native duplicate and consistent-small-pivot groups unchanged.
- [x] Qualify four managers and all five existing modes with selected state/events,
  consumed work, scratch cleanup, factor ownership, callback wrapping and cancellation.
  Confirm every expected rejection/refresh event is actually reached. Include a
  separate successful candidate/direct path control so unconditional rejection
  cannot satisfy the helper's proof. Do not repeat accepted whole corpus.
- [x] Audit exit/source/pins and original redirected assertions. Local acceptance
  does not prove x64 arithmetic or historical CI root cause. If qualified, propose
  a separate permanent RED/GREEN subplan naming the narrower recovery contract and
  retaining public-path coverage. No assertion weakening or safeguard change.
- [x] One fresh final independent numerical/work/memory review before integration;
  combine with the eventual permanent test review only if qualification is complete
  and the same helper is being transferred. Preserve all failed attempts.

Use the single-process memory guard and fresh host absence checks before launch or
pinned edits. Keep CI disabled, all user files/environments/raw attempts preserved.
Production unchanged means no performance claim or benchmark requirement.

Final ruling: local qualification recorded; permanent S6-J proposal REJECTED by
combined final review. No production/test integration. See S6-DUAL-BOUNDARY-REVIEW.md.
