"""Fresh independent exact-stage admission. No imported historical controls or Julia."""
from pathlib import Path
import hashlib,json,os,subprocess,time
T=Path(__file__).resolve().parent;N=T.parent/'NATIVE-PIVOT-INTEGRATION-180-PREPARATION';R=N.parents[3];run=N/'runs/integration';P=N.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION';E=N.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT';K=N.parent/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION'
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
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
s=rd(run/'sealed.json');cfg=s['config'];stage=R/'.superpowers/native-pivot-integration-180/integration';mp=N/'preparation-pins.json';m=rd(mp);rv=rd(N/'review-final.json');h=rd(run/'host.json')
ck('phase_config',s['phase']=='integration' and cfg==rd(run/'config.json') and cfg==dict(phase='integration',seconds=180,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(run/'output'),command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(P/'driver.jl'),str(run/'output'),'integration',str(stage)]))
ck('offline_acceptance_bound',rv['accepted'] is True and rv['findings']==[] and rv['scope']=='offline preparation' and rv['pins_sha256']==sha(mp) and set(rv['sha256'])==set(m['sha256'])|{str(mp)})
ck('preparation_readtime_hashes',all(sha(p)==v for p,v in rv['sha256'].items()) and set(m['sha256'])==set(rd(N/'required-paths.json')['paths']))
ck('offline_supplemental_readtime_hashes',all(sha(p)==v for p,v in rv['evidence_sha256'].items()))
overlay=rd(P/'overlay-manifest.json')['candidate'];expected_stage={str(stage/e['destination']) for e in overlay}
ck('stage76_regular_no_symlinks',len(overlay)==76 and stage.is_dir() and not stage.is_symlink() and not any(p.is_symlink() for p in stage.rglob('*')) and {str(p) for p in stage.rglob('*') if p.is_file()}==expected_stage)
ck('stage76_exact_source_bytes',all(sha(stage/e['destination'])==sha(e['source'])==e['sha256'] for e in overlay))
expected=set(m['sha256'])|{str(mp),str(N/'review-final.json'),str(run/'host.json'),str(run/'config.json'),str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}|expected_stage
ck('sealed_exact1738_membership',len(s['files'])==len(set(s['files']))==1738 and set(s['files'])==set(s['inventory'])==expected and s['trees']==[str(stage)] and s['inputs']==[])
ck('all1738_resolved_hashes',all(v==dict(resolved=str(Path(p).resolve(strict=True)),sha256=sha(p)) for p,v in s['inventory'].items()))
ck('prep_seal_same_hashes',all(s['inventory'][p]['sha256']==v for p,v in m['sha256'].items()))
ck('unconsumed_new_attempt',{p.name for p in run.iterdir()}=={'sealed.json','host.json','config.json'} and not (run/'output').exists() and not (run/'reservation.json').exists())
prior=rd(K/'result-review.json');oldres=rd(E/'runs/integration/reservation.json');oldaudit=rd(E/'runs/integration/audit.json')
ck('old_allowance_consumed',prior['attempt']=='FAILED/CONSUMED' and prior['qualification_accepted'] is False and oldaudit['all_passed'] is False and oldres['one_attempt'] is True and oldres['max_seconds']==60)
ck('old_failure_still_immutable',all(sha(p)==v for p,v in prior['sha256'].items()) and all(sha(p)==v for p,v in prior['evidence_sha256'].items()))
ck('environment_exact_current',all(os.environ.get(k)==v for k,v in rd(N/'environment.json').items()))
ck('inner172_reserve8',"seconds=cfg['seconds']-8" in (N/'control.py').read_text() and "'--seconds',str(seconds),'--deadline',str(started+seconds)" in (N/'control.py').read_text() and cfg['seconds']-8==172)
ck('original_guard_supervisor_audit_oracle',all(sha(N/n)==sha(E/n) for n in ('guard.py','supervisor.py','audit.py','oracle.py','launch.py')))
ck('solver5_unchanged','time_limit=5.0, iteration_limit=100' in (P/'observed-tests.jl').read_text())
groups=s['groups'];ck('218_process_history',len(groups)==len(set(groups))==218 and groups==h['groups']==rd(K/'closure-host.json')['groups'] and not h['matches'])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();head=git('rev-parse','HEAD');master=git('rev-parse','master');branch=git('branch','--show-current')
ck('exact_refs_boot',head==s['head']==h['head']=='e649eb18798611c0a46ca3ef5e12b1416acc2b40' and master==s['master']==h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and boot==s['boot_id']==h['boot_id'] and branch=='codex/simplex-core-architecture')
ck('no_tracked_drift',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh_no_julia_or_old_groups',not matches)
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};resources=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
ck('current_resource_headroom',resources['available_kib']>=6*1024**2 and resources['swap_used_kib']<=1024**2)
save(T/'admission-host.json',dict(time=time.time(),boot_id=boot,head=head,master=master,branch=branch,groups=groups,matches=matches,inaccessible_exe_pids=unreadable,resources=resources,scope='Fresh stat/comm/readable executable scan; inaccessible executable links remain visibility limitation'))
save(T/'admission-checks.json',dict(all_passed=all(checks.values()),checks=checks,sealed_files=len(s['files']),staged_files=len(overlay),seal_sha256=sha(run/'sealed.json'),scope='Fresh independent exact-stage read-time verification; no Julia or old auditor imports/execution'))
print(json.dumps(dict(all_passed=all(checks.values()),checks=len(checks),sealed_files=len(s['files']),resources=resources)))
