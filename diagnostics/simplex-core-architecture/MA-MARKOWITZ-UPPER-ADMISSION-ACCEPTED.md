# MA-E accepted offline admission — final decision

Accepted by independent review-final.md/json for ONE bounded MA-F attempt.
No Julia/query/parser/import/compile/Pkg/launcher/seal/guard or numerical execution
in MA-E. Production/test/Project/env/master unchanged. Runtime correctness and
performance benefit remain unqualified.

Canonical controls: results/MA-E/control_reviewed.py, guard-reviewed.py,
launcher-reviewed.py, seal-reviewed.py, admission-reviewed.md,
admission-pins-reviewed.json and required-paths-reviewed.json. The original
admission report,1740pins, rejected review and scripts are historical drafts;
never execute their launcher/seal/guard. Final1761pins independently fully verified.

Five independent findings E1–E5 resolved: session-wide pidfd termination with
bounded incomplete-cleanup refusal; frozen master/primarybranch protection;
750s clock includes entry validation;432row publications distinguished from456terms;
precise read-only preflight versus consumed reservation boundary. Original versions
and five-failure RED preserved; separate7/7GREEN +46/46 +24/24offline suites.
Initial45/46 synthetic deadline-expectation failure is preserved separately.
Canonical historical phrase 'four issues' is superseded by explicit five here and
in final review; no additional scope or unresolved finding.

Prospective qualification381assertions,48fixture/prefix cases; cost48cases across
20serialprocesses. Caps RED30s, qualification120s, eachcost60s, costglobal600s,
whole750s. All previous resource guards apply. No retry, tuning, hidden warmup,
production promotion or assertion weakening. Human short-run permission persists.

No unnecessary NEW production work/memory found. Candidate eligibility/scalar
scratch costs remain explicitly included in future full-forward timing. Native
live/free memory, full backend work, universal speedup and integration unproven.
Next: docs/superpowers/plans/2026-10-13-ma-markowitz-upper-qualification-reviewed.md.
