# HH Markowitz component attribution plan

> **For agentic workers:** Use superpowers:executing-plans inline and sequentially.

**Goal:** Extend S4 component and ownership attribution to Float64 Markowitz,
without repeating the accepted native reference or changing production code.
**Architecture:** A separate diagnostic driver reuses the native fixture recipe,
three independently measured scopes and fixed six rounds of16 calls. Markowitz
uses two private construction slots; inspect both slots, workspace and packed
pools, and distinguish fresh-owner costs from warm compilation.
**Tech Stack:** Julia LinearAlgebra/SparseArrays/TOML/SHA, guarded_run.py.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md

## Constraints and interpretation

One numerical Julia/BLAS thread, heap2GiB, VM8GiB, availableRAM6GiB, swap1GiB;
only synthetic fixtures, no forbidden models/aliases or changed production policy.
Preserve attempts and native script/results. Exact current production is master
b720674. This slice covers Float64 only; other precisions remain explicit gaps.
Regions retain different objects; never sum their independent times. No speedup
comparison or attribution of native-medium costs to Markowitz. Record GC without
subtracting it as a measured arithmetic time. Base.summarysize describes reachable
Julia objects, not hidden backing capacity or complete native BLAS memory.
Each sample starts with a fresh factor: its first new inactive slot is included
in the16 measured calls. Warm compilation is not steady-state slot allocation.

## Review focus

- Mutable backend slots/workspace cannot alias the published immutable HH base.
- A saved checkpoint continues solving its old matrix after slot cycling/failure.
- Dense-core/sparse-elimination transitions and dimensional shrink need distinct
  retention rows; report old checkpoint and both private slots without double count.
- Method compilation, backend solves and serialization stay outside timed regions.
- Exact matrix hashes match native fixtures, but backend arithmetic may differ.

## Task 1: backend-specific diagnostic and audit

Create reproduce/hh_component_markowitz.jl under diagnostics/simplex-core-architecture.
Interface main(output): same72 timing-record schema plus fresh/cycled graph rows
and backend-specific lifecycle retention. No new production API.

- [x] Adapt a separate copy of the accepted driver to Val(:markowitz). Validate
  backend-only output with _backend_forward_solve! and _backend_transpose_solve!,
  not the native backend backslash interface. Keep native fixture/hash recipe.
- [x] Warm four fixtures (sparse/dense64/256), measure six rotating rounds x16calls
  for backend/extraction/whole refactor. Require complete72records and compile0.
- [x] Check original/saved FTRAN/BTRAN residuals, exact saved base fingerprints,
  changed pattern,256->64->256 and singular failure outside timing. Additionally
  traverse sparse256->dense256->sparse64->sparse64->empty->empty->sparse64 so both
  slots and dictionary/core/pool retention are visible. Record graph(f,saved_old)
  separately from a fresh shared-base checkpoint; do not equate shrink with freed
  process memory. Assert all four solve scratch vectors are independently owned.
- [x] Guard600s, verify exit/pins/source/matrix hashes, all records/resources and
  preserve partial failures. No long solve is needed for these component gates.
- [x] Independent numerical/work/memory review; record findings/limits and choose
  the next concrete hypothesis. Commit portable results and update STATUS/roadmap.

Ruling: keep the native diagnostic snapshot unchanged; small duplicate driver
code is preferable here to changing accepted measurement machinery mid-study.
This is measurement/validation code only. No production RED or before/after
optimization claim applies; all asserted contracts must pass before acceptance.

Task 1 complete: markowitz-components-1 exit0,72 compile0 records,all17 audit
checks and independent pins pass. Independent review no blocker. Report
S4-COMPONENTS.md documents active-slot-only pool count (optional naming minor),
first inactive-slot allocation and overlapping graph sizes. No production cost
or memory added. Next hypothesis is Markowitz triplet capacity reservation,
requiring a separate implementation subplan and allocation regression gate.
