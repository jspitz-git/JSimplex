"""Independent offline preparation review. Standard-library file checks only."""
from pathlib import Path
import hashlib,json,os,subprocess,time
N=Path(__file__).resolve().parent;R=N.parents[3];B=N.parent
P=B/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION';E=B/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT';K=B/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION';A=B/'NATIVE-PIVOT-INTEGRATION-COMPILE-ANALYSIS'
checks={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def verify(z,mapping={}):return all(sha(mapping.get(str(path(p)),path(p)))==h for p,h in z['sha256'].items())
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
m=rd(N/'preparation-pins.json');required=rd(N/'required-paths.json')['paths']
ck('exact1656_preparation_membership',len(m['sha256'])==1656 and len(required)==len(set(required))==1656 and set(required)==set(m['sha256']))
ck('all1656_readtime_hashes',verify(m))
ck('required_local_inputs',all(str(N/n) in m['sha256'] for n in ('REPORT.md','prepare-check.py','prepare-checks.json','required-paths.json','environment.json','host.json','prepare-host.json','authorization.json','source-map.json','control.py','common.py','guard.py','seal.py','launch.py','audit.py','supervisor.py','oracle.py','loaded-paths.json','controls-baseline.json','STATUS.md.before-180','roadmap.md.before-180')))
ck('source_analysis_inputs',all(str(p) in m['sha256'] for p in A.iterdir() if p.is_file()))
s=rd(N/'source-map.json');expected={'guard.py','supervisor.py','seal.py','launch.py','audit.py','oracle.py','loaded-paths.json','controls-baseline.json'}
ck('exact_eight_infrastructure_copies',set(s['byte_identical'])==expected and all(sha(N/n)==h==sha(E/n) for n,h in s['byte_identical'].items()))
ck('only_common_HEAD_delta',(N/'common.py').read_text()==(E/'common.py').read_text().replace('5fd40966abc84be5bb88a789853273b41f754717','e649eb18798611c0a46ca3ef5e12b1416acc2b40'))
# Independently reconstruct the allowed control delta, including exact predecessor addition.
old=(E/'control.py').read_text();new=(N/'control.py').read_text()
base=old.replace('native-pivot-integration-env1/integration','native-pivot-integration-180/integration').replace('seconds=60,','seconds=180,').replace("D/'STATUS.md.before-environment'","D.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/STATUS.md.before-environment'").replace("D/'roadmap.md.before-environment'","D.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/roadmap.md.before-environment'")
start=new.index(" K=D.parent/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION'");end=new.index(' return sorted(files)',start)
ck('only_reviewed_control_delta',new[:start]+new[end:]==base)
ck('new_limit_and_unique_route',s['old_seconds']==60 and s['new_seconds']==180 and s['inner_seconds']==172 and "seconds=180" in new and "seconds=cfg['seconds']-8" in new)
ck('environment_exact_predecessor',rd(N/'environment.json')==rd(E/'environment.json'))
ck('environment_current',all(os.environ.get(k)==v for k,v in rd(N/'environment.json').items()))
ck('no_attempt_or_stage',not (N/'runs').exists() and not (R/'.superpowers/native-pivot-integration-180').exists())
pm=rd(P/'preparation-pins.json');pr=rd(P/'review-final.json')
ck('original_driver_review',pr['accepted'] is True and pr['findings']==[] and pr['scope']=='offline preparation' and pr['pins_sha256']==sha(P/'preparation-pins.json') and set(pr['sha256'])==set(pm['sha256'])|{str(P/'preparation-pins.json')} and verify(pr) and verify(pm))
ck('driver_supplemental',all(sha(path(p))==h for p,h in pr['evidence_sha256'].items()))
status=str(R/'diagnostics/simplex-core-architecture/STATUS.md');road=str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')
for root,mapping,label in [(P,{status:E/'STATUS.md.before-environment',road:E/'roadmap.md.before-environment'},'driver'),(K,{status:N/'STATUS.md.before-180',road:N/'roadmap.md.before-180'},'prior_failed')]:
 for name in ('closure.json','publication.json'):
  z=rd(root/name);ck(label+'_'+name,z['all_passed'] is True and verify(z,mapping))
  ck(label+'_membership_'+name,str(root/name) in m['sha256'] and all(str(mapping.get(str(path(p)),path(p))) in m['sha256'] for p in z['sha256']))
kr=rd(K/'result-review.json');ar=rd(E/'runs/integration/audit.json')
ck('failed_consumed_predecessor',kr['accepted'] is True and kr['qualification_accepted'] is False and kr['findings']==[] and kr['scope']=='diagnostic result' and kr['attempt']=='FAILED/CONSUMED' and ar['all_passed'] is False and ar['result']=={})
ck('failed_result_bindings',set(kr['sha256'])==set(ar['sha256'])|{str(E/'runs/integration/audit.json')} and verify(kr) and verify(ar) and kr['audit_sha256']==sha(E/'runs/integration/audit.json'))
ck('failed_result_supplemental',all(sha(path(p))==h for p,h in kr['evidence_sha256'].items()))
ck('predecessor_required_membership',all(str(path(p)) in m['sha256'] for z in (pm,pr,kr,ar) for p in z['sha256']) and all(str(path(p)) in m['sha256'] for z in (pr,kr) for p in z['evidence_sha256']))
groups=rd(K/'closure-host.json')['groups'];ck('218_groups_extension',len(groups)==len(set(groups))==218 and set(rd(P/'closure-host.json')['groups'])<set(groups) and all(not rd(x/'closure-host.json')['matches'] for x in (P,K)) and set(rd(N/'host.json')['groups'])==set(rd(N/'prepare-host.json')['groups'])==set(groups))
actual=rd(E/'actual-baseline.json');ck('520_actual_baseline',len(actual['sha256'])==520 and verify(actual))
overlay=rd(P/'overlay-manifest.json')['candidate'];ck('76_source_overlay',len(overlay)==76 and len({e['destination'] for e in overlay})==76 and all(sha(e['source'])==e['sha256'] and str(path(e['source'])) in m['sha256'] for e in overlay))
ck('original_driver_files',all(str(P/n) in m['sha256'] for n in ('driver.jl','probe.jl','recorder.jl','observed-tests.jl','overlay-manifest.json')))
t=(P/'observed-tests.jl').read_text();ck('unchanged_solver_deadline_and_cases','time_limit=5.0, iteration_limit=100' in t and '(:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)' in t and '(:default,:threshold_one)' in t and t.count('public_case(mode,symbol)')==1 and t.count('recovery_case()')==2)
o=(N/'oracle.py').read_text();ck('strict_original_oracle',all(x in o for x in ("assertions=162,public_solves=8,recovery_trials=1","group(recovery,'Native pivot policy private recovery',114,0)","c['status']=='OPTIMAL'","[514,512,32770,32774]","c['point']==['4000000000000000','4000000000000000']","c['objective']=='c024000000000000'")))
log=(E/'runs/integration/output/run.log').read_text();ck('JIT_stack_source',all(x in log for x in ('signal 15','MemoryDependenceResults','GVNPass','jl_compile_codeinst_now','jl_compile_method_internal','ijl_apply_generic','public_case','observed-tests.jl:20','Allocations: 220232274','GC: 37')) and t.splitlines()[19].strip()=='result = solve(problem; options)')
ck('old_raw_absent',not (E/'runs/integration/output/raw.toml').exists())
oldstage=R/'.superpowers/native-pivot-integration-env1/integration';opts=(oldstage/'src/options.jl').read_text();sol=(oldstage/'src/solver.jl').read_text()
ck('policy_symbol_not_type_parameter','struct SolverOptions{T<:Real,M,R}' in opts and 'native_pivot_policy::Symbol' in opts)
ck('solver_clock_and_check','start_ns = time_ns()' in sol and 'SolveContext(start_ns, typed_options.time_limit' in sol and 'time_limit_reached(context)' in sol)
report=(A/'REPORT.md').read_text();ck('analysis_limits_explicit',all(x in report for x in ('not the exact compiled method','specific active manager/policy','not a measured specialization count','compilation before clock creation is outside it','compilation after clock creation can consume it','plausible contributor, not proven','cannot be attributed to solver kernels')))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();c=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or c.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),comm=c,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
head=git('rev-parse','HEAD');master=git('rev-parse','master');ck('fresh_host',not matches and boot==rd(N/'host.json')['boot_id'] and head=='e649eb18798611c0a46ca3ef5e12b1416acc2b40' and master=='6f68e24e8ddac42b948da8fcc2d636c010751194')
ck('tracked_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
save(N/'review-host.json',dict(time=time.time(),head=head,master=master,boot_id=boot,groups=groups,matches=matches,inaccessible_exe_pids=unreadable,scope='stat/comm/readable exe scan; inaccessible executable links remain a visibility limitation'))
save(N/'review-checks.json',dict(all_passed=all(checks.values()),checks=checks,pins_count=len(m['sha256']),scope='Independent standard-library offline checks; no historical script imports/execution, Julia, compiler, cache probe, stage or launch'))
print(json.dumps(dict(all_passed=all(checks.values()),checks=len(checks),pins=len(m['sha256']))))
