"""Independent reviewer checks. Offline Python only; no old script or Julia execution."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,tomllib
D=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(D))
import analysis as a
import evidence as e
checks={}
def ck(name,value):
    checks[name]=bool(value)
    if not value:raise AssertionError(name)
def refuses(fn):
    try:fn()
    except (ValueError,RuntimeError,KeyError,TypeError):return True
    return False
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
p=rd(D/'preparation-pins.json');paths=rd(D/'required-paths.json')['paths']
ck('exact_2100_membership',len(paths)==len(set(paths))==len(p['sha256'])==2100 and set(paths)==set(p['sha256']))
ck('all_2100_hashes',all(sha(x)==h for x,h in p['sha256'].items()))
rt=rd(D/'runtime-inputs-complete.json')['inventory']
ck('runtime_all_pinned',set(rt)<=set(paths))
ck('runtime_hash_resolution',all(sha(x)==v['sha256'] and str(Path(x).resolve(strict=True))==v['resolved'] for x,v in rt.items()))
st=rd(D/'stages.json')['cost'];root=Path(st['path'])
actual={str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()}
ck('stage_exact_83',len(actual)==83 and actual==set(st['sha256']) and all(sha(root/n)==h for n,h in st['sha256'].items()))
ck('no_stage_symlinks',not root.is_symlink() and not any(x.is_symlink() for x in root.rglob('*')))
inv=rd(D/'probe-inverse.json');seed=Path(inv['seed']);C=D.parents[3]/'diagnostics/direct-bg-export-workspace/reproduce'
ck('four_root_includes_only',(root/'src/JSimplex.jl').read_text().replace(inv['stage_addition'],'')==(seed/'src/JSimplex.jl').read_text())
ck('seed_unchanged',all(x.read_bytes()==(root/x.relative_to(seed)).read_bytes() for x in seed.rglob('*') if x.is_file() and x!=seed/'src/JSimplex.jl'))
for name in ('workspace','export','import','factor'):
    text=(D/f'probe-{name}.jl').read_text()
    ck('clone_stage_'+name,text==(root/'src'/f'_bgxp_{name}.jl').read_text())
    if name=='workspace':
        ck('single_counter_header',text.startswith(inv['header']))
        text=text[len(inv['header']):]
    for old,new,count in reversed(inv['edits'][name]):
        ck('inverse_occurrence_'+name+'_'+str(len(checks)),text.count(new)==count)
        text=text.replace(new,old)
    text=text.replace('_bgxp_','_bgx_').replace('BGProbeExport','BGExport').replace('_BGXPBuildOwner','_BGXBuildOwner')
    ck('whole_file_inverse_'+name,text==(C/(name+'.jl')).read_text())
ck('original_inputs_json_toml',rd(D/'inputs.json')==tomllib.loads((D/'inputs.toml').read_text()))
for name,v in rd(D/'reused-files.json').items():
    ck('reused_'+name,sha(D/name)==sha(v['path'])==v['sha256'])
for x in D.glob('*.py'):ast.parse(x.read_text(),filename=str(x))
ck('python_syntax_only',True)
ck('no_sealed_run',not (D/'runs').exists())
ck('preserved_builder_failure',rd(D/'prepare-failure.json')['error']=="RuntimeError('Root end')" and (D/'root.before-completion.jl').read_bytes()==(seed/'src/JSimplex.jl').read_bytes())
ck('author_offline_checks',rd(D/'source-check.json')['all_passed'] is True and len(rd(D/'source-check.json')['checks'])==129)
# Derive the complete explicit API budget independently from the fixed loops.
timed=8*10*2;pre=8;probes=8
totals=dict(constructions=timed+pre*2+probes*3+4,refactors=timed*2+pre*4+probes*6+12,
 updates=timed*8+probes*24,ftran=timed*16+probes*48,btran=timed*8+probes*24,copies=4)
ck('api_schedule',totals==dict(constructions=204,refactors=412,updates=1472,ftran=2944,btran=1472,copies=4))
ck('native_orientation_upper_bound',(totals['constructions']+totals['refactors'])//2==308)
fixtures=rd(D/'inputs.json')['fixtures']
cells=[dict(fixture=f['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default',
 statistics=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,probe_memory_gate=True,faster_pairs=3))
 for f in fixtures for b in ('native','markowitz')]
good=dict(all_passed=True,pure_timeout=False,cells=cells)
ck('first_all_eight',a.first_process_viable(good,fixtures))
for i in range(8):
 for key,bad in [('time_median_gate',False),('allocation_gate',False),('memory_gate',False),('probe_memory_gate',False),('faster_pairs',2)]:
    v=copy.deepcopy(good);v['cells'][i]['statistics'][key]=bad
    ck('first_reject_'+str(i)+'_'+key,not a.first_process_viable(v,fixtures))
s=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,faster_pairs=5)
ck('combined_10_of_14',a.qualify(s,s) and not a.qualify(s,dict(s,faster_pairs=4)))
for key in ('time_median_gate','allocation_gate','memory_gate'):
 ck('combined_reject_'+key,not a.qualify(s,dict(s,**{key:False})))
# One-dimensional exact arithmetic fixture tests the output predicate without a numerical runtime.
one='3ff0000000000000';zero='0000000000000000'
m=dict(n=1,colptr=[1,2],rowval=[1],nzval=[one])
f=dict(n=1,matrices=[m]*9,steps=[dict(j=1,a=[one],dse=[one],unit=[one])]*8)
matrices=[(a.matrix(m),a.matrix(m,True))]*9
row=dict(pair=4,order=1,side='candidate',measured=True,policy='threshold_one',correct=True,inputs_unchanged=True,
 modes=['normalized']*3,seconds=1.,bytes=1,events=1,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,
 retained_bytes=1,nested_seconds=[0.1]*6,outputs=[[one] for _ in range(24)])
ck('synthetic_valid_window',a.window_ok(row,f,1,4,1,matrices))
for key,val in [('pair',5),('order',2),('side','reference'),('measured',False),('correct',False),('inputs_unchanged',False),
 ('compile_seconds',0.1),('recompile_seconds',0.1),('retained_bytes',-1),('seconds',float('nan')),('nested_seconds',[1.]*6),
 ('outputs',[[zero] for _ in range(24)])]:
 v=copy.deepcopy(row);v[key]=val
 ck('window_refuses_'+key,refuses(lambda:a.window_ok(v,f,1,4,1,matrices)))
for process in (1,2):
 ck('alternating_'+str(process),all(a.schedule(process,k)==list(reversed(a.schedule(process,k+1))) for k in range(1,10)))
v=dict(present=True,dimension=96,charge=528,limit=600,seen_bytes=16,orientation_bytes=0,graph_bytes=600)
e.cache(v);ck('cache_valid',True)
for key,val in [('limit',527),('charge',529),('dimension',64),('orientation_bytes',1),('graph_bytes',0)]:
 ck('cache_refuses_'+key,refuses(lambda:e.cache(dict(v,**{key:val}))))
baseproc=dict(returncode=-15,reason='wall_time',pins_unchanged=True)
sup=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
ck('pure_timeout_only',e.timeout_ok(baseproc,sup,'BEGIN BG export workspace cost cost1-300',293.,300))
for log in ['Warning:','world-age','ERROR:','FATAL COST:','Measured compilation; stop']:
 ck('timeout_refuses_'+log,not e.timeout_ok(baseproc,sup,'BEGIN BG export workspace cost cost1-300 '+log,293.,300))
for key in ('hard_timeout','child_kill','guard_term','guard_kill'):
 ck('timeout_refuses_'+key,not e.timeout_ok(baseproc,dict(sup,**{key:True}),'BEGIN BG export workspace cost cost1-300',293.,300))
ck('inclusive_timeout_refusal',not e.timeout_ok(baseproc,sup,'BEGIN BG export workspace cost cost1-300',300.01,300))
result=dict(all_passed=all(checks.values()),checks=checks,check_count=len(checks),api_budget=totals,
 scope='Independent offline source/hash/predicate review only; no Julia, seal, launch, parser, import or numerical execution',
 pins_sha256=sha(D/'preparation-pins.json'))
with (D/'reviewer-check.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),api_budget=totals)))
