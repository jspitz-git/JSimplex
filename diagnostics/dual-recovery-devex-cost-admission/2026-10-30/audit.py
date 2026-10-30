"""Full guarded cost audit; definitions only, no Julia."""
from pathlib import Path
import json,math,re,sys,tomllib
import common as C
import binding_checks as B
import cost_checks as K
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

def resource(q):
 C.require(type(q) is dict and integer(q['available_kib']) and integer(q['swap_used_kib']) and q['available_kib']>=6*1024**2 and q['swap_used_kib']<=1024**2,'resource memory type/guard')
def ordinary(log,phase):
 C.phase_ok(phase)
 C.require(type(log) is str and not any(x in log.lower() for x in ('world age','error during test','undefvarerror','syntax:','segmentation fault','error:','test failed at')),'load/test/runtime defect')
 q=summary(log,'TASK4_COST')
 C.require(q.get('Pass')==q.get('Total')==272 and all(q.get(k,0)==0 for k in ('Fail','Error','Broken')),'ordinary272 wholly-green tests')
 C.require(log.splitlines().count('TASK4_COST_COMPLETED '+C.side(phase))==1,'side completion')
 C.require(not any(s.startswith('TASK4_COST_COMPLETED ') and s!='TASK4_COST_COMPLETED '+C.side(phase) for s in log.splitlines()),'wrong side completion')
 return q
def process(done,sup,proc,phase,used):
 C.require(type(proc['returncode']) is int and proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==C.command(phase),'process exit/command/pins')
 C.require(sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0 and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')) and 'cleanup_error' not in sup,'supervisor refusal')
 C.require(done['supervisor_accepted'] is True and type(done['limit_seconds']) is int and done['limit_seconds']==1800,'completion scope')
 C.require(number(done['elapsed_inclusive_seconds']) and done['elapsed_inclusive_seconds']>0 and number(done['total_inclusive_seconds']) and done['total_inclusive_seconds']==used+done['elapsed_inclusive_seconds']<=1800,'prior clock reset/shared ceiling')
 C.require(number(sup['elapsed_seconds']) and sup['elapsed_seconds']<=done['elapsed_inclusive_seconds'],'supervisor inclusive')
def evaluate(phase):
 r=C.out(phase);seal=C.read(r/'seal.json');pins=C.read(r/'pins.json');attempt=C.read(r/'attempt.json')
 B.interpreter(seal,pins,sys.executable);C.check_inventory(pins,C.required_paths(phase));C.driver_ready()
 C.require(seal['phase']==phase and seal['command']==C.command(phase) and seal['environment']==C.environment(phase) and type(seal['expected_exit']) is int and seal['expected_exit']==0 and type(seal['shared_total_seconds']) is int and seal['shared_total_seconds']==1800,'seal scope/command/environment')
 used,facts=C.prior(phase);C.require(seal['used_seconds']==used and seal['previous']==facts and seal['remaining_seconds']==1800-used,'prior elapsed/facts')
 ad=C.validate_admission(seal,pins,attempt['admission_path'],C.git('rev-parse','HEAD'),phase)
 C.require(C.sha(attempt['admission_path'])==attempt['admission_sha256'] and C.sha(r/'seal.json')==attempt['seal_sha256'],'attempt/admission binding')
 C.require(attempt['phase']==phase and attempt['remaining_seconds']==1800-used and number(attempt['started_monotonic']),'attempt phase/clock')
 proc=C.read(r/'guard/process.json');sup=C.read(r/'supervisor.json');done=C.read(r/'completion.json');process(done,sup,proc,phase,used)
 C.require(C.sha(r/'pins.json')==seal['pins_sha256']==proc['pins_sha256'] and C.read(r/'guard/pins.json')==pins,'guard pin manifest')
 C.require(C.read(r/'invocation.json')==dict(command=C.guard_command(seal,attempt['started_monotonic'],phase),cwd=str(C.D),environment=seal['environment']),'exact invocation')
 for name in ('prelaunch-host.json','postflight.json'):
  h=C.read(r/name);C.require(h['conflicts']==[] and h['refs']['master']==h['refs']['origin/master']==C.MASTER,'host closure/master')
  B.head(seal,ad,h['refs']['HEAD']);resource(h['memory'])
 post=C.read(r/'postflight.json')
 C.require(set(post['checked_groups'])==C.expected_groups(phase,post['boot_id'],False) and post['still_active_current_launcher']==[attempt['runner']],'full prior/guard/child closure, own launcher explicitly live')
 for role in ('runner','child'):
  a=proc[role];C.require(a['boot_id']==post['boot_id'] and a['pid']==a['pgid']==a['sid'] and integer(a['start_ticks']) and type(a['command']) is str and bool(a['command']),'owned identity')
 gate=C.read(r/'guard/gate.json');current=C.read(r/'guard/current.json');permit=C.read(r/'guard/permit.json')
 C.require(gate['identity']==proc['child'] and gate['parent']==proc['runner'] and gate['parent_death_signal']==9 and gate['command']==seal['command'],'parent-death entry/command')
 C.require(gate['current_sha256']==C.sha(r/'guard/current.json') and gate['permit_sha256']==C.sha(r/'guard/permit.json') and permit==dict(current_sha256=C.sha(r/'guard/current.json'),command=seal['command']) and current['child']==proc['child'] and current['runner']==proc['runner'] and current['command']==seal['command'],'entry publication')
 fresh=C.host();C.require(fresh['refs']['HEAD']==ad['head'],'current HEAD')
 result=ordinary((r/'guard/run.log').read_text(errors='replace'),phase)
 record=tomllib.loads((r/'result.toml').read_text());K.check_cost(record,C.side(phase))
 samples=[json.loads(s) for s in (r/'guard/resources.jsonl').read_text().splitlines()];C.require(bool(samples),'resource samples missing')
 for s in [*samples,proc['terminal_memory'],fresh['memory']]:resource(s)
 if phase=='candidate-cost':
  ref=tomllib.loads((C.out('reference-cost')/'result.toml').read_text())
  comparison=K.comparison_data(ref,record);C.fresh(r/'comparison.json',comparison)
  C.require(comparison['accepted'],'allocation/event/retained graph increase; full comparison preserved')
 return result
def main(phase):
 C.phase_ok(phase);r=C.out(phase);accepted=False;result=None;error=None
 try:result=evaluate(phase);accepted=True
 except Exception as e:error=type(e).__name__+': '+str(e)
 bindings={str(p):C.sha(p) for p in sorted(r.rglob('*')) if p.is_file() and p.name!='audit.json'}
 try:
  attempt=C.read(r/'attempt.json');ad=C.read(attempt['admission_path'])
  for p in (attempt['admission_path'],ad['review_report']):bindings[p]=C.sha(p)
 except (OSError,KeyError,ValueError):pass
 if phase=='candidate-cost':
  for p in C.out('reference-cost').rglob('*'):
   if p.is_file():bindings[str(p)]=C.sha(p)
 C.fresh(r/'audit.json',dict(accepted=accepted,phase=phase,error=error,test_summary=result,bindings=bindings,production_admission=False,scope='this guarded cost stage only; full postexit closure and independent result review remain required'))
 return accepted
if __name__=='__main__':
 C.require(len(sys.argv)==2,'phase required');raise SystemExit(0 if main(sys.argv[1]) else 1)
