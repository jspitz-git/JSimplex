from pathlib import Path
import ast,copy,hashlib,json,math,os,re,statistics,struct,subprocess,sys,tomllib,traceback,types
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/cost-1/candidate-cost';F=R.parent/'reference-cost';D=W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30';T=Path('/tmp/devex-candidate-cost-run-20261030');OUT=Path('/tmp/devex-candidate-cost-numerical-admission-check-result.json')
checks={};bindings={};counts={};details={}
def check(k,v):
 assert type(v) is bool,(k,'not bool');checks[k]=v
 if not v:raise AssertionError(k)
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bind(p):
 p=str(Path(p).absolute());h=sha(p);bindings[p]=h;return h
def read(p):bind(p);return json.loads(Path(p).read_text())
def bound_record(label,a):
 for i,(p,h) in enumerate(a['bindings'].items()):check(f'{label}.hash.{i}',bind(p)==h)
 counts[label]=len(a['bindings'])
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split();return dict(pid=int(pid),pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def bits(v,t):return struct.pack('>f' if t=='Float32' else '>d',v).hex()
def stats(k,s,measured=False):
 for n in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):check(k+'.'+n,type(s[n]) in (int,float) and math.isfinite(s[n]) and s[n]>=0)
 for n in ('bytes','events'):check(k+'.'+n,type(s[n]) is int and s[n]>=0)
 if measured:check(k+'.zero_baseline',all(s[n]==0 for n in ('bytes','events','gc_seconds','compile_seconds','recompile_seconds')))
try:
 seal=read(R/'seal.json');pins=read(R/'pins.json');fs=read(F/'seal.json');fp=read(F/'pins.json');fa=read(F/'attempt.json');ad=read(fa['admission_path']);closed=read(F/'closed.json');audit=read(F/'audit.json');review=read(D/'review-final.json')
 check('concrete_seal_sha',sha(R/'seal.json')=='671caa90ed4bf4c5222fad3e35ae295792dfea5cbdf93a4f4ad395339a3934d1');check('concrete_pins_sha',sha(R/'pins.json')==seal['pins_sha256']);check('fresh_unused_candidate',set(p.name for p in R.iterdir())=={'seal.json','pins.json'})
 for label,a in [('reference_admission',ad),('reference_result_review',review),('reference_audit',audit),('reference_closed',closed)]:bound_record(label,a)
 check('reference_admission_801',len(ad['bindings'])==801);check('reference_result_934',len(review['bindings'])==934)
 check('reference_review_scope',review['accepted'] is True and review['runtime_accepted'] is True and review['cost_qualified'] is False and review['production_admission'] is False)
 check('reference_admission_schema',ad['accepted'] is True and ad['scope']=='numerical_admission' and ad['phase']=='reference-cost' and ad['head']==fs['head'] and ad['command']==fs['command'] and ad['seal_sha256']==sha(F/'seal.json') and ad['pins_sha256']==sha(F/'pins.json')==fs['pins_sha256'] and ad['review_report_sha256']==bind(ad['review_report']) and bool(ad['checks']) and all(v is True for v in ad['checks'].values()))
 check('reference_attempt_bindings',fa['admission_sha256']==sha(fa['admission_path']) and fa['seal_sha256']==sha(F/'seal.json'))
 actual={str(p) for p in F.rglob('*') if p.is_file()};external={fa['admission_path'],ad['review_report']}
 check('reference_closed_exact_membership',set(closed['bindings'])==(actual-{str(F/'closed.json')})|external);check('reference_audit_exact_membership',set(audit['bindings'])==(actual-{str(F/'closed.json'),str(F/'audit.json')})|external);check('reference_21_runtime',len(actual)==21)
 check('reference_closed_acceptance',closed['accepted'] is True and closed['phase']=='reference-cost' and closed['head']==fs['head'] and closed['host']['conflicts']==[] and not closed['host']['still_active_current_launcher']);check('reference_audit_acceptance',audit['accepted'] is True and audit['test_summary']=={'Pass':272,'Total':272})
 pubdirs=[O,W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30',W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30',W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30',W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30',W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30',P]
 published=set()
 for folder in pubdirs:
  pub=read(folder/'publication.json');check('published.'+folder.parent.name,pub['accepted'] is True);published.update(str(W/n) for n in pub['expected_names'])
 check('published_560',len(published)==560)
 for i,p in enumerate(sorted(published)):
  check('committed_blob.'+str(i),Path(p).is_file() and not Path(p).is_symlink() and git('hash-object',p)==git('rev-parse','HEAD:'+str(Path(p).relative_to(W))))
 runtime=Path(seal['command'][0]).parents[1];required=published|{seal['guard_python'],seal['command'][0],str(runtime/'lib/libjulia.so.1.13.0'),str(runtime/'lib/julia/sys.so'),str(runtime/'lib/julia/libjulia-internal.so.1.13.0'),str(runtime/'share/julia/base/timing.jl')}
 for label,q,expected in [('ref',fp,required),('candidate',pins,required|actual|external)]:
  check(label+'.exact_inventory',set(q['inventory'])==expected and set(q['files'])==expected and len(q['files'])==len(expected) and q['trees']==q['inputs']==[])
  for i,(p,v) in enumerate(q['inventory'].items()):check(label+'.pin.'+str(i),bind(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'])
  counts[label+'_pins']=len(q['inventory'])
 check('566_589_pins',len(fp['inventory'])==566 and len(pins['inventory'])==589)
 for p in [D/'publication.json',D/'closure.json']:
  a=read(p)
  if 'bindings' in a:bound_record(p.name,a)
 # Historical accepted and rejected outcomes retained, including all original evidence already bound above.
 hist=[]
 for folder,stage,accepted in [(pubdirs[1],'red',True),(pubdirs[2],'green',False),(pubdirs[5],'green2',True)]:
  done=read(folder/stage/'completion.json');check('old_outcome.'+stage,done['supervisor_accepted'] is accepted);hist.append(done['elapsed_inclusive_seconds'])
 check('failed_green_not_reclassified',not (pubdirs[2]/'green/audit.json').exists() and read(pubdirs[2]/'green/supervisor.json')['accepted'] is False)
 done=read(F/'completion.json');sup=read(F/'supervisor.json');proc=read(F/'guard/process.json')
 check('reference_full_elapsed',done['elapsed_inclusive_seconds']==37.39421487902291 and done['total_inclusive_seconds']==sum(hist)+done['elapsed_inclusive_seconds']==1070.9948121299385 and done['supervisor_accepted'] is True)
 check('candidate_cumulative_budget',seal['used_seconds']==done['total_inclusive_seconds'] and seal['remaining_seconds']==1800-seal['used_seconds']==729.0051878700615 and seal['shared_total_seconds']==1800 and seal['remaining_seconds']>20)
 check('previous_facts',[(a['accepted'],a['elapsed']) for a in seal['previous']]==list(zip([True,False,True,True],hist+[done['elapsed_inclusive_seconds']])));
 for fact,folder,stage in zip(seal['previous'],pubdirs[1:3]+[pubdirs[5],F.parent],['red','green','green2','reference-cost']):check('previous_completion.'+stage,fact['completion_sha256']==sha(folder/stage/'completion.json'))
 check('previous_reference_audit_closed',seal['previous'][-1]['audit_sha256']==sha(F/'audit.json') and seal['previous'][-1]['closed_sha256']==sha(F/'closed.json'))
 check('reference_process_success',type(proc['returncode']) is int and proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==fs['command'] and proc['pins_sha256']==sha(F/'pins.json') and read(F/'guard/pins.json')==fp)
 check('reference_supervisor_success',sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0 and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')) and 'cleanup_error' not in sup and sup['elapsed_seconds']<=done['elapsed_inclusive_seconds'])
 gate=read(F/'guard/gate.json');current=read(F/'guard/current.json');permit=read(F/'guard/permit.json')
 check('reference_gate',gate['identity']==proc['child'] and gate['parent']==proc['runner'] and gate['parent_death_signal']==9 and gate['command']==fs['command'] and gate['current_sha256']==sha(F/'guard/current.json') and gate['permit_sha256']==sha(F/'guard/permit.json') and permit==dict(current_sha256=sha(F/'guard/current.json'),command=fs['command']) and current['child']==proc['child'] and current['runner']==proc['runner'] and current['command']==fs['command'])
 inv=read(F/'invocation.json');check('reference_invocation',inv['environment']==fs['environment'] and inv['cwd']==str(P) and inv['command']==[fs['guard_python'],'-B',str(P/'guard/guard_reviewed.py'),'run',str(F/'pins.json'),str(F/'guard'),'--expected-exit','0','--seconds',str(1800-fs['used_seconds']-12),'--deadline',str(fa['started_monotonic']+1800-fs['used_seconds']-12),'--',*fs['command']])
 log=(F/'guard/run.log').read_text();check('ordinary_reference_272',re.search(r'Test Summary:\s*\|\s*Pass\s+Total\s+Time\nTASK4_COST\s*\|\s*272\s+272\s+',log) is not None and log.splitlines().count('TASK4_COST_COMPLETED reference')==1 and log.count('TASK4_COST_COMPLETED ')==1 and not any(x in log.lower() for x in ('error:','error during test','test failed at','undefvarerror','world age','segmentation fault')))
 reference=tomllib.loads((F/'result.toml').read_text());check('reference_side_cases',reference['side']=='reference' and len(reference['cases'])==8)
 for z,(q,(ty,layout,bad)) in enumerate(zip(reference['cases'],[(ty,layout,bad) for ty in ['Float32','Float64'] for layout in ['sparse','dense'] for bad in [False,True]])):
  k='case.'+str(z);check(k+'.keys',(q['type'],q['layout'],q['unreliable'])==(ty,layout,bad) and type(q['unreliable']) is bool and type(q['dimension']) is int and q['dimension']==64)
  matrix=[bits(64 if i==j else ((-1 if (i+j)%2==0 else 1)*(1+(i+2*j)%5))/64 if layout=='dense' or abs(i-j)==1 else 0,ty) for j in range(1,65) for i in range(1,65)]
  check(k+'.matrix_policy',q['matrix_bits']==matrix and type(q['nnz']) is int and q['nnz']==(190 if layout=='sparse' else 4096) and q['policy_solve_tolerance_bits']==('38000000' if ty=='Float32' else '3d30000000000000'))
  check(k+'.schedule',len(q['warm'])==3 and len(q['samples'])==7);check(k+'.work',type(q['solve_entries_total']) is int and type(q['stop_entries_total']) is int and q['solve_entries_total']==q['stop_entries_total']==(10 if bad else 0));check(k+'.retained',type(q['retained_julia_bytes']) is int and q['retained_julia_bytes']>=0)
  stats(k+'.prep',q['preparation']);stats(k+'.gc',q['post_warm_gc'])
  for i,s in enumerate(q['warm']):stats(k+'.warm.'+str(i),s)
  for i,s in enumerate(q['samples'],1):
   sk=k+'.sample.'+str(i);stats(sk,s,True);check(sk+'.types_work',type(s['index']) is int and s['index']==i and type(s['solve_entries']) is int and type(s['stop_entries']) is int and s['solve_entries']==s['stop_entries']==int(bad));check(sk+'.quality_owner',s['finite'] is True and s['reliable'] is (not bad) and s['owners_preserved'] is True and s['absolute_bits']==bits(32 if bad else 0,ty) and s['relative_bits']==bits(1/3 if bad else 0,ty));check(sk+'.input_output',s['rhs_bits']==matrix[::64] and s['point_bits']==[bits(.5 if bad else 1,ty)]+[bits(0,ty)]*63)
 # Only pure new-preparation cost definitions are evaluated; no imported submitted mains.
 ns={};exec(compile((P/'cost_checks.py').read_text(),str(P/'cost_checks.py'),'exec'),ns)
 can=copy.deepcopy(reference);can['side']='candidate';check('pure_equal_pair_gate',ns['comparison_data'](reference,can)['accepted'] is True)
 for z in range(8):
  for field in ('bytes','events','retained_julia_bytes'):
   altered=copy.deepcopy(can)
   if field=='retained_julia_bytes':altered['cases'][z][field]+=1
   else:
    for sample in altered['cases'][z]['samples']:sample[field]+=1
   comparison=ns['comparison_data'](reference,altered);check(f'strict_gate.{z}.{field}',comparison['accepted'] is False and len(comparison['cases'])==8 and any(v is False for v in comparison['cases'][z]['gates'].values()))
 for field,value in [('finite',1),('owners_preserved',1),('solve_entries',True),('bytes',False),('compile_seconds',1),('absolute_bits','00000000'),('rhs_bits',[])]:
  altered=copy.deepcopy(can);altered['cases'][1]['samples'][0][field]=value
  try:ns['comparison_data'](reference,altered);rejected=False
  except (ValueError,KeyError,TypeError):rejected=True
  check('typed_pair_reject.'+field,rejected)
 # Full original/candidate project equivalence to the accepted GREEN2 project.
 green=pubdirs[3]/'prepared/overlays/candidate';rp=O/'overlays/reference';cp=O/'overlays/candidate';names=lambda p:{str(x.relative_to(p)) for x in p.rglob('*') if x.is_file()}
 check('project_membership74',names(rp)==names(cp)==names(green) and len(names(cp))==74);different=[]
 for i,n in enumerate(sorted(names(cp))):
  check('green2_project.'+str(i),bind(cp/n)==bind(green/n))
  if sha(cp/n)!=bind(rp/n):different.append(n)
  if n.startswith('src/'):check('reference_master_source.'+str(i),git('hash-object',str(rp/n))==git('rev-parse','master:'+n))
 check('three_source_differences',different==['src/simplex_numerics.jl','src/simplex_pivot.jl','src/simplex_recovery.jl'])
 contract=read(P/'contract.json');check('driver_schedule',sha(O/'cost.jl')==contract['driver_sha256'] and sha(O/'tests/reference.jl')==contract['reference_sha256'] and contract['cost']==read(O/'contract.json')['cost'])
 expected_cmd=list(fs['command']);expected_cmd[-1]='candidate';expected_cmd[-3]='--project='+str(cp)
 check('candidate_exact_command',seal['command']==expected_cmd and seal['phase']=='candidate-cost' and type(seal['expected_exit']) is int and seal['expected_exit']==0)
 env=dict(fs['environment']);env['TASK4_OUTPUT']=str(R/'result.toml');check('candidate_exact_environment',seal['environment']==env and not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'));check('guard_interpreter',seal['guard_python']=='/usr/bin/python3' and str(Path(sys.executable).absolute())==seal['guard_python'])
 for i,p in enumerate(env['JULIA_DEPOT_PATH'].split(':')):check('depot.'+str(i),Path(p).is_dir())
 # Independent full current host census, includes both PGID and SID for every owner.
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();old=read(P/'host.json')['host'];groups=set(old['checked_groups']) if boot==old['boot_id'] else set();owners=[fa['runner'],proc['runner'],proc['child']]
 for a in owners:
  check('owner_fields.'+str(a['pid']),a['boot_id']==boot and type(a['start_ticks']) is int and a['start_ticks']>0 and type(a['command']) is str and bool(a['command']));groups.update((a['pgid'],a['sid']))
  try:now=identity(a['pid'])
  except (FileNotFoundError,ProcessLookupError):now=None
  check('old_owner_absent.'+str(a['pid']),now is None or (now['boot_id'],now['start_ticks'])!=(a['boot_id'],a['start_ticks']))
 check('739_full_group_session_membership',len(groups)==739 and groups==set(closed['host']['checked_groups'])==set(seal['preflight']['checked_groups']))
 conflicts=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=identity(p.name);comm=(p/'comm').read_text().strip()
   if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 check('fresh_noJulia_groups_sessions',not conflicts)
 mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);check('fresh_resource_bounds',memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2)
 samples=[json.loads(s) for s in (F/'guard/resources.jsonl').read_text().splitlines()]
 for i,s in enumerate(samples+[proc['terminal_memory']]):check('reference_resource.'+str(i),type(s['available_kib']) is int and type(s['swap_used_kib']) is int and s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2)
 refs={n:git('rev-parse',n) for n in ['HEAD','master','origin/master']};check('fresh_head_master',refs['HEAD']==seal['head']=='14720147d8850525c0603921064dfe3ba83d3fcb' and refs['master']==refs['origin/master']==seal['master']=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b');check('tracked_source_clean',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only') and not git('diff','master','HEAD','--','src','test','Project.toml','.github'))
 remote={a.split()[1]:a.split()[0] for a in git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines()};check('remote_refs',remote=={'refs/heads/master':refs['master'],'refs/heads/codex/native-quality-finite':refs['HEAD']})
 for p in [Path(__file__),T/'preflight.py',T/'preflight.json',T/'admission-check.py',T/'postcheck.py',D/'REVIEW-FINAL.md',P/'ADMISSION-PREPARATION.md',P/'REVIEW-FINAL.md',W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md',W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md']:bind(p)
 details.update(host=dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,memory=memory,refs=refs,remote_refs=remote,owners=owners),used_seconds=seal['used_seconds'],remaining_seconds=seal['remaining_seconds'],reference_resource_samples=len(samples),reference_call_counts=dict(api=80,correction_BTRAN=40,stop=40,explicit_GC=8,measured=56,ordinary_assertions=272))
 result=dict(accepted=True,checks=checks,bindings=bindings,counts=counts,details=details)
except Exception:
 result=dict(accepted=False,checks=checks,bindings=bindings,counts=counts,details=details,error=traceback.format_exc())
with OUT.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=result['accepted'],checks=len(checks),bindings=len(bindings),counts=counts,error=result.get('error'))))
sys.exit(0 if result['accepted'] else 1)
