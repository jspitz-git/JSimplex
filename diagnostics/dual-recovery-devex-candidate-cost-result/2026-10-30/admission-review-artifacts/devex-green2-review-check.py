"""Fresh independent read-only preparation review. No Julia or program mains."""
import ast,copy,hashlib,json,math,re,subprocess,tomllib,types
from pathlib import Path
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
D=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30'
F=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30'
T=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
checks={};bindings={}
def ck(n,v):checks[n]=bool(v);assert v,n
source=read(D/'source-check.json');pres=read(D/'preservation.json');contract=read(D/'contract.json')
for name,h in source['bindings'].items():ck('source_binding:'+name,sha(name)==h);bindings[name]=h
ck('425_source_bindings',len(source['bindings'])==425)
for name,h in pres['frozen_publications'].items():ck('preservation:'+name,sha(name)==h)
ck('402_prior_files',len(pres['frozen_publications'])==402)
for name,q in pres['copies'].items():ck('copy:'+name,sha(name)==sha(q['source'])==q['sha256'])
ck('6_copies',len(pres['copies'])==6)
prepared=[p for p in (F/'prepared').rglob('*') if p.is_file()]
ck('91_corrected_files',len(prepared)==91 and all(str(p) in pres['frozen_publications'] for p in prepared))
for p in D.rglob('*.py'):
 if p.name=='prepare-initial.py':continue
 ast.parse(p.read_text());bindings[str(p)]=sha(p)
ck('canonical_python_AST',True)
initial=(D/'prepare-initial.py').read_text();corrected=(D/'prepare.py').read_text()
ck('single_removed_parenthesis',len(initial)==len(corrected)+1 and any(initial[:i]+initial[i+1:]==corrected for i,c in enumerate(initial) if c==')'))
try:ast.parse(initial)
except SyntaxError as e:ck('initial_failure_preserved',e.lineno==22 and "unmatched ')'" in str(e))
else:raise AssertionError('initial syntax unexpectedly valid')
# Extract only explicitly named NEW pure helpers; never import executable mains or guards.
cns=dict(Path=Path,hashlib=hashlib,json=json,math=math)
selected={'require','sha','read','number','accumulate','includes','prior','command','environment','admission_fields','check_inventory','ensure_unused'}
tree=ast.parse((D/'common.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected],type_ignores=[]),str(D/'common.py'),'exec'),cns)
cns.update(D=D,W=W,FIX=F,PREPARED=F/'prepared',ORIGINAL=W/'diagnostics/dual-recovery-devex-task4/2026-10-30',OLD_RED=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30',OLD_GREEN=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30',OUT=Path(contract['output_root']),USED=527.9604928489425,TOTAL=1800,JULIA=contract['command'][0],DEPOTS=contract['environment']['JULIA_DEPOT_PATH'])
C=types.SimpleNamespace(**cns)
used,facts=C.prior();ck('prior_facts_exact',used==contract['used_seconds']==527.9604928489425 and facts==contract['previous'])
ck('remaining_exact',1800-used==contract['remaining_seconds']==1272.0395071510575)
ck('command_environment_exact',C.command()==contract['command'] and C.environment()==contract['environment'])
ck('no_output',not C.OUT.exists())
ck('old_green_failed',not (C.OLD_GREEN/'green/audit.json').exists() and read(C.OLD_GREEN/'green/supervisor.json')['accepted'] is False)
# New copied fixture helper: only definitions/constant assignments/imports, never its CLI.
ft=ast.parse((D/'fixture_check.py').read_text());fns={}
exec(compile(ast.Module(body=[n for n in ft.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.Assign))],type_ignores=[]),str(D/'fixture_check.py'),'exec'),fns)
fq=fns['check'](F/'prepared',read(D/'fixture-manifest.json'))
ck('fixture_graph',fq['accepted'] and (fq['program_count'],fq['fixture_count'],fq['include_edges'])==(15,2,14))
ans=dict(C=C,math=math,re=re)
at=ast.parse((D/'audit.py').read_text())
exec(compile(ast.Module(body=[n for n in at.body if isinstance(n,ast.FunctionDef) and n.name in {'integer','number','stats','summary','ordinary','endpoint','process','resource'}],type_ignores=[]),str(D/'audit.py'),'exec'),ans)
records=tomllib.loads((C.OLD_GREEN/'green/result.toml').read_text())['cases']
ck('recorded_endpoint_valid',ans['endpoint'](records))
refusals=[]
for k,v in [('iterations',True),('final_ftran',3),('final_btran',3),('point',[True,0]),('retained_julia_bytes',False)]:
 q=copy.deepcopy(records);q[0][k]=v
 try:ans['endpoint'](q)
 except ValueError:refusals.append(k)
ck('endpoint_mutants_refused',len(refusals)==5)
try:ans['ordinary']((C.OLD_GREEN/'green/guard/run.log').read_text())
except ValueError:ck('recorded_failed_green_refused',True)
else:raise AssertionError('old failure accepted')
# Accurate output SHAPE implied by inspected local Test source, not simulated Julia success.
log=''.join('TASK4_INCLUDED '+p+'\n' for p in C.includes())+'Test Summary: | Pass Total Time\nTASK4_GREEN | 6000 6000 1.0s\nTASK4_GREEN_COMPLETED\n'
try:ans['ordinary'](log)
except ValueError as e:summary_failure=str(e)
else:summary_failure=None
ck('all_green_shape_false_rejection_reproduced',summary_failure=='missing/duplicate ordinary summary TASK4_POST_FALLBACK')
text=T.read_text();driver=(F/'prepared/green.jl').read_text()
ck('source_establishes_nonverbose_nested_suppression', 'if get_testset_depth() != 0' in text and 'if ((n_passes + n_broken != subtotal) || print_verbose(ts))' in text and 'Base.get_bool_env("JULIA_TEST_VERBOSE", false)' in text and '@testset "TASK4_GREEN" begin' in driver and 'verbose' not in driver and 'JULIA_TEST_VERBOSE' not in contract['environment'])
ck('launch_clears_inherited_julia_env',"if key.startswith('JULIA_'):del os.environ[key]" in (D/'launch.py').read_text())
for p in [T,*[p for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts]]:bindings[str(p)]=sha(p)
refs=subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD','master','origin/master'],text=True).splitlines()
ck('refs_exact',refs==['514e22c1a5e8a056bb81e4d9a63b1e6003040df1','c0fa748ffa61ccb7c1caaf248c40324f60bc737b','c0fa748ffa61ccb7c1caaf248c40324f60bc737b'])
for args in [('diff','HEAD','--name-only'),('diff','--cached','--name-only'),('diff','master','HEAD','--','src','test','Project.toml','.github')]:ck('git:'+str(args),not subprocess.check_output(['git','-C',str(W),*args],text=True).strip())
ck('host733',len(read(D/'host.json')['host']['checked_groups'])==733)
result=dict(accepted=False,scope='offline_preparation',runtime_qualified=False,numerical_admission=False,checks=checks,bindings=bindings,source_bindings_verified=425,prior_files_verified=402,corrected_files_verified=91,exact_copies_verified=6,fixture_graph=[15,14,2],finding=dict(priority=1,path=str(D/'audit.py'),line=26,error=summary_failure,reason='Unchanged nonverbose all-green parent Test hides nested endpoint summary; required line cannot be emitted.'),no_julia=True)
Path('/tmp/devex-green2-review-check-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','checks')},indent=2));print('Assertions passed:',len(checks))
