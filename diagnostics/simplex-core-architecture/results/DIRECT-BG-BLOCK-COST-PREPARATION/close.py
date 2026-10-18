"""One-shot diagnostic closure after independent preparation review."""
from control import *
checks={}
def ok(v,k):
 checks[k]=bool(v);require(v,k)
preparation();ok(True,'accepted_exact_preparation_review')
validate_environment();validate_sources();predecessor('cost1-300');ok(True,'sources_runtime_environment_GREEN')
ok(all(rd(D/n)['all_passed'] is True for n in ['source-check.json','offline-tests.json','prefix-tests.json','negative-supplement.json']),'all_author_checks')
ok(not (D/'runs').exists(),'no_Julia_phase_seal_reservation_output')
h=full_host();save(D/'closure-host.json',h)
ok(not h['matches'] and len(h['groups'])==238,'fresh_all238groups_ANDsessions_noJulia')
ok(h['head']==ENTRY and h['master']==MASTER,'entry_refs')
ok(git('branch','--show-current')=='codex/simplex-core-architecture','branch')
ok(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no_tracked_or_staged_changes')
files=sorted(p for p in D.iterdir() if p.is_file());names=[str(p.relative_to(R)) for p in files]
ok(not any(p.is_symlink() for p in files),'no_evidence_symlinks')
ok(names==rd(D/'closure-names.json')['names'],'explicit_exact_names')
save(D/'closure.json',dict(all_passed=True,checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='OFFLINE preparation only; no run or performance admission'))
print('Closure PASS',len(checks),'checks;',len(files),'bindings')
