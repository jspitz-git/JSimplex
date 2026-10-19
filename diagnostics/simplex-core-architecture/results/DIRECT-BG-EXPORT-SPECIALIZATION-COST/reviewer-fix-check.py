"""Independent correction review. Pure schema/TOML tests and fresh hashes only.
Never runs old checkers, control/preparation, operational audit or Julia.
"""
from pathlib import Path
import ast,copy,hashlib,json,math,struct,sys,tempfile,time
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import record_schema as schema,analysis as a,evidence as e
checks={};repros={}
def ck(k,v):checks[k]=bool(v)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def refuses(f):
 try:f();return False
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,OverflowError):return True
pins=rd(D/'preparation-pins-reviewed.json')['sha256'];paths=rd(D/'required-paths-reviewed.json')['paths'];mp=rd(D/'review-fix-map.json')['mapping']
ck('exact2594_canonical_membership',len(pins)==len(paths)==len(set(paths))==2594 and set(pins)==set(paths))
ck('canonical_required_selfbound',str(D/'required-paths-reviewed.json') in pins)
for p,h in pins.items():ck('canonical:'+p,sha(p)==h)
for name in ['preparation-pins.json','source-check.json','offline-tests-2.json','review.json']:
 for p,h in rd(D/name)['sha256'].items():ck('preserved:'+name+':'+p,sha(mp[p]['preserved'] if p in mp else p)==h)
for p,h in rd(D/'review.json')['evidence_sha256'].items():ck('initial_evidence:'+p,sha(p)==h)
for n in ['review.json','review.md']:ck('initial_copy:'+n,sha(D/n)==sha(D/(n+'.initial')))
for p,v in mp.items():ck('mapping:'+p,v['sha256']==sha(v['preserved'])==rd(D/'preparation-pins.json')['sha256'][p])
fix=rd(D/'review-fix-check.json');ck('author2922',fix['all_passed'] is True and len(fix['checks'])==2922 and all(fix['checks'].values()))
for p,h in fix['sha256'].items():ck('author_binding:'+p,sha(p)==h)
# Read writer-produced record values as positive schema examples only, not a re-audit.
G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')/'runs/greengc300'
p=rd(G/'output/process.json');cur=rd(G/'output/current.json');inv=rd(G/'invocation.json');res=[json.loads(s) for s in (G/'output/resources.jsonl').read_text().splitlines()];hosts=[rd(G/n) for n in ['prehost.json','host.json','posthost.json']];args=[p,cur,inv,res,hosts,300]
ck('writer_schema_valid',not refuses(lambda:schema.runtime(*args)));ck('writer_success_valid',schema.success(p,inv['supervisor']))
for name,mut in [('process_boolean_exit',lambda x:x[0].update(returncode=False)),('supervisor_boolean_exit',lambda x:x[2]['supervisor'].update(returncode=False)),('infinite_available',lambda x:x[3][0].update(available_kib=float('inf'))),('negative_swap',lambda x:x[3][0].update(swap_used_kib=-1)),('negative_infinite_swap',lambda x:x[3][0].update(swap_used_kib=-float('inf'))),('boolean_swap',lambda x:x[3][0].update(swap_used_kib=False))]:
 v=copy.deepcopy(args);mut(v);ck('original_R1:'+name,refuses(lambda:schema.runtime(*v)))
for name in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']:
 s=dict(inv['supervisor']);s[name]=True;ck('success_refuses:'+name,not schema.success(p,s))
 for malformed in [0,1,None,'false']:
  v=copy.deepcopy(args);v[2]['supervisor'][name]=malformed;ck('strictflag:'+name+':'+repr(malformed),refuses(lambda:schema.runtime(*v)))
for position,record in [(0,p),(1,cur),(2,inv)]:
 for key in record:
  v=copy.deepcopy(args);del v[position][key];ck('required_runtime:'+str(position)+':'+key,refuses(lambda:schema.runtime(*v)))
 v=copy.deepcopy(args);v[position]['unknown']=True;ck('unknown_runtime:'+str(position),refuses(lambda:schema.runtime(*v)))
for name,mut in [('terminal_inf',lambda x:x[0]['terminal_memory'].update(available_kib=float('inf'))),('terminal_negative',lambda x:x[0]['terminal_memory'].update(swap_used_kib=-1)),('identity_bool',lambda x:x[0]['child'].update(pid=True)),('elapsed_inf',lambda x:x[0].update(elapsed_including_launch=float('inf'))),('rss_float',lambda x:x[0].update(child_maxrss_kib=5.0)),('resource_boolean_elapsed',lambda x:x[3][0].update(elapsed=False))]:
 v=copy.deepcopy(args);mut(v);ck('additional_runtime:'+name,refuses(lambda:schema.runtime(*v)))
tp=dict(reason='wall_time',returncode=-15,pins_unchanged=True);ts=dict(returncode=1,soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,accepted=False);log='BEGIN BG export workspace cost cost1-300'
ck('valid_pure_timeout',e.timeout_ok(tp,ts,log,292.,300))
for name,s in [('missing_soft_and_accepted',{k:v for k,v in ts.items() if k not in ['soft_timeout','accepted']}),('contradictory_soft',dict(ts,soft_timeout=True)),('accepted_true',dict(ts,accepted=True))]:ck('original_timeout:'+name,not e.timeout_ok(tp,s,log,292.,300))
v=copy.deepcopy(args);v[0].update(reason='wall_time',returncode=-15);v[2]['supervisor'].update(returncode=1,accepted=False);ck('valid_timeout_runtime_schema',not refuses(lambda:schema.runtime(*v)))
# Only our frozen pure fixture definitions are reused. No prior top-level checker executes.
s=(D/'reviewer-check.py').read_text();pure=s[s.index('def tok(x):'):s.index("with tempfile.TemporaryDirectory(prefix='bgxs-reviewer-pure-')")];exec(compile(pure,'reviewer-pure-fixture-definitions','exec'))
with tempfile.TemporaryDirectory(prefix='bgxs-reviewer-correction-') as temp:
 root=Path(temp);out=root/'runs/cost1-300/output';out.mkdir(parents=True);(root/'inputs.json').write_text(json.dumps(dict(fixtures=fx)));(root/'loaded-paths.json').write_text('{}');cfg=dict(phase='cost1-300',process=1,stage='/synthetic/stage')
 data={'controls.toml':controls}
 for n in ['pins.json','current.json','process.json','resources.jsonl','run.log']:(out/n).write_text('{}')
 for i in range(1,9):
  b='native' if i%2 else 'markowitz';ident=dict(fixture=fx[(i-1)//2]['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default')
  data.update({f'started-{i}.toml':ident,f'preflight-{i}.toml':preflight(b),f'probe-{i}.toml':probe(),f'cell-{i}.toml':dict(ident,windows=20)})
  for w in range(1,21):data[f'window-{i}-{w}.toml']=window(1,w,b)
 data['raw.toml']=dict(phase='cost1-300',loaded=dict(JSimplex='/synthetic/stage/src/JSimplex.jl'),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1)
 for n,v in data.items():dump_toml(out/n,v)
 rows,totals=e.output_checks(out,cfg);ck('complete_live_TOML_residuals',totals==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576));ck('complete_first_gates',a.first_process_viable(dict(all_passed=True,pure_timeout=False,cells=rows),fx))
 mutations=[('probe_infinite_graph','probe-1.toml',lambda v:(v.update(coexistence_graph_peak=float('inf')),[s.update(coexistence_graph_peak=float('inf')) for s in v['states']])),('probe_boolean_copies','probe-1.toml',lambda v:v.update(copies=False)),('probe_float_constructions','probe-1.toml',lambda v:v.update(constructions=3.0)),('probe_unknown_key','probe-1.toml',lambda v:v.update(unrecognized=True)),('probe_boolean_step','probe-1.toml',lambda v:v['states'][0].update(step=False)),('control_boolean_call','controls.toml',lambda v:v.update(orientation_synthetic_calls=True)),('control_infinite_graph','controls.toml',lambda v:v['transitions'][0]['states'][0].update(coexistence_graph=float('inf'))),('control_unknown_key','controls.toml',lambda v:v.update(unrecognized=True)),('raw_integer_completed','raw.toml',lambda v:v.update(completed=1)),('cell_float_window_count','cell-1.toml',lambda v:v.update(windows=20.0))]
 for name,file,mut in mutations:
  v=copy.deepcopy(data[file]);mut(v);dump_toml(out/file,v);ck('original_R2:'+name,refuses(lambda:e.output_checks(out,cfg)));dump_toml(out/file,data[file])
 # Final aggregate counters are separate serialized objects; detach aliases in our constructor.
 for counter in countnames:
  for typ in ([float,bool] if data['probe-1.toml']['counts'][counter] in (0,1) else [float]):
   v=copy.deepcopy(data['probe-1.toml']);v['counts']=dict(v['counts']);v['counts'][counter]=typ(v['counts'][counter]);dump_toml(out/'probe-1.toml',v)
   label='final_counter:'+counter+':'+typ.__name__;rejected=refuses(lambda:e.output_checks(out,cfg));ck(label,rejected);repros[label]=dict(rejected=rejected,mutation=v['counts'],predicate='live full TOML output_checks; checkpoint counters unchanged')
   dump_toml(out/'probe-1.toml',data['probe-1.toml'])
 # Equivalent numeric leaves at sibling nested levels must also reject.
 for name,file,mut in [('checkpoint_count_float','probe-1.toml',lambda v:v['states'][0]['counts'].update(factorizations=1.0)),('import_count_float','controls.toml',lambda v:v['imports'][0]['counts'].update(raw_stores=6.0)),('transition_count_float','controls.toml',lambda v:v['transitions'][0].update(constructions=2.0)),('cache_count_bool','controls.toml',lambda v:v['transitions'][0]['copy_cache'].update(charge=False)),('preflight_refactor_float','preflight-1.toml',lambda v:v.update(refactors=4.0)),('window_event_bool','window-1-1.toml',lambda v:v.update(events=True)),('raw_thread_bool','raw.toml',lambda v:v.update(threads=True))]:
  v=copy.deepcopy(data[file]);mut(v);dump_toml(out/file,v);ck('sibling_refusal:'+name,refuses(lambda:e.output_checks(out,cfg)));dump_toml(out/file,data[file])
 order=['controls.toml']+[n for i in range(1,9) for n in [f'started-{i}.toml',f'preflight-{i}.toml',f'probe-{i}.toml']+[f'window-{i}-{w}.toml' for w in range(1,21)]+[f'cell-{i}.toml']]
 for n in data:(out/n).unlink()
 for length in range(len(order)):
  if length:dump_toml(out/order[length-1],data[order[length-1]])
  ck('legal_partial_live:'+str(length),not refuses(lambda:e.output_checks(out,cfg,partial=True)))
 for n,v in data.items():
  if n.startswith('window-'):
   _,i,w=n.removesuffix('.toml').split('-');v=window(2,int(w),'native' if int(i)%2 else 'markowitz')
  elif n=='raw.toml':v=dict(v,phase='cost2-300')
  dump_toml(out/n,v)
 reverse,_=e.output_checks(out,dict(cfg,phase='cost2-300',process=2));ck('complete_reversed_gates',all(a.qualify(x['statistics'],y['statistics']) for x,y in zip(rows,reverse)))
# Verify hooks before result classification, without importing operational modules.
s=(D/'audit.py').read_text();ck('runtime_hook_before_timeout',s.index("schema.runtime(p,cur,inv,resources,[pre,hs,post],cfg['seconds'])")<s.index('if timeout_ok('));ck('strict_success_hook',"require(schema.success(p,sup),'Exact exit')" in s)
old=(D/'control.py.before-review').read_text();new=old.replace("D/'preparation-pins.json'","D/'preparation-pins-reviewed.json'").replace("D/'required-paths.json'","D/'required-paths-reviewed.json'").replace("D/'review.json'","D/'review-final.json'");ck('control_only_canonical_receipt_names',new==(D/'control.py').read_text())
ck('schema_pure_imports',all(isinstance(n,ast.Import) and all(x.name in ['math','re'] for x in n.names) for n in ast.parse((D/'record_schema.py').read_text()).body if isinstance(n,(ast.Import,ast.ImportFrom))))
for n in ['runs','outers']:ck('no_operational_'+n,not (D/n).exists())
result=dict(all_passed=all(checks.values()),checks=checks,failures=[k for k,v in checks.items() if not v],reproductions=repros,pins_sha256=sha(D/'preparation-pins-reviewed.json'),primary_bindings=2595,sha256={str(D/n):sha(D/n) for n in ['reviewer-fix-check.py','preparation-pins-reviewed.json','record_schema.py','evidence.py','audit.py','control.py']},scope='Fresh independent cold correction review; actual TOML/live residuals; no operational checker or Julia executed',time=time.time())
with (D/'reviewer-fix-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failures=result['failures'],primary_bindings=2595)))
