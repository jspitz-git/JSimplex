"""Independent one-shot hash/text/host review; imports no author control or Julia."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time,tomllib
E=Path(__file__).resolve().parent
R=E.parents[3]; D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION'; run=D/'runs/red300'
def read(p): return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def check(x,label):
 checks[label]=bool(x)
 if not x:raise AssertionError(label)
def resolve(n):return Path(n) if Path(n).is_absolute() else R/n
checks={}; s=read(run/'sealed.json'); cfg=read(run/'config.json'); inv=s['inventory']
check(set(p.name for p in run.iterdir())=={'config.json','host.json','sealed.json'},'unlaunched exclusive run')
check(len(s['files'])==len(set(s['files'])),'file list unique')
actual=set(s['files']); tree_counts={}
for t in s['trees']:
 root=Path(t); nodes=list(root.rglob('*'));check(not root.is_symlink() and not any(p.is_symlink() for p in nodes),'tree without symlinks '+t)
 members={str(p) for p in nodes if p.is_file()};actual.update(members);tree_counts[t]=len(members)
check(actual==set(inv),'exact inventory membership')
for n,b in inv.items():
 check(str(Path(n).resolve(strict=True))==b['resolved'] and sha(n)==b['sha256'],'inventory '+n)
prep=read(D/'preparation-pins.json'); req=read(D/'required-paths.json'); rev=read(D/'review.json')
check(set(prep['sha256'])==set(req['paths']),'preparation exact membership')
for n,h in prep['sha256'].items():check(sha(resolve(n))==h,'preparation '+n)
check(rev['accepted'] is True and rev['findings']==[] and rev['scope']=='split BG driver preparation','preparation accepted')
check(rev['pins_sha256']==sha(D/'preparation-pins.json') and set(rev['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')},'preparation review membership')
for key in ['sha256','evidence_sha256']:
 for n,h in rev.get(key,{}).items():check(sha(resolve(n))==h,'preparation review '+n)
runtime=read(D/'runtime-inputs-complete.json')['inventory'];check(all(inv.get(n)==b for n,b in runtime.items()),'complete runtime sealed')
stages=read(D/'stages.json')
for mode,st in stages.items():
 root=Path(st['path']); members={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 check(members==set(st['sha256']),'stage exact membership '+mode)
 check(all(sha(root/n)==h for n,h in st['sha256'].items()),'stage hashes '+mode)
check(len(stages['red']['sha256'])==75 and len(stages['green']['sha256'])==81,'RED75 GREEN81')
redroot=Path(stages['red']['path']); reference=Path(stages['red']['source'])
check({str(p.relative_to(reference)) for p in reference.rglob('*') if p.is_file()}==set(stages['red']['sha256']),'accepted DIRECT baseline membership')
check(all(sha(reference/n)==h for n,h in stages['red']['sha256'].items()),'accepted DIRECT baseline bytes')
check(cfg==s['config'] and cfg['phase']==s['phase']=='red300' and cfg['stage']==str(redroot) and cfg['seconds']==300 and cfg['expected_exit']==1,'exact phase stage limits')
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
expected_command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(redroot),str(D/'driver.jl'),str(run/'output'),str(redroot),'red300']
check(cfg['command']==expected_command and cfg['run']==str(run) and cfg['output']==str(run/'output'),'exact command output')
env=read(D/'environment.json');check({k:os.environ.get(k) for k in env}==env,'current loading environment')
check('--startup-file=no' in Path(wrapper).read_text() and 'ulimit -v 8388608' in Path(wrapper).read_text(),'wrapper startup and VM')
expected=['BGSplitUpper','_sbu_target','_sbu_reserve_block!','_sbu_build','_sbu_insert_at!','_sbu_rotate_rows!','SplitBGFactor','_split_bg_factor','_split_bg_replace!','_split_bg_copy_with']
red=(D/'red.jl').read_text();symbols=re.findall(r'@test isdefined\(JSimplex,:(\w+!?)\)',red)
check(symbols==expected and red.count('@test ')==10 and red.count('@testset ')==1,'ten exact missing-contract assertions')
redtext='\n'.join(p.read_text() for p in (redroot/'src').rglob('*.jl')); greentext='\n'.join(p.read_text() for p in (Path(stages['green']['path'])/'src').rglob('*.jl'))
check(all(name not in redtext for name in expected),'RED symbols absent')
check(all(name in greentext for name in expected),'GREEN symbols present')
check(not re.search(r'(?<![\w])(?:forward_solve!|transpose_solve!|replace_column!|refactorize!|_split_bg_factor|_sbu_build)\s*\(',red),'no RED numerical API call')
expected_red=read(D/'expected-tests.json')['red'];check(expected_red=={'assertions':10,'groups':[['Missing split BG U contracts (ten expected failures)',0,10,0,0]]},'RED exact JSON tree')
rt=tomllib.loads((D/'expected-tests.toml').read_text())['red'];check(rt['assertions']==10 and rt['groups']==[dict(name=expected_red['groups'][0][0],pass_=0)] if False else len(rt['groups'])==1 and rt['groups'][0]=={'name':expected_red['groups'][0][0],'pass':0,'fail':10,'error':0,'broken':0},'RED exact TOML leaf')
loaded=read(D/'loaded-paths.json');check(set(loaded)=={'SparseArrays','LinearAlgebra','TOML','Test','PrecompileTools'} and all(str(Path(p).resolve())==p and p in inv for p in loaded.values()),'exact loaded module path inputs including Test')
driver=(D/'driver.jl').read_text();check(driver.index('include(joinpath(@__DIR__,"red.jl"))')<driver.index('function main()') and 'include(' not in driver[driver.index('function main()'):],'top-level loading before main')
check('(JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools)' in driver and 'Threads.nthreads()==BLAS.get_num_threads()==1' in driver,'driver reports exact modules threads')
control=(D/'control.py').read_text();guard=(D/'guard.py').read_text();audit=(D/'audit.py').read_text();oracle=(D/'oracle.py').read_text();launch=(D/'launch.py').read_text();supervisor=(D/'supervisor.py').read_text()
check("seconds=cfg['seconds']-8" in control and 'started+seconds' in control,'292 absolute inner deadline')
check("resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))" in guard and "< 6 * 1024**2" in guard and "> 1024**2" in guard,'VM RAM swap guards')
check("int(a[2]) in groups or int(a[3]) in groups" in control and "int(fields[2]) == pgid or int(fields[3]) == pgid" in guard,'full groups AND sessions scans')
check("('pid','start_ticks','boot_id','command')" in guard and 'os.pidfd_open' in guard and 'signal.pidfd_send_signal' in guard and 'owner=a' in supervisor,'owned boot start command pidfd cleanup')
check(audit.index("require(not warning_log(log)")<audit.index('if pure:return') and 'if warning_log(log):return False' in oracle and "raw['loaded']==loaded" in oracle,'warnings timeout and exact loaded rejection')
check("verify_review(rd(rp),sp,sealed['files']+[str(sp)]" in launch and "save(res,dict(one_attempt=True" in launch and "require(not Path(cfg['output']).exists()" in launch,'review and exclusive reservation gates')
check('record[\'terminal_memory\'] = memory()' in guard and "resources+[p['terminal_memory']]" in audit,'terminal resources required')
MASTER='26e2291745999f485a74f643298ca997d65c7205';HEAD='5ce49601a6312d565a4275b765ffdc814b481801'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
check(git('rev-parse','HEAD')==s['head']==HEAD and git('branch','--show-current')=='codex/simplex-core-architecture','diagnostic HEAD branch')
check(git('rev-parse','master')==s['master']==MASTER and git('rev-parse','HEAD',cwd=W)==MASTER,'master production')
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
check(MASTER+'\trefs/heads/master' in remote and HEAD+'\trefs/heads/codex/simplex-core-architecture' in remote,'fresh remote refs')
check(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no tracked changes')
for label,root in [('diagnostic',R),('production',W)]:
 b=read(D/'baseline.json')[label]
 check(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b) and all(sha(root/n)==h for n,h in b.items()),'baseline membership bytes '+label)
groups=set(s['groups']);check(len(groups)==240 and groups==set(read(D/'host.json')['groups']) and groups==set(read(E/'preflight.json')['host']['groups']),'all 240 historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();check(boot==s['boot_id'],'same boot')
matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
check(not matches,'fresh no historical groups sessions or visible Julia');check(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'fresh RAM swap')
allow=read(E/'allowance.json');check(allow['phase']=='red300' and allow['max_attempts']==1 and allow['outer_seconds']==300 and allow['inner_seconds']==292 and not allow['green_allowed'] and not allow['cost_allowed'],'one RED allowance')
result=dict(all_passed=True,checks=len(checks),checked_labels=list(checks),inventory_files=len(inv),sealed_files=len(s['files']),preparation_files=len(prep['sha256']),runtime_files=len(runtime),tree_counts=tree_counts,stage_counts={k:len(v['sha256']) for k,v in stages.items()},sealed_sha256=sha(run/'sealed.json'),host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,memory=memory,remote_refs=remote,scope='Read-only stat/comm/readable exe inspection; inaccessible exe links remain visibility limits'),scope='Independent exact RED300 hash/text/host checks; no author script imports or execution, no Julia')
with (E/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checked_labels','host','tree_counts')}));print(json.dumps(result['host']))
