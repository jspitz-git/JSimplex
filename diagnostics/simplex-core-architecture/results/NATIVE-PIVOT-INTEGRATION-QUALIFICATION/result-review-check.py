"""Fresh independent preservation review. Standard-library reads only; no historical code execution."""
from pathlib import Path
import json, hashlib, os, subprocess, time
K=Path(__file__).resolve().parent; R=K.parents[3]; E=K.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT'; P=K.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'; run=E/'runs/integration'; out=run/'output'
def rd(p):return json.loads(Path(p).read_text())
cache={}
def sha(p):
 p=Path(p); key=str(p)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[key]=h.hexdigest()
 return cache[key]
def bindings(z,key='sha256'):
 return all(Path(n).is_absolute() and sha(n)==s for n,s in z[key].items())
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
checks={};details={}
def check(n,v):checks[n]=bool(v)
try:
 a=rd(run/'audit.json');ad=rd(run/'admission.json');s=rd(run/'sealed.json');pins=rd(run/'launch-pins.json');inv=rd(run/'invocation.json');p=rd(out/'process.json');cur=rd(out/'current.json');cfg=rd(run/'config.json');sup=inv['supervisor'];post=rd(run/'posthost.json');th=rd(K/'timeout-host.json');tc=rd(K/'timeout-postcheck.json')
 check('65_original_audit_bindings',len(a['sha256'])==65 and bindings(a))
 check('original_failure_preserved',a['all_passed'] is False and a['error']=="RuntimeError('Exact output membership')" and a['result']=={})
 check('exact_five_output_files_no_raw',{x.name for x in out.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log'} and all(x.is_file() for x in out.iterdir()) and not (out/'raw.toml').exists())
 check('1644_admission_exact_bindings',ad['accepted'] is True and ad['findings']==[] and ad['scope']=='exact-stage admission' and ad['phase']=='integration' and ad['pins_sha256']==sha(run/'sealed.json') and len(ad['sha256'])==1644 and set(ad['sha256'])==set(s['inventory'])|{str(run/'sealed.json')} and bindings(ad) and bindings(ad,'evidence_sha256'))
 ac=rd(K/'admission-checks.json');check('admitted_53_checks',ac['all_passed'] is True and len(ac['checks'])==53 and all(ac['checks'].values()))
 for label,z,count in [('seal',s,1643),('launch',pins,1646)]:
  check(label+'_exact_inventory',len(z['inventory'])==count and set(z['files'])==set(z['inventory']) and len(z['files'])==count)
  check(label+'_all_hashes_and_resolutions',all(Path(n).is_absolute() and sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in z['inventory'].items()))
 check('launch_additions_and_output_identity',set(pins['inventory'])==set(s['inventory'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']} and all(pins['inventory'][n]==v for n,v in s['inventory'].items()) and rd(out/'pins.json')==pins and p['pins_unchanged'] is True)
 check('exact_command_all_records',s['config']==cfg and all(z['command']==cfg['command'] for z in [inv,p,cur,rd(run/'reservation.json')]) and cfg['seconds']==60 and cfg['expected_exit']==0 and cfg['phase']=='integration')
 expected_guard=[inv['python'],'-B',str(E/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','52','--deadline',str(inv['monotonic_start']+52),'--expected-exit','0','--',*cfg['command']]
 check('exact_absolute_guard_deadline',inv['guard_command']==expected_guard)
 check('reservation_and_invocation_linkage',rd(run/'reservation.json')==dict(one_attempt=True,phase='integration',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=60) and inv['pins_sha256']==p['pins_sha256']==cur['pins_sha256']==sha(run/'launch-pins.json') and inv['review_sha256']==sha(run/'admission.json') and inv['reservation_sha256']==sha(run/'reservation.json'))
 check('recorded_identities_consistent',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'] and p['runner']['command']==' '.join(expected_guard)+' ' and p['child']['command']==' '.join(cfg['command'])+' ')
 check('exact_boot_pid_start_ticks',all(p[role]['boot_id']==s['boot_id'] and p[role]['pid']==p[role]['pgid']==p[role]['sid']==pid and p[role]['start_ticks']==ticks for role,pid,ticks in [('runner',283004,17890497),('child',283006,17890547)]))
 check('failed_timeout_with_bounded_outer_cleanup',p['reason']=='wall_time' and p['returncode']==-9 and sup['soft_timeout'] is True and sup['hard_timeout'] is False and sup['guard_term'] is True and sup['accepted'] is False and 'cleanup_error' not in sup and 0<=sup['elapsed_seconds']<=inv['elapsed_seconds']<=60)
 check('guard_elapsed_and_termination_interval',p['elapsed_including_launch']==52.504130901012104 and inv['elapsed_seconds']==56.128167785005644 and p['ended']-p['started']>p['elapsed_including_launch'])
 check('all_saved_host_boot_refs',all(all(rd(f)[key]==s[key] for key in ['head','master','boot_id']) and not rd(f)['matches'] for f in [K/'host.json',run/'host.json',run/'prehost.json',run/'posthost.json',K/'timeout-host.json']))
 check('saved_host_group_closure',len(s['groups'])==216 and set(post['groups'])==set(th['groups'])==set(s['groups'])|{283004,283006} and len(th['groups'])==218)
 check('saved_chronology',rd(K/'host.json')['time']<=ac['details']['fresh_host']['time']<=rd(run/'prehost.json')['time']<=p['started']<p['ended']<=post['time']<=th['time'])
 groups=set(th['groups']);matches=[];unreadable=[];seen=0
 for q in Path('/proc').glob('[0-9]*'):
  try:
   fields=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe='';seen+=1
   try:exe=os.readlink(q/'exe')
   except PermissionError:unreadable.append(int(q.name))
   except FileNotFoundError:pass
   if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
    matches.append(dict(pid=int(q.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),comm=comm,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
 fresh=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,processes_seen=seen,scope='All readable stat/comm/exe; inaccessible system executable links remain a visibility limit')
 details['fresh_host']=fresh
 check('fresh_218_groups_and_sessions_no_Julia',not matches and fresh['boot_id']==s['boot_id'])
 def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
 check('current_refs_clean',git('rev-parse','HEAD')==s['head']=='052523788b14c84982e4b770804d3b32e5a47a9b' and git('rev-parse','master')==s['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and not git('diff','--name-only') and not git('diff','--cached','--name-only'))
 resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
 check('53_samples_and_terminal_guards',len(resources)==53 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]) and min(x['available_kib'] for x in resources)==21169564 and max(x['swap_used_kib'] for x in resources)==0 and p['child_maxrss_kib']==1887136)
 check('preserved_23_timeout_checks_and_hashes',tc['all_passed'] is True and len(tc['checks'])==23 and all(tc['checks'].values()) and bindings(tc) and tc['summary']['qualification_accepted'] is False and tc['summary']['attempt_consumed'] is True)
 check('preflight_bindings',rd(K/'preflight.json')['all_passed'] is True and bindings(rd(K/'preflight.json')))
 for origin in [E,P]:
  z=rd(origin/'actual-baseline.json');check(origin.name+'_520_actual_unchanged',len(z['sha256'])==520 and all(sha(R/n)==h for n,h in z['sha256'].items()))
  m=rd(origin/'preparation-pins.json');review=rd(origin/'review-final.json')
  check(origin.name+'_preparation_review_unchanged',bindings(m) and review['accepted'] is True and review['findings']==[] and review['pins_sha256']==sha(origin/'preparation-pins.json') and set(review['sha256'])==set(m['sha256'])|{str(origin/'preparation-pins.json')} and bindings(review) and bindings(review,'evidence_sha256'))
 stage=Path(cfg['stage']);manifest=rd(P/'overlay-manifest.json')['candidate'];members={str(x.relative_to(stage)) for x in stage.rglob('*') if x.is_file()}
 check('stage_76_exact_unchanged_candidate',len(manifest)==76 and members=={x['destination'] for x in manifest} and not any(x.is_symlink() for x in stage.rglob('*')) and all(sha(stage/x['destination'])==x['sha256']==sha(x['source']) for x in manifest))
 env=rd(E/'environment.json');check('same_actual_nine_key_environment',len(env)==9 and all(os.environ.get(n)==v for n,v in env.items()))
 check('before_publication_texts_unchanged',sha(R/'diagnostics/simplex-core-architecture/STATUS.md')==sha(K/'STATUS.md.before-integration-run') and sha(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')==sha(K/'roadmap.md.before-integration-run'))
 log=(out/'run.log').read_text();tests=(P/'observed-tests.jl').read_text().splitlines()
 check('interruption_stack_is_public_solve_compilation','signal 15' in log and 'GVNPass' in log and 'jl_compile_codeinst' in log and 'public_case at '+str(P/'observed-tests.jl')+':20' in log and tests[19].strip()=='result = solve(problem; options)')
 check('original_postcheck_output_absent',not (K/'postcheck.json').exists() and not (K/'post-exit-host.json').exists())
 details.update(audit_bindings=65,review_bindings=66,launch_pins=1646,seal_pins=1643,stage_files=76,actual_baseline_files=520,assertion_results='UNKNOWN',selected_work_counts='UNKNOWN',qualification_accepted=False,attempt_consumed=True,inner_elapsed_before_cleanup=p['elapsed_including_launch'],outer_elapsed_through_termination=inv['elapsed_seconds'],runtime_signal_summary='Allocations: 220232274; GC: 37. Process aggregate including runtime/compiler, not selected solver/native allocation evidence.')
except Exception as exc:
 check('review_completed_without_exception',False);details['exception']=repr(exc)
result=dict(all_passed=all(checks.values()),checks=checks,details=details,scope='Fresh read-only diagnostic preservation checks, not numerical acceptance')
save(K/'result-review-checks.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[n for n,v in checks.items() if not v],exception=details.get('exception'))))
