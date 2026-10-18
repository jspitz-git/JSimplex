"""Fresh independent read-only RED300 admission checks; no preparation imports/execution."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time,tomllib
E=Path(__file__).resolve().parent
D=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');R=D.parents[3]
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
run=D/'runs/red300';checks={};hashes={};bytes_read=0
HEAD='69715b09ce3baa317464303a0023465e94435342';MASTER='26e2291745999f485a74f643298ca997d65c7205'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 global bytes_read
 p=str(p)
 if p not in hashes:
  h=hashlib.sha256()
  with Path(p).open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);bytes_read+=len(chunk)
  hashes[p]=h.hexdigest()
 return hashes[p]
def ck(name,v):checks[name]=bool(v)
def bindings(j,mapping={}):return all(sha(mapping.get(n,n))==h for n,h in j.items())
def git(*args,root=R):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
s=rd(run/'sealed.json');cfg=rd(run/'config.json');prep=rd(D/'preparation-pins.json');review=rd(D/'review.json');stages=rd(D/'stages.json');env=rd(D/'environment.json')
ck('authorized_only_one_red300',rd(E/'authorization.json')['phase']=='red300' and rd(E/'authorization.json')['one_attempt'] is True and rd(E/'authorization.json')['no_green'] is True and rd(E/'authorization.json')['limit_seconds']==300)
ck('run_exact_prelaunch_membership',{p.name for p in run.iterdir()}=={'host.json','config.json','sealed.json'})
ck('only_red_phase',{p.name for p in (D/'runs').iterdir()}=={'red300'})
ck('seal_phase_refs',s['phase']=='red300' and s['head']==HEAD and s['master']==MASTER and s['inputs']==[])
ck('preparation1870_exact_membership',len(prep['sha256'])==1870 and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']))
ck('all1870_preparation_hashes',bindings(prep['sha256']))
ck('canonical_preparation_review_acceptance',review['accepted'] is True and review['findings']==[] and review['scope']=='BG export workspace driver preparation' and review['pins_sha256']==sha(D/'preparation-pins.json'))
ck('canonical_review_exact_bindings',set(review['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and bindings(review['sha256']) and bindings(review['evidence_sha256']))
old=rd(D/'review.json.before-R1');oldpins=rd(D/'preparation-pins.json.before-R1')
remap={str(D/n):str(D/(n+'.before-R1')) for n in ['preparation-pins.json','required-paths.json','review.json','review.md']}
ck('R1_preserved_rejection',old['accepted'] is False and len(old['findings'])==1 and old['findings'][0]['id']=='R1' and old['pins_sha256']==sha(D/'preparation-pins.json.before-R1'))
ck('R1_original1858_membership_and_hashes',len(oldpins['sha256'])==1858 and set(oldpins['sha256'])==set(rd(D/'required-paths.json.before-R1')['paths']) and bindings(oldpins['sha256'],remap))
ck('R1_original_review_and_evidence',bindings(old['sha256'],remap) and bindings(old['evidence_sha256'],remap))
fixture=str(R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl');fh='835b6e4241705b4c7a6a2625c904999ffe30e90ec99c937d257cbe2a2c289517'
ck('corrected_fixture_pin_propagation',prep['sha256'][fixture]==fh and fixture in s['files'] and s['inventory'][fixture]['sha256']==fh and sha(fixture)==fh and not re.search(r'\binclude\s*\(',Path(fixture).read_text()))
for t in ['TASK1','TASK2']:
 v=rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-'+t)/'final-review.json')
 ck(t+'_accepted_fixture_continuity',v['accepted'] is True and v['readtime_sha256'][fixture]==fh)
for mode,count in [('red',75),('green',79)]:
 st=stages[mode];root=Path(st['path']);paths=list(root.rglob('*'));files={str(p.relative_to(root)) for p in paths if p.is_file()}
 ck(mode+'_stage_exact_membership',len(files)==count and files==set(st['sha256']) and not root.is_symlink() and not any(p.is_symlink() for p in paths))
 ck(mode+'_stage_all_hashes',all(sha(root/n)==h for n,h in st['sha256'].items()))
 ck(mode+'_historical75_full_continuity',len(st['baseline_sha256'])==75 and all(sha(Path(st['source'])/n)==h for n,h in st['baseline_sha256'].items()))
ck('RED_exact_original75',stages['red']['sha256']==stages['red']['baseline_sha256'])
redroot=Path(stages['red']['path']);greenroot=Path(stages['green']['path']);overlay=rd(R/'diagnostics/direct-bg-export-workspace/reproduce/overlay-manifest.json')
ck('RED_no_candidate_symbols',not any(re.search(r'BGExportWorkspace|BGExportFactor|_bgx_',p.read_text()) for p in (redroot/'src').rglob('*.jl')))
ck('GREEN_only_four_added_files',len(set(stages['green']['sha256'])-set(stages['red']['sha256']))==4 and [n for n in stages['red']['sha256'] if stages['red']['sha256'][n]!=stages['green']['sha256'][n]]==['src/JSimplex.jl'])
expected=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json'),str(run/'host.json'),str(run/'config.json')}
ck('seal_exact1874_files',len(s['files'])==1874 and set(s['files'])==expected and len(s['files'])==len(set(s['files'])))
ck('seal_exact_trees',s['trees']==[str(redroot),str(R/'diagnostics/direct-bg-export-workspace/reproduce')])
actual=set(s['files'])
for tree in s['trees']:
 root=Path(tree);paths=list(root.rglob('*'));ck('tree_no_directory_or_dangling_symlinks_'+root.name,not root.is_symlink() and not any(p.is_symlink() and (p.is_dir() or not p.exists()) for p in paths));actual.update(str(p) for p in paths if p.is_file())
ck('seal_full_inventory_membership',actual==set(s['inventory']))
ck('seal_all_resolved_paths_and_hashes',all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in s['inventory'].items()))
runtime=rd(D/'runtime-inputs-complete.json')['inventory']
ck('runtime609_hash_and_resolved_closure',len(runtime)==609 and all(n in s['files'] and s['inventory'][n]==v for n,v in runtime.items()))
for label,root in [('diagnostic',R),('production',W)]:
 b=rd(D/'baseline.json')[label]
 ck(label+'_tracked_source_membership',set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(b))
 ck(label+'_all_baseline_hashes',all(str(root/n) in s['files'] and sha(root/n)==h for n,h in b.items()))
ck('exact_environment',{k:os.environ.get(k) for k in env}==env)
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
cmd=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(redroot),str(D/'driver.jl'),str(run/'output'),str(redroot),'red300']
ck('exact_config_command_limits',cfg==dict(phase='red300',mode='red',seconds=300,expected_exit=1,stage=str(redroot),run=str(run),output=str(run/'output'),command=cmd) and s['config']==cfg)
for p in [wrapper,'/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/julia.sh']:
 t=Path(p).read_text();ck('wrapper_guardrails_'+str(Path(p).parent),'ulimit -v 8388608' in t and 'JULIA_PKG_OFFLINE=true JULIA_PKG_PRECOMPILE_AUTO=0 OPENBLAS_NUM_THREADS=1 JULIA_NUM_THREADS=1' in t and '--startup-file=no "$@"' in t and p in runtime)
r= (D/'red.jl').read_text();driver=(D/'driver.jl').read_text();guard=(D/'guard.py').read_text();ctl=(D/'control.py').read_text();launch=(D/'launch.py').read_text();audit=(D/'audit.py').read_text();oracle=(D/'oracle.py').read_text();supervisor=(D/'supervisor.py').read_text()
symbols=['BGExportWorkspace','_bgx_scratch!','_bgx_scale_mode','_bgx_import_upper','BGExportFactor','_bgx_refactor_with!']
ck('RED_exact_six_isdefined_assertions',re.findall(r'@test isdefined\(JSimplex, :([^\)]+)\)',r)==symbols and r.count('@test ')==6 and r.count('@testset ')==1)
ck('RED_structural_no_numerical_calls',not re.search(r'\b(ldiv!|factorize|refactorize!|ftran!|btran!|solve|include)\s*\(',r))
expect=rd(D/'expected-tests.json')['red'];toml=tomllib.loads((D/'expected-tests.toml').read_text())['red']
ck('RED_onegroup_expected0pass6fail0errors',expect=={'assertions':6,'groups':[['Missing BG export workspace contracts (six expected failures)',0,6,0,0]]} and [[g['name'],g['pass'],g['fail'],g['error'],g['broken']] for g in toml['groups']]==expect['groups'])
ck('driver_top_level_RED_loading',driver.index('include(joinpath(@__DIR__,"red.jl"))')<driver.index('function main()') and 'if startswith(ARGS[3],"red")' in driver and driver.count('run_bg_export_red()')==1 and 'invokelatest' not in driver and 'eval(' not in driver)
ck('driver_raw_before_final_validation',driver.index('TOML.print(io,raw)')<driver.index('valid=raw["complete"]') and 'exit(valid ? (mode=="red" ? 1 : 0) : 2)' in driver)
ck('driver_threads_and_source_checks','Threads.nthreads()==BLAS.get_num_threads()==1' in driver and 'realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl"))' in driver and 'PrecompileTools.verbose[] && error' in driver)
ck('loaded_dependencies_individually_pinned',all(p in s['files'] for p in rd(D/'loaded-paths.json').values()))
ck('guard_VM_RAM_swap_threads', 'resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in guard and "sample['available_kib'] < 6 * 1024**2 or sample['swap_used_kib'] > 1024**2" in guard and "OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'" in guard)
ck('inner292_outer300',"seconds=cfg['seconds']-8" in ctl and 'started+seconds' in ctl and 'started+limit-6' in supervisor and 'started+limit-2' in supervisor and "record['elapsed_seconds']<=limit" in supervisor)
ck('one_attempt_failclosed',"save(res,dict(one_attempt=True" in launch and "with Path(p).open('x')" in ctl and "require(not Path(cfg['output']).exists()" in launch)
ck('warnings_worldage_rejected',r'\bwarning\b|world[ -]age' in oracle and "require(not warning_log(log)" in audit and "log.count('TEST FAILURE:')==(6" in audit)
ck('identity_and_group_session_closure',all(x in guard for x in ['start_ticks','boot_id','command','pidfd_open','pidfd_send_signal',"int(fields[2]) == pgid or int(fields[3]) == pgid"]) and "for key in ['pgid','sid']" in audit and 'all(host_safe(h)' in audit)
ck('no_automatic_retry','main(sys.argv[1])' in launch and 'launch.py' not in supervisor and "if phase.endswith('600')" in ctl and "'pure timeout result'" in ctl)
ck('author_fresh_inputs_bindings',rd(E/'input-check.json')['all_passed'] is True and bindings(rd(E/'input-check.json')['sha256']))
# Fresh host inspection is independent of preparation/control implementations.
groups=set(s['groups']);matches=[];unreadable_exe=[];unreadable_identity=[];identities=[]
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text();a=stat[stat.rindex(')')+2:].split();comm=(p/'comm').read_text().strip();command=(p/'cmdline').read_bytes();argv0=command.split(b'\0',1)[0].decode(errors='replace');exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable_exe.append(int(p.name))
  except FileNotFoundError:pass
  ident=dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=boot,comm=comm,argv0=argv0,exe=exe,command=command.replace(b'\0',b' ').decode(errors='replace'));identities.append(ident)
  if ident['pgid'] in groups or ident['sid'] in groups or any(Path(v).name.lower().startswith('julia') for v in [comm,argv0,exe]):matches.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unreadable_identity.append(int(p.name))
m={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};mem=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree'])
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
host=dict(time=time.time(),groups=sorted(groups),matches=matches,boot_id=boot,unreadable_exe_pids=unreadable_exe,unreadable_identity_pids=unreadable_identity,visible_identities=identities,memory=mem,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),production_head=git('rev-parse','HEAD',root=W),branch=git('branch','--show-current'),remote=remote,status=git('status','--porcelain'),scope='Fresh stat/comm/argv0 plus readable exe; all historical groups AND sessions; inaccessible exe links limit recognizable-process proof, not universal executable proof')
ck('historical246_groups_full_continuity',len(groups)==246 and groups==set(rd(D/'host.json')['groups'])==set(rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-TASK2')/'host-closure.json')['groups'])==set(rd(E/'host.json')['groups']))
ck('fresh_host_no_recognizable_Julia_or_historical_members',not matches and not unreadable_identity)
ck('fresh_host_boot_refs',host['head']==HEAD and host['master']==host['production_head']==MASTER and boot==s['boot_id'] and host['branch']=='codex/simplex-core-architecture')
ck('fresh_remote_refs',remote==HEAD+'\trefs/heads/codex/simplex-core-architecture\n'+MASTER+'\trefs/heads/master')
ck('fresh_memory',mem['available_kib']>=6*1024**2 and mem['swap_used_kib']<=1024**2)
ck('tracked_worktree_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
ck('user_changes_preserved',host['status']==rd(E/'host.json')['status'])
save(E/'admission-independent-host.json',host)
result=dict(all_passed=all(checks.values()),checks=checks,failed=[n for n,v in checks.items() if not v],phase='red300',sealed_sha256=sha(run/'sealed.json'),sha256=hashes,bytes_hashed=bytes_read,scope='Independent offline exact RED300 admission checks; no Julia or prior checker/control execution')
save(E/'admission-independent-check-v2.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=result['failed'],unique_hashes=len(hashes),bytes_hashed=bytes_read,memory=mem,unreadable_exe_count=len(unreadable_exe),unreadable_identity_count=len(unreadable_identity))))
raise SystemExit(0 if result['all_passed'] else 1)
