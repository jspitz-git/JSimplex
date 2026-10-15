"""One-shot offline assembly. No Julia parse/import/runtime or old script execution."""
from common import *
import re,os
A=Q.parent/'NATIVE-ACCURACY-PREPARATION'
for n in ['guard.py','supervisor.py']:
 with (Q/n).open('xb') as f:f.write((A/n).read_bytes())
g=(Q/'guard.py').read_text().replace("if record['reason'] == 'exit0' and pressure", "if record['reason'] == f'exit{args.expected_exit}' and pressure").replace("return 0 if record['reason'] == 'exit0' and record['pins_unchanged'] else 1", "return 0 if record['reason'] == f'exit{args.expected_exit}' and record['pins_unchanged'] else 1").replace("execute.add_argument('--seconds'", "execute.add_argument('--expected-exit', type=int, choices=(0,1), required=True)\n    execute.add_argument('--seconds'")
(Q/'guard.py').write_text(g)
# New exact-oracle helper copy, never imports or executes the old auditor.
analysis=(A/'analysis.py').read_text();analysis=analysis[:analysis.index('def analyze(')]
with (Q/'exact.py').open('x') as f:f.write(analysis)
inputs=rd(A/'inputs.json');fixtures=inputs['fixtures'];schedule=[]
for fixture in fixtures:
 for round in range(1,12):
  for arm in (['C','P'] if round%2 else ['P','C']):schedule.append(dict(id=len(schedule)+1,fixture=fixture['name'],arm=arm,round=round,warm=round<=3))
save(Q/'inputs.json',dict(fixtures=fixtures,schedule=schedule))
# Reuse exact original TOML input, driver reads only its four fixture tables.
with (Q/'inputs.toml').open('xb') as f:f.write((A/'inputs.toml').read_bytes())
# All saved default-arm outputs, no old execution.
old=Q.parent/'NATIVE-ACCURACY-QUALIFICATION/portable'
import tomllib
refs={}
for s in inputs['schedule']:
 if s['arm']=='C':
  z=tomllib.loads((old/f"window-{s['id']:03d}.toml").read_text())
  refs.setdefault(s['fixture'],[]).append(dict(path=str(old/f"window-{s['id']:03d}.toml"),sha256=sha(old/f"window-{s['id']:03d}.toml"),outputs=z['outputs']))
save(Q/'saved-C.json',refs)
# Exact lexical slices: select whole top-level testsets and required helper, no edits.
specs=[('test/factorization_tests.jl',['Parametric factorization backends','Float64 factorization backend stability','Dimension-changing refactorization resizes solve scratch']),('test/hypersparse_factorization_edge_tests.jl',['Owned snapshots survive backend reuse and solve aliases']),('test/triangular_reset_allocation_tests.jl',['Triangular identity reset uses current BigFloat precision without changing copies'])]
text='using Test, JSimplex, LinearAlgebra, SparseArrays\n';slices=[]
for name,titles in specs:
 src=(R/name).read_text();starts=list(re.finditer(r'^@testset "([^"]+)"',src,re.M))
 if name=='test/factorization_tests.jl':
  block=src[:starts[0].start()];text+=block;slices.append(dict(source=name,start=0,end=starts[0].start(),text=block))
 for title in titles:
  i=next(i for i,m in enumerate(starts) if m[1]==title);lo=starts[i].start();hi=starts[i+1].start() if i+1<len(starts) else len(src)
  block=src[lo:hi];text+=block;slices.append(dict(source=name,title=title,start=lo,end=hi,text=block))
with (Q/'neighbors-original.jl').open('x') as f:f.write(text)
save(Q/'neighbor-slices.json',slices)
# Diagnostic wrappers only in test text; every substitution reverses exactly.
names=['_factorize_basis','_basis_factorization','PFIFactorization','ForrestTomlinFactorization','SuhlSuhlFactorization','BartelsGolubFactorization','UMFPACKBackend','refactorize!','_refactorize_backend','copy_basis_factorization','replace_column!','forward_solve','transpose_solve','hypersparse_forward_solve!','hypersparse_transpose_solve!','sparse_solve_view']
changes={}
for source,dest,prefix in [(PREV/'candidate/test/native_pivot_policy_tests.jl','tests-observed.jl','J'),(Q/'neighbors-original.jl','neighbors-observed.jl','JSimplex')]:
 src=source.read_text();new=src;edits=[]
 for name in names:
  a=prefix+'.'+name;b='Main.NP.'+name
  # Don't replace a prefix of a longer identifier or bang variant.
  pat=re.escape(a)+r'(?![A-Za-z0-9_!])';count=len(re.findall(pat,new));new=re.sub(pat,b,new)
  if count:edits.append([a,b,count])
 # Raw LU wraps only these test expressions; no production method mutation.
 new,count=re.subn(r'(?<![A-Za-z0-9_.])lu\(', 'Main.NP.raw_lu(',new)
 if count:edits.append(['lu(','Main.NP.raw_lu(',count])
 undo=new
 for a,b,count in reversed(edits):require(undo.count(b)==count,'inverse count');undo=undo.replace(b,a)
 require(undo==src,'whole inverse')
 with (Q/dest).open('x') as f:f.write(new)
 changes[dest]=dict(source=str(source),source_sha256=sha(source),sha256=sha(Q/dest),edits=edits)
save(Q/'test-inverse.json',changes)
# Fixed expected assertion and entry counts. No runtime measurement implied.
main=dict(_factorize_basis=7,_basis_factorization=114,UMFPACKBackend=2,refactorize=120,copy_basis_factorization=24,replace_column=24,forward_solve=226,transpose_solve=202,sparse_solve_view=2,raw_lu=1)
neighbors=dict(PFIFactorization=9,ForrestTomlinFactorization=1,SuhlSuhlFactorization=1,BartelsGolubFactorization=1,_factorize_basis=6,refactorize=6,_refactorize_backend=6,copy_basis_factorization=3,replace_column=3,forward_solve=7,transpose_solve=6,hypersparse_forward_solve=8,hypersparse_transpose_solve=2,sparse_solve_view=9,UMFPACKBackend=1,raw_lu=1)
save(Q/'budget.json',dict(test_groups={'options_and_copy_intent':4946,'backend_owned_policy':35,'private_spare_copy_and_failure':1568,'precision_and_factory_dispatch':245,'Parametric factorization backends':25,'Float64 factorization backend stability':4,'Dimension-changing refactorization resizes solve scratch':4,'Owned snapshots survive backend reuse and solve aliases':19,'Triangular identity reset uses current BigFloat precision without changing copies':12},main=main,neighbors=neighbors,green_assertions=6858,red_assertions=4,cost=dict(construction=88,refactor=176,forward=2816,transpose=1408,windows=88,fresh_native_source=176,private_lu_source=88),public_solves=0))
# Freeze actual environment and read-time runtime/library dependency set.
keys=('HOME','PATH','JULIA_LOAD_PATH','JULIA_PROJECT','JULIA_DEPOT_PATH','JULIA_CPU_TARGET','JULIA_BINDIR','LD_LIBRARY_PATH','LD_PRELOAD')
save(Q/'environment.json',{k:os.environ.get(k) for k in keys})
base=rd(A/'preparation-pins-reviewed.json')
files=sorted({n for n in base['files'] if Path(n).is_file() and not Path(n).is_relative_to(R/'diagnostics') and not Path(n).is_relative_to(R/'docs') and not Path(n).is_relative_to(R/'test')})
save(Q/'runtime-pins.json',dict(sha256={n:sha(n) for n in files},scope='Fresh read-time hashes, not retrospective launch pins; includes wrapper chain, Julia, installed source/libs and actual source/env. No loaded-image/cache completeness claim.'))
save(Q/'prepare.json',dict(all_passed=True,windows=len(schedule),neighbors=len(slices)-1,sha256={str(p):sha(p) for p in [Path(__file__),PREV/'candidate/test/native_pivot_policy_tests.jl',PREV/'overlay-manifest.json',A/'inputs.json',A/'inputs.toml',A/'guard.py',A/'supervisor.py',A/'analysis.py']}))
print('Offline preparation only: 88 windows, five unchanged neighbors, invertible test instrumentation')
