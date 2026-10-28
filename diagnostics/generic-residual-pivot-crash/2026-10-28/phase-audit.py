from common import *
import re

def main():
 c=read('contract.json');p=read('output/process.json');s=read('supervisor.json');done=read('completed.json');reservation=read('reservation.json');log=(D/'output/run.log').read_text()
 need(p['returncode']==c['expected_exit'] and p['pins_unchanged'] is True,'child exit/pins')
 need(s['accepted'] is True and s['returncode']==0 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'supervisor')
 need(done['accepted'] is True and done['elapsed_shared_seconds']<=3600 and s['elapsed_seconds']<=3600,'inclusive3600deadline')
 need(p['command']==c['command'] and p['pins_sha256']==sha(D/'pins.json'),'command/pins')
 need(s['guard_identity']==p['runner'],'supervised runner')
 gate=read('output/gate.json');cur=read('output/current.json');permit=read('output/permit.json')
 need(gate['identity']==p['child']==cur['child'] and gate['parent']==p['runner']==cur['runner'],'entry identities')
 need(gate['command']==permit['command']==cur['command']==c['command'] and gate['parent_death_signal']==9,'entry command/signal')
 need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'entry hash links')
 need(sha(D/'output/pins.json')==sha(D/'pins.json'),'copied pins')
 need(reservation['guard_deadline']==reservation['started_monotonic']+3592 and reservation['outer_deadline']==reservation['started_monotonic']+3600,'shared deadlines')
 need('RPC_SOURCE '+str(Path(c['source_root'])/'src/JSimplex.jl') in log,'source identity')
 need(re.findall(r'^INCLUDING (.*)$',log,re.M)==c['files'],'ordered ordinary includes')
 need('Error During Test' not in log,'no test errors')
 name='Residual pivot crash '+c['arm'];line=next((x for x in log.splitlines() if x.startswith(name) and '|' in x),None);need(line is not None,'root Test summary')
 header=next((x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x),None)
 need(header is not None,'root summary header')
 fields=header.split('|',1)[1].split();wanted=['Pass','Fail','Total','Time'] if c['expected_failures'] else ['Pass','Total','Time']
 need(fields==wanted,'exact ordinary summary schema, no broken/skips/errors')
 columns=line.split('|',1)[1].split();need(len(columns)==len(wanted),'exact ordinary data columns')
 pass_count=int(columns[0]);fails=c['expected_failures']
 if fails:
  need(int(columns[1])==fails and int(columns[2])==pass_count+fails>=c['minimum_total'] ,'exact expected failures');need(c['expected_total'] is None or pass_count+fails==c['expected_total'],'exact RED total when frozen')
  actual_locations=[[path,int(line)] for path,line in re.findall(r'Test Failed at (.*?):(\d+)',log)]
  need(actual_locations==c['expected_failure_locations'],'only exact allocation failure locations')
  need(log.count('Test Failed at ')==fails,'only allocation failures')
 else:
  need(int(columns[1])==pass_count>=c['minimum_total'],'all tests passed')
  need(log.count('RPC_COMPLETED '+c['arm'])==1 and 'Test Failed at ' not in log,'ordinary completion')
  if c.get('expected_total') is not None:need(pass_count==c['expected_total'],'frozen GREEN total on master')
 if fails:
  admitted=read('admission.json')
  need(type(admitted['expected_total']) is int and type(admitted['expected_passes']) is int,'frozen independent RED totals')
  need(pass_count==admitted['expected_passes'] and pass_count+fails==admitted['expected_total'],'exact independently admitted RED total')
 resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()]
 need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resources')
 need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
 unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];put('audit-host.json',host(extra))
 put('audit.json',dict(accepted=True,arm=c['arm'],passed=pass_count,expected_failures=fails,total=pass_count+fails,elapsed_shared_seconds=done['elapsed_shared_seconds'],samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=p['child_maxrss_kib'],bindings={str(D/n):sha(D/n) for n in ['output/run.log','output/process.json','pins.json','audit.py','contract.json']}))
 print(json.dumps({k:v for k,v in read('audit.json').items() if k!='bindings'}))
if __name__=='__main__':main()
