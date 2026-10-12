# S6-C: restore pricing refresh test reachability

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Exercise the named fresh-pricing budget path without rejecting an already
valid tolerated bound flip. Test-only correction, no production behavior change.
**Architecture:** Qualify one changed synthetic finite bound, retain all terminal,
iteration/refactorization/basis/exclusion assertions, then add an explicit fixture
precondition and diagnostic event proof. Preserve old failure evidence.
**Tech Stack:** Julia Test, guarded diagnostic probe, Python pin audit.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md; S6-A/B evidence.

## Constraints and review focus

No tolerance/precision/safeguard change. Synthetic fixture column_upper[1] may be
raised from1 to1e8 solely to make1e-14*upper exceed the existing primal tolerance;
this is a test reachability repair, not a performance comparison. No external input
or full suite, no accepted measurement repeat, CI disabled. Single guarded Julia
with existing limits, fresh separate absence check before source edits/next run.

## Tasks

- [x] Probe this one fixture change diagnostically before editing the test; require
  terminalNUMERICAL_ERROR,iterations0,refactors1,unchangedbasis,emptyexclusions,
  and observer-free/observed exact selected-state equality. Save event sequence;
  if these fail, preserve and reconsider instead of adjusting solver/tolerances.
- [x] After proof, update only the fixture bound/comment and add a precondition
  showing its bound flip exceeds the existing tolerance. Preserve all original
  behavior assertions (guard terminal access to report failure instead of error).
  Existing oracle-1 is RED2pass2fail1error; new fixture must pass relevant whole
  preference file. Verify no production source diff.
- [x] Fresh independent review of S6-A/B evidence plus this test correction, with
  explicit numerical/work/memory ruling; no benchmark for test-only work. Integrate
  only reviewed test commit, focused master check, preserve user hashes, push refs.
- [x] Update STATUS and automation. This fixes at most one test family; no overall
  CI/full-suite/S6 pass and no change to disabled workflow state.

Closed: independent review accepted; mastera465da5 focused20/20,11audit gates, push verified. Other CI families remain open.
