"""New GREEN admission gate tests; temporary records/mocks only, no process launch."""
from pathlib import Path
from unittest.mock import patch
import copy,json,tempfile
import control as c,evidence as e,prior_evidence as pe,guard,audit
D=c.D;R=c.R;checks={}
def reject(name,fn):
 try:fn()
 except (ValueError,OSError,KeyError):checks[name]=True
 else:checks[name]=False
cfg=c.phase_config('green');checks['green_config']=sum(g['counts'][0] for g in cfg['groups'])==19557
for phase in ('red','retry','green2',''):reject('phase_forbidden_'+repr(phase),lambda phase=phase:c.phase_config(phase))
package=c.rd(D/'config.json');realrd=c.rd
mutations=[('time',lambda x:x['phases']['green'].update(seconds=91)),('exit',lambda x:x['phases']['green'].update(expected_exit=1)),('project',lambda x:x['phases']['green'].update(project='/old')),('output',lambda x:x['phases']['green'].update(output='/old')),('old_count',lambda x:x['phases']['green']['groups'][0]['counts'].__setitem__(0,100)),('missing_group',lambda x:x['phases']['green']['groups'].pop()),('thread',lambda x:x['phases']['green']['command'].__setitem__(3,'--threads=2')),('old_driver',lambda x:x['phases']['green']['command'].__setitem__(7,str(D.parent/'DIRECT-LU-ADMISSION/driver.jl'))),('red_command',lambda x:x['phases']['green']['command'].__setitem__(8,'red')),('extra_phase',lambda x:x['phases'].update(red={}))]
for name,mutate in mutations:
 v=copy.deepcopy(package);mutate(v)
 with patch.object(c,'rd',side_effect=lambda p,v=v:v if p==D/'config.json' else realrd(p)):reject('reject_'+name,lambda:c.phase_config('green'))
paths=e.validate_predecessor();checks['real_immutable_RED_and_repair']=len(paths)==20
redpaths=pe.phase_paths('red',pe.phase_config('red'));realsha=pe.sha;isfile=Path.is_file
for p in redpaths:
 with patch.object(pe,'sha',side_effect=lambda n,p=p:'changed' if Path(n)==p else realsha(n)):reject('red_changed_'+p.name,e.validate_predecessor)
 with patch.object(Path,'is_file',lambda self,p=p:False if self==p else isfile(self)):reject('red_missing_'+p.name,e.validate_predecessor)
repair=D.parent/'DIRECT-LU-TEST-REPAIR';erealrd=e.rd
for name,mutate in [('unaccepted',lambda v:v.update(accepted=False)),('findings',lambda v:v.update(findings=['unresolved'])),('membership',lambda v:v['sha256'].pop(next(iter(v['sha256']))))]:
 v=copy.deepcopy(erealrd(repair/'review.json'));mutate(v)
 # Isolate repair gating; full real RED validation was checked above.
 with patch.object(pe,'validate_predecessor',return_value=redpaths+[pe.D/'red-audit.json']),patch.object(e,'rd',side_effect=lambda p,v=v:v if p==repair/'review.json' else erealrd(p)):reject('repair_'+name,e.validate_predecessor)
rows=[dict(name=g['name'],**dict(zip(('pass','fail','error','broken'),g['counts'])),expected=g['counts'],counts_match=True) for g in cfg['groups']]
raw=dict(phase='green',completed=True,all_expected=True,fatal='',loaded_path=str(Path(cfg['project'])/'src/JSimplex.jl'),groups=rows)
checks['complete_new_raw']=c.raw_ok(raw,'green',cfg)
for name,mutate in [('old_count',lambda v:v['groups'][0].update(pass_=100,counts_match=False)),('error',lambda v:v['groups'][0].update(error=1)),('incomplete',lambda v:v['groups'].pop()),('fatal',lambda v:v.update(fatal='error')),('old_source',lambda v:v.update(loaded_path='old')),('wrong_phase',lambda v:v.update(phase='red'))]:
 v=copy.deepcopy(raw);mutate(v);checks['raw_reject_'+name]=not c.raw_ok(v,'green',cfg)
with tempfile.TemporaryDirectory() as tmp:
 td=Path(tmp)
 with patch.object(audit,'D',td):
  result=audit.audit('green');checks['missing_outputs_false_audit']=result['all_passed'] is False and result['checks']==dict(complete_records=False)
 p=td/'exclusive';c.save(p,dict(first=True));reject('exclusive_cannot_overwrite',lambda:c.save(p,dict(first=False)));checks['exclusive_bytes_preserved']=c.rd(p)==dict(first=True)
s=c.rd(D/'staging.json');w=Path(s['root']);old=Path(s['original_root'])
checks['overlay_exact_membership']=set(s['original_sha256'])=={str(p.relative_to(w)) for p in w.rglob('*') if p.is_file()}
checks['overlay_only_reviewed_test_changed']=all(c.sha(w/n)==(s['correctness_sha256'] if n=='correctness.jl' else h) and c.sha(old/n)==h for n,h in s['original_sha256'].items())
checks['driver_exact_reviewed_bytes']=c.sha(D/'driver.jl')==s['driver_sha256']==c.sha(repair/'driver.jl')
checks['six_exact_focused_slices']=len(s['focused'])==6 and all((D/'focused'/v['output']).read_bytes()==(R/v['source']).read_bytes()[v['start_byte']:v['end_byte']] and c.sha(R/v['source'])==v['source_sha256'] for v in s['focused'])
checks['guard_supervisor_unchanged']=all(c.sha(D/n)==h for n,h in c.rd(D/'source-lineage.json')['unchanged'].items())
checks['seal_predecessor_before_output']=(D/'seal.py').read_text().index('extra=validate_predecessor()')<(D/'seal.py').read_text().index("phase+'-seal-host.json'")
checks['launch_predecessor_before_reservation']=(D/'launch.py').read_text().index('phase_config(phase);validate_predecessor()')<(D/'launch.py').read_text().index("phase+'-reservation.json'")
checks['no_stage_records_created']=not any((D/n).exists() for n in ('green-seal-host.json','green-sealed-pins.json','green-admission.json','green-reservation.json','green-run','red-run'))
baseline=c.rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['baseline514']=len(baseline)==514 and all(c.sha(R/n)==h for n,h in baseline.items())
result=dict(all_passed=all(checks.values()),checks=checks,scope='New Python helper gates/read-only predecessor validation; no Julia or old script execution')
c.save(D/'offline-tests.json',result);print(json.dumps(dict(checks=len(checks),passed=sum(checks.values()))));c.req(result['all_passed'],'Offline gates failed')
