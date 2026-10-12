# S4-F independent numerical/work/memory review

Fresh-context gpt-6-astra/high read-only review accepts the native component
result. No Critical finding. One Important next-plan gap and one Minor evidence
label clarification were identified. No Julia, writes or old/exclusive audit rerun
by the reviewer.

Reviewer inspected driver/auditor/protocol/raw/process/supplement and current
native wrapper, pattern helper and HH lifecycle. Sample hashes for production
factorization files, driver, wrapper, loaded UMFPACK library and environment
matched; frozen driver matched; four raw/portable pairs matched. Reviewer did NOT
repeat author full649rehash. Separate author supplement checked all649pins,
five raw/portable pairs,12exact input representations,controls,13libraryfiles,
source/driver/user hashes and audit gates (10checks). Allpassed.

Six-pair12setup/12refactor/20solve/10metadata/10graph accounting accepted. Existing
numeric object and wrapper guard justify no extra factorization at metadata
access. Held owners support identity checks; separate input arrays and sentinel
mutation plus planned solves support direct native input lifetime. Two expected
singular factors are discarded; no rollback proof. Exact factor residuals remain
nonzero. Reviewer independently compared exact residual norms against saved
bounds on10successful records: every ratio below0.007813, including nonzero exact
residuals where the floating residual was zero. The auditor's fixed-bound gate
itself compares saved floating residual/bound; its exact-representation check is
separate. Observed five-pair equality is restricted to these fixtures.

No unnecessary production work, allocations or retained memory introduced;
production/test/CI unchanged. Diagnostic exact arithmetic/copies/extractions/
graph walks are bounded and justified. Future pattern check addsO(n+nnz) per
refactor without a solve or new persistent cache. Production performance remains
unmeasured. Single-call metrics, held owners and Julia graph sizes do not establish
speedup or native retained-memory bounds.

Important fix: the original S4-G plan had false->false prepared_valid across
successful refactor, because the previous replace_column! already invalidates it.
One offline RED4missing -> GREEN4/4 correction moves the existing live forward
solve to B2 before refactor, asserts true before/false immediately after, binds
its oracle to B2, and uses the already-planned B3update-direction FTRAN to check
forward correctness. Five matrices now have explicit oracle inventory. Total
24HHsolves unchanged. Before plan/source/hash and fix evidence preserved; no
numerical rerun or relaxed safeguard. No second review pass is substituted for
this explicit checked correction.

Final minor (deferred): independent_check.py's launch_group_absent checks only
/proc/3788 (leader PID), not all PGID members. Preserve accepted script/result.
Fresh separate host-group-closure.json explicitly scanned every process PGID for
3788 and3793 on the recorded boot; both groups and all numerical processes absent.
This later observation does not turn the earlier leader check into a group scan.
Future preflight must scan PGIDs as well as boot/start/command identities.

Declined broader claims stay open: HH publication/copies/prepared-state integration,
actual borrowed workspace assembly, dimension/empty/nonfinite and changed-control
eligibility, asymptotic native retention, representative performance, fullsuite/x64
and historical CI causes. S4-G remains a separate bounded qualification only.
CI disabled; S2-A/S6-J/wholeAF rejection and original-model safeguards unchanged.
