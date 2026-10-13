# Separate correction of rejected S5-U admission

Original admission-review.md is REJECTED for Important I1. All original source,
required1445/admission1446 manifests, failure cases and author evidence remain
unchanged. No actual test edit or Julia operation occurred.

Canonical NEW source is common_reviewed.py, launcher-reviewed.py, audit-reviewed.py.
review_fix.py was saved before its single execution. New required-reviewed-paths
and admission-reviewed-pins supersede the old manifests only for future admission.
The numerical driver/candidate/insertions/schema/guard are unchanged.

Stage acceptance now requires literal accepted=true, no unresolved findings,
exact stage/root, BOTH current Git HEAD identities, exact candidate SHA and required
hash membership including actual candidate test, accepted admission review/binding,
manifest, required paths and canonical source. For master, mandatory GREEN audit,
postcheck, review and pins bindings are additionally required; their literal PASS
checks, review acceptance and immutable postcheck artifact bindings are validated.
Freeze enforces this stage admission. Run AND offline audit independently enforce
stage plus launch admission. Launch binding has mandatory stage/command/no findings,
manifest/audit/launcher/stage/admission identities and required manifest membership.

reviewed-failure-tests.json has18 PASS checks: two positive synthetic stage-binding
metadata examples; nine negative empty/wrong stage/root/refs/unresolved/candidate/
missing GREEN review/missing GREEN post/changed-hash cases; three NEW auditor
missing/malformed/incomplete durable refusals; four source-enforcement checks.
Synthetic hash readers represent declared bindings only; they are not actual stage
acceptance, runtime validation or numerical attempts. Original empty-binding
acceptance is preserved as offline RED. No old test script or auditor was rerun.
The new full admission manifest must be independently reviewed before any actual
edit or Julia. Driver costs and all safeguards/scopes in original admission remain.
