from pathlib import Path
import sys,shutil,json
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');O=D/'comparison-2';sys.path.insert(0,str(O));import common_ready as c
c.unchanged();p=c.read('output/process.json');c.need(p['returncode']==1 and p['pins_unchanged'] and p['reason']=='exit1','second failed process unchanged')
log=(O/'output/run.log').read_text();c.need('120716 passed, 4 failed, 0 errored' in log and log.count('Test Failed at ')==4 and log.count('fixtures.jl:171\n  Expression:')==4,'four exact literal oracle failures')
h=c.host([p[k][v] for k in ['runner','child'] for v in ['pgid','sid']]);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);c.put('failure-host.json',h)
Q=D/'comparison-3';Q.mkdir()
for n in ['Reference.jl','A.jl','B.jl','C.jl','extra-tests-ready.jl','common_ready.py','launch-ready.py','environment.json','protected-before.json']:shutil.copyfile(O/n,Q/n)
shutil.copyfile('/tmp/vfp-native-oracle.jl',Q/'native-oracle.jl')
s=(O/'fixtures.jl').read_text();a='if scope===:pivot;@test pattern===:zero ? all(iszero,a.proposal.column)&&all(iszero,b.proposal.column) : same(a.proposal.column,a.wanted)&&same(b.proposal.column,b.wanted);end';b='''if scope===:pivot
    @test same(a.proposal.column,b.proposal.column)
    @test pattern===:zero ? all(iszero,a.proposal.column)&&all(iszero,b.proposal.column) : T===Float64 ? native_direction_oracle(a)&&native_direction_oracle(b) : same(a.proposal.column,a.wanted)&&same(b.proposal.column,b.wanted)
   end''';c.need(s.count(a)==1,'one native oracle correction');s=s.replace(a,b);(Q/'fixtures.jl').write_text(s)
s=(O/'driver-ready.jl').read_text();s=s.replace('include(joinpath(@__DIR__,"extra-tests-ready.jl"))','include(joinpath(@__DIR__,"extra-tests-ready.jl"))\ninclude(joinpath(@__DIR__,"native-oracle.jl"))');s=s.replace('"preparation"=>PREP','"preparation"=>PREP,"native_oracles"=>NATIVE_ORACLES');(Q/'driver-ready.jl').write_text(s)
for n in ['host-seed.json','host-before.json']:(Q/n).write_text(json.dumps(h,indent=2)+'\n')
co=c.read('contract-ready.json');co['command']=[x.replace(str(O),str(Q)) for x in co['command']];(Q/'contract-ready.json').write_text(json.dumps(co,indent=2)+'\n')
s=(O/'audit-ready.py').read_text().replace(str(O),str(Q))
where="c.unchanged();extra=[p[k][v]"
extra='''from fractions import Fraction as F
oracles=data['native_oracles'];c.need(len(oracles)==12,'six native pairs')
for i,o in enumerate(oracles):
 n=o['rows'];c.need(n==4 and len(o['matrix'])==16 and all(type(v) is float for k in ['matrix','column','rhs','wanted'] for v in o[k]),'native typed snapshot')
 A=[[F(o['matrix'][i+n*j]) for j in range(n)] for i in range(n)];x=list(map(F,o['column']));rhs=list(map(F,o['rhs']));wanted=list(map(F,o['wanted']))
 residual=[sum(A[i][j]*x[j] for j in range(n))-rhs[i] for i in range(n)]
 bound=8*F(1,2**52)*max(F(1),max(sum(map(abs,row)) for row in A)*max(map(abs,x)),max(map(abs,rhs)))
 c.need([sum(A[i][j]*wanted[j] for j in range(n)) for i in range(n)]==rhs and list(map(F,o['residual']))==residual and F(o['bound'])==bound and max(map(abs,residual))<=bound and o['construction_exact'] is True and o['passed'] is True,'independent exact native oracle')
 if i%2:c.need(o==oracles[i-1],'original/candidate native snapshots equal')
'''
c.need(s.count(where)==1,'auditor supplement');s=s.replace(where,extra+where);(Q/'audit-ready.py').write_text(s)
(Q/'FIX.md').write_text('Comparison2 rejected unchanged:120716pass4fail0error/exit1. The4failures are newly authored Float64 exact ideal-direction expectations, not baseline/candidate disagreement. Full3328/59904raw retained but not accepted. Float64 uses default UMFPACK sparse LU with scaling, which does not promise bit-exact dyadic output. Replace only that Float64 ideal test with independently recomputed exact-rational residual <=8eps(Float64)*max(1,||B||inf||x||inf,||rhs||inf), frozen before run; require exact B*wanted==rhs. Keep strict bitwise original/candidate columns, all existing status/quality/inputowners/safeguards/context/compilation checks, and exact ideal comparisons for all other types. Twelve tiny native snapshots outsidewindows record matrix/column/rhs/wanted/residual/bound; Pythonauditor independently recomputes everyFraction. Numerical production tolerance/precision/backend and all candidates/grid/costs unchanged. One reviewed corrected600scomparison, all earlier failedraw/pins remain frozen.\n')
(Q/'fix-checks.json').write_text(json.dumps(dict(accepted=True,exact_fixture_inverse=(Q/'fixtures.jl').read_text().replace(b,a)==(O/'fixtures.jl').read_text(),original_failures=4,original_errors=0,source_candidates_unchanged=True,bindings={str(O/n):c.sha(O/n) for n in ['fixtures.jl','driver-ready.jl','output/run.log','output/process.json','output/results.toml','pins-ready.json','supervisor.json']}),indent=2)+'\n')
shutil.copytree(O/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'));shutil.copyfile(__file__,Q/'prepare.py')
paths=set(c.read('pins-ready.json')['inventory']);paths.update(str(O/n) for n in ['pins-ready.json','admission.json','INDEPENDENT-CORRECTION-REVIEW.md','independent-host.json','output/process.json','output/run.log','output/results.toml','supervisor.json','failure-host.json']);paths.update(str(p) for p in Q.rglob('*') if p.is_file())
pins=dict(files=sorted(paths),trees=c.read('pins-ready.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)});(Q/'pins-ready.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n');print(len(paths),'pins; corrected native oracle noJulia')
