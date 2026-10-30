"""Complete fail-closed GREEN2 auditor; definitions only on import."""
from pathlib import Path
import json,math,re,sys,tomllib
import common as C
import binding_checks as B
def integer(v):return type(v) is int and v>=0
def number(v):return type(v) in (int,float) and math.isfinite(v) and v>=0
def stats(q):
 C.require(type(q) is dict,'stats type')
 C.require(all(number(q[k]) for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds')),'stats time type/range')
 C.require(integer(q['bytes']) and integer(q['events']),'allocation type/range')
def summary(log,name):
 rows=log.splitlines();matches=[i for i,s in enumerate(rows) if '|' in s and s.split('|',1)[0].strip()==name]
 C.require(len(matches)==1,'missing/duplicate ordinary summary '+name)
 i=matches[0];header=next((rows[j] for j in range(i-1,-1,-1) if rows[j].startswith('Test Summary:')),None)
 C.require(header is not None,'missing Test header')
 keys=re.findall(r'Pass|Fail|Error|Broken|Total|Time',header.split('|',1)[1]);values=rows[i].split('|',1)[1].split()
 C.require(len(keys)==len(values) and len(keys)==len(set(keys)) and {'Pass','Total'}<=set(keys),'summary columns')
 return {k:int(v) for k,v in zip(keys,values) if k!='Time'}
def ordinary(log):
 C.require(type(log) is str and not any(s in log.lower() for s in ('world age','error during test','undefvarerror','syntax:','segmentation fault','error:','test failed at')),'load/test/runtime defect')
 result=summary(log,'TASK4_GREEN')
 C.require(result.get('Pass',0)>0 and result['Pass']==result['Total'] and all(result.get(k,0)==0 for k in ('Fail','Error','Broken')),'ordinary Test not wholly green')
 C.require(log.splitlines().count('TASK4_GREEN_COMPLETED')==1,'missing/duplicate completion')
 C.require(re.findall(r'^TASK4_INCLUDED (.+)$',log,re.M)==C.includes(),'exact twelve includes')
 post=summary(log,'TASK4_POST_FALLBACK')
 C.require(post.get('Pass')==post.get('Total')==46 and all(post.get(k,0)==0 for k in ('Fail','Error','Broken')),'endpoint46 ordinary assertions')
 return result
def endpoint(records):
 C.require(type(records) is list and len(records)==2 and all(type(q) is dict for q in records),'endpoint records')
 C.require({q['type'] for q in records}=={'Float32','Float64'},'two endpoint types')
 for q in records:
  for k in ('preparation','whole_fallback','component_preparation','component_revalidation','component_reset'):stats(q[k])
  C.require(all(q[k] is True for k in ('original_primal_certified','original_optimality_certified','invalid_witness_rejected','invalid_row_rejected','trajectory_changed')),'endpoint certificate/refusal booleans')
  for k in ('point','witness'):
   C.require(type(q[k]) is list and len(q[k])==2 and all(type(v) in (int,float) and math.isfinite(v) for v in q[k]) and q[k]==[1,0],'endpoint exact point/witness')
  expected=dict(iterations=1,factorizations=1,attempted_weight_rows=1,avoided_weight_rows=1,core_and_weight_ftran=1,core_and_weight_btran=3,final_ftran=2,final_btran=4)
  C.require(all(type(q[k]) is int and q[k]==v for k,v in expected.items()),'endpoint exact integer work')
  C.require(integer(q['retained_julia_bytes']),'retained Julia graph type')
 return True
def process(done,sup,proc):
 C.require(type(proc['returncode']) is int and proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==C.command(),'process exit/command/pins')
 C.require(sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0 and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')) and 'cleanup_error' not in sup,'supervisor refusal')
 C.require(done['supervisor_accepted'] is True and type(done['limit_seconds']) is int and done['limit_seconds']==C.TOTAL,'completion accepted/limit')
 C.require(number(done['elapsed_inclusive_seconds']) and done['elapsed_inclusive_seconds']>0 and number(done['total_inclusive_seconds']) and done['total_inclusive_seconds']==C.USED+done['elapsed_inclusive_seconds']<=C.TOTAL,'prior time reset/shared ceiling')
 C.require(number(sup['elapsed_seconds']) and sup['elapsed_seconds']<=done['elapsed_inclusive_seconds'],'supervisor inclusive time')
def resource(q):
 C.require(type(q) is dict and integer(q['available_kib']) and integer(q['swap_used_kib']) and q['available_kib']>=6*1024**2 and q['swap_used_kib']<=1024**2,'resource memory type/guard')
def evaluate():
 r=C.OUT;seal=C.read(r/'seal.json');pins=C.read(r/'pins.json');attempt=C.read(r/'attempt.json')
 B.interpreter(seal,pins,sys.executable)
 C.check_inventory(pins,C.required_paths(),C.expected_inputs())
 C.require(seal['phase']=='green2' and seal['command']==C.command() and seal['environment']==C.environment() and seal['expected_exit']==0 and seal['shared_total_seconds']==1800,'seal scope/command/env')
 used,facts=C.prior();C.require(seal['used_seconds']==used==C.USED and seal['previous']==facts,'prior raw time/bindings')
 ad=C.validate_admission(seal,pins,attempt['admission_path'],C.git('rev-parse','HEAD'))
 C.require(C.sha(attempt['admission_path'])==attempt['admission_sha256'] and C.sha(r/'seal.json')==attempt['seal_sha256'],'attempt/admission/seal changed')
 C.require(attempt['phase']=='green2' and attempt['remaining_seconds']==C.TOTAL-used and number(attempt['started_monotonic']),'attempt budget')
 proc=C.read(r/'guard/process.json');sup=C.read(r/'supervisor.json');done=C.read(r/'completion.json')
 process(done,sup,proc)
 C.require(C.sha(r/'pins.json')==seal['pins_sha256']==proc['pins_sha256'] and C.read(r/'guard/pins.json')==pins,'guard pins')
 C.require(C.read(r/'invocation.json')==dict(command=C.guard_command(seal,attempt['started_monotonic']),cwd=str(C.D),environment=seal['environment']),'exact invocation')
 for n in ('prelaunch-host.json','postflight.json'):
  h=C.read(r/n);C.require(h['conflicts']==[] and h['refs']['master']==h['refs']['origin/master']==C.MASTER,'host closure/master')
  B.head(seal,ad,h['refs']['HEAD']);resource(h['memory'])
 post=C.read(r/'postflight.json')
 expected_groups=set(C.read(C.D/'host.json')['host']['checked_groups']) if post['boot_id']==C.read(C.D/'host.json')['host']['boot_id'] else set()
 for role in ('runner','child'):
  a=proc[role];C.require(a['boot_id']==post['boot_id'] and a['pid']==a['pgid']==a['sid'] and integer(a['start_ticks']) and type(a['command']) is str and bool(a['command']),'guard/child identity')
  expected_groups.update((a['pgid'],a['sid']))
 C.require(set(post['checked_groups'])==expected_groups and post['still_active_current_launcher']==[attempt['runner']],'postflight full prior/guard/child closure and explicit live launcher')
 gate=C.read(r/'guard/gate.json');current=C.read(r/'guard/current.json');permit=C.read(r/'guard/permit.json')
 C.require(gate['identity']==proc['child'] and gate['parent']==proc['runner'] and gate['parent_death_signal']==9 and gate['command']==seal['command'],'entry parent-death/identity/command')
 C.require(gate['current_sha256']==C.sha(r/'guard/current.json') and gate['permit_sha256']==C.sha(r/'guard/permit.json') and permit==dict(current_sha256=C.sha(r/'guard/current.json'),command=seal['command']) and current['child']==proc['child'] and current['runner']==proc['runner'] and current['command']==seal['command'],'entry publication hashes')
 C.fixtures()
 fresh_host=C.host();C.require(fresh_host['refs']['HEAD']==ad['head'],'current HEAD')
 log=(r/'guard/run.log').read_text(errors='replace');result=ordinary(log)
 endpoint(tomllib.loads((r/'result.toml').read_text())['cases'])
 samples=[json.loads(s) for s in (r/'guard/resources.jsonl').read_text().splitlines()]
 C.require(bool(samples),'missing resource samples')
 for q in [*samples,proc['terminal_memory'],fresh_host['memory']]:resource(q)
 return result
def main():
 r=C.OUT;accepted=False;result=None;error=None
 try:result=evaluate();accepted=True
 except Exception as e:error=type(e).__name__+': '+str(e)
 bindings={str(p):C.sha(p) for p in sorted(r.rglob('*')) if p.is_file() and p.name!='audit.json'}
 try:
  ad=C.read(C.read(r/'attempt.json')['admission_path'])
  for p in (C.read(r/'attempt.json')['admission_path'],ad['review_report']):bindings[p]=C.sha(p)
 except (OSError,KeyError,ValueError):pass
 C.fresh(r/'audit.json',dict(accepted=accepted,phase='green2',error=error,test_summary=result,bindings=bindings,production_admission=False,scope='guarded GREEN2 only; independent full launcher/group result closure and review remain required'))
 return accepted
if __name__=='__main__':raise SystemExit(0 if main() else 1)
