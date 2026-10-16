from pathlib import Path
import json,hashlib,tomllib,time,os,subprocess,math
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-RED';run=D/'runs/red300';out=run/'output'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def bound(v):
 for n,h in v.items():assert sha(n)==h,n
s=rd(run/'sealed.json');ad=rd(run/'admission.json');lp=rd(run/'launch-pins.json');a=rd(run/'audit.json');cfg=rd(run/'config.json');p=rd(out/'process.json');cur=rd(out/'current.json');inv=rd(run/'invocation.json');sup=inv['supervisor'];res=rd(run/'reservation.json')
files={str(x) for x in run.rglob('*') if x.is_file()};assert len(files)==17
assert set(a['sha256'])==files-{str(run/'audit.json')};bound(a['sha256'])
assert ad['accepted'] is True and ad['findings']==[] and ad['scope']=='dynamic BG exact-stage admission' and ad['phase']=='red300' and ad['pins_sha256']==sha(run/'sealed.json')
assert set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')};bound(ad['sha256']);bound(ad['evidence_sha256'])
assert set(lp['files'])==set(s['files'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']} and lp['trees']==s['trees'] and lp['inputs']==[]
for pins in [s,lp]:
 actual=set(pins['files'])
 for tree in pins['trees']:
  root=Path(tree);assert not root.is_symlink()
  for x in root.rglob('*'):
   assert not (x.is_symlink() and (x.is_dir() or not x.exists()))
   if x.is_file():actual.add(str(x))
 assert actual==set(pins['inventory'])
 for n,v in pins['inventory'].items():assert v==dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)),n
assert rd(out/'pins.json')==lp and all(lp['inventory'][n]==v for n,v in s['inventory'].items())
assert {x.name for x in out.iterdir()}=={'raw.toml','pins.json','current.json','process.json','resources.jsonl','run.log'}
assert all(x.is_file() and not x.is_symlink() for x in out.iterdir())
assert cfg==s['config'] and cfg['phase']=='red300' and cfg['seconds']==300
assert inv['command']==p['command']==cur['command']==cfg['command'];assert p['cwd']==str(R)
assert p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(run/'launch-pins.json')
assert inv['review_sha256']==sha(run/'admission.json') and inv['reservation_sha256']==sha(run/'reservation.json')
assert res==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300)
assert inv['guard_command']==[inv['python'],'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','1','--',*cfg['command']]
assert p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child']
for role in ['runner','child']:
 i=p[role];assert i['pid']==i['pgid']==i['sid'] and i['start_ticks']>0 and i['boot_id']==s['boot_id'] and i['command']
assert p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True and 'error' not in p
assert sup['returncode']==0 and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup
for t,limit in [(p['elapsed_including_launch'],292),(inv['elapsed_seconds'],300),(sup['elapsed_seconds'],300)]:assert math.isfinite(t) and 0<t<limit
assert rd(run/'launcher.log')==p
raw=tomllib.loads((out/'raw.toml').read_text());assert set(raw)=={'fatal','complete','threads','blas_threads','phase','tests','loaded'}
assert raw['fatal']=='' and raw['complete'] is True and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1 and raw['phase']=='red300'
assert raw['loaded']==dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
root=raw['tests'];assert set(root)=={'pass','name','fail','broken','failures','error','children'} and root['name']=='root' and root['failures']==[]
assert all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','broken','error']) and len(root['children'])==1
leaf=root['children'][0];assert set(leaf)==set(root) and leaf['children']==[]
assert [leaf[k] for k in ['name','pass','fail','error','broken']]==rd(D/'expected-tests.json')['red']['groups'][0]
symbols=['BGSlotUpper','_bg_slots','_bg_reserve!','_bg_swap_rows!','_bg_rotate_rows!','DynamicBGFactor','_dynamic_bg_factor','_dynamic_bg_replace!']
failures=[f'Test Failed at {D}/red.jl:{i+4}\n  Expression: isdefined(JSimplex, :{n})\n   Evaluated: isdefined(JSimplex, {n})' for i,n in enumerate(symbols)]
assert leaf['failures']==failures
log=(out/'run.log').read_text();assert log.count('TEST FAILURE:')==8
for f in failures:assert log.count('TEST FAILURE: '+f)==1
assert log.startswith('BEGIN dynamic BG driver red300\n') and all(x not in log for x in ['FATAL DRIVER:','GROUP/COUNT MISMATCH','BROKEN TEST:','ERROR:','Test Error','BEGIN slots'])
assert a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='red300' and a['error']=='' and a['result']['assertions']==8
samples=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()];assert len(samples)==5
assert all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in samples+[p['terminal_memory']]) and 0<p['child_maxrss_kib']<8*1024**2
hosts=[rd(run/n) for n in ['host.json','prehost.json','posthost.json']];assert all(not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']) for h in hosts)
groups=set(hosts[-1]['groups']);assert len(groups)==230 and groups==set(s['groups'])|{p['runner']['pid'],p['child']['pid']}
assert set(rd(E/'posthost.json')['groups'])==groups and rd(E/'posthost.json')['matches']==[]
assert {x.name for x in (D/'runs').iterdir()}=={'red300'}
assert {k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==s['head']
assert subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()==s['master']
assert not subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).strip()
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id'];matches=[];unreadable=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  st=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe=''
  try:exe=str((q/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(q.name))
  except FileNotFoundError:pass
  if int(st[2]) in groups or int(st[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(q.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),comm=comm,exe=exe,command=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
assert not matches
proof=dict(all_passed=True,time=time.time(),run_files=17,exact_missing_symbols=symbols,failures=8,errors=0,broken=0,child_exit=1,guard_exit=0,outer_seconds=inv['elapsed_seconds'],resource_samples=len(samples),min_available_kib=min(z['available_kib'] for z in samples),max_swap_kib=max(z['swap_used_kib'] for z in samples),child_maxrss_kib=p['child_maxrss_kib'],groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,world_age_warning_retained=True,scope='Independent saved RED result; offline only; no auditor or Julia rerun')
with (E/'independent-result-proof.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in proof.items() if k not in ['groups','unreadable_exe_pids']},indent=2))
