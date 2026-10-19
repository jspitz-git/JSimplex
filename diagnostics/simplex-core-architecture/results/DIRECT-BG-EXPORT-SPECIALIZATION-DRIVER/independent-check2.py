"""Independent offline review; no candidate main, Julia, launch, seal, or audit.
Pure predicate sources are copied into isolated in-memory Python namespaces.
All new output is exclusive and confined to this review directory.
"""
from pathlib import Path
import ast,copy,hashlib,json,os,re,struct,subprocess,sys,types,tomllib
D=Path(__file__).resolve().parent;R=D.parents[3];E=D.parent
C=R/'diagnostics/direct-bg-export-specialized/reproduce'
checks={};details={};errors=[]
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def check(name,value,detail=None):
 checks[name]=bool(value)
 if detail is not None:details[name]=detail
 if not value:errors.append(name)
def rejects(name,call):
 try:call()
 except (ValueError,TypeError,KeyError,IndexError,OverflowError) as e:check(name,True,type(e).__name__+': '+str(e))
 else:check(name,False,'Malformed input was accepted')
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def unrename(s):
 for a,b in [('_bgxs_','_bgx_'),('BGSpecializedExport','BGExport'),('_BGXSBuildOwner','_BGXBuildOwner')]:s=s.replace(a,b)
 return s
pins=rd(D/'preparation-pins.json')['sha256'];actual={p:digest(p) for p in pins}
check('all2097_manifest_hashes',len(pins)==2097 and actual==pins)
check('exact_required_membership',set(pins)==set(rd(D/'required-paths.json')['paths']))
check('manifest_absolute_paths',all(Path(p).is_absolute() for p in pins))
check('HEAD',git('rev-parse','HEAD')=='b504ea4fbf3bc40a9fa87cfc0b9a7dd69cc821cd')
check('master',git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
check('tracked_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
check('no_runs',not (D/'runs').exists())
check('author_results_bound',rd(D/'source-check.json')['all_passed'] is True and len(rd(D/'source-check.json')['checks'])==37 and rd(D/'offline-tests.json')['all_passed'] is True and len(rd(D/'offline-tests.json')['checks'])==144)
for n,v in rd(D/'copied-files.json').items():check('copy_'+n,digest(D/n)==digest(v['source'])==v['sha256'])
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
check('Python_syntax',True)
manifest=rd(C/'overlay-manifest.json');stage=Path(manifest['stage']);base=Path(manifest['base'])
check('same_RED_GREEN_stage',rd(D/'stages.json')['red']==rd(D/'stages.json')['green']==dict(path=str(stage),sha256=manifest['stage_sha256']))
check('exact83_stage',len(manifest['stage_sha256'])==83 and {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}==set(manifest['stage_sha256']) and all(digest(stage/p)==h for p,h in manifest['stage_sha256'].items()) and not any(p.is_symlink() for p in stage.rglob('*')))
check('old79_base',len(manifest['base_sha256'])==79 and all(digest(base/p)==h for p,h in manifest['base_sha256'].items()))
check('78_inherited_unchanged',all((stage/p).read_bytes()==(base/p).read_bytes() for p in manifest['base_sha256'] if p!='src/JSimplex.jl'))
newroot=(stage/'src/JSimplex.jl').read_text();oldroot=(base/'src/JSimplex.jl').read_text()
addition=''.join('include("_bgxs_'+n+'.jl")\n' for n in ['workspace','export','import','factor'])
check('root_four_includes_only',newroot.count(addition)==1 and newroot.replace(addition,'')==oldroot)
inv=rd(C/'source-inverse.json')
for n,v in inv['files'].items():
 s=(C/(n+'.jl')).read_text()
 for change in v['edits']:
  check('inverse_site_'+n+'_'+str(v['edits'].index(change)),s.count(change['after'])==1)
  s=s.replace(change['after'],change['before'],1)
 check('whole_source_inverse_'+n,unrename(s)==Path(v['source']).read_text())
for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl']:
 old=R/'diagnostics/direct-bg-export-workspace/reproduce'/n
 if n=='import-tests.jl':old=R/'diagnostics/direct-bg-export-workspace-harness-fix/reproduce'/n
 check('test_inverse_'+n,unrename((C/n).read_text())==old.read_text())
check('corrected_import_sha',digest(R/'diagnostics/direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl')=='628a74265bc5ed75e0a9507b9a7f3f453ba76d413ccbcb8a90e177e9e2329260')
oldcost=(E/'DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION/cost.jl').read_text()
oldbody=oldcost[oldcost.index('token(x::Float64)'):oldcost.index('# Untimed bounded controls')].replace('function save(name,data)','function save_window(name,data)')
red=(D/'red-kernel.jl').read_text();green=(D/'green-kernel.jl').read_text();header='# UNEXECUTED. Exact old lifecycle/window body except save name and candidate namespace.\n'
check('RED_exact_old_body',red==header+oldbody)
check('GREEN_only_factory_namespace',green==red.replace('_bgx_','_bgxs_') and red.count('_bgx_')==1)
driver=(D/'driver.jl').read_text()
check('top_level_test_includes',all(driver.index('include('+json.dumps(p)+')')<driver.index('function exact_tree') for p in manifest['test_order']))
check('test_entries_once',all(driver.count(p)==1 for p in manifest['test_entries']))
check('no_dynamic_load_workaround',all(x not in driver for x in ['invokelatest','eval(','@eval']))
check('same_complete_return_capture','return factor,clocks,(m0,m1,m2)' in red and 'factor,clocks,modes=timed.value' in red and 'retained=Base.summarysize(factor)' in red)
check('detached_pair_retention','"outputs"=>[token.(x) for x in outputs]' in red and 'paired[row["side"]]=row' in driver)
check('3warm7observed_pairs','for pair in 1:10' in driver and 'pair>3' in driver and 'median7(x)=length(x)==7 ? sort(x)[4]' in driver)
check('events_AND_bytes_gate','@test median7(cands_events)<=median7(refs_events) && median7(cands_bytes)<=median7(refs_bytes)' in driver)
expected=rd(D/'expected-tests.json');toml=tomllib.loads((D/'expected-tests.toml').read_text())
original=rd(E/'DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION/expected-tests.json')['green']
check('eleven_accepted_groups',expected['green']['groups'][:11]==original['groups'] and sum(g[1] for g in original['groups'])==7935)
# Independent derivation from the actual bounded loops and reachable @test sites.
reqs=sum(3+2*n+int(norm) for n in [0,1,3,2,2] for norm in [False,True])
orientation=2*(8+5*3)+6
requests=orientation+10*5+4*reqs
hooks=2*(2*(5+5*4)+6)
hot=24*(3+2*2+1)+12+4*4
check('source_count_derivation',(reqs,orientation,requests,hooks,hot)==(67,52,370,112,220),dict(requests=reqs,orientation=orientation,groups=[requests,hooks,hot]))
check('new_groups_exact',expected['green']['groups'][11:14]==[[n,c,0,0,0] for n,c in [('boundary_request_equivalence',requests),('boundary_hook_order',hooks),('boundary_hot_and_hook_agree',hot)]])
check('full8640',expected['green']['assertions']==7935+requests+hooks+hot+3==8640)
check('exact3RED',expected['red']['assertions']==3 and len(expected['red']['groups'])==3 and all(g[1:]==[0,1,0,0] for g in expected['red']['groups']))
for mode in ['red','green']:check('expected_TOML_'+mode,toml[mode]['assertions']==expected[mode]['assertions'] and [[x[k] for k in ['name','pass','fail','error','broken']] for x in toml[mode]['groups']]==expected[mode]['groups'])
historical=rd(E/'DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION/runs/cost1-300/audit.json')
provenance=rd(E/'DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED/attribution.json')
for name,ref,cand in [('sparse32',1274,1279),('dense32',1282,1291),('sparse96',2513,2514)]:
 old=next(c for c in historical['cells'] if c['fixture']==name and c['backend']=='native')['statistics']
 check('historical_exact_samples_'+name,old['events']['reference']['values']==([2513,2977,2513,2513,2513,2513,2513] if name=='sparse96' else [ref]*7) and old['events']['candidate']['values']==[cand]*7 and sorted(old['events']['reference']['values'])[3]==ref,dict(reference=old['events']['reference']['values'],candidate=old['events']['candidate']['values']))
 for side,value in [('reference',ref),('candidate',cand)]:
  p=next(p for p in provenance['profiles'] if (p['fixture'],p['backend'],p['side'])==(name,'native',side))
  check('independent_provenance_'+name+'_'+side,p['ordinary_events']==p['profiled_events']==value)
  if side=='reference':check('harness_effects_'+name,p['categories']['lifecycle_return_tuples']==2 and p['categories']['outside_lifecycle_timer_result']==14)
# Isolated in-memory copies only; no original script/module executed by path.
mods={}
for name in ['analysis','oracle','allocation_oracle']:
 module=types.ModuleType(name);module.__file__='<independent-memory-copy:'+name+'>'
 sys.modules[name]=module;exec(compile((D/(name+'.py')).read_text(),module.__file__,'exec'),module.__dict__);mods[name]=module
A=mods['analysis'];O=mods['oracle'];G=mods['allocation_oracle']
bt=lambda x:struct.pack('>d',float(x)).hex()
fixtures=[];rows={}
for c,name in enumerate(['sparse32','dense32','sparse96'],1):
 # Sparse 2x2 diagonal with nonuniform scale; both signs and -0 bits exercised.
 m=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[bt(2),bt(4)])
 step=dict(j=1,a=[bt(2),bt(0)],dse=[bt(-2),bt(4)],unit=[bt(1),bt(0)])
 f=dict(name=name,n=2,matrices=[copy.deepcopy(m) for _ in range(9)],steps=[copy.deepcopy(step) for _ in range(8)]);fixtures.append(f)
 out=[[bt(1),bt(0)],[bt(-1),bt(1)],[bt(.5),bt(0)]]*8
 for pair in range(1,11):
  for order in [1,2]:
   side=['reference','candidate'][(order-1) if pair%2 else (2-order)]
   rows[f'window-{c}-{2*(pair-1)+order}.toml']=dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.,bytes=100,events=10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.01]*6,outputs=copy.deepcopy(out))
check('equal_allocation_GREEN',len(G.allocation_results(rows,fixtures,'green'))==3)
rejects('equal_allocation_reject_RED',lambda:G.allocation_results(rows,fixtures,'red'))
for metric in ['events','bytes']:
 r=copy.deepcopy(rows)
 for x in r.values():
  if x['side']=='candidate':x[metric]+=1
 check('RED_'+metric+'_alone',len(G.allocation_results(r,fixtures,'red'))==3)
 rejects('GREEN_reject_'+metric,lambda:G.allocation_results(r,fixtures,'green'))
r=copy.deepcopy(rows)
for k,x in r.items():
 if not k.startswith('window-3-') and x['side']=='candidate':x['events']+=1
rejects('RED_requires_all3_failures',lambda:G.allocation_results(r,fixtures,'red'))
mutations={
 'missing_window':lambda r:r.pop('window-1-1.toml'),
 'extra_window':lambda r:r.update(extra={}),
 'wrong_side':lambda r:r['window-1-1.toml'].update(side='candidate'),
 'measured_compile':lambda r:r['window-1-7.toml'].update(compile_seconds=.01),
 'measured_recompile':lambda r:r['window-1-7.toml'].update(recompile_seconds=.01),
 'boolean_events':lambda r:r['window-1-1.toml'].update(events=True),
 'NaN_seconds':lambda r:r['window-1-1.toml'].update(seconds=float('nan')),
 'negative_bytes':lambda r:r['window-1-1.toml'].update(bytes=-1),
 'policy':lambda r:r['window-1-1.toml'].update(policy='default'),
 'extra_metric':lambda r:r['window-1-1.toml'].update(extra=0),
 'input':lambda r:r['window-1-1.toml'].update(inputs_unchanged=False),
 'mode_pair':lambda r:r['window-1-1.toml'].update(modes=['direct']*3),
 'residual':lambda r:r['window-1-1.toml']['outputs'][0].__setitem__(0,bt(2)),
 'signed_zero_pair':lambda r:r['window-1-1.toml']['outputs'][0].__setitem__(1,bt(-0.)),
 'nonfinite_output':lambda r:r['window-1-1.toml']['outputs'][0].__setitem__(0,bt(float('inf'))),
 'timer_overflow':lambda r:r['window-1-1.toml'].update(nested_seconds=[1.]*6)}
for name,mut in mutations.items():
 r=copy.deepcopy(rows);mut(r);rejects('malformed_'+name,lambda:G.allocation_results(r,fixtures,'green'))
schedule=[f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)]
for length in [0,1,2,19,20,21,39,59,60]:check('prefix_'+str(length),G.partial_windows({n:rows[n] for n in schedule[:length]},fixtures))
rejects('prefix_gap',lambda:G.partial_windows({schedule[1]:rows[schedule[1]]},fixtures))
r=copy.deepcopy(rows);r[schedule[0]]['outputs'][0][0]=bt(2)
rejects('prefix_bad_residual',lambda:G.partial_windows({schedule[0]:r[schedule[0]]},fixtures))
loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(stage/'src/JSimplex.jl'))
def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['expected allocation failure']*(f+e),children=[])
for mode in ['red','green']:
 root=node('root');root['children']=[node(*row) for row in expected[mode]['groups']]
 raw=dict(phase=mode+'300',complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=root)
 check('exact_test_tree_'+mode,O.test_results(raw,expected[mode],loaded,mode+'300')['assertions']==expected[mode]['assertions'])
 for name,change in [('loaded',lambda x:x['loaded'].update(JSimplex='/other')),('count',lambda x:x['tests']['children'][0].update(**{'pass':999})),('boolthreads',lambda x:x.update(threads=True)),('incomplete',lambda x:x.update(complete=False)),('error',lambda x:x['tests']['children'][0].update(error=1))]:
  bad=copy.deepcopy(raw);change(bad);rejects('raw_'+mode+'_'+name,lambda:O.test_results(bad,expected[mode],loaded,mode+'300'))
process=dict(reason='wall_time',returncode=-15,pins_unchanged=True);supervisor=dict(returncode=1,hard_timeout=False);log='BEGIN BG specialization driver red300'
check('pure_timeout',O.timeout_only(process,supervisor,None,log,299,300,loaded,'red300'))
for token in ['WARNING: something','world-age mismatch','ERROR: failure','TEST FAILURE: allocation','FATAL DRIVER: bad','GROUP/COUNT MISMATCH']:
 check('timeout_reject_log_'+token,not O.timeout_only(process,supervisor,None,log+'\n'+token,299,300,loaded,'red300'))
for name,p,s,t in [('memory',dict(process,reason='memory_guard'),supervisor,299),('pins',dict(process,pins_unchanged=False),supervisor,299),('hard',process,dict(supervisor,hard_timeout=True),299),('cleanup',process,dict(supervisor,cleanup_error='bad'),299),('elapsed',process,supervisor,301),('nan',process,supervisor,float('nan'))]:
 check('timeout_reject_'+name,not O.timeout_only(p,s,None,log,t,300,loaded,'red300'))
# Control/guard review is static; never invoke sealing, launch, saved-run audit,
# process signals, reservations, or the author test scripts.
control=(D/'control.py').read_text();launch=(D/'launch.py').read_text();seal=(D/'seal.py').read_text();audit=(D/'audit.py').read_text();guard=(D/'guard.py').read_text();supervisor_source=(D/'supervisor.py').read_text()
check('review_requires_red_support',"get('red_expectation_supported') is True" in control)
check('exact_review_keys',"set(v.get('sha256',{}))==set(required)" in control)
check('exclusive_reservation',"Path(p).open('x')" in control and "res=run/'reservation.json';save(res" in launch)
check('fresh_host_twice','h=full_host(groups)' in seal and "h=full_host(groups+sealed['groups'])" in launch)
check('groups_AND_sessions',"int(a[2]) in groups or int(a[3]) in groups" in control and "int(fields[2]) == pgid or int(fields[3]) == pgid" in guard)
check('runtime_identity_checks',"startswith('julia')" in control and 'unreadable_identity_pids' in control and 'start_ticks' in guard and 'boot_id' in guard)
check('bounded_options',all(s in control for s in ['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G',"seconds=cfg['seconds']-8"]) and '(8 * 1024**3, 8 * 1024**3)' in guard)
check('ownership_lock_pidfd',all(s in guard for s in ['os.O_NOFOLLOW','fcntl.LOCK_EX | fcntl.LOCK_NB','os.pidfd_open','signal.pidfd_send_signal','os.WNOWAIT']))
check('auditor_partial_before_timeout',audit.index('partial_windows({')<audit.index('pure=timeout_only'))
check('no_automatic_retry','main(phase)' in launch and 'config(prev)' in control and "first['command'][:-3]==cfg['command'][:-3]" in control)
check('warning_and_exact_failure_gates',"not warning_log(log)" in audit and "log.count('TEST FAILURE:')==(3 if cfg['mode']=='red' else 0)" in audit)
check('runtime_hash_resolution',all(str(Path(p).resolve(strict=True))==v['resolved'] and digest(p)==v['sha256'] for p,v in rd(D/'runtime-inputs-complete.json')['inventory'].items()))
check('all_loaded_paths_pinned',all(p in pins for p in loaded.values()))
host=rd(D/'host.json');task1host=rd(E/'DIRECT-BG-EXPORT-SPECIALIZATION-TASK1/host-closure.json')
check('historical256groups',len(host['groups'])==256 and set(task1host['groups'])<=set(host['groups']) and host['matches']==[] and host['unreadable_identity_pids']==[])
check('work_counts',(60,60*2,60*8,60*16,60*8,60*24)==(60,120,480,960,480,1440))
check('payload_counts',(24*(32+32+96)*8,60*6*8,20*24*(32+32+96))==(30720,2880,76800))
# Final rehash detects changes during review, and explicitly binds this checker.
check('manifest_unchanged_during_check',all(digest(p)==h for p,h in pins.items()))
result=dict(all_passed=all(checks.values()),checks=checks,details=details,errors=errors,sha256={**actual,str(D/'preparation-pins.json'):digest(D/'preparation-pins.json'),str(Path(__file__).resolve()):digest(__file__)},scope='Independent offline Task2 source, full hash, count, historical expectation and in-memory saved-data review; no Julia or launch')
with (D/'independent-check2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),bindings=len(result['sha256']),errors=errors)))
sys.exit(0 if result['all_passed'] else 1)
