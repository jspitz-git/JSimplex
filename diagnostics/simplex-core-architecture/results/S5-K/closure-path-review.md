# S5-K closure path correction review

Verdict: ACCEPTED for one new offline closure-2 attempt. Critical: none. Important:
none. Minor: none. The accepted K oracle report/review remain unchanged. This is
not a closure PASS, permission for numerical execution, or publication evidence.
At this review, closure.json does not exist and closure-2 has not been run by this
reviewer. Publication must still require successful closure exit and all checks.

The preserved closure-1-failure.json records exit 1/ValueError from original(p)
calling relative_to(ROOT) on the external absolute Julia executable path, before
closure.json creation and without publication. The original closure.py hash matches
both the failure record and closure-path-fix.json. The failure is consistent with
the inspected original source; I did not recreate it by rerunning the old script.

The complete diff to closure-2.py changes its descriptive docstring and only the
original(p) mapping: construct Path(p), return an external absolute path unchanged,
otherwise retain the previous internal/relative mapping and optional before-review
lookup. Consequently external runtime/user files still pass through sha() and
must equal their recorded digest. They are not skipped, remapped to local files,
or accepted without a comparison. Internal absolute and relative repository files
retain the existing lookup behavior. The inventory consists of trusted recorded
paths; this correction is not a general path sanitization feature.

All 12 closure predicates, streaming SHA-256 implementation, previous-J reconciliation,
user-file checks, source/test/CI comparison, master check, process-group/boot checks,
review acceptance binding, preserved false-G evidence check, final all_passed, exclusive
output creation and nonzero exit on a failed predicate are unchanged. There is no
semantics weakening. RED1/GREEN3 in closure-path-fix.json is the author's bounded
path-mapping evidence; I read it and checked its source bindings, without rerunning
that probe or importing/executing either closure script.

The saved STATUS.md.before-K and roadmap.before-K hashes independently equal their
J closure entries. Current status/roadmap changes preserve the offline-only scope,
the original closure refusal, prospective cost-equality limitation and the requirement
for separate closure/publication evidence. Any wording about closure being recorded
is prospective until the new attempt actually passes; this review supplies no such
success assertion. No review-fix.json exists, so the unchanged optional before-review
branch currently falls back to the empty mapping. The external path fix is needed
independently of that optional mechanism.

No unnecessary new production work, allocation or retained memory was found: this
changes an offline evidence path helper only. It adds one bounded path containment
check per mapped inventory entry, preserves full streaming file hashing, and adds
no production or numerical calls. No benchmark is warranted. Runtime/library bytes
are read for identity only; they are never executed by this review.

Fresh SHA-256 bindings:

| Artifact | SHA-256 |
| --- | --- |
| closure.py (preserved failed original) | 7622be631a7294b060d5faa8188e11f1943eec7b9bee1bff8509130032a55147 |
| closure-2.py (reviewed replacement) | 7113bb0a9b5abbf828aa50d51c11e62a329eacb8195c3345caccec9377d9bc5e |
| closure-1-failure.json | bee5242abc7ec452e9b77103bafdb510d9716fb41102b1b0bfca7cb34157d8c7 |
| closure-path-fix.json | cad96f0954c87fec30979be73a08471a1541ed659faf8ff9eccdf3fb6ae767a5 |
| evidence.json | 45639751d59d80985dd28f97d4bd9ddd84a1d357c6e291ee4e67be3f521d1a4d |
| independent.json | 7e67e9a398acd269be7f2ad4af7104e1a2b28e074f2e0fdcad20902c2f2cb2e1 |
| review-acceptance.json | 07d0ab028dd71959702acce0a844ba1946751eb600bed835dde35b47fc3f7f28 |
| S5-DUAL-AUXILIARY-PENDING-OBSERVER-ORACLE-REVIEW.md | dcf616a073048278eaec4cee5e86e802ad6e8108e3da145628c351bf44627dee |
| STATUS.md.before-K | c7975cef221d352c393c956c6586945df5ea34a8d07c28c2fb6e1f6d7b8fa741 |
| 2026-10-11-simplex-core-architecture.md.before-K | e50fc1b86077552dbe7604e241e60912544e65b605bbf036eec56db3ee785323 |

Only this new supplemental review was written for the path-correction task.
No existing oracle report/review, frozen evidence, script, test, environment, cache
or source was modified. No Julia, numerical arithmetic, old audit or closure rerun.
