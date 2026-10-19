"""New offline source verification. No Julia, no frozen checker execution."""
from pathlib import Path
import json,ast,tomllib,sys,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3]
import control as c
E=D.parent;T=E/'DIRECT-BG-EXPORT-SPECIALIZATION-TASK1';A=E/'DIRECT-BG-EXPORT-SPECIALIZATION-PLAN';H=E/'DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION';G=E/'DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION';O=E/'DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION';P=E/'DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED';C=R/'diagnostics/direct-bg-export-specialized/reproduce'
checks={}
def check(v,n):
 checks[n]=bool(v)
 c.require(v,n)
check(c.bindings(c.rd(T/'review.json')) and c.rd(T/'review.json')['accepted'] is True,'Task1_review_bound')
check(c.bindings(c.rd(T/'publication.json')),'Task1_publication_bound')
check(c.rd(D/'offline-tests.json')['all_passed'] is True and len(c.rd(D/'offline-tests.json')['checks'])==144,'new_offline144')
for name,record in c.rd(D/'copied-files.json').items():check(c.sha(D/name)==record['sha256']==c.sha(record['source']),'copy_'+name)
for f in D.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
check(True,'new_Python_syntax_only')
c.validate_environment();check(True,'environment_exact')
c.validate_sources();check(True,'baseline_stage_runtime_exact')
m=c.rd(C/'overlay-manifest.json');stage=c.rd(D/'stages.json')
check(all(x=={'path':m['stage'],'sha256':m['stage_sha256']} for x in stage.values()) and len(m['stage_sha256'])==83,'same83stage')
s=(O/'cost.jl').read_text();body=s[s.index('token(x::Float64)'):s.index('# Untimed bounded controls')].replace('function save(name,data)','function save_window(name,data)')
header='# UNEXECUTED. Exact old lifecycle/window body except save name and candidate namespace.\n'
check((D/'red-kernel.jl').read_text()==header+body,'RED_kernel_exact_old')
check((D/'green-kernel.jl').read_text()==header+body.replace('_bgx_','_bgxs_'),'GREEN_only_namespace')
driver=(D/'driver.jl').read_text();mainpos=driver.index('function main()')
check(all(driver.index('include('+json.dumps(p)+')')<mainpos for p in m['test_order']),'all_test_loads_before_main')
check([driver.index('include('+json.dumps(p)+')') for p in m['test_order']]==sorted(driver.index('include('+json.dumps(p)+')') for p in m['test_order']),'test_order')
check(all(driver.count(e)==1 for e in m['test_entries']),'each_entry_once')
check('invokelatest' not in driver and 'eval(' not in driver,'no_world_age_workaround')
check('for pair in 1:10' in driver and 'pair>3' in driver and 'median7(x)=length(x)==7 ? sort(x)[4]' in driver,'schedule_3warm7observed')
check('median7(cands_events)<=median7(refs_events) && median7(cands_bytes)<=median7(refs_bytes)' in driver,'event_AND_byte_gate')
check('paired["reference"]["outputs"]==paired["candidate"]["outputs"]' in driver,'paired_bits')
check('Val(:native)' in driver and '"sparse32","dense32","sparse96"' in driver,'three_native_cells')
check('Statistics' not in driver,'no_new_dependency')
x=c.rd(D/'expected-tests.json');t=tomllib.loads((D/'expected-tests.toml').read_text());old=c.rd(G/'expected-tests.json')['green']
check(x['green']['groups'][:11]==old['groups'] and sum(g[1] for g in old['groups'])==7935,'accepted_GREEN2_counts_retained')
check(x['green']['groups'][11:14]==[['boundary_request_equivalence',370,0,0,0],['boundary_hook_order',112,0,0,0],['boundary_hot_and_hook_agree',220,0,0,0]],'new_source_count_inventory')
check(x['green']['assertions']==sum(sum(g[1:]) for g in x['green']['groups'])==8640 and x['red']['assertions']==3,'total_counts')
for mode in x:check(t[mode]['assertions']==x[mode]['assertions'] and [[a[k] for k in ('name','pass','fail','error','broken')] for a in t[mode]['groups']]==x[mode]['groups'],'TOML_JSON_'+mode)
check('red_expectation_supported' in (D/'control.py').read_text(),'independent_RED_support_required')
check('partial_windows' in (D/'audit.py').read_text(),'partial_window_gate')
check(not (D/'runs').exists(),'no_runs_seals_reservations_outputs')
check(c.git('rev-parse','HEAD')==c.ENTRY and not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'entry_clean')
# Bind original artifacts as evidence, not execution. All actual runtime/baseline paths included.
files=set(c.rd(T/'source-check.json')['sha256'])|set(c.rd(T/'review.json')['sha256'])
files|={str(p) for p in C.iterdir() if p.is_file()}
files|={str(p) for p in D.iterdir() if p.is_file()}
files|=set(c.rd(D/'runtime-inputs-complete.json')['inventory'])
for label,root in [('diagnostic',R),('production',c.W)]:files|={str(root/n) for n in c.rd(D/'baseline.json')[label]}
for stage in c.rd(D/'stages.json').values():files|={str(Path(stage['path'])/n) for n in stage['sha256']}
for folder,names in [(T,['review.json','publication.json','source-check.json','host-closure.json']), (A,['review.json','review.md']), (G,['driver.jl','expected-tests.json','expected-tests.toml','inverse.json','runs/green2-300/sealed.json','runs/green2-300/audit.json','runs/green2-300/result-review.json']), (O,['cost.jl','inputs.json','inputs.toml','analysis.py','runs/cost1-300/audit.json','runs/cost1-300/result-review.json']), (P,['attribution.json','REPORT.md','result-review.md','driver.jl','helpers.jl']), (H,['WORK-MEMORY.md','ASSERTION-INVENTORY.md','control.py','audit.py','offline-tests.py'])]:files|={str(folder/n) for n in names}
files|={str(R/'diagnostics/direct-bg-export-workspace/reproduce'/n) for n in ['composition-ledger.md','work-memory-ledger.md']}
# Paths relative in old evidence normalized to checkout explicitly.
files={str(c.path(p)) for p in files}
sha={p:c.sha(p) for p in sorted(files)}
c.save(D/'source-check.json',dict(all_passed=True,checks=checks,sha256=sha,scope='New offline source/count/inverse/hashes only; no Julia or performance acceptance'))
files.add(str(D/'source-check.json'));c.save(D/'required-paths.json',dict(paths=sorted(files)))
files.add(str(D/'required-paths.json'))
# Required list includes itself to make mutation fail before review.
r=c.rd(D/'required-paths.json');r['paths']=sorted(files)
(D/'required-paths.json').write_text(json.dumps(r,indent=2)+'\n')
c.save(D/'preparation-pins.json',dict(sha256={p:c.sha(p) for p in sorted(files)},scope='Task2 offline concrete driver/admission preparation, no launch'))
print(json.dumps({'checks':len(checks),'bindings':len(files),'all_passed':True}))
