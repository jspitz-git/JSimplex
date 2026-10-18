"""Independent reviewer: read-only text/hash/integer/host checks; imports no project code."""
from pathlib import Path
import hashlib,json,os,subprocess,time,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION'
E=D.parent/'DIRECT-BG-SPLIT-GREEN'; run=D/'runs/green300'; red=D/'runs/red300'
HEAD='1062b4cbd87dc042d7182a7fc3bd1a7b25ce15bd'; MASTER='26e2291745999f485a74f643298ca997d65c7205'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
checks={};details={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bind(j,key='sha256'):
 return all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in j[key].items())
def ck(n,v):checks[n]=bool(v)
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def inventory(files,trees):
 paths=set(map(Path,files))
 for t in map(Path,trees):
  assert t.is_dir() and not t.is_symlink()
  for p in t.rglob('*'):
   assert not (p.is_symlink() and (p.is_dir() or not p.exists()))
   if p.is_file():paths.add(p)
 return {str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
s=rd(run/'sealed.json');cfg=rd(run/'config.json');st=rd(D/'stages.json');prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');rv=rd(red/'result-review.json');a=rd(red/'audit.json')
ck('seal_inventory_exact',inventory(s['files'],s['trees'])==s['inventory'])
ck('runtime_inventory_exact',inventory(rd(D/'runtime-inputs-complete.json')['inventory'],[])==rd(D/'runtime-inputs-complete.json')['inventory'])
ck('preparation_pins_membership_hashes',set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']) and bind(prep))
ck('preparation_review_exact',pr['accepted'] is True and pr['findings']==[] and pr['scope']=='split BG driver preparation' and pr['pins_sha256']==sha(D/'preparation-pins.json') and set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and bind(pr))
ck('entry_bindings',bind(rd(D/'entry.json')))
redfiles={str(p) for p in red.rglob('*') if p.is_file() and p!=red/'result-review.json'}
ck('red_result_review_exact',rv['accepted'] is True and rv['findings']==[] and rv['scope']=='split BG RED result' and rv['phase']=='red300' and set(rv['sha256'])==redfiles and bind(rv) and bind(rv,'evidence_sha256'))
rs=rd(red/'sealed.json');ck('red_seal_unchanged',inventory(rs['files'],rs['trees'])==rs['inventory'])
ck('red_audit_accepted',a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='red300' and bind(a))
raw=tomllib.loads((red/'output/raw.toml').read_text());rt=raw['tests'];rg=rt['children'];rp=rd(red/'output/process.json')
ck('red_exact_result',raw['complete'] is True and raw['fatal']=='' and len(rg)==1 and rg[0]['pass']==0 and rg[0]['fail']==10 and rg[0]['error']==rg[0]['broken']==0 and len(rg[0]['failures'])==10 and rp['returncode']==1 and rp['reason']=='exit1')
for mode,stage in st.items():
 root=Path(stage['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck(mode+'_stage_exact',len(actual)==(75 if mode=='red' else 81) and actual==set(stage['sha256']) and not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')) and all(sha(root/n)==h for n,h in stage['sha256'].items()))
 ck(mode+'_frozen_source_bytes',all(sha(Path(stage['source'])/n)==h for n,h in stage['sha256'].items()))
for label,root in [('diagnostic',R),('production',W)]:
 b=rd(D/'baseline.json')[label]
 ck(label+'_source_membership_hashes',set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b) and all(sha(root/n)==h for n,h in b.items()))
expectedfiles=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(rd(D/'runtime-inputs-complete.json')['inventory'])|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]}|{str(Path(st['green']['path'])/n) for n in st['green']['sha256']}|redfiles|{str(red/'result-review.json'),str(run/'host.json'),str(run/'config.json')}
ck('sealed_file_membership',set(s['files'])==expectedfiles and len(s['files'])==len(set(s['files'])))
ck('sealed_tree_membership',s['trees']==[st['green']['path'],str(R/'diagnostics/direct-bg-split-upper/reproduce')] and s['inputs']==[])
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+st['green']['path'],str(D/'driver.jl'),str(run/'output'),st['green']['path'],'green300']
ck('config_exact',cfg==dict(phase='green300',mode='green',seconds=300,expected_exit=0,stage=st['green']['path'],run=str(run),output=str(run/'output'),command=command) and s['config']==cfg and s['phase']=='green300')
env=rd(D/'environment.json');ck('environment_exact',{k:os.environ.get(k) for k in env}==env)
allow=rd(E/'allowance.json');ck('allowance_exact',allow['phase']=='green300' and allow['max_attempts']==1 and allow['outer_seconds']==300 and allow['inner_seconds']==292 and allow['cost_allowed'] is False and allow['master_change'] is False)
ck('unlaunched_exact_run_membership',{p.name for p in run.iterdir()}=={'host.json','config.json','sealed.json'})
ex=rd(D/'expected-tests.json');tx=tomllib.loads((D/'expected-tests.toml').read_text())
ck('green_exact_expected_tree',len(ex['green']['groups'])==34 and sum(x[1] for x in ex['green']['groups'])==15929 and all(x[2:]==[0,0,0] for x in ex['green']['groups']) and [[x['name'],x['pass'],x['fail'],x['error'],x['broken']] for x in tx['green']['groups']]==ex['green']['groups'])
ld=rd(D/'loaded-paths.json');ck('loaded_module_schema',set(ld)=={'SparseArrays','LinearAlgebra','TOML','Test','PrecompileTools'} and all(str(Path(p).resolve(strict=True))==p for p in ld.values()))
driver=(D/'driver.jl').read_text();ck('top_level_includes_before_main',driver.rfind('include(')<driver.index('function main()') and '(JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools)' in driver)
w=rd(D/'work-ledger.json');ck('work_integer_totals',all([sum(side) for side in w['per_group_reference_candidate'][k]]==v for k,v in w['totals'].items()) and sum(w['factorization_attempts'])==389 and sum(v for k,v in w['allocation_probe_operations'].items() if k!='total')==706 and sum(w['new_injection_detail'].values())==419 and w['explicit_storage_allocation_requests']-w['expected_injected_storage_failures']==w['completed_before_injected_throw']==9973 and 'two n-entry Int vector conversions and sorts' in w['new_storage_only_pair_work']['full_partition_token_scans'])
ck('callback_integer_budget',sum(n+n*(n+1)//2 for n in [21,21,14,90,69])+42+124+35+52+60+2784+3==10392)
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');head=git('rev-parse','HEAD');master=git('rev-parse','master');branch=git('branch','--show-current')
ck('fresh_refs',head==HEAD==s['head'] and master==MASTER==s['master'] and git('rev-parse','HEAD',cwd=W)==MASTER and branch=='codex/simplex-core-architecture' and HEAD+'\trefs/heads/codex/simplex-core-architecture' in remote and MASTER+'\trefs/heads/master' in remote)
ck('diagnostic_ancestry',subprocess.run(['git','merge-base','--is-ancestor','73216b71debb99c7515b3d265702e0d68afe7064','HEAD'],cwd=R).returncode==0)
ck('tracked_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
groups=set(rd(D/'host.json')['groups'])|set(rd(red/'posthost.json')['groups']);ck('full242_history',len(groups)==242 and groups==set(s['groups'])==set(rd(run/'host.json')['groups'])==set(rd(E/'preflight.json')['host']['groups']))
matches=[];unreadable=[];observed=0
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe='';observed+=1
  try:exe=os.readlink(p/'exe')
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
ck('fresh_host_clear',not matches and boot==s['boot_id']);ck('fresh_resources',memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2)
details.update(sealed_files=len(s['files']),sealed_inventory=len(s['inventory']),runtime_inventory=len(rd(D/'runtime-inputs-complete.json')['inventory']),preparation_files=len(prep['sha256']),head=head,master=master,remote_refs=remote,branch=branch,boot_id=boot,groups=sorted(groups),processes_observed=observed,matches=matches,unreadable_exe_pids=unreadable,memory=memory,visibility_limit='Unreadable executable links remain a visibility limit; stat and comm inspected',sealed_sha256=sha(run/'sealed.json'))
record=dict(scope='Independent GREEN300 exact-stage text/hash/integer and fresh host/ref review; no Julia or author script execution',all_passed=all(checks.values()),checks=checks,details=details,checked_at=time.time(),source_sha256=sha(__file__))
with (E/'admission-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],sealed_files=details['sealed_files'],inventory=details['sealed_inventory'],memory=memory,groups=len(groups))))
