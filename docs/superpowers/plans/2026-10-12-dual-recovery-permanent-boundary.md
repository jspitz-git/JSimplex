# S6-J: explicit recovery boundary in permanent tests

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Make recovery tests explicitly exercise transactional retry, while keeping
native public-iteration safety tests distinct and unchanged.
**Architecture:** Transfer qualified test-only explicit_dual_retry entry helper
from S6-I under a unique permanent name. Preserve entry preparation/exception
semantics and unchanged production retry. Only two recovery groups use this helper.
Name/comments must state that they test the retry boundary, not natural entry.
**Evidence:** S6-DUAL-BOUNDARY.md;140 qualification+108 original assertions.

## Tasks and RED/GREEN contract

- [x] Add a test-owned per-call entry counter to the helper, incremented immediately
  before invoking production retry (after public entry checks). Give each recovery
  case its own counter and assert exactly one explicit retry entry. Keep the old
  public calls initially: expect20 new entry failures and108 old assertions pass
  locally. Save the RED source and log; do not call this CI reproduction.
- [x] Redirect only the four recovery iteration callsites to the helper and pass
  the owned counter. Rename the two groups to state explicit retry scope. Keep all
  original numeric, budget, cancellation, exception and state assertions unchanged.
  Require full-file GREEN; both public native safety/small-pivot groups byte-identical.
- [x] Retain focused permanent successful-candidate and early-cancel/stop-exception/
  invalid-finite-entry controls from S6-I, now also checking entry count1 or0 as
  appropriate. A helper that unconditionally rejects or skips entry guards fails.
  No weakening policies, tolerance or production safeguards; no generic factor API.
- [ ] Fresh independent final review of permanent helper dispatch/ownership/work,
  then test-only commit, master focused verification with source/pins/user hashes,
  authorized push and remote verification. No production benchmark is required.
- [ ] Publish STATUS, report and next failure-family plan. Keep CI disabled and
  actual x64/full-suite status unverified. Preserve all raw/failed attempts.

The counter verifies entry to the specifically declared recovery boundary, not a
particular downstream numerical failure mechanism. Such a path requirement is the
reason for this change. S6-I selected-state equality is bounded local evidence;
no full-workspace or cross-platform equivalence follows. Use the existing single
Julia/memory guard and a separate fresh runner/child/driver absence check before
any Julia or pinned-source mutation. Do not repeat accepted S6-H/I matrices.

## Closure: REJECTED

Independent final review found a blocking downstream-refactor assumption despite
local292/292 GREEN. Candidate source preserved; permanent test restored to HEAD.
Integration/master-run/push gates are deliberately not performed for this rejected
candidate. No assertion weakened. See S6-DUAL-BOUNDARY-REVIEW.md.
