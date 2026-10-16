"""Fresh offline review only. No historical executable imports, Julia, or mutations outside review outputs."""
from pathlib import Path
import hashlib,json,difflib,subprocess,tomllib,time,statistics,traceback
Q=Path(__file__).resolve().parent; R=Q.parents[3]; B=Q.parent
P=B/'NATIVE-PIVOT-PREPARATION'; D=B/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'
PLAN=R/'docs/superpowers/plans/2026-10-16-native-pivot-production-integration.md'
MASTER='6f68e24e8ddac42b948da8fcc2d636c010751194'; HEAD='e20d4fd3018a778e853e6c03f1ed1f3063d69ab0'
checks={}; bindings={}; details={}
def path(p):
 p=Path(p); return p if p.is_absolute() else R/p
def read(p):
 p=path(p); b=p.read_bytes(); bindings[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]=hashlib.sha256(b).hexdigest(); return b
def digest(p): return hashlib.sha256(read(p)).hexdigest()
def js(p): return json.loads(read(p))
def txt(p): return read(p).decode()
def tom(p): return tomllib.loads(txt(p))
def check(name,value):
 checks[name]=bool(value)
 if not value: raise RuntimeError(name)
def git(*args): return subprocess.check_output(['git',*args],cwd=R).decode().strip()
def count(t,key): return t.get(key,0)+sum(count(c,key) for c in t.get('children',[]))
def clean(t): return all(count(t,k)==0 for k in ('fail','error','broken'))
def save(name,data):
 with (Q/name).open('x') as f: json.dump(data,f,indent=2); f.write('\n')
try:
 read(__file__)
 author=js(Q/'author-check.json'); source=js(Q/'source-check.json'); manifest=js(Q/'payload-manifest.json')
 check('author8_and_source9_PASS',author['all_passed'] and len(author['checks'])==8 and all(author['checks'].values()) and source['all_passed'] and len(source['checks'])==9 and all(source['checks'].values()))
 author_maps=[]
 for p,h in author['sha256'].items():
  pp=path(p)
  if pp==PLAN and digest(pp)!=h:
   pp=Q/'plan.before-review.md'; author_maps.append({'original':p,'preserved':str(pp.relative_to(R)),'sha256':h})
  check('author_binding:'+p,digest(pp)==h)
 check('author_binding_count26',len(author['sha256'])==26)
 details['author_preservation_mapping']=author_maps
 for p,h in source['sha256'].items(): check('source_binding:'+p,digest(p)==h)
 expected=['src/'+n+'.jl' for n in ['options','factorization','triangular_factorization','simplex_phase_one','simplex_precision','solver','lp_refinement_driver']]+['test/native_pivot_policy_tests.jl','test/native_pivot_integration_tests.jl','test/runtests.jl']
 check('exact10_manifest',manifest['master']==MASTER and [e['destination'] for e in manifest['files']]==expected)
 check('exact10_payload_set',sorted(str(p.relative_to(Q/'payload')) for p in (Q/'payload').rglob('*') if p.is_file())==sorted(expected))
 patch=[]; texts={}; originals={}
 for e in manifest['files']:
  name=e['destination']; new=read(e['payload']); texts[name]=new.decode()
  check('payload_qualified:'+name,digest(e['source'])==hashlib.sha256(new).hexdigest()==e['sha256'])
  if e['original_git_blob'] is not None:
   old=subprocess.check_output(['git','show',MASTER+':'+name],cwd=R)
   check('baseline_blob:'+name,git('rev-parse',MASTER+':'+name)==e['original_git_blob'] and hashlib.sha256(old).hexdigest()==e['original_sha256'] and read(name)==old)
  else:
   old=b''; check('new_test_absent:'+name,not (R/name).exists() and subprocess.run(['git','cat-file','-e',MASTER+':'+name],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0)
  originals[name]=old.decode()
  patch.extend(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+name if e['original_git_blob'] else '/dev/null',tofile='b/'+name))
 check('whole_patch_reconstructed',''.join(patch)==txt(Q/'production.patch'))
 inverse=js(P/'inverse.json'); reversed_src={n:texts[n] for n in expected[:7]}
 for edit in reversed(inverse['edits']):
  s=reversed_src[edit['file']]; check('inverse_fragment:'+str(len(checks)),edit['after'] in s); reversed_src[edit['file']]=s.replace(edit['after'],edit['before'])
 check('whole7_source_inverse',all(reversed_src[n]==originals[n] for n in expected[:7]))
 check('runtests_exact2_include_inverse',texts['test/runtests.jl'].replace('    include("native_pivot_policy_tests.jl")\n    include("native_pivot_integration_tests.jl")\n','',1)==originals['test/runtests.jl'])
 check('no_promoted_hooks',all(all(t not in s for t in ('NativePivotIntegrationProbe','Main.NP.','tests-observed','observed-factorization')) for s in texts.values()))
 baseline=js(Q/'actual-baseline.json'); check('actual513_unchanged',len(baseline)==513 and all(digest(p)==h for p,h in baseline.items()))
 check('actual_source_test_CI_project_match_master',not git('diff',MASTER,'--name-only','--','src','test','.github','Project.toml'))
 check('actual_index_clean',not git('diff','--cached','--name-only'))
 check('auxiliary_dual_source_whole_identity',read('src/dual_simplex.jl')==subprocess.check_output(['git','show',MASTER+':src/dual_simplex.jl'],cwd=R))
 # Bind exact evidence links without rehashing unrelated installed runtime inventories.
 stages=[('green2',B/'NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2',B/'NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2/result-review.json'),('cost',B/'NATIVE-PIVOT-COST-PREPARATION/runs/cost',B/'NATIVE-PIVOT-COST-PREPARATION/runs/cost/result-review.json'),('integration',B/'NATIVE-PIVOT-INTEGRATION-180-PREPARATION/runs/integration',B/'NATIVE-PIVOT-INTEGRATION-180-QUALIFICATION/result-review.json')]
 raws={}; audits={}; reviews={}
 for label,run,rp in stages:
  rev=js(rp); reviews[label]=rev; cfg=js(run/'config.json'); ap=run/'audit.json'; au=js(ap); audits[label]=au
  check('accepted_result:'+label,rev['accepted'] and au['all_passed'] and rev['sha256'][str(ap)]==digest(ap))
  pinpath=run/'launch-pins.json'; pins=js(pinpath)
  check('accepted_launch_link:'+label,rev['sha256'][str(pinpath)]==digest(pinpath))
  rawpath=run/'output/raw.toml'; raws[label]=tom(rawpath)
  check('accepted_raw_link:'+label,rev['sha256'][str(rawpath)]==digest(rawpath))
  stage=Path(cfg['stage'])
  for n in expected[:7]:
   f=stage/n; current=digest(f); check('stage_launch_binding:'+label+':'+n,pins['inventory'][str(f)]['sha256']==current)
   qualified=read(Q/'payload'/n)
   if label=='integration' and n=='src/factorization.jl':
    check('integration_observed_factor_exact',read(f)==read(D/'observed-factorization.jl'))
   else: check('stage_qualified_source:'+label+':'+n,read(f)==qualified)
  for n in ['src/dual_simplex.jl','src/simplex_recovery.jl','src/moi/attributes.jl']:
   f=stage/n
   if f.exists(): check('unmodified_support:'+label+':'+n,pins['inventory'][str(f)]['sha256']==digest(f)==digest(R/n))
  read(rp.with_suffix('.md') if rp.with_suffix('.md').exists() else rp.parent/'result-review.md')
 # Exact removal of six production observer seams and all three observed integration edits.
 seams=js(B/'NATIVE-PIVOT-INTEGRATION-PREPARATION/observer-seams.json'); observed=txt(D/'observed-factorization.jl')
 for i in reversed(seams['application_order']):
  e=seams['edits'][i]; check('observer_seam:'+str(i),observed.count(e['after'])==e['count']); observed=observed.replace(e['after'],e['before'],e['count'])
 check('whole_observer_inverse',observed==texts['src/factorization.jl'])
 ti=js(D/'test-inverse.json'); observed=txt(D/'observed-tests.jl')
 for e in reversed(ti['edits']):
  check('test_observer_seam:'+str(len(checks)),observed.count(e['after'])==1); observed=observed.replace(e['after'],e['before'],1)
 check('whole_public_test_observer_inverse',observed==texts['test/native_pivot_integration_tests.jl'])
 inv=js(B/'NATIVE-PIVOT-QUALIFICATION/test-inverse.json')['tests-observed.jl']; observed=txt(B/'NATIVE-PIVOT-QUALIFICATION/tests-observed.jl')
 check('policy_observed_bound',digest(B/'NATIVE-PIVOT-QUALIFICATION/tests-observed.jl')==inv['sha256'])
 for before,after,n in reversed(inv['edits']):
  check('policy_observer_seam:'+str(len(checks)),observed.count(after)==n); observed=observed.replace(after,before,n)
 check('whole_policy_test_observer_inverse',observed==texts['test/native_pivot_policy_tests.jl'])
 gr=raws['green2']; ir=raws['integration']; cr=raws['cost']
 expected_groups=[('options_and_copy_intent',4946),('backend_owned_policy',35),('private_spare_copy_and_failure',1568),('precision_and_factory_dispatch',245),('Native pivot policy public integration',48),('Native pivot policy private recovery',114)]
 actual_groups=[(t['name'],count(t,'pass')) for t in gr['tests']['children'][:4]]+[(t['name'],count(t,'pass')) for t in ir['tests']['children']]
 check('exact6956_six_groups',actual_groups==expected_groups and sum(n for _,n in actual_groups)==6956)
 check('green6977_and_no_failures',count(gr['tests'],'pass')+count(gr['regression_tests'],'pass')==6977 and clean(gr['tests']) and clean(gr['regression_tests']) and len(gr['events'])==792 and len(gr['equations'])==324)
 check('integration162_and_8children',count(ir['tests'],'pass')==162 and clean(ir['tests']) and [count(t,'pass') for t in ir['tests']['children'][0]['children']]==[6]*8 and ir['started']==9 and ir['active']==0 and not ir['probe_failed'])
 check('three_raw_complete',all(v['complete'] and not v['fatal'] and v['threads']==v['blas_threads']==1 for v in raws.values()))
 check('cost_work_counts',cr['windows']==88 and cr['counts']=={'construction':88,'refactor':176,'forward':2816,'transpose':1408})
 windows=[]; costrun=stages[1][1]; costreview=reviews['cost']; audit=audits['cost']
 for i in range(1,89):
  f=costrun/'output'/('window-%03d.toml'%i); w=tom(f); windows.append(w)
  check('cost_window_accepted:'+str(i),costreview['sha256'][str(f)]==digest(f))
 measured=[w for w in windows if not w['schedule']['warm']]
 regions=['construction','refactor_fresh','refactor_spare','solve','total']
 check('cost320_measured_compile0',len(measured)==64 and all(w[r]['compile_time']==w[r]['recompile_time']==0 for w in measured for r in regions))
 check('cost64_solve_zero_allocations',all(w['solve']['bytes']==w['solve']['events']==0 for w in measured))
 residuals=audit['result']['residuals']; perarm={arm:[e for e in residuals if windows[e['window']-1]['schedule']['arm']==arm] for arm in ('C','P')}
 check('cost_residual_counts',len(residuals)==4224 and len(perarm['C'])==len(perarm['P'])==2112 and sum(e['passed'] for e in perarm['P'])==2112 and sum(e['passed'] for e in perarm['C'])==1936)
 check('cost176_sparse96_DSE_forward',all(windows[e['window']-1]['schedule']['fixture']=='sparse96' and e['solve']%3==2 for e in residuals if not e['passed']))
 ratios={}; deltas={}
 for fixture in ('sparse32','dense32','sparse96','dense96'):
  arms={arm:{w['schedule']['round']:w for w in measured if w['schedule']['arm']==arm and w['schedule']['fixture']==fixture} for arm in ('C','P')}
  ratios[fixture]=statistics.median(arms['P'][r]['total']['seconds']/arms['C'][r]['total']['seconds'] for r in arms['C'])
  deltas[fixture]=statistics.median(arms['P'][r]['total']['bytes']-arms['C'][r]['total']['bytes'] for r in arms['C'])
 check('cost_no_consistent_speedup',min(ratios.values())<1<max(ratios.values()) and [round(ratios[k],6) for k in ratios]==[0.963886,1.000939,0.971995,1.013807])
 details['cost_total_median_ratios']=ratios; details['cost_total_median_byte_deltas']=deltas
 # Recorder inverse is purely logging; test invocation is fixed and hook-free.
 recorder=txt(Q/'recorder.jl'); oldrec=txt(D/'recorder.jl')
 log=';println(stderr,"TEST FAILURE: ",sprint(show,r));flush(stderr)'
 check('recorder_logging_only_inverse',recorder.count(log)==2 and recorder.replace(log,'').replace(';println(stderr,"BROKEN TEST: ",sprint(show,r));flush(stderr)','')==oldrec)
 driver=txt(Q/'master-driver.jl')
 check('driver_exact_group_constants',all('"'+name+'"=>'+str(n) in driver for name,n in expected_groups))
 check('driver_fixed2tests_and_no_probe',all(n in driver for n in ('native_pivot_policy_tests.jl','native_pivot_integration_tests.jl')) and not any(t in driver for t in ('Probe','observed-','_basis_factorization','forward_solve','solve(problem')))
 check('driver_source_threads_counts_exit',all(t in driver for t in ('realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl"))','Threads.nthreads()==BLAS.get_num_threads()==1','failed(root)==0','passed(root)==6956','raw["complete"]=true','ispath(p) && error("raw exists")','println(stderr,"BEGIN ",name);flush(stderr)')))
 check('immutable_public_deadlines', 'time_limit=5.0, iteration_limit=100' in texts['test/native_pivot_integration_tests.jl'])
 for p in [Q/'REPORT.md',Q/'author-check.failure.json',Q/'author-failure-note.md',PLAN,R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md',Q/'review-initial.json',Q/'finalize.py',Q/'publication.py',Q/'continuation-text.md']: read(p)
 # Fresh host evidence; both process-group and session IDs, no Julia by comm/exe.
 prior=js(Q/'host.json'); groups=set(prior['groups']); matches=[]; hidden=[]; boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 for p in Path('/proc').glob('[0-9]*'):
  try:
   stat=(p/'stat').read_text().rsplit(')',1)[1].split(); comm=(p/'comm').read_text().strip(); exe=''
   try: exe=str((p/'exe').resolve(strict=True))
   except PermissionError: hidden.append(int(p.name))
   except FileNotFoundError: pass
   if int(stat[2]) in groups or int(stat[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(stat[2]),sid=int(stat[3]),start_ticks=int(stat[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
  except (FileNotFoundError,ProcessLookupError): pass
 host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,unreadable_exe_pids=hidden,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),scope=prior['scope'])
 save('review-host.json',host); read(Q/'review-host.json')
 check('fresh220_groups_sessions_noJulia',len(groups)==220 and not matches and boot==prior['boot_id'])
 check('fresh_local_remote_refs',host['head']==HEAD and host['master']==MASTER and HEAD+'\trefs/heads/codex/simplex-core-architecture' in host['remote'] and MASTER+'\trefs/heads/master' in host['remote'])
 details['evidence_scope']='Targeted accepted result/raw/source links rehashed; unrelated runtime inventories were not replayed or rehashed. Existing numerical certificates are reused, not newly computed.'
except Exception as e:
 details['error']=str(e);details['traceback']=traceback.format_exc()
finally:
 result=dict(all_passed=bool(checks) and all(checks.values()) and 'error' not in details,checks=checks,sha256=bindings,details=details)
 save('review-checks.json',result)
 print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'bindings':len(bindings),'error':details.get('error'),'details':{k:v for k,v in details.items() if k in ('cost_total_median_ratios','cost_total_median_byte_deltas')}}))
