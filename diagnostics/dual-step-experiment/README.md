# Coupled dual engine experiment

- Branch: `codex/dual-step-experiment`.
- Production starting point: `9940bdabe149e922afa60b5364227a7e7393bc75`.
- Current deliverable: [design proposal](../../docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md).
- Status: DESIGN ONLY; no experimental engine implemented, no Julia run, no speedup claim. The design needs human approval before an implementation plan.

The experiment may change arithmetic order, pricing trajectories, monitoring and recovery organization. It must preserve correctness on the original model at the requested tolerances. First proposed scope is Float64 with the existing production PFI factor interface and a fixed-Devex reference comparison; Float32 and other backend support follow later qualification. This scope is an author proposal, not an already accepted implementation contract.

The previous native-quality-scans checkout, its uncommitted Task4 diagnostics, frozen source candidates and numerical records are preserved there. No old scripts or numerical allowances are reused. The latest SS timing is evidence about index/admission/fallback costs: all16 instrumented cases had zero local elimination pivots. It does not establish the speed of an activated local SS kernel or justify a production change.

This directory will hold source/ownership records and future admitted experimental results. Use ordinary Test testsets, explicit activation checks and total time to verified answer, including setup, repairs, fallback and final certification. No benchmark is required for this documentation-only deliverable. Do not enable CI, change environments, publish production changes or start numerical runs from this README.
