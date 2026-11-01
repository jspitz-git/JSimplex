# Coupled dual engine experiment

- Branch: `codex/dual-step-experiment`.
- Production starting point: `9940bdabe149e922afa60b5364227a7e7393bc75`.
- Current deliverable: [approved design](../../docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md) and [implementation plan](../../docs/superpowers/plans/2026-10-31-experimental-dual-engine.md).
- Status: Task1/2 qualified; Task3 Harris/BFRT proposals and planned writes qualified555/555 including371 unchanged Task1/2 regressions. [Task3 report](task3/REPORT.md), [work/ownership ledger](task3/WORK-MEMORY.md). No commit/controller or speedup claim yet; Tasks4–6 remain open.

The experiment may change arithmetic order, pricing trajectories, monitoring and recovery organization. It must preserve correctness on the original model at the requested tolerances. First proposed scope is Float64 with the existing production PFI factor interface and a fixed-Devex reference comparison; Float32 and other backend support follow later qualification. The user approved the design scope; concrete policy and task details are recorded in the implementation plan.

The previous native-quality-scans checkout, its uncommitted Task4 diagnostics, frozen source candidates and numerical records are preserved there. No old scripts or numerical allowances are reused. The latest SS timing is evidence about index/admission/fallback costs: all16 instrumented cases had zero local elimination pivots. It does not establish the speed of an activated local SS kernel or justify a production change.

This directory will hold source/ownership records and future admitted experimental results. Use ordinary Test testsets, explicit activation checks and total time to verified answer, including setup, repairs, fallback and final certification. Task2 reports component correctness and explicit work/storage budgets; it makes no timing/allocation improvement claim. Do not enable CI, change environments, publish production changes or start numerical runs from this README.
