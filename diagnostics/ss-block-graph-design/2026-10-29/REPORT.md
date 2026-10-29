# Block-aware factorization and graph-local SS: source/design handoff

New design, not an implementation or launch admission. The previous realistic-sequence investigation remains frozen and was not rerun. Diagnostic baseline cb68b71975ecb8aafffe501e5c6076026348bb3d; master c0fa748ffa61ccb7c1caaf248c40324f60bc737b unchanged.

The proposed design is `docs/superpowers/specs/2026-10-29-ss-block-graph-design.md`. The user chose block-aware factorization plus graph-local SS, then asked about KLU. KLU is included as a separately qualified backend option, retaining its native L*U+F representation rather than assuming compatibility with the existing multiplicative direct-LU exporter. No new package is installed.

The SS proposal retains current packed U and numerical elimination/pivot rules, uses maintained current-U incidence to discover affected columns and fill, includes cross-block/trailing coupling writes, and falls back to the original prepared remainder at explicit phase boundaries. O(rotation length), list shifts, graph maintenance, capacities and fallback sunk work remain charged. Old BTF labels cannot authorize omission after an exchange.

Independent builder review identified one important design gap: imported explicit zeros conflict with a literal incidence rotation. The initial review and exact reviewed design are preserved. The amendment refuses only the local optimization at the existing initial scan and retains original behavior without normalizing or repairing zeros. The final review binds the corrected design. No implementation, performance or numerical acceptance follows from source review.

The native q API was read from installed Julia 1.13 sources. UMFPACK may change the supplied symbolic order, so actual exported block order must be checked; merely supplying q is not proof. The KLU source and both guides are newly downloaded source evidence pinned to exact upstream commits, not evidence of an installed runtime or retroactive pins of earlier runs.

Work/memory assessment: no new production computation or allocation. The proposed candidate requires O(n+e) private indexing and local discovery/maintenance, and must be rejected if inclusive costs erase savings. A separate implementation plan and independently reviewed numerical admission follow design approval. No Julia/query/import/compile/native call, production/permanent-test/env/CI/master change or new numerical result in this task.

Fresh host snapshot: 711 historic groups and sessions absent, no Julia; refs and preexisting untracked environment files recorded in host.json. Only new design/evidence files are published. No existing continuation file or frozen evidence is modified.

Review path mapping: temporary DESIGN.md denotes the byte-identical final spec; DESIGN.before-zero-fix.md denotes DESIGN.before-review.md. BUILDER-REVIEW*.md denotes REVIEW-INITIAL.md/REVIEW-FINAL.md. These are original read-time bindings, not retroactive edits. Upstream snapshots retain exact bytes, including any verbatim whitespace.
