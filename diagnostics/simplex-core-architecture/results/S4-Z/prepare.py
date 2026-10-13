"""One-use OFFLINE entry reconciliation and immutable admission inventory."""
from common import *
import datetime
checks={}
def test(n,x):require(x,n);checks[n]=True
mapping=read(D/'continuation-map.json')['mapping'];ymap=read(Y/'fix.json')['initial_source_mapping']
for name in ('source.json','fix.json','review.json','closure.json','publication.json','historical-retention.json'):
 data=read(Y/name)
 for p,h in data['sha256'].items():
  if name=='source.json' and p in ymap:q=Y/ymap[p]
  elif p in mapping:q=R/mapping[p]['saved_path']
  else:q=R/p
  test('Y:'+name+':'+p,sha(q)==h)
for p,h in read(Y/'entry.json')['user_sha256'].items():test('user:'+p,sha(p)==h)
for b in read(Y/'entry.json')['previous_continuation_mapping'].values():test('G-preserved:'+b['saved_path'],sha(R/b['saved_path'])==b['sha256'])
pub=read(Y/'publication.json');commit=read(D/'host.json')['head']
actual=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],text=True).splitlines()
test('Y_exact26_committed_names',actual==pub['expected_staged_names'] and len(actual)==26)
for p in actual:
 q=R/mapping[p]['saved_path'] if p in mapping else R/p
 test('Y_actual_blob:'+p,subprocess.check_output(['git','show',commit+':'+p])==q.read_bytes())
test('production_test_CI_equal_master',not subprocess.check_output(['git','diff','master','--','src','test','.github']))
test('noJulia_full28groups_sessions',not absent()['matches'])
test('no_allowance_reservation_launch_output',not OUT.exists() and not any((D/n).exists() for n in ('allowance.json','attempt-reserved.json','launch-pins.json','numerical-review.md','launcher.log','invocation.json','audit.json')))
test('driver_canonical',sha(Y/'driver-reviewed.jl')=='476c5ea1556b4f8b8c35291f07527cf55579e9c920fe4c9537593dab87f46f6a')
test('guard_byteidentical',sha(D/'guard.py')==sha(D.parent/'S2-D/guard.py'))
test('synthetic47PASS',read(D/'synthetic.json')['all_passed'] is True and len(read(D/'synthetic.json')['checks'])==47)
for p,h in read(D/'synthetic.json')['sha256'].items():test('synthetic-binding:'+p,sha(p)==h)
dump(D/'command.json',{'command':command(),'guard_command':guard_command(),'refs_at_preparation':refs(),'stage':'S4-Z-qualification-1','permission':'ABSENT; future fresh exact refs required','source_schedule':{'cases':2,'constructors':2,'copies':2,'refactors':6,'solves':20,'snapshots':8,'predicates':66},'limits':{'seconds':120,'VM_GiB':8,'heap_hint_GiB':2,'RAM_floor_GiB':6,'swap_max_GiB':1,'Julia_threads':1,'BLAS_threads':1}})
dump(D/'entry.json',{'checks':checks,'all_passed':True,'previous_Y_mapping':mapping,'Y_initial_mapping':ymap,'actual_Y_commit':commit,'source':'Fresh readtime reconciliation; no old scripts rerun.'})
# Fresh hashes, not reused old recorded hashes. Runtime path set is inherited from
# admitted ordinary loader; no claim that it captures all runtime-loaded libraries.
old=read(D.parent/'S2-D/admission-pins-reviewed.json')['inventory']
paths={Path(p) for p in old if not p.startswith(str(R)+'/')}
for tree in ('src','test','.github'):
 paths.update(p for p in (R/tree).rglob('*') if p.is_file())
paths.update(p for p in Y.iterdir() if p.is_file())
paths.update(p for p in D.iterdir() if p.is_file())
paths.update(R/p for p in ('Project.toml','Manifest.toml','LocalPreferences.toml','AGENTS.md','diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-PREPARATION.md','diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-PREPARATION-REVIEW.md','diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-ADMISSION.md','docs/superpowers/plans/2026-10-13-markowitz-retention-admission.md','docs/superpowers/plans/2026-10-13-markowitz-retention-qualification.md'))
paths.update(Path(p) for p in (sys.executable,'/bin/bash','/usr/bin/sed'))
required={str(p):sha(p) for p in sorted(paths)}
dump(D/'required-paths.json',required)
paths.add(D/'required-paths.json')
inv={str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
dump(D/'admission-pins.json',{'files':list(inv),'trees':[],'inputs':[],'inventory':inv,'scope':'OFFLINE readtime admission inventory, not launch pins. Future seal adds final independent review/closure/publication.'})
print(json.dumps({'entry_checks':len(checks),'required':len(required),'admission_pins':len(inv),'no_numerics':True}))
