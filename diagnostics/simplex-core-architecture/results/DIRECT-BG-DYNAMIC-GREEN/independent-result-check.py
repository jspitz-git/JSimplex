"""New saved-result review; no imported prior executable, Julia or auditor execution."""
from pathlib import Path
import json,hashlib,tomllib,re,math
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';r=D/'runs/green300'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks=[]
def ck(v,n):
 assert v,n
 checks.append(n)
s=rd(r/'sealed.json');a=rd(r/'admission.json');pins=rd(r/'launch-pins.json');audit=rd(r/'audit.json');cfg=rd(r/'config.json');inv=rd(r/'invocation.json');p=rd(r/'output/process.json');cur=rd(r/'output/current.json');sup=inv['supervisor'];pre=rd(r/'prehost.json');host=rd(r/'host.json');post=rd(r/'posthost.json')
ck(a['accepted'] is True and a['findings']==[] and a['phase']=='green300' and a['pins_sha256']==sha(r/'sealed.json'),'accepted exact admission')
ck(set(a['sha256'])==set(s['files'])|{str(r/'sealed.json')} and all(sha(n)==h for n,h in a['sha256'].items()),'all exact admission bindings')
ck(all(sha(n)==h for n,h in a['evidence_sha256'].items()),'all admission evidence unchanged')
for name,j in [('seal',s),('launch',pins)]:
 ck(all(str(Path(n).resolve())==v['resolved'] and sha(n)==v['sha256'] for n,v in j['inventory'].items()),name+' resolved inventory digests')
ck(set(pins['files'])==set(s['files'])|{str(r/'sealed.json'),str(r/'admission.json'),str(r/'prehost.json')} and pins['trees']==s['trees'],'exact launch membership')
ck(rd(r/'output/pins.json')==pins and all(pins['inventory'][n]==v for n,v in s['inventory'].items()),'seal launch output continuity')
ck(cfg==s['config'] and cfg['phase']=='green300' and cfg['seconds']==300 and cfg['expected_exit']==0,'exact configuration')
ck(p['command']==cur['command']==inv['command']==cfg['command'] and p['pins_unchanged'] is True,'command and pins')
ck(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(r/'launch-pins.json'),'launch digest linkage')
ck(inv['review_sha256']==sha(r/'admission.json') and inv['reservation_sha256']==sha(r/'reservation.json'),'admission reservation linkage')
ck(rd(r/'reservation.json')==dict(one_attempt=True,phase='green300',command=cfg['command'],pins_sha256=sha(r/'launch-pins.json'),review_sha256=sha(r/'admission.json'),max_seconds=300),'one exact reservation')
ck(inv['guard_command']==[inv['python'],'-B',str(D/'guard.py'),'run',str(r/'launch-pins.json'),cfg['output'],'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']],'exact inner deadline and guard command')
ck(p['returncode']==0 and p['reason']=='exit0' and sup['accepted'] is True and sup['returncode']==0 and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']),'clean normal exit no timeout/kill')
ck(all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=300 for v in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 'cleanup_error' not in sup,'inclusive bounded elapsed')
ck(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'runner child identity linkage')
ck(all(h['matches']==[] and h['boot_id']==s['boot_id'] and h['head']==s['head'] and h['master']==s['master'] for h in [host,pre,post]),'clean saved host closures and identity')
ck(set(s['groups'])<=set(pre['groups'])<=set(post['groups']) and all(p[role][k] in post['groups'] for role in ['runner','child'] for k in ['pgid','sid']),'group/session closure coverage')
ck(all(p[role]['boot_id']==s['boot_id'] and p[role]['start_ticks']>0 and p[role]['command'] for role in ['runner','child']),'positive start/boot/command identities')
resources=[json.loads(x) for x in (r/'output/resources.jsonl').read_text().splitlines()]
ck(len(resources)==13 and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']]),'all sampled and terminal resource limits')
ck(p['child_maxrss_kib']==689904,'saved process RSS')
raw=tomllib.loads((r/'output/raw.toml').read_text());expected=rd(D/'expected-tests.json')['green']
ck(set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'} and raw['phase']=='green300' and raw['complete'] is True and raw['fatal']=='','complete exact raw schema')
ck(type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'Julia BLAS threads')
ck(raw['loaded']==dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl')),'exact loaded module paths')
t=raw['tests'];nodes=[t]+t['children']
ck(all(set(n)=={'name','pass','fail','error','broken','failures','children'} and all(type(n[k]) is int and n[k]>=0 for k in ['pass','fail','error','broken']) and n['fail']==n['error']==n['broken']==0 and n['failures']==[] for n in nodes),'all exact node schemas zero failures/errors/broken')
ck(t['name']=='root' and t['pass']==0 and all(n['children']==[] for n in t['children']),'empty root and flat leaves')
actual=[[n['name'],n['pass'],n['fail'],n['error'],n['broken']] for n in t['children']]
ck(actual==expected['groups'] and sum(n['pass'] for n in t['children'])==expected['assertions']==8776,'all exact nine leaves 8776 passing')
log=(r/'output/run.log').read_text();warn=re.findall(r'WARNING: Detected access to binding `([^`]+)`',log)
ck(warn==['Main.DynamicBGSlotTests','DynamicBGSlotTests.run_slots','Main.DynamicBGTests','DynamicBGTests.lifecycles','DynamicBGTests.rejection_and_aliases','DynamicBGTests.export_modes','DynamicBGTests.focused_updates'],'exact seven retained binding warnings')
ck([x for x in log.splitlines() if x.startswith(('BEGIN','END'))]==['BEGIN dynamic BG driver green300']+[x for n in ['slots','lifecycles','rejection_and_aliases','export_modes','focused_updates'] for x in ['BEGIN '+n,'END '+n]],'all five suite boundaries completed')
ck(not any(x in log+(r/'launcher.log').read_text() for x in ['TEST FAILURE:','BROKEN TEST:','FATAL DRIVER:','GROUP/COUNT MISMATCH','ERROR:']),'no fatal/failure logs')
ck(audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']=='' and audit['result']['groups']==actual,'saved original audit agrees independently')
ck(set(audit['sha256'])=={str(x) for x in r.rglob('*') if x.is_file() and x.name not in ['audit.json','result-review.json']} and all(sha(n)==h for n,h in audit['sha256'].items()),'exact original audit bindings')
result={'accepted':True,'findings':[],'checks':checks,'check_count':len(checks),'assertions':8776,'warnings':warn,'elapsed_seconds':inv['elapsed_seconds'],'resource_samples':len(resources),'minimum_available_kib':min(z['available_kib'] for z in resources),'max_swap_used_kib':max(z['swap_used_kib'] for z in resources),'rss_kib':p['child_maxrss_kib'],'scope':'Independent saved GREEN correctness result, no execution or performance qualification'}
with (E/'independent-result-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
