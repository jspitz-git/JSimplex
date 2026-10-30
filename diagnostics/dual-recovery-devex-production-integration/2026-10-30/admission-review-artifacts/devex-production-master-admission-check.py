from pathlib import Path
import sys,json,hashlib,ast,re,subprocess,copy,math
from unittest.mock import patch
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-production-integration/2026-10-30')
sys.path.insert(0,str(D))
import common as C
import audit as A
T=Path('/tmp/devex-production-integration-20261030')
checks={};bindings={};historical=[]
def check(k,v):
 checks[k]=bool(v)
 if not v: raise AssertionError(k)
def bind(p):
 p=str(Path(p).absolute()); bindings[p]=C.sha(p);return bindings[p]
def rejects(fn):
 try:fn()
 except (ValueError,KeyError,TypeError,IndexError):return True
 return False
seal=C.read(C.R/'seal.json');pins=C.read(C.R/'pins.json');contract=C.read(D/'contract.json');state=C.read(D/'integration.json');before=C.read(D/'before.json');manifest=C.read(C.P/'manifest.json');prod=C.read(D/'production-commit.json')
check('seal_exact',bind(C.R/'seal.json')=='f500580d7b89f3c99611715134760da46a2d061e8083e0aaa731bf64f5116c0b')
check('pins_digest',bind(C.R/'pins.json')==seal['pins_sha256'])
check('pin_count_membership',len(pins['inventory'])==164 and set(pins['inventory'])==set(pins['files'])==set(C.paths()) and pins['trees']==[])
for n,v in pins['inventory'].items():check('pin:'+n,bind(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'])
check('concrete_command_environment',seal['command']==contract['command'] and seal['environment']==contract['environment'])
check('concrete_interpreter',str(Path(sys.executable).absolute())==seal['guard_python'] and str(Path(sys.executable).resolve())==pins['inventory'][seal['guard_python']]['resolved'])
C.unused();check('exclusive_attempt_unused',sorted(p.name for p in C.R.iterdir())==['pins.json','seal.json'])
check('eleven_manifest_payload',len(prod['names'])==11 and prod['names']==manifest['payload']==sorted(state['payload_sha256']) and manifest['payload_sha256']==state['payload_sha256'])
check('exact_production_parent',C.git(C.M,'rev-parse',prod['commit']+'^')==prod['parent']=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
check('production_changed_names',C.git(C.M,'diff-tree','--no-commit-id','--name-only','-r',prod['commit']).splitlines()==prod['names'])
check('production_commit_tree',C.git(C.M,'rev-parse',prod['commit']+'^{tree}')==prod['tree'])
check('diagnostic_same_production',not C.git(C.W,'diff',prod['commit'],'HEAD','--','src','test','Project.toml','.github'))
for n in prod['names']:
 check('payload:'+n,bind(C.M/n)==bind(C.W/n)==bind(C.P/'prepared'/n)==manifest['payload_sha256'][n])
 check('blob:'+n,C.git(C.M,'rev-parse',prod['commit']+':'+n)==prod['blobs'][n])
 blob=subprocess.check_output(['git','-C',str(C.M),'show',prod['commit']+':'+n]);check('blob_bytes:'+n,hashlib.sha256(blob).hexdigest()==manifest['payload_sha256'][n])
check('explicit_before_maps',len(state['before_maps'])==8 and state['before_maps']==before['before_maps'])
for n,v in state['before_maps'].items():check('before_copy:'+n,bind(v['copy'])==v['sha256'] and C.sha(n)!=v['sha256'])
review=C.read(C.P/'review-final.json');check('source_only_review',review['accepted'] is True and review['runtime_qualified'] is False and review['numerical_admission'] is False and len(review['checks'])==825 and all(v is True for v in review['checks'].values()) and len(review['bindings'])==971)
for n,v in review['bindings'].items():
 if n in state['before_maps'] and v==state['before_maps'][n]['sha256']:
  mapped=state['before_maps'][n]['copy'];check('historical_before:'+n,bind(mapped)==v);historical.append(dict(original=n,copy=mapped,sha256=v))
 else:check('historical_binding:'+n,bind(n)==v)
check('failed_source_check_preserved',C.read(C.P/'source-check.json')['accepted'] is False and C.read(C.P/'source-check-endpoint.json')['accepted'] is True)
for n,v in manifest['exact_copies'].items():check('prepared_copy:'+n,bind(n)==bind(v['copy'])==v['sha256'])
for n,v in manifest['transforms'].items():
 src=v['source'];src=state['before_maps'][src]['copy'] if src in state['before_maps'] and v['source_sha256']==state['before_maps'][src]['sha256'] else src
 check('transform_source:'+n,bind(src)==v['source_sha256']);s=Path(src).read_text()
 for r in v['replacements']:
  check('transform_occurrence:'+n+':'+str(len(s)),s.count(r['old'])==1);s=s.replace(r['old'],r['new'])
 check('transform_exact:'+n,s==(C.M/n).read_text())
for n in ('Project.toml','Manifest.toml','LocalPreferences.toml'):
 candidate=C.W/'diagnostics/dual-recovery-devex-task4/2026-10-30/overlays/candidate'/n
 check('qualified_environment:'+n,bind(C.M/n)==bind(candidate))
for n,v in contract['guard_exact_copies'].items():check('copied_guard:'+n,bind(D/'guard'/n)==v)
for p in [*D.rglob('*.py'),T/'admission-check.py',T/'postcheck.py']:
 ast.parse(p.read_text());bind(p);check('ast:'+str(p),True)
for p in (T/'PLAN.md',T/'preparation-path-note.json',C.P/'manifest.json',C.P/'review-final.json',C.P/'REVIEW-FINAL.md'):bind(p)
check('external_document_correction',C.read(T/'preparation-path-note.json')['numerical_executed'] is False and C.read(T/'preparation-path-note.json')['seal_preserved'] is True)
check('prior_five_records',len(C.budget_paths())==5 and C.prior_time()==contract['previous_seconds']==1108.3747013349202)
check('shared_remaining',contract['remaining_seconds']==691.6252986650798 and contract['remaining_seconds']+C.prior_time()==1800 and contract['maximum_processes']==1)
check('cleanup_reserves',contract['inner_cleanup_reserve_seconds']==12 and contract['outer_cleanup_reserve_seconds']==4)
driver=(D/'verify.jl').read_text();includes=re.findall(r'include\(joinpath\(DEVEX_MASTER_ROOT,"test","([^"]+)"\)\)',driver)
check('ordinary_driver_order',includes==contract['ordered_test_files'] and len(includes)==12 and '@assert realpath(pathof(JSimplex))' in driver and 'using JSimplex,Test,LinearAlgebra,SparseArrays,Logging' in driver and 'record' not in driver.lower())
check('no_new_driver_profiling',not any(t in driver for t in ('@timed','TOML','Serialization','push_testset','pop_testset','include_string')))
check('six_cold_entry_boundaries',sum((C.M/'test'/n).read_text().count('Base.invokelatest(') for n in includes[:5])==6)
for n in includes[5:]:
 blob=subprocess.check_output(['git','-C',str(C.M),'show',prod['parent']+':test/'+n]);check('unchanged_regression:'+n,blob==(C.M/'test'/n).read_bytes())
for n in contract['known_fixtures']:check('actual_fixture:'+n,str(Path(n).resolve())==n and bind(n)==C.read(C.P/'source-check.json')['bindings'][str(C.W/Path(n).relative_to(C.M))])
endpoint=(C.M/'test/recovery_devex_pivot_tests.jl').read_text()
check('endpoint_new_two_runtime_assertions',len(re.findall(r'^\s*@test(?:_throws)?\b',endpoint,re.M))==24 and 'for T in (Float32,Float64)' in endpoint and '@test calls==(1,3) && (f.builder.last.forwards,f.builder.last.backwards)==(2,4)' in endpoint)
good='Test Summary: | Pass Total Time\nDEVEX_PRODUCTION_MASTER | 5776 5776 2.5s\nDEVEX_PRODUCTION_MASTER_COMPLETED\n'
check('ordinary_summary_valid',A.summary(good)==dict(Pass=5776,Total=5776))
bads=[good.replace('5776','5774'),good.replace('5776 5776','5776 5777'),good+good,good.replace('DEVEX_PRODUCTION_MASTER_COMPLETED',''),good+'DEVEX_PRODUCTION_MASTER_COMPLETED\n',good.replace('Test Summary:','Summary:'),good.replace('Pass Total','Pass Pass'),good.replace('5776 5776','true 5776'),good.replace('5776 5776','5776.0 5776'),good.replace('Pass Total','Pass Fail Total').replace('5776 5776','5776 1 5777'),good.replace('Pass Total','Pass Error Total').replace('5776 5776','5776 1 5777'),good.replace('Pass Total','Pass Broken Total').replace('5776 5776','5776 1 5777')]
bads += [good+'\n'+s for s in ('world age','Error During Test','UndefVarError','syntax:','segmentation fault','ERROR:','Test Failed at')]
for i,s in enumerate(bads):check('malformed_summary_rejected:'+str(i),rejects(lambda:A.summary(s)))
for i,v in enumerate((dict(available_kib=True,swap_used_kib=0),dict(available_kib=6*1024**2,swap_used_kib=False),dict(available_kib=6*1024**2-1,swap_used_kib=0),dict(available_kib=6*1024**2,swap_used_kib=1024**2+1))):check('bad_resource_rejected:'+str(i),rejects(lambda:A.resource(v)))
# Exercise evaluate predicates with isolated in-memory evidence; never its main.
idguard=dict(pid=9001,pgid=9001,sid=9001,start_ticks=1,boot_id=seal['preflight']['boot_id'],command='guard')
idchild=dict(pid=9002,pgid=9002,sid=9002,start_ticks=2,boot_id=seal['preflight']['boot_id'],command='entry')
idlaunch=dict(pid=9000,pgid=9000,sid=9000,start_ticks=3,boot_id=seal['preflight']['boot_id'],command='launcher')
mem=dict(available_kib=7*1024**2,swap_used_kib=0);h=dict(conflicts=[],refs=seal['preflight']['refs'],memory=mem,checked_groups=[9001,9002],boot_id=seal['preflight']['boot_id'],still_active_current_launcher=[idlaunch])
evidence={str(D/'contract.json'):contract,str(C.R/'seal.json'):seal,str(C.R/'pins.json'):pins,str(C.R/'attempt.json'):dict(admission_path='/synthetic/admission',admission_sha256='s',seal_sha256='s',started_monotonic=100,runner=idlaunch),str(C.R/'guard/process.json'):dict(returncode=0,reason='exit0',pins_unchanged=True,command=contract['command'],pins_sha256=seal['pins_sha256'],runner=idguard,child=idchild,terminal_memory=mem),str(C.R/'supervisor.json'):dict(accepted=True,returncode=0,soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,abnormal_cleanup_attempted=False,child_cleanup_attempted=False,elapsed_seconds=50),str(C.R/'completion.json'):dict(supervisor_accepted=True,limit_seconds=1800,elapsed_inclusive_seconds=51,total_inclusive_seconds=1108.3747013349202+51),str(C.R/'guard/pins.json'):pins,str(C.R/'invocation.json'):dict(command=C.guard_command(100),cwd=str(D),environment=contract['environment']),str(C.R/'guard/gate.json'):dict(identity=idchild,parent=idguard,parent_death_signal=9,command=contract['command'],current_sha256='s',permit_sha256='s'),str(C.R/'guard/current.json'):dict(runner=idguard,child=idchild,command=contract['command']),str(C.R/'guard/permit.json'):dict(current_sha256='s',command=contract['command']),str(C.R/'prelaunch-host.json'):h,str(C.R/'postflight.json'):h,str(D/'integration.json'):state,str(D/'production-commit.json'):prod}
real_text=Path.read_text
def text_fake(p,*a,**k):
 if p==C.R/'guard/run.log':return good
 if p==C.R/'guard/resources.jsonl':return json.dumps(mem)+'\n'
 return real_text(p,*a,**k)
def fake_sha(p):
 if str(p)==str(C.R/'pins.json'):return seal['pins_sha256']
 if str(p).startswith(str(C.M)+'/'):return state['payload_sha256'][str(Path(p).relative_to(C.M))]
 return 's'
def fake_git(root,*args):return '\n'.join(prod['names']) if args[0]=='diff-tree' else prod['blobs'][args[-1].split(':',1)[1]]
def exercise(ev):
 with patch.object(C,'read',side_effect=lambda p:ev[str(p)]),patch.object(C,'admit',return_value={}),patch.object(C,'verify_pins',return_value=True),patch.object(C,'sha',side_effect=fake_sha),patch.object(C,'paths',return_value=pins['files']),patch.object(C,'prior_time',return_value=1108.3747013349202),patch.object(C,'groups',return_value={9001,9002}),patch.object(C,'host',return_value=h),patch.object(C,'git',side_effect=fake_git),patch.object(Path,'read_text',text_fake):return A.evaluate()
check('synthetic_full_evaluate_valid',exercise(evidence)==dict(Pass=5776,Total=5776))
mutants=[('guard/process.json','returncode',False),('guard/process.json','returncode',1),('guard/process.json','reason','wall_time'),('guard/process.json','pins_unchanged',False),('guard/process.json','command',[]),('supervisor.json','returncode',False),('supervisor.json','accepted',1),('completion.json','supervisor_accepted',1),('completion.json','limit_seconds',1800.0),('completion.json','elapsed_inclusive_seconds',True),('completion.json','elapsed_inclusive_seconds',float('nan')),('completion.json','elapsed_inclusive_seconds',0),('completion.json','total_inclusive_seconds',1801),('completion.json','total_inclusive_seconds',51),('guard/gate.json','parent_death_signal',15),('guard/gate.json','current_sha256','wrong'),('guard/gate.json','command',[]),('guard/permit.json','current_sha256','wrong'),('postflight.json','conflicts',['x']),('postflight.json','checked_groups',[9001]),('postflight.json','still_active_current_launcher',[]),('invocation.json','cwd','wrong')]
mutants += [('supervisor.json',k,True) for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')]
for i,(n,k,v) in enumerate(mutants):
 ev=copy.deepcopy(evidence);ev[str(C.R/n)][k]=v;check('malformed_evidence_rejected:'+str(i)+':'+n+':'+k,rejects(lambda:exercise(ev)))
# Fresh unrestricted process and Git snapshot, independently of saved seal.
host=C.host();check('fresh742_groups_and_sessions',len(host['checked_groups'])==742 and host['conflicts']==[] and host['still_active_current_launcher']==[])
check('fresh_correct_refs',host['refs']==seal['preflight']['refs'])
check('all_new_binding_values_current',all(C.sha(n)==v for n,v in bindings.items()))
result=dict(accepted=True,checks=checks,bindings=bindings,historical_before_substitutions=historical,host=host,counts=dict(checks=len(checks),bindings=len(bindings),sealed_pins=164,malformed_summary_cases=len(bads),malformed_evidence_cases=len(mutants),historical_bindings=971),no_julia=True,no_historical_main=True)
with Path('/tmp/devex-production-master-admission-check-result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,counts=result['counts'],historical_substitutions=len(historical),memory=host['memory'],refs=host['refs'])))
