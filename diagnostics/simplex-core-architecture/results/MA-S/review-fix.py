"""One offline correction; original sources/pins/review retained unchanged."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,text):
 with (E/name).open('x') as f:f.write(text)
old=(E/'audit.py').read_text()
new=old.replace("require(w['pair']==pair and w['order']==order", "require(type(w['pair'])==int and type(w['order'])==int and w['pair']==pair and w['order']==order")
new=new.replace("D/'pins.json'","D/'pins-reviewed.json'")
helper='''def stage_scalars(proc,inv,res,samples,post,context,sequence):
 checks={}
 try:
  integer=lambda x:type(x)==int and x>=0
  positive=lambda x:type(x)==int and x>0
  checks['exit_codes']=all(type(x)==int and x==0 for x in (proc['returncode'],inv['returncode']))
  checks['elapsed_schema']=all(finite(x) for x in (proc['started'],proc['ended'],proc['elapsed_including_launch'],inv['elapsed_seconds'],inv['cumulative_seconds'],post['time'])) and proc['ended']>=proc['started'] and proc['elapsed_including_launch']<=114 and proc['elapsed_including_launch']<=inv['elapsed_seconds']<=120 and inv['elapsed_seconds']<=inv['cumulative_seconds']<=360
  checks['limit_schema']=type(res['seconds'])==int and res['seconds']==120 and type(context['maximum_processes'])==int and context['maximum_processes']==3 and type(context['maximum_seconds_per_process'])==int and context['maximum_seconds_per_process']==120 and type(sequence['maximum_processes'])==int and sequence['maximum_processes']==3 and type(sequence['total_cap_seconds'])==int and sequence['total_cap_seconds']==360 and sequence['no_retry'] is True
  boot=context['boot_id'];require(isinstance(boot,str) and bool(boot),'context boot')
  checks['identity_schema']=True
  for who in ('runner','child'):
   v=proc[who]
   checks['identity_schema'] &= all(positive(v[k]) for k in ('pid','pgid','sid')) and integer(v['start_ticks']) and v['boot_id']==boot and isinstance(v['command'],str) and bool(v['command']) and v['pid']==v['pgid']==v['sid']
  groups=post['groups']
  checks['post_identity_schema']=isinstance(groups,list) and len(groups)>=158 and all(positive(v) for v in groups) and len(set(groups))==len(groups) and post['boot_id']==boot and post['matches']==[] and post['refs']==context['refs'] and all(proc[who][k] in groups for who in ('runner','child') for k in ('pgid','sid'))
  checks['memory_schema']=len(samples)>=2 and all(integer(s['available_kib']) and integer(s['swap_used_kib']) and s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples)
 except Exception as e:checks['stage_scalar_complete']=False;checks['stage_scalar_error']=repr(e)
 return checks

'''
new=new.replace('def stage(index):',helper+'def stage(index):')
new=new.replace("checks['memory']=len(samples)>=2 and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples)","checks['memory']=len(samples)>=2 and all(type(s['available_kib'])==int and type(s['swap_used_kib'])==int and s['available_kib']>=6*1024**2 and 0<=s['swap_used_kib']<=1024**2 for s in samples)")
new=new.replace("raw=tomllib.loads((out/'raw.toml').read_text());checks.update(validate_raw(raw,index))","checks.update(stage_scalars(proc,inv,res,samples,post,read(D/'launch-context.json'),read(D/'sequence-reservation.json')))\n  raw=tomllib.loads((out/'raw.toml').read_text());checks.update(validate_raw(raw,index))")
write('audit_reviewed.py',new)
launcher=(E/'launcher.py').read_text().replace('import audit','import audit_reviewed as audit').replace("D/'launcher.py'","D/'launcher-reviewed.py'").replace("D/'pins.json'","D/'pins-reviewed.json'").replace("D/'required-paths.json'","D/'required-paths-reviewed.json'").replace("D/'admission-review.json'","D/'admission-review-final.json'")
write('launcher-reviewed.py',launcher)
# Source-bound RED: the preserved predicates themselves admit malformed values.
red={'pair_bool':True==1,'pair_float':1.0==1,'order_bool':True==1,'order_float':1.0==1,'exit_bool':False==0,'available_infinity':float('inf')>=6*1024**2,'negative_swap':-1<=1024**2}
with (E/'review-fix-red.json').open('x') as f:json.dump(dict(scope='Source-derived Python predicate counterexamples, no old auditor main/stage execution.',malformed_accepted=red,all_reproduced=all(red.values()),sha256={str(E/n):sha(E/n) for n in ['audit.py','launcher.py','admission-review.json','review-fix.py']}),f,indent=2);f.write('\n')
print('Preserved originals; created canonical audited variants; RED7 reproduced')
