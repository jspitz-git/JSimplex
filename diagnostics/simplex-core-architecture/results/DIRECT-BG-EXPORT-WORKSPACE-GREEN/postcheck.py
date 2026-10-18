"""Saved failed GREEN diagnostic validation, not a replacement acceptance audit."""
from pathlib import Path
import sys,json,hashlib,tomllib
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');sys.path.insert(0,str(D));import control as c
run=D/'runs/green300';out=run/'output';checks={}
def ck(v,n):checks[n]=bool(v)
a=c.rd(run/'audit.json');raw=tomllib.loads((out/'raw.toml').read_text());p=c.rd(out/'process.json');iv=c.rd(run/'invocation.json');s=c.rd(run/'sealed.json');ad=c.rd(run/'admission.json');pins=c.rd(run/'launch-pins.json')
ck(a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Exact exit')",'original_failure_preserved')
ck(raw['phase']=='green300' and raw['complete'] is True and raw['fatal']=='','complete_phase_without_fatal')
t=raw['tests'];ch=t['children'];ex=c.rd(D/'expected-tests.json')['green']['groups']
ck(t['name']=='root' and all(t[x]==0 for x in ('pass','fail','error','broken')) and not t['failures'] and len(ch)==len(ex)==11,'root_and_eleven_groups')
actual=[[z['name'],z['pass'],z['fail'],z['error'],z['broken']] for z in ch];want=[list(x) for x in ex];want[3][1]-=1;want[3][3]+=1
ck(actual==want and all(not z['children'] for z in ch),'exact7934_pass_one_error')
failures=[x for z in ch for x in z['failures']]
ck(len(failures)==1 and 'import-tests.jl:28' in failures[0] and 'reducing over an empty collection' in failures[0],'sole_error_in_diagnostic_reducer')
ck(raw['threads']==raw['blas_threads']==1 and raw['loaded']==c.loaded_for(c.config('green300')),'loaded_source_and_threads')
ck(p['returncode']==2 and p['reason']=='exit2' and iv['supervisor']['accepted'] is False and iv['supervisor']['returncode']==1,'Julia2_guard1_preserved')
ck(0<=iv['elapsed_seconds']<=300 and not iv['supervisor']['hard_timeout'] and not iv['supervisor']['soft_timeout'],'no_timeout')
ck(all(Path(n).resolve(strict=True)==Path(v['resolved']) and c.sha(n)==v['sha256'] for n,v in pins['inventory'].items()),'all_launch_resolved_hashes')
c.verify_review(ad,run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG export workspace exact-stage admission','green300');ck(True,'admission_exact_and_evidence')
log=(out/'run.log').read_text()+'\n'+(run/'launcher.log').read_text();from oracle import warning_log
ck(log.count('TEST FAILURE:')==1 and not warning_log(log) and 'FATAL DRIVER:' not in log and 'END all BG export workspace tests' in log,'sole_error_no_warning_full_completion')
cur=c.rd(out/'current.json');ck(cur['runner']==p['runner']==iv['supervisor']['guard_identity'] and cur['child']==p['child'],'process_identity_linkage')
ck(p['command']==cur['command']==iv['command']==c.config('green300')['command'] and p['pins_unchanged'] and p['pins_sha256']==cur['pins_sha256']==iv['pins_sha256']==c.sha(run/'launch-pins.json'),'command_pin_linkage')
res=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck(bool(res) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in res+[p['terminal_memory']]),'samples_terminal_resources')
groups=c.rd(run/'posthost.json')['groups'];host=c.full_host(groups);c.save(E/'postcheck-host.json',host)
ck(c.host_safe(host) and host['boot_id']==s['boot_id'] and len(set(groups))==250 and set(groups)<=set(host['groups']),'fresh250groups_sessions_no_Julia')
ck(host['head']==s['head'] and host['master']==c.MASTER,'refs_unchanged')
source=c.R/'diagnostics/direct-bg-export-workspace/reproduce/import-tests.jl';txt=source.read_text()
ck(txt.count('sum(n for (T,n) in a.requests if T===Float64)')==1 and 'inputs=(spzeros(0,0)' in txt,'source_bound_empty_input_reducer')
paths=sorted(p for p in run.rglob('*') if p.is_file())+[Path(__file__),E/'postcheck-host.json',source]
v=dict(all_passed=all(checks.values()),correctness_accepted=False,checks=checks,sha256={str(p):c.sha(p) for p in paths},resources=dict(samples=len(res),min_available_kib=min(x['available_kib'] for x in res),max_swap_kib=max(x['swap_used_kib'] for x in res),elapsed_seconds=iv['elapsed_seconds']),scope='Diagnostic failure integrity only; original GREEN remains rejected; no rerun or performance acceptance')
c.save(E/'postcheck.json',v);print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),resources=v['resources'],failed=[n for n,b in checks.items() if not b])))
c.require(v['all_passed'],'Postcheck failed; preserve')
