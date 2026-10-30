"""Plain Test summary plus actual-master/process/evidence audit; no Test recorder."""
import re,sys,math,json
from pathlib import Path
import common as C
def summary(log):
 C.require(type(log) is str and not any(s in log.lower() for s in ('world age','error during test','undefvarerror','syntax:','segmentation fault','error:','test failed at')),'test/load/runtime defect')
 lines=log.splitlines();idx=[i for i,s in enumerate(lines) if '|' in s and s.split('|',1)[0].strip()=='DEVEX_PRODUCTION_MASTER'];C.require(len(idx)==1,'one ordinary master summary');i=idx[0];header=next((lines[j] for j in range(i-1,-1,-1) if lines[j].startswith('Test Summary:')),None);C.require(header is not None,'Test header');keys=re.findall(r'Pass|Fail|Error|Broken|Total|Time',header.split('|',1)[1]);values=lines[i].split('|',1)[1].split();C.require(len(keys)==len(values) and len(keys)==len(set(keys)) and {'Pass','Total'}<=set(keys),'summary schema');out={k:int(v) for k,v in zip(keys,values) if k!='Time'};C.require(out.get('Pass')==out.get('Total')==5776 and all(out.get(k,0)==0 for k in ('Fail','Error','Broken')),'all5776 ordinary tests green');C.require(lines.count('DEVEX_PRODUCTION_MASTER_COMPLETED')==1,'single master completion');return out
def resource(q):C.require(type(q['available_kib']) is int and type(q['swap_used_kib']) is int and q['available_kib']>=6*1024**2 and q['swap_used_kib']<=1024**2,'RAM/swap guard')
def evaluate():
 c=C.read(C.D/'contract.json');C.require(C.prior_time()==c['previous_seconds'],'actual prior time');seal=C.read(C.R/'seal.json');pins=C.read(C.R/'pins.json');attempt=C.read(C.R/'attempt.json');ad=C.admit(attempt['admission_path'],seal,pins);C.verify_pins(pins);C.require(set(pins['files'])==set(C.paths()),'complete source pins');C.require(C.sha(attempt['admission_path'])==attempt['admission_sha256'] and C.sha(C.R/'seal.json')==attempt['seal_sha256'],'attempt sealed');proc=C.read(C.R/'guard/process.json');sup=C.read(C.R/'supervisor.json');done=C.read(C.R/'completion.json')
 C.require(proc['returncode']==0 and type(proc['returncode']) is int and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==c['command'],'child exit/command/pins');C.require(sup['accepted'] is True and sup['returncode']==0 and type(sup['returncode']) is int and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')) and 'cleanup_error' not in sup,'supervisor/cleanup');C.require(done['supervisor_accepted'] is True and type(done['limit_seconds']) is int and done['limit_seconds']==1800,'completion scope');elapsed=done['elapsed_inclusive_seconds'];C.require(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>0 and done['total_inclusive_seconds']==1108.3747013349202+elapsed<=1800 and sup['elapsed_seconds']<=elapsed,'shared clock reset/overflow')
 C.require(C.sha(C.R/'pins.json')==seal['pins_sha256']==proc['pins_sha256'] and C.read(C.R/'guard/pins.json')==pins,'guard manifest');C.require(C.read(C.R/'invocation.json')==dict(command=C.guard_command(attempt['started_monotonic']),cwd=str(C.D),environment=c['environment']),'invocation');C.require(seal['command']==c['command'] and seal['environment']==c['environment'] and seal['previous_seconds']==1108.3747013349202 and seal['remaining_seconds']==691.6252986650798,'exact concrete schedule')
 gate=C.read(C.R/'guard/gate.json');current=C.read(C.R/'guard/current.json');permit=C.read(C.R/'guard/permit.json');C.require(gate['identity']==proc['child'] and gate['parent']==proc['runner'] and gate['parent_death_signal']==9 and gate['command']==c['command'],'PDEATH entry ownership');C.require(gate['current_sha256']==C.sha(C.R/'guard/current.json') and gate['permit_sha256']==C.sha(C.R/'guard/permit.json') and permit==dict(current_sha256=C.sha(C.R/'guard/current.json'),command=c['command']) and current['runner']==proc['runner'] and current['child']==proc['child'] and current['command']==c['command'],'current/permit/gate binding')
 for role in ('runner','child'):
  a=proc[role];C.require(a['pid']==a['pgid']==a['sid'] and type(a['start_ticks']) is int and a['start_ticks']>0 and a['boot_id']==seal['preflight']['boot_id'] and bool(a['command']),'owner identity')
 for name in ('prelaunch-host.json','postflight.json'):
  h=C.read(C.R/name);C.require(h['conflicts']==[] and h['refs']==seal['preflight']['refs'],'saved host/refs');resource(h['memory'])
 h=C.read(C.R/'postflight.json');C.require(set(h['checked_groups'])==C.groups(h['boot_id'],False) and h['still_active_current_launcher']==[attempt['runner']],'all old/guard/child groups ANDsessions; own launcher explicit');fresh=C.host();C.require(fresh['refs']==h['refs'],'current refs')
 samples=[json.loads(s) for s in (C.R/'guard/resources.jsonl').read_text().splitlines()];C.require(bool(samples),'resource records')
 for q in [*samples,proc['terminal_memory'],fresh['memory']]:resource(q)
 state=C.read(C.D/'integration.json');p=C.read(C.D/'production-commit.json');C.require(C.git(C.W,'diff-tree','--no-commit-id','--name-only','-r',p['commit']).splitlines()==p['names'] and all(C.git(C.W,'rev-parse',p['commit']+':'+n)==v for n,v in p['blobs'].items()),'actual production commit exact names/blobs');C.require(all(C.sha(C.M/n)==v for n,v in state['payload_sha256'].items()),'actual master payload');return summary((C.R/'guard/run.log').read_text(errors='replace'))
def main():
 accepted=False;result=None;error=None
 try:result=evaluate();accepted=True
 except Exception as e:error=type(e).__name__+': '+str(e)
 b={str(p):C.sha(p) for p in C.R.rglob('*') if p.is_file() and p.name!='audit.json'}
 try:
  a=C.read(C.R/'attempt.json');ad=C.read(a['admission_path'])
  for p in (a['admission_path'],ad['review_report']):b[p]=C.sha(p)
 except (OSError,ValueError,KeyError):pass
 C.fresh(C.R/'audit.json',dict(accepted=accepted,scope='one actual-master focused verification; independent result review and remote publication remain required',test_summary=result,error=error,bindings=b,production_commit=C.read(C.D/'integration.json')['production_commit'],master_push_performed=False));return accepted
if __name__=='__main__':raise SystemExit(0 if main() else 1)
