from common import *
import re

def main():
 c=read('contract.json');p=read('output/process.json');s=read('supervisor.json');done=dict(accepted=False,elapsed_shared_seconds=s['elapsed_seconds']);reservation=read('reservation.json');log=(D/'output/run.log').read_text()
 need(p['returncode']==1 and p['pins_unchanged'] is True,'preserved failed actualMASTER exit/pins')
 need(s['accepted'] is False and s['returncode']==1 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'honest failed test supervisor')
 need(not (D/'completed.json').exists() and s['elapsed_seconds']<=4500,'no accepted completion; bounded failed supervisor')
 need(p['command']==c['command'] and p['pins_sha256']==sha(D/'pins.json'),'command/pins')
 need(s['guard_identity']==p['runner'],'supervised runner')
 gate=read('output/gate.json');cur=read('output/current.json');permit=read('output/permit.json')
 need(gate['identity']==p['child']==cur['child'] and gate['parent']==p['runner']==cur['runner'],'entry identities')
 need(gate['command']==permit['command']==cur['command']==c['command'] and gate['parent_death_signal']==9,'entry command/signal')
 need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json'),'entry hash links')
 need(sha(D/'output/pins.json')==sha(D/'pins.json'),'copied pins')
 need(reservation['guard_deadline']==reservation['started_monotonic']+4492 and reservation['outer_deadline']==reservation['started_monotonic']+4500,'shared deadlines')
 need('EBA_SOURCE '+str(Path(c['source_root'])/'src/JSimplex.jl') in log,'source identity')
 need(re.findall(r'^INCLUDING (.*)$',log,re.M)==c['files'],'ordered ordinary includes')
 need('Error During Test' not in log,'no test errors')
 name='Epsilon bound auxiliary '+c['arm'];line=next((x for x in log.splitlines() if x.startswith(name) and '|' in x),None);need(line is not None,'root Test summary')
 header=next((x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x),None)
 need(header is not None,'root summary header')
 fields=header.split('|',1)[1].split();need(fields==['Pass','Fail','Total','Time'],'exact failed ordinary summary, no errors/broken/skips')
 columns=line.split('|',1)[1].split();need(columns[:3]==['380370','2','380372'] and len(columns)==4,'exact rejected MASTER root')
 pass_count,fails=380370,2
 need(c['expected_failures']==0 and c['expected_total']==380372,'original all-pass expectation preserved')
 locations=[[path,int(n)] for path,n in re.findall(r'Test Failed at (.*?):(\d+)',log)]
 need(locations==[[str(Path(c['source_root'])/'test/generic_unit_perturb_residual_tests.jl'),581],[str(Path(c['source_root'])/'test/generic_dual_comparisons_tests.jl'),709]],'only two known oldcost failures')
 need('EBA_COMPLETED MASTER' not in log,'no successful completion marker')
 resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()]
 need(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resources')
 need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
 unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];put('failure-audit-host.json',host(extra))
 put('failure-audit.json',dict(accepted=False,audit_completed=True,production_qualification_rejected=True,original_expected_failures=0,arm=c['arm'],passed=pass_count,actual_failures=fails,total=pass_count+fails,failed_supervisor_elapsed_seconds=s['elapsed_seconds'],samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=p['child_maxrss_kib'],bindings={str(D/n):sha(D/n) for n in ['output/run.log','output/process.json','pins.json','failure-postcheck.py','audit.py','audit-failure.log','contract.json']}))
 print(json.dumps({k:v for k,v in read('failure-audit.json').items() if k!='bindings'}))
if __name__=='__main__':main()
