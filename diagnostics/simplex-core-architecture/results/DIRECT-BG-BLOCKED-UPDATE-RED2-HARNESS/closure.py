"""One-shot offline closure; does not seal, reserve or execute a numerical attempt."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
checks={}
def ck(n,v):c.require(v,n);checks[n]=True
p=D/'preparation-pins.json';v=c.rd(D/'review.json')
c.preparation();ck('complete_preparation_and_review',True)
ck('four_runtime_flags_false',all(v.get(k) is False for k in ['launch_admitted','runtime_acceptance','numerical_acceptance','performance_acceptance']))
ck('source_checks',c.rd(D/'source-check.json')['all_passed'] is True and c.bindings(c.rd(D/'source-check.json')))
for name in ['routing-tests.json','auditor-tests.json']:ck(name,c.rd(D/name)['all_passed'] is True)
c.validate_sources();c.validate_environment();ck('actual_sources_runtime_environment',True)
ck('no_run_outer_reservation',not any((D/n).exists() for n in ['runs','outers','sealed.json','reservation.json','admission.json']))
ck('old_failed_RED_preserved',c.rd(c.OLD/'runs/red300/audit.json')['all_passed'] is False and not (c.OLD/'runs/red300/result-review.json').exists())
ck('tracked_index_clean',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
h=c.full_host();h['memory']=c.guard.memory();c.save(D/'host-closure.json',h)
ck('fresh_host_safe',c.host_safe(h) and not c.guard.pressure(h['memory']))
ck('entry_refs_boot_groups',all(h[k]==c.rd(D/'host-entry.json')[k] for k in ['head','master','boot_id','groups']) and len(h['groups'])==271)
ledger=c.R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
ck('continuation_preserved',ledger.read_bytes()==(D/'progress.md.after-red2').read_bytes())
names=c.rd(D/'publication-names.json')['paths'];actual={str(p.relative_to(c.R)) for p in D.rglob('*') if p.is_file()}
ck('exact_package',actual==set(names)-{str((D/n).relative_to(c.R)) for n in ['closure.json','publication.json']} and len(names)==len(set(names)))
c.save(D/'closure.json',dict(all_passed=True,launch_admitted=False,checks=checks,sha256={n:c.sha(c.R/n) for n in sorted(actual)}))
print('Offline RED2 closure PASS',len(checks),'checks',len(actual),'bindings')
