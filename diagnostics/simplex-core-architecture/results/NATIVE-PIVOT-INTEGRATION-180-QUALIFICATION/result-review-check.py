"""Independent saved-result verification. No project/historical imports or numerical execution."""
from pathlib import Path
import hashlib,json,tomllib,subprocess,time,math
T=Path(__file__).resolve().parent;N=T.parent/'NATIVE-PIVOT-INTEGRATION-180-PREPARATION';R=N.parents[3]
D=N.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION';E=N.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT';K=N.parent/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION'
run=N/'runs/integration';out=run/'output';checks={}
def rd(p):return json.loads(Path(p).read_text())
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def sha(p):
 h=hashlib.sha256()
 with path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bound(z,field='sha256'):return all(sha(p)==h for p,h in z[field].items())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def ck(k,v):
 checks[k]=bool(v)
 if not v:
  save(T/'result-review-checks-rejected.json',dict(all_passed=False,checks=checks));raise RuntimeError(k)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
a=rd(run/'audit.json');s=rd(run/'sealed.json');l=rd(run/'launch-pins.json');cfg=rd(run/'config.json');stage=Path(cfg['stage']);iv=rd(run/'invocation.json');p=rd(out/'process.json');cur=rd(out/'current.json');sup=iv['supervisor'];res=rd(run/'reservation.json')
ck('original_audit_PASS',a['phase']=='integration' and a['all_passed'] is True and a['error']=='')
expected_audit={str(x) for x in run.rglob('*') if x.is_file() and x!=run/'audit.json'}|{str(x) for x in N.iterdir() if x.is_file()}
ck('exact43_audit_bindings',len(a['sha256'])==43 and set(a['sha256'])==expected_audit and bound(a))
for name,z,count in [('seal',s,1738),('launch',l,1741)]:
 ck(name+'_membership',len(z['files'])==len(set(z['files']))==count and set(z['files'])==set(z['inventory']) and z['trees']==[str(stage)] and z['inputs']==[])
 ck(name+'_all_resolved_hashes',all(v==dict(resolved=str(Path(k).resolve(strict=True)),sha256=sha(k)) for k,v in z['inventory'].items()))
ck('launch_exact_extension',set(l['files'])==set(s['files'])|{str(run/x) for x in ('sealed.json','admission.json','prehost.json')} and all(l['inventory'][k]==v for k,v in s['inventory'].items()) and rd(out/'pins.json')==l)
mp=N/'preparation-pins.json';m=rd(mp);rv=rd(N/'review-final.json');ad=rd(run/'admission.json')
for name,v,pin,required,count,scope,checksfile,nchecks in [('preparation',rv,mp,set(m['sha256'])|{str(mp)},1657,'offline preparation',N/'review-checks.json',38),('stage',ad,run/'sealed.json',set(s['files'])|{str(run/'sealed.json')},1739,'exact-stage admission',T/'admission-checks.json',21)]:
 ck(name+'_accepted_exact_bindings',v['accepted'] is True and v['findings']==[] and v['scope']==scope and v['pins_sha256']==sha(pin) and len(v['sha256'])==count and set(v['sha256'])==required and bound(v) and bound(v,'evidence_sha256'))
 c=rd(checksfile);ck(name+'_recorded_checks',c['all_passed'] is True and len(c['checks'])==nchecks and all(x is True for x in c['checks'].values()) and v['checks']==dict(all_passed=True,count=nchecks))
ck('preparation_exact_required',set(m['sha256'])==set(rd(N/'required-paths.json')['paths']) and bound(m))
overlay=rd(D/'overlay-manifest.json')['candidate'];entries={str(stage/x['destination']) for x in overlay}
ck('76_stage_source_exact',len(overlay)==76 and not stage.is_symlink() and not any(x.is_symlink() for x in stage.rglob('*')) and {str(x) for x in stage.rglob('*') if x.is_file()}==entries and all(sha(stage/x['destination'])==sha(x['source'])==x['sha256'] for x in overlay))
ck('seal_exact_expected_membership',set(s['files'])==set(m['sha256'])|{str(mp),str(N/'review-final.json'),str(run/'host.json'),str(run/'config.json'),str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}|entries)
baseline=rd(E/'actual-baseline.json');ck('actual520_unchanged',len(baseline['sha256'])==520 and bound(baseline))
old=rd(K/'result-review.json');oa=rd(E/'runs/integration/audit.json');ck('old60_failed_consumed_immutable',old['accepted'] is True and old['qualification_accepted'] is False and old['attempt']=='FAILED/CONSUMED' and oa['all_passed'] is False and bound(old) and bound(old,'evidence_sha256') and bound(oa) and not (E/'runs/integration/output/raw.toml').exists() and rd(E/'runs/integration/reservation.json')['max_seconds']==60)
sm=rd(N/'source-map.json');ck('original_infrastructure_unchanged',all(sha(N/k)==sha(E/k)==v for k,v in sm['byte_identical'].items()))
ck('original_driver_bound',all(sha(D/k)==m['sha256'][str(D/k)] for k in ('driver.jl','probe.jl','observed-tests.jl','observed-factorization.jl','recorder.jl')))
cmd=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'driver.jl'),str(out),'integration',str(stage)]
ck('config_command_exact',cfg==dict(phase='integration',seconds=180,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=cmd) and s['config']==cfg and all(x['command']==cmd for x in (iv,p,cur)))
ck('172_inner_command',iv['guard_command']==[iv['python'],'-B',str(N/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','172','--deadline',str(iv['monotonic_start']+172),'--expected-exit','0','--',*cmd] and Path(iv['python']).resolve()==Path('/usr/bin/python3').resolve())
ck('exclusive_reservation_linkage',res==dict(one_attempt=True,phase='integration',command=cmd,pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=180) and iv['reservation_sha256']==sha(run/'reservation.json') and iv['review_sha256']==sha(run/'admission.json') and iv['pins_sha256']==p['pins_sha256']==cur['pins_sha256']==sha(run/'launch-pins.json'))
ck('exit_and_inclusive180',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and sup['returncode']==0 and sup['accepted'] is True and 'cleanup_error' not in sup and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 0<=p['elapsed_including_launch']<=sup['elapsed_seconds']<=iv['elapsed_seconds']<=180)
ck('process_identity_linkage',cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'] and p['runner']['command'].strip()==' '.join(iv['guard_command']) and p['child']['command'].strip()==' '.join(cmd))
pre=rd(run/'prehost.json');post=rd(run/'posthost.json');h=rd(run/'host.json');groups=post['groups']
ck('full220_history',len(groups)==len(set(groups))==220 and set(s['groups'])<=set(pre['groups'])<=set(groups) and set(groups)==set(s['groups'])|{p[r][k] for r in ('runner','child') for k in ('pgid','sid')} and len(s['groups'])==218 and all(not x['matches'] and all(x[k]==s[k] for k in ('head','master','boot_id')) for x in (pre,post,h)))
ck('boot_start_ticks_own_sessions',all(x['boot_id']==s['boot_id'] and type(x['start_ticks']) is int and x['start_ticks']>0 and x['pid']==x['pgid']==x['sid'] and x['pgid'] in groups and x['command'] for x in (p['runner'],p['child'])) and p['runner']['start_ticks']==18777083 and p['child']['start_ticks']==18777134)
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck('107_resource_samples_guards',len(resources)==107 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]) and type(p['child_maxrss_kib']) is int and p['child_maxrss_kib']>0)
ck('output_exact_six',{x.name for x in out.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(x.is_file() for x in out.iterdir()))
raw=tomllib.loads((out/'raw.toml').read_text());loaded=rd(N/'loaded-paths.json');loaded['JSimplex']=str(stage/'src/JSimplex.jl')
ck('raw_complete_threads_loaded',raw['phase']=='integration' and raw['complete'] is True and raw['fatal']=='' and raw['probe_failed'] is False and type(raw['started']) is int and raw['started']==9 and type(raw['active']) is int and raw['active']==0 and raw['threads']==raw['blas_threads']==1 and raw['loaded']==loaded)
ids=[x+'/'+y for x in ('pfi','forrest_tomlin','suhl_suhl','bartels_golub') for y in ('default','threshold_one')]+['recovery']
def group(g,name,passed,n):return g['name']==name and type(g['pass']) is int and g['pass']==passed and all(type(g[k]) is int and g[k]==0 for k in ('fail','error','broken')) and not g['failures'] and len(g['children'])==n
root=raw['tests'];pub,rec=root['children'];ck('162_assertions_exact_tree',group(root,'root',0,2) and group(pub,'Native pivot policy public integration',0,8) and all(group(g,ids[i].replace('/',' / '),6,0) for i,g in enumerate(pub['children'])) and group(rec,'Native pivot policy private recovery',114,0))
base=rd(N/'controls-baseline.json');ck('control_baseline_source',len(base['default'])==20 and sha(base['source'])==base['source_sha256'])
ck('nine_exact_cases',len(raw['cases'])==9 and [x['id'] for x in raw['cases']]==ids)
totals=[0]*4;entries_checked=0;coverage={};construct=[]
def counts(v,n):return type(v) is list and len(v)==n and all(type(x) is int and x>=0 for x in v)
for i,c in enumerate(raw['cases']):
 expected=base['default'].copy();policy='threshold_one' if i==8 or i%2 else 'default'
 if policy=='threshold_one':expected[3]='3ff0000000000000';expected[7]='0000000000000000'
 aa,ss,ee=c['attempts'],c['successes'],c['empty'];caps=(2,0,2,6) if i==8 else (64,64,4096,4096)
 ck('case_'+str(i)+'_work_controls',c['finished'] is True and c['policy']==policy and counts(aa,4) and counts(ss,2) and counts(ee,2) and all(x<=y for x,y in zip(aa,caps)) and all(ee[k]<=ss[k]<=aa[k] for k in (0,1)) and ss[0]-ee[0]>=1 and c['expected_controls']==c['last_controls']==expected)
 if i<8:ck('case_'+str(i)+'_exact_optimum',c['status']=='OPTIMAL' and c['has_point'] is True and c['has_objective'] is True and c['point']==['4000000000000000']*2 and c['objective']=='c024000000000000' and aa[:2]==ss==[1,1] and ee==[0,0])
 else:ck('recovery_work_and_shape',aa==[2,0,2,3] and ss==[2,0] and ee==[0,0] and c['status']=='recovery' and c['has_point'] is False and c['has_objective'] is False and c['point']==[] and c['objective']=='')
 totals=[x+y for x,y in zip(totals,aa)];entries_checked+=20*sum(ss[k]-ee[k] for k in (0,1));coverage[c['id']]=dict(attempts=aa[1],successful_nonempty=ss[1]-ee[1]);construct.append(ss[0]-ee[0])
ck('totals_and_scope',totals==[10,8,82,67] and entries_checked==360 and all(x<=y for x,y in zip(totals,[514,512,32770,32774])) and raw['selected_scope']=='managed Float64 UMFPACK backend attempts; extracted-factor and raw auxiliary LU work excluded')
expected_result=dict(assertions=162,public_solves=8,recovery_trials=1,selected_attempts=totals,control_entries_checked=entries_checked,refactor_coverage=coverage,nonempty_constructions=construct,scope=raw['selected_scope'],limitation='Selected boundaries only, not complete manager/native work or a performance comparison',resident_highwater_kib=p['child_maxrss_kib'],resources=resources)
ck('audit_result_independently_reconstructed',a['result']==expected_result)
postcheck=rd(T/'postcheck.json');ck('supplemental_postcheck8_bound',postcheck['all_passed'] is True and len(postcheck['checks'])==8 and all(postcheck['checks'].values()) and bound(postcheck) and postcheck['summary']['cases']==raw['cases'] and postcheck['summary']['tests']==raw['tests'] and postcheck['summary']['audit_result']==a['result'])
source=(D/'observed-tests.jl').read_text();probe=(D/'probe.jl').read_text();guard=(N/'guard.py').read_text()
ck('source_options_and_owners_present',all(x in source for x in ('time_limit=5.0, iteration_limit=100','refactorization_interval=2','trial.factorization.base.factorization.control !== controls','trial.factorization.base.factorization !== native','w.factorization === factor','native.control === controls','w.refactorizations == old_refactors + 1','w.iterations == old_iterations','copied_options(options,J._phase_options','copied_options(options,J._remaining_options','copied_options(options,J._lp_auxiliary_options','J._copy_precision_options(BigFloat,options)','J._copy_precision_options(Float64,J._copy_precision_options(BigFloat,options))')))
ck('unchanged_diagnostic_bounds_and_VM',all(x in probe for x in ('zeros(Int,4,9)','zeros(UInt64,20,9)','for j in 1:20','No backend/owner references are retained')) and 'resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in guard)
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();head=git('rev-parse','HEAD');master=git('rev-parse','master');matches=[];unreadable=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  f=(proc/'stat').read_text().rsplit(')',1)[1].split();comm=(proc/'comm').read_text().strip();exe=''
  try:exe=str((proc/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(proc.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(proc.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()}
host=dict(time=time.time(),boot_id=boot,head=head,master=master,groups=groups,matches=matches,inaccessible_exe_pids=unreadable,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],scope='Fresh stat/comm/readable executable scan across all220 PGIDs AND SIDs; inaccessible executable links remain a visibility limit')
save(T/'result-review-host.json',host)
ck('fresh_refs_and_full_host_closure',not matches and boot==s['boot_id'] and head==s['head']=='e649eb18798611c0a46ca3ef5e12b1416acc2b40' and master==s['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194')
ck('no_tracked_or_index_changes',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
ck('fresh_resource_headroom',host['available_kib']>=6*1024**2 and host['swap_used_kib']<=1024**2)
save(T/'result-review-checks.json',dict(all_passed=all(checks.values()),checks=checks,audit_bindings=43,result_bindings=44,seal_files=1738,launch_files=1741,source_stage_files=76,actual_baseline_files=520,assertions=162,public_solves=8,recovery_trials=1,selected_attempts=totals,control_entries_checked=entries_checked,resource_samples=len(resources),inclusive_seconds=iv['elapsed_seconds'],maxrss_kib=p['child_maxrss_kib'],scope='Independent read-only saved-result/source/host verification; no old auditor/oracle execution or import, no Julia/query/compiler/solve'))
print(json.dumps(dict(all_passed=all(checks.values()),checks=len(checks),bindings=44,assertions=162,attempts=totals,control_entries=entries_checked,groups=len(groups))))
