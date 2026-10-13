"""New offline synthetic audit checks and exact admission manifest."""
from common import *
import ast,copy

def synthetic():
 raw={'lifecycles':[],'work':[],'cost':[],'errors':[],'ambient_restored':True,'all_passed':True,'source':str(R/'src/JSimplex.jl'),'Julia_version':'1.13.0'}
 for n,H in ((3,3),(3,64),(8,8),(8,64)):
  raw['work'].append({'n':n,'H':H,'checks':dict.fromkeys([s+'_'+k for s in ('reference','candidate') for k in ('counts','failure','clear_and_retain')],True),'counts':[{'side':'reference','row_reads':[2]*n+[1]*(H-n)},{'side':'candidate','row_reads':[1]*n+[0]*(H-n)}]})
 for t in ('Float32','Float64','BigFloat','Rational{BigInt}'):
  for d in ('Dict','OrderedDict'):
   for k in ('sparse','dense','storedzeros'):
    ck=[f'stage{i}_{q}' for i in range(1,5) for q in ('same_factor','reference_solves','candidate_solves','private_owners')]+['saved_reference','saved_candidate','inputs_preserved']
    raw['lifecycles'].append({'type':t,'dictionary':d,'kind':k,'checks':dict.fromkeys(ck,True),'stages':[dict(dimension=n,row_capacity=24,reference_workspace_graph=100,candidate_workspace_graph=100) for n in (24,6,6,24)]})
  for k in ('sparse','retained','dense'):
   windows=[]
   for pair in range(1,11):
    for side in (('reference','candidate') if pair%2 else ('candidate','reference')):
     windows.append(dict(pair=pair,side=side,phase='warm' if pair<=3 else 'measured',repetitions=4,seconds=1.,bytes=32,events=1,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.))
   raw['cost'].append(dict(type=t,kind=k,n=32,H=256 if k=='retained' else 32,checks=dict.fromkeys([f'pair{i}_same_factor' for i in range(1,11)]+['reference_solves','candidate_solves','input_preserved','compile_zero'],True),windows=windows,reference_graph=100,candidate_graph=100))
 return raw
raw=synthetic();ck={'synthetic_valid':raw_ok(raw)}
mutations={
 'missing_life':lambda r:r['lifecycles'].pop(),
 'missing_work':lambda r:r['work'].pop(),
 'wrong_count':lambda r:r['work'][0]['counts'][1]['row_reads'].__setitem__(0,2),
 'wrong_dict':lambda r:r['lifecycles'][0].update(dictionary='other'),
 'bad_solve':lambda r:r['lifecycles'][0]['checks'].update(saved_candidate=False),
 'bad_owner':lambda r:r['lifecycles'][0]['checks'].update(stage1_private_owners=False),
 'missing_window':lambda r:r['cost'][0]['windows'].pop(),
 'compile':lambda r:r['cost'][0]['windows'][6].update(compile_seconds=1.),
 'nan':lambda r:r['cost'][0]['windows'][6].update(seconds=float('nan')),
 'negative':lambda r:r['cost'][0]['windows'][6].update(bytes=-1),
 'wrong_order':lambda r:r['cost'][0]['windows'][0].update(side='candidate'),
 'truthy':lambda r:r.update(all_passed=1),
 'error':lambda r:r['errors'].append('failed')}
for name,mutate in mutations.items():
 x=copy.deepcopy(raw);mutate(x);ck['reject_'+name]=not raw_ok(x)
for p in D.glob('*.py'):ast.parse(p.read_text())
ck['source_checks_pass']=read(D/'source-checks.json')['all_passed'] is True
ck['plan_copies_identical']=(D/'plan.md').read_bytes()==(R/'docs/superpowers/plans/2026-10-13-markowitz-row-count-fusion.md').read_bytes()
ck['constructor_count']=8+24*2+12*2==80
ck['refactor_count']=24*6+12*(4+20*4)==1152
ck['solve_count']=24*20+12*4==528
require(all(ck.values()),'offline admission checks')
dump(D/'preparation.json',{'all_passed':True,'checks':ck,'scope':'Python-only synthetic/source checks. No Julia parse/import/execution.'})
paths={p for p in D.rglob('*') if p.is_file() and p.name!='postcheck.py'}
paths.add(R/'docs/superpowers/plans/2026-10-13-markowitz-row-count-fusion.md')
paths.update(R/p for p in subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],text=True).splitlines())
paths.update(R/p for p in ('Manifest.toml','LocalPreferences.toml'))
old=read(D.parent/'MA-A/launch-pins.json')
paths.update(Path(p).resolve() for p in old['inventory'] if '/juliaup/' in p)
paths.update(p for p in Path('/home/jspitz/.julia/packages/OrderedCollections').glob('*/src/**/*.jl'))
paths.update((WRAPPER,Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/julia.sh'),Path('/usr/bin/python3'),Path('/bin/bash')))
required={str(p):sha(p) for p in sorted(paths)};dump(D/'required-paths.json',required);paths.add(D/'required-paths.json')
pins={'files':sorted(map(str,paths)),'trees':[],'inputs':[],'inventory':{str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}}
dump(D/'launch-pins.json',pins)
print({'checks':len(ck),'pins':len(paths),'manifest_sha256':sha(D/'launch-pins.json')})
