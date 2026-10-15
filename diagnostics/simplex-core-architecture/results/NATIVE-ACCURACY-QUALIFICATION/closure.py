"""Separate one-time result closure; checks saved evidence without numerical rerun."""
from final_helpers import *
import ast
review=rd(Q/'result-review.json');cont=rd(Q/'continuation.json');maps=cont['mappings']
def mapped_record(rec,field):
 z=rd(rec)[field]
 for n,v in z.items():
  digest=v['sha256'] if isinstance(v,dict) else v
  if isinstance(v,dict) and 'resolved' in v and str(path(n).resolve())!=v['resolved']:return False
  if sha(path(n))==digest:continue
  mm=[m for m in maps if m['record']==str(rec.relative_to(R)) and m['field']==field and m['key']==n and m['sha256']==digest]
  if len(mm)!=1 or sha(R/mm[0]['preserved_path'])!=digest:return False
 return True
h=host();save(Q/'closure-host.json',h);verify_host(h)
audit=rd(Q/'accuracy-audit.json');post=rd(Q/'postcheck.json');summary=rd(Q/'summary.json');inv=rd(Q/'accuracy-invocation.json');proc=rd(Q/'accuracy-run/process.json')
required=set(rd(Q/'result-review-required.json')['paths'])|{str(Q/'result-review-required.json'),str(Q/'continuation-text.md')}
checks=dict(result_accepted=review['accepted'] is True and review['findings']==[],result_bindings=bindings(review),result_scope=required<=set(review['sha256']),result_independent_check=rd(Q/'result-check.json')['accepted'] is True and rd(Q/'result-check.json')['check_count']==47 and not rd(Q/'result-check.json')['error'],admission_accepted=rd(Q/'accuracy-admission.json')['accepted'] is True,admission50=rd(Q/'admission-check.json')['all_passed'] is True and len(rd(Q/'admission-check.json')['checks'])==50,integrity13=audit['all_passed'] is True and len(audit['checks'])==13,post9=post['all_passed'] is True and len(post['checks'])==9 and bindings(post),accuracy_summary=summary['accuracy']=={'C':False,'P':True,'R':True},summary_bound=bindings(summary),one_attempt=rd(Q/'accuracy-reservation.json')['one_attempt'] is True,inclusive45=inv['elapsed_seconds']<45,process_exit=proc['returncode']==0 and proc['reason']=='exit0',full208groups_sessions=len(h['groups'])==208 and h['groups']==rd(Q/'accuracy-posthost.json')['groups'] and not h['matches'],refs_boot=h['head']==HEAD and h['master']==MASTER and h['boot_id']==proc['runner']['boot_id'],baseline514=len(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514 and bindings(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')),continuation_bound=bindings(cont),fourteen_maps=len(maps)==14 and all((rd(R/m['record'])[m['field']][m['key']]['sha256'] if m['field']=='inventory' else rd(R/m['record'])[m['field']][m['key']])==m['sha256']==sha(R/m['preserved_path']) for m in maps),previous_closure=mapped_record(D/'closure.json','sha256'),previous_publication=mapped_record(D/'publication.json','sha256'),sealed_pins=mapped_record(Q/'accuracy-sealed-pins.json','inventory'),launch_pins=mapped_record(Q/'accuracy-launch-pins.json','inventory'),admission_bindings=mapped_record(Q/'accuracy-admission.json','sha256'),raw_pins=mapped_record(Q/'accuracy-run/pins.json','inventory'),portable_pins=mapped_record(Q/'portable/pins.json','inventory'),old_cost1_false=rd(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,no_cost2=not any((Q.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),tracked_scope=not git('diff','--name-only','--','src','test','.github','Project.toml'),index_empty=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
raws=sorted((Q/'accuracy-run').iterdir());copies=sorted((Q/'portable').iterdir());checks['portable141']=len(raws)==len(copies)==141 and all(a.name==b.name and sha(a)==sha(b) for a,b in zip(raws,copies))
checks['launch_membership']=sorted(rd(Q/'accuracy-launch-pins.json')['files'])==sorted(rd(Q/'accuracy-launch-pins.json')['inventory']) and len(rd(Q/'accuracy-launch-pins.json')['files'])==1191
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_syntax']=True
paths=sorted([p for p in Q.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]+[R/'diagnostics/simplex-core-architecture/NATIVE-ACCURACY-QUALIFICATION.md',STATUS,ROAD])
save(Q/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='Accepted fixed component result and bounded next-design decision only; no production propagation or old benchmark resumption'))
require(all(checks.values()),'Closure failed; preserve all outputs and stop');print(dict(all_passed=True,checks=len(checks),bindings=len(paths)))
