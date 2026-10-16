"""One-shot offline closure AFTER independent review. No Julia or phase controls."""
from pathlib import Path
import json,subprocess
import control as c
D=Path(__file__).resolve().parent;R=D.parents[3];checks={}
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
c.preparation();ok(True,'independent_preparation_review_and_complete_pins')
c.validate_sources();ok(True,'actual_source_runtime_stage_integrity')
c.validate_environment();ok(True,'environment_unchanged')
ok(c.bindings(c.rd(D/'entry.json')),'accepted_dependencies_and_continuation_unchanged')
ok(c.bindings(c.rd(D/'source-check.json')),'author_source_bindings')
for n in ('source-check.json','offline-tests.json','negative-supplement.json'):
 ok(c.rd(D/n)['all_passed'] is True,n)
ok(not (D/'runs').exists(),'no_Julia_seal_reservation_or_output')
ok(c.git('rev-parse','HEAD')=='8faca92005efbb65ad7212222b17844a248d208a','entry_head_unchanged')
ok(c.git('branch','--show-current')=='codex/simplex-core-architecture','diagnostic_branch')
ok(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'no_tracked_or_staged_changes')
h=c.full_host();c.save(D/'closure-host.json',h)
ok(not any(p['pgid'] in h['groups'] or p['sid'] in h['groups'] for p in h['matches']),'historical_groups_AND_sessions_absent')
ok(h['master']==c.MASTER,'master_unchanged')
# Foreign user Julia remains untouched; no numerical no-Julia-host assertion.
files=sorted(p for p in D.iterdir() if p.is_file())
ok(not any(p.is_symlink() for p in files),'no_new_evidence_symlinks')
expected=c.rd(D/'closure-names.json')['names']
ok([p.name for p in files]==expected,'explicit_exact_closure_membership')
c.save(D/'closure.json',dict(all_passed=True,checks=checks,sha256={str(p.relative_to(R)):c.sha(p) for p in files},scope='Offline preparation closure, not RED/GREEN or performance acceptance',foreign_processes=h['matches']))
print('Closure PASS',len(checks),'bindings',len(files))
