from pathlib import Path
import hashlib,json,os,re,subprocess,time,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-RED';run=D/'runs/red300'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def bound(m):
 for n,h in m.items():assert sha(n if Path(n).is_absolute() else R/n)==h,n
s=rd(run/'sealed.json');prep=rd(D/'preparation-pins.json');review=rd(D/'review.json');required=rd(D/'required-paths.json')['paths'];stages=rd(D/'stages.json');runtime=rd(D/'runtime-inputs-complete.json')['inventory'];baseline=rd(D/'baseline.json');W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
assert set(prep['sha256'])==set(required) and len(required)==1867
bound(prep['sha256']);assert review['accepted'] is True and review['findings']==[] and review['scope']=='dynamic BG driver preparation'
assert review['pins_sha256']==sha(D/'preparation-pins.json') and set(review['sha256'])==set(required)|{str(D/'preparation-pins.json')}
bound(review['sha256']);bound(review['evidence_sha256']);bound(rd(E/'entry.json')['sha256'])
expected=set(required)|{str(D/'preparation-pins.json'),str(D/'review.json'),str(run/'host.json'),str(run/'config.json')}|set(runtime)
for label,root in [('diagnostic',R),('production',W)]:
 assert set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(baseline[label])
 for n,h in baseline[label].items():assert sha(root/n)==h;expected.add(str(root/n))
for mode,stage in stages.items():
 root=Path(stage['path']);files={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file()}
 assert not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*'))
 assert set(files)==set(stage['sha256']) and len(files)==(75 if mode=='red' else 81)
 for n,p in files.items():assert sha(p)==stage['sha256'][n]
 if mode=='red':
  assert stage['sha256']==stage['baseline_sha256']
  for n,p in files.items():assert sha(Path(stage['source'])/n)==sha(p);expected.add(str(p))
assert set(s['files'])==expected and len(s['files'])==len(expected)==1871
assert s['trees']==[stages['red']['path'],str(R/'diagnostics/direct-bg-dynamic-upper/reproduce')] and s['inputs']==[]
inventory=set(s['files'])
for tree in s['trees']:
 root=Path(tree);assert root.is_dir() and not root.is_symlink()
 for p in root.rglob('*'):
  assert not (p.is_symlink() and (p.is_dir() or not p.exists()))
  if p.is_file():inventory.add(str(p))
assert inventory==set(s['inventory'])
for n,v in s['inventory'].items():assert v==dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)),n
for n,v in runtime.items():assert s['inventory'][n]==v
assert {k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json')
head='d7d090d86b1f1ed2d7b68a079437a0136f73a9f6';master='26e2291745999f485a74f643298ca997d65c7205'
assert git('rev-parse','HEAD')==s['head']==head and git('rev-parse','master')==s['master']==git('rev-parse','HEAD',cwd=W)==master
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');assert master+'\trefs/heads/master' in remote and head+'\trefs/heads/codex/simplex-core-architecture' in remote
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
cfg=rd(run/'config.json');assert cfg==s['config'] and cfg['phase']=='red300' and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh';stage=stages['red']['path'];out=run/'output'
assert cfg['stage']==stage and cfg['run']==str(run) and cfg['output']==str(out)
assert cfg['command']==['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'driver.jl'),str(out),stage,'red300']
assert {p.name for p in run.iterdir()}=={'sealed.json','host.json','config.json'}
symbols=['BGSlotUpper','_bg_slots','_bg_reserve!','_bg_swap_rows!','_bg_rotate_rows!','DynamicBGFactor','_dynamic_bg_factor','_dynamic_bg_replace!']
red=(D/'red.jl').read_text();assert re.findall(r'@test isdefined\(JSimplex,:(\w+!?)\)',red)==symbols and red.count('@test ')==8
for p in (Path(stage)/'src').rglob('*.jl'):
 txt=p.read_text()
 assert not any(x in txt for x in symbols),str(p)
expected_tests=rd(D/'expected-tests.json')['red'];assert expected_tests==dict(assertions=8,groups=[['Missing dynamic BG U contracts (eight expected failures)',0,8,0,0]])
toml=tomllib.loads((D/'expected-tests.toml').read_text())['red'];assert [[t[k] for k in ['name','pass','fail','error','broken']] for t in toml['groups']]==expected_tests['groups']
groups=set(s['groups']);assert len(groups)==228 and groups==set(rd(D/'host.json')['groups'])==set(rd(E/'host.json')['groups'])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==s['boot_id'];matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=boot,comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
assert not matches
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2
proof=dict(all_passed=True,time=time.time(),head=head,master=master,remote=remote,files=len(expected),inventory=len(inventory),red_stage_files=75,runtime_files=len(runtime),preparation_files=len(required),groups=sorted(groups),matches=matches,boot_id=boot,unreadable_exe_pids=unreadable,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],expected_assertions=8,numerical_api_calls=0,scope='Fresh independent offline exact RED admission; no Julia or prior executable invoked')
with (E/'independent-admission-proof.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in proof.items() if k not in ('groups','unreadable_exe_pids')},indent=2))
