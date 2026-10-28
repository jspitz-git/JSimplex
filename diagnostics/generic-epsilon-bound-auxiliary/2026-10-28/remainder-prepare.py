from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
P=D/'remaining';P.mkdir();c.unchanged();h=c.read('failed-close-host.json');c.put(str(P/'host-seed.json'),h);c.put(str(P/'host-before.json'),h)
for n in ['protected-before.json','environment.json']:shutil.copyfile(D/n,P/n)
s=(D/'fixtures.jl').read_text();a=s.index('  for density in (:sparse,:dense)\n');b=s.index('  for scope in (:errors,:direction)\n',a)
s=s[:a]+'''  if T<:AbstractFloat
'''+s[a:b]+'''  else
   for tag in (Val(:original),Val(:C))
    a=fixture(T,8,:sparse,:positive,:auxiliary);before=deepcopy(inputvalues(a));own=owners(inputvalues(a));budget=outputstate(a)
    @test_throws MethodError whole(tag,a)
    @test same(before,inputvalues(a))
    @test sameowners(own,owners(inputvalues(a)))
    @test same(budget,outputstate(a))
   end
  end
'''+s[b:]
(D/'fixtures-supported.jl').write_text(s)
grid=[v for v in c.read('expected-cases.json') if v['context']=='Rational{Int64}' and v['variant']=='B'];c.put(str(P/'expected-cases.json'),grid)
with (P/'grid.toml').open('x') as f:
 for g in grid:
  f.write('[[cells]]\n');f.writelines(f'{k} = {json.dumps(v)}\n' for k,v in g.items())
s=(D/'driver.jl').read_text().replace('joinpath(@__DIR__,arm*".jl")','joinpath(dirname(@__DIR__),arm*".jl")').replace('joinpath(@__DIR__,"fixtures.jl")','joinpath(dirname(@__DIR__),"fixtures-supported.jl")')
a=s.index('  for bits in (64,128,256)');b=s.index('\n end\nfinally',a)
s=s[:a]+'  for T in (Rational{BigInt},Rational{Int64});context(T,string(T));end'+s[b:]
s=s.replace('Epsilon bound auxiliary whole-function comparison','Remaining bound metrics comparison').replace('EPSILON_BOUND_AUXILIARY_COMPLETE','EPSILON_BOUND_AUXILIARY_REMAINING_COMPLETE');(P/'driver.jl').write_text(s)
common=(D/'common_qualified.py').read_text().replace('contract-qualified.json','contract.json').replace('pins-qualified.json','pins.json');(P/'common.py').write_text(common)
launch=(D/'launch-qualified.py').read_text().replace('common_qualified','common').replace('contract-qualified.json','contract.json').replace('pins-qualified.json','pins.json').replace('admission-qualified.json','admission.json');(P/'launch.py').write_text(launch)
audit=(D/'audit-qualified.py').read_text().replace('common_qualified','common').replace('contract-qualified.json','contract.json').replace("D/'pins-qualified.json'","D/'pins.json'").replace("'audit-qualified.py','contract.json','pins-qualified.json'","'audit.py','contract.json','pins.json'").replace('Epsilon bound auxiliary whole-function comparison','Remaining bound metrics comparison').replace('EPSILON_BOUND_AUXILIARY_COMPLETE','EPSILON_BOUND_AUXILIARY_REMAINING_COMPLETE')
audit=audit.replace('len(grid)+38','len(grid)+4').replace('contexts=list(dict.fromkeys(v[\'context\'] for v in grid))',"contexts=con['context_labels']").replace('len(contexts)==19','len(contexts)==2');(P/'audit.py').write_text(audit)
shutil.copytree(D/'guard',P/'guard',ignore=shutil.ignore_patterns('__pycache__'))
cmd=c.read('contract-qualified.json')['command'];cmd[-2:]=[str(P/'driver.jl'),str(P/'output/results.toml')]
c.put(str(P/'contract.json'),dict(command=cmd,attempts=1,contexts=2,context_labels=['Rational{BigInt}','Rational{Int64}'],cases=30,measured_windows=540,correctness_assertions=408,expected_assertions=1428,optimal_status=0,expected_exit=0,shared_limit_seconds=900,guard_limit_seconds=892,baseline=c.TARGET,ordinary_Test=True,scope='ONLY previously unmeasured RationalInt64 B cells, plus conventional Rational C unsupported-route preservation checks. No completed measurement rerun.'))
c.put('route-supplement.json',dict(original_attempt_accepted=False,root_cause='Original _precision_current_bits generic calls precision(T), undefined for Rational; actual LP controller excludes exact types at lp_refinement_driver.jl:308. Failure occurs before C changed body. No production fix or runtime workaround.',prefix_cells=1196,prefix_windows=21528,remaining_cells=30,remaining_windows=540,supported_total_cells=1226,supported_total_windows=22068,original_contract_and_failed_attempt_preserved=True,supported_correctness_assertions=7153,remaining_correctness_assertions=408,original_floating_correctness_assertions=6745,bindings={str(D/n):c.sha(D/n) for n in ['fixtures.jl','fixtures-supported.jl','output/run.log','output/process.json','output/results.toml','supervisor.json']}))
(P/'PLAN.md').write_text('''# Remaining supported cases\n\nOriginal run remains FAILED (55626pass/1fail/2errors); all1196 complete paired cells remain untouched. This separate run measures ONLY thirty previously unmeasured RationalInt64 B cells. It also runs ordinary RationalBigInt/RationalInt64 correctness with four unchanged-input/owner/budget assertions per side proving the original unsupported C wrapper MethodError. No precision method or source workaround. Other floating correctness/measurements are reused from preserved raw with separate strict prefix audit. Separate independent admission,900s shared/892guard, same all resources and fresh677groups/sessions. No Julia before admission.\n''')
shutil.copyfile(__file__,D/'remainder-prepare.py')
paths=set(c.read('pins-qualified.json')['inventory'])
paths.update(str(p) for p in D.iterdir() if p.is_file());paths.update(str(p) for p in (D/'output').iterdir() if p.is_file());paths.update(str(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put(str(P/'pins.json'),dict(files=sorted(paths),trees=c.read('pins-qualified.json')['trees'],inputs=[str(P/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
for p in P.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('remaining-only30 cells540windows/1428checks sealed',len(paths),'pins; no Julia')
