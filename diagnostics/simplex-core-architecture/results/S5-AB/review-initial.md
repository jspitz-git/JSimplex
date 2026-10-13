# S5-AB fresh independent numerical/work/memory review — initial

Verdict: REJECTED

Critical findings: none.

Important finding I1 — the S5-O execution identity selects the wrong permanent test.
`results/S5-AB/reconcile-2.py` names `adaptive_pricing_tests.jl` in its S5-O
integration specification, and `reconciliation-2.json` propagates that selection.
The actual S5-O 42/42 run executes the pending-observer append from
`test/adaptive_pricing_lifecycle_tests.jl`, whose target begins at line 540.
The S5-O integration report explicitly identifies the lifecycle file and the
actual-source helper/suffix extraction. Matching the unrelated general pricing
file against launch pins does not bind the executed observer target. Consequently
the AB claim that its six selected integrations bind their current actual tests is
not established by that selector, even though its Boolean checks pass.

The evidence is available without any numerical rerun: both current lifecycle
files and both S5-O actual-master launch entries have SHA256
`10e77c9bc35956c8078f38df1be42511eea76642753a1a98ef2ed225c19783aa`.
AB's complete entry map independently pins that same actual file. Preserve the
incorrect selector/output, add a bounded correction binding this actual executed
target and its provenance, and adjust the report/downstream acceptance so the
wrong binding is not silently treated as valid. This is a documentation/evidence
selector defect, not evidence of a solver or numerical regression.

Minor findings: none.

Unresolved findings: [I1]

## Independent verification already performed

I read the original inventory, parent S5 gate, AB plan/report, next design plan,
auditor sources (without executing them), and actual boundary code in solver,
transformations, phase-one, primal, precision, dual, driver and perturbation
sources. I inspected selected permanent assertion bodies covering original-model
certification, projection, legacy normalization, phase ownership/invalidation,
precision interruption and reconstruction/reliable-exchange fixtures.

A new read-only Python check independently rehashed all 1883 distinct paths in
AB's entry/reconciliation/source-contract/independent maps. I rebound all AA
admission1464, required1463, GREEN1468 and master1493 inventories using the recorded
physical historical mappings; both raw8 and invocation3 sets; audit33/post10/9;
stage36; closure95; and exact99 committed names with all98 listed committed blobs.
All511 current source/test pairs match. Local/remote refs remain architecture
e701e1ecd5536411fa89a41c15b11d603d44dba3 and master
d02416c108f06fcd41d58e0a1980b70a51fef9ef. Same-boot host inspection found no Julia or
members of any of the26 old process groups or sessions.

My first inline checker mistakenly applied the current path to AA entry-2's
historical start-test key. It stopped after completing the1883 rehash and the four
large inventories. A separate fresh continuation applied the documented
AA/original-test.jl mapping and completed the checks above. Both tool outputs
remain in the review transcript; no author artifact or frozen script was altered.
This reviewer-check mistake is not an author finding.

All82 stored historical rows were independently compared with their exact raw log
lines, normalized counts and two FAILED metadata records. All48 historical/current
source comparisons were recomputed from Git blobs; the only selected production
mismatch is the acknowledged S5-C perturbation change. I read the actual C driver
and nine FILE records, checked all nine historical whole-file identities/current
prefixes, and confirmed1463/1463. The reliable AA target AND its actual fixture
helper match current source; the later AC whole-file change is not confused with
whole-file AA identity. Six selected integration manifests/audits were rebound,
with the I1 limitation above. This is complete verification of the named pin/row/
comparison sets, not exhaustive semantic review of all511 files or a solver run.

## Numerical scope and work/memory assessment

Apart from I1, the seven-row disposition is supported at the stated contract
scope. Passing selected groups inside failed historical CI runs do not prove a
current full solver, precision/backend cross-product, or unresolved private CI
cause. Working certificates remain separate from original-model certification.
No equivalent new seven-boundary census is warranted. The parent measured
initialization-reuse/end-to-end gate must remain OPEN.

No unnecessary NEW production computation, allocations or retained memory were
introduced: this is source/evidence documentation, and production/test/CI/Project
tracked deltas are empty. Existing boundary scans/copies, factor ownership and
reconstruction remain required unless a future separately qualified proposal
proves otherwise. S5-C saves one eligible O(m+n) cost copy; it is not an
initialization reduction. No new per-iteration/per-candidate scans, basis solves,
update-chain retention or precision change occur here. No benchmark is warranted.

The proposed bounded source/design decision is justified by S5-A's unresolved
native/no-observer/infinite-budget hypothesis, provided it remains an eligibility
and numerical-failure/fallback decision. It must preserve the rejection of
unconditional omission, consumed work, logging, stored precision, internal versus
context deadlines and ownership. It grants no implementation or numerical
permission. All broader S3/S4/S5/S6, native HH-disabled, fullsuite/x64/cause and
resource/retention limitations remain open. Final acceptance awaits I1 correction.
