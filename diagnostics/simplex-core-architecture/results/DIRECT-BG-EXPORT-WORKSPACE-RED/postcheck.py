"""New independent author postcheck of saved RED data; no auditor rerun or Julia."""
from pathlib import Path
import sys,json,hashlib,tomllib,math
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');sys.path.insert(0,str(D));import control as c
run=D/'runs/red300';out=run/'output';checks={}
def ck(v,n):checks[n]=bool(v)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
a=c.rd(run/'audit.json');raw=tomllib.loads((out/'raw.toml').read_text());p=c.rd(out/'process.json');iv=c.rd(run/'invocation.json');s=c.rd(run/'sealed.json');ad=c.rd(run/'admission.json');pins=c.rd(run/'launch-pins.json')
ck(a['all_passed'] is True and a['pure_timeout'] is False,'admitted_audit_pass')
ck(raw['phase']=='red300' and raw['complete'] is True and not raw['fatal'],'raw_complete_phase')
t=raw['tests'];ch=t['children'];ck(t['name']=='root' and all(t[x]==0 for x in ('pass','fail','error','broken')) and len(ch)==1,'one_RED_group')
ck(ch[0]['name']=='Missing BG export workspace contracts (six expected failures)' and ch[0]['pass']==ch[0]['error']==ch[0]['broken']==0 and ch[0]['fail']==len(ch[0]['failures'])==6 and ch[0]['children']==[],'six_expected_failures_only')
ck(raw['threads']==raw['blas_threads']==1 and raw['loaded']==c.loaded_for(c.config('red300')),'loaded_source_and_threads')
ck(p['returncode']==1 and p['reason']=='exit1' and iv['supervisor']['accepted'] is True and iv['supervisor']['returncode']==0,'RED1_guard0')
ck(0<=iv['elapsed_seconds']<=300 and not iv['supervisor']['hard_timeout'],'inclusive300')
ck(all(Path(n).resolve(strict=True)==Path(v['resolved']) and sha(n)==v['sha256'] for n,v in pins['inventory'].items()),'all_launch_resolved_hashes')
ck(all(sha(n)==h for n,h in ad['sha256'].items()) and all(sha(n)==h for n,h in ad['evidence_sha256'].items()),'admission_bindings')
log=(out/'run.log').read_text()+'\n'+(run/'launcher.log').read_text();from oracle import warning_log
ck(log.count('TEST FAILURE:')==6 and not warning_log(log) and 'FATAL DRIVER:' not in log,'failure_log6_no_warning')
res=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck(bool(res) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in res+[p['terminal_memory']]),'samples_terminal_resources')
groups=c.rd(run/'posthost.json')['groups'];host=c.full_host(groups);c.save(E/'postcheck-host.json',host)
ck(c.host_safe(host) and host['boot_id']==s['boot_id'] and set(groups)<=set(host['groups']),'fresh_full_groups_sessions_no_Julia')
ck(host['head']==s['head'] and host['master']==c.MASTER,'refs_unchanged')
paths=sorted(p for p in run.rglob('*') if p.is_file())+[Path(__file__),E/'postcheck-host.json']
v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},resources=dict(samples=len(res),min_available_kib=min(x['available_kib'] for x in res),max_swap_kib=max(x['swap_used_kib'] for x in res),elapsed_seconds=iv['elapsed_seconds']),scope='Saved structural RED only, not GREEN/performance; no rerun')
c.save(E/'postcheck.json',v);print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),resources=v['resources'],failed=[n for n,b in checks.items() if not b])))
c.require(v['all_passed'],'Postcheck failed; preserve')
