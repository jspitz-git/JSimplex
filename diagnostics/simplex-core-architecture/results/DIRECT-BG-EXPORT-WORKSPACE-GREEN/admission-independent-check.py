from pathlib import Path
import hashlib,json,os,subprocess,time,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION';E=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN');run=D/'runs/green300'
checks=[]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(v,n):checks.append(dict(name=n,passed=bool(v)))
def bind(j,k='sha256'):
 return all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in j[k].items())
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def inv(j):
 paths=set(j['files'])
 for root in j['trees']:
  root=Path(root);ck(not root.is_symlink(),'not symlink root '+str(root))
  for p in root.rglob('*'):
   ck(not(p.is_symlink() and (p.is_dir() or not p.exists())),'safe tree item '+str(p))
   if p.is_file():paths.add(str(p))
 return {n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)) for n in sorted(paths)}
s=rd(run/'sealed.json');cfg=rd(run/'config.json');prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');st=rd(D/'stages.json')
ck(s['inventory']==inv(s) and set(s['files'])==set(s['inventory']),'full streaming seal hashes resolutions and exact membership')
ck(len(prep['sha256'])==1870 and bind(prep) and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'1870 preparation hashes and membership')
ck(pr['accepted'] is True and pr['findings']==[] and pr['scope']=='BG export workspace driver preparation','preparation acceptance')
ck(pr['pins_sha256']==sha(D/'preparation-pins.json') and set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and bind(pr) and bind(pr,'evidence_sha256'),'preparation review hashes')
fixture=str(R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl');ck(fixture in prep['sha256'] and fixture in s['files'],'corrected R1 transitive fixture pinned')
for task in ('TASK1','TASK2'):
 j=rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-'+task)/'final-review.json');ck(j['accepted'] is True and j['findings']==[] and bind(j,'readtime_sha256'),'historical '+task+' readtime hashes')
 if 'evidence_sha256' in j:ck(bind(j,'evidence_sha256'),'historical '+task+' evidence hashes')
 ck(j['readtime_sha256'].get(fixture)==sha(fixture),'historical '+task+' fixture continuity')
red=D/'runs/red300';rr=rd(red/'result-review.json');rs=rd(red/'sealed.json')
ck(rr['accepted'] is True and rr['findings']==[] and rr['scope']=='BG export workspace RED result' and rr['phase']=='red300','RED result scope')
ck(len(rr['sha256'])==17 and len(rr['evidence_sha256'])==20 and bind(rr) and bind(rr,'evidence_sha256') and set(rr['sha256'])=={str(p) for p in red.rglob('*') if p.is_file() and p!=red/'result-review.json'},'RED exact17 run20 evidence bindings')
ck(rs['inventory']==inv(rs),'RED full seal unchanged')
ck(rd(red/'audit.json')['all_passed'] is True and rd(red/'audit.json')['pure_timeout'] is False and rr['result']['failed']==6 and rr['result']['errored']==0,'RED six expected failures')
ck([p.name for p in (D/'runs').iterdir() if p.name.startswith('red') and (p/'result-review.json').exists()]==['red300'],'one accepted RED')
for mode,e in st.items():
 root=Path(e['path']);ck({str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}==e['sha256'] and len(e['sha256'])==(75 if mode=='red' else 79) and not any(p.is_symlink() for p in root.rglob('*')),'exact stage '+mode)
orig=Path(st['red']['source']);rrt=Path(st['red']['path']);grt=Path(st['green']['path'])
ck({str(p.relative_to(orig)):sha(p) for p in orig.rglob('*') if p.is_file()}==st['red']['sha256'],'exact original75')
app='\ninclude("_bgx_workspace.jl")\ninclude("_bgx_export.jl")\ninclude("_bgx_import.jl")\ninclude("_bgx_factor.jl")\n';root=(grt/'src/JSimplex.jl').read_text()
ck(root.count(app)==1 and root.replace(app,'')==(rrt/'src/JSimplex.jl').read_text(),'exact GREEN root inverse')
ck(all(st['green']['sha256'][n]==h for n,h in st['red']['sha256'].items() if n!='src/JSimplex.jl'),'74 unchanged original stage files')
ck(all(sha(grt/f'src/_bgx_{n}.jl')==sha(R/f'diagnostics/direct-bg-export-workspace/reproduce/{n}.jl') for n in ['workspace','export','import','factor']),'four exact candidate mappings')
for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
 b=rd(D/'baseline.json')[label];ck(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b) and all(sha(root/n)==h for n,h in b.items()),'unchanged '+label+' baseline')
env=rd(D/'environment.json');diff={k:[v,os.environ.get(k)] for k,v in env.items() if os.environ.get(k)!=v};ck(not diff,'actual nonlogin environment')
expected=dict(phase='green300',mode='green',seconds=300,expected_exit=0,stage=str(grt),run=str(run),output=str(run/'output'),command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(grt),str(D/'driver.jl'),str(run/'output'),str(grt),'green300'])
ck(s['phase']=='green300' and s['config']==cfg==expected,'exact GREEN300 config');ck({p.name for p in run.iterdir()}=={'config.json','host.json','sealed.json'},'no reservation output admission')
ex=rd(D/'expected-tests.json')['green'];to=tomllib.loads((D/'expected-tests.toml').read_text())['green'];ck(ex['assertions']==7935 and [g[1] for g in ex['groups']]==[42,6,35,56,108,53,303,6236,378,108,610] and all(g[2:]==[0,0,0] for g in ex['groups']),'frozen exact7935 groups')
ck(to['assertions']==7935 and [[g['name'],g['pass'],g['fail'],g['error'],g['broken']] for g in to['groups']]==ex['groups'],'TOML JSON identical')
driver=(D/'driver.jl').read_text();ck(all(driver.index('include("'+str(R/'diagnostics/direct-bg-export-workspace/reproduce'/n)+'")')<driver.index('function main()') for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl']),'three top-level modules')
ck(all(driver.count(n+'()')==1 for n in ['BGExportWorkspaceTests.run_workspace_tests','BGExportImportTests.run_import_tests','BGExportLifecycleTests.run_lifecycle_tests']),'three entries once')
ck('GROUP/COUNT MISMATCH OR FATAL' in driver and 'exact_tree(root,expected)' in driver,'group mismatch fails closed');ck(pr['prospective_assertions']['runtime_premises']==dict(native_allocation_requests=25,markowitz_allocation_requests=21,dense_retained_branches=4),'M25 M21 P4 unproven premises unchanged')
co=(D/'control.py').read_text();gu=(D/'guard.py').read_text();au=(D/'audit.py').read_text();ck("seconds=cfg['seconds']-8" in co and '8 * 1024**3' in gu and '6 * 1024**2' in gu and '1024**2' in gu,'292inner VM8GiB RAM6GiB swap1GiB');ck("require(not warning_log(log),'Warning/world-age outcome rejected')" in au,'warning world-age failclosed')
ck(rd(E/'authorization.json')['phase']=='green300' and rd(E/'authorization.json')['one_attempt'] is True,'current autonomous authority');ck(bind(rd(E/'input-check.json')),'current input-check bindings')
groups=sorted(set(rd(D/'host.json')['groups'])|set(rd(red/'posthost.json')['groups'])|set(s['groups']));ck(len(groups)==248 and groups==s['groups'],'all248 historical groups and sessions')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];ue=[];ui=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();raw=(p/'cmdline').read_bytes();argv0=raw.split(b'\0',1)[0].decode(errors='replace');exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:ue.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or any(Path(v).name.lower().startswith('julia') for v in [comm,argv0,exe]):matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=boot,comm=comm,argv0=argv0,exe=exe,command=raw.replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:ui.append(int(p.name))
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=ue,unreadable_identity_pids=ui,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],scope='Recognizable-process closure only; inaccessible exe links are an explicit visibility limit.')
ck(not matches and not ui,'fresh recognizable-process closure');ck(host['available_kib']>=6*1024**2 and host['swap_used_kib']<=1024**2,'fresh memory');ck(host['head']==s['head']=='d3c04f9c6836646e2324d1000df9ddb467782343' and host['master']==s['master']=='26e2291745999f485a74f643298ca997d65c7205' and boot==s['boot_id'],'fresh local refs boot');ck(set(host['remote'].splitlines())=={host['head']+'\trefs/heads/codex/simplex-core-architecture',host['master']+'\trefs/heads/master'},'fresh remote refs')
status=git('status','--short');allowed={'LocalPreferences.toml','Manifest.toml','diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PLAN/host.json','diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-QUALIFICATION/__pycache__/','diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-GREEN/','diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION/runs/green300/'};ck(all(x.startswith('?? ') and x[3:] in allowed for x in status.splitlines()),'only allowed untracked additions')
findings=[x['name'] for x in checks if not x['passed']];counts=dict(checks=len(checks),seal_files=len(s['files']),preparation_inputs=len(prep['sha256']),RED_run_bindings=len(rr['sha256']),RED_evidence_bindings=len(rr['evidence_sha256']),historical_groups=len(groups));result=dict(all_passed=not findings,findings=findings,counts=counts,checks=checks,host=host,environment_differences=diff,status=status,scope='Fresh independent admission only; no Julia or historical checker execution')
with (E/'admission-independent-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=not findings,findings=findings,counts=counts,unreadable_exe=len(ue),available_kib=host['available_kib'],swap_used_kib=host['swap_used_kib'])))
