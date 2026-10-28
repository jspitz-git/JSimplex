from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');sys.path.insert(0,str(D));import common as c
c.need(c.read('admission.json')['accepted'] is False,'initial rejection preserved');c.unchanged()
s=(D/'fixtures.jl').read_text()
old='column=[T((shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*((i*7)%n+1)//16) for i in 1:n]'
new='''column=[density===:sparse&&i%4!=0 ? zero(T) : T((shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*((i*7)%n+1)//16) for i in 1:n]
 @assert count(!iszero,column)==(density===:sparse ? div(n,4) : n)'''
c.need(s.count(old)==1,'sparse defect selector');s=s.replace(old,new)
needle='  if T<:AbstractFloat\n'
extra='''  if T<:AbstractFloat
   a=fixture(T,0,:sparse,:positive,:residual;mode=:slack);b=fixture(T,0,:sparse,:positive,:residual;mode=:slack)
   @test iszero(checkpair(a,b,:A)[2])
   for tag in (Val(:original),Val(:C))
    a=fixture(T,4,:dense,:positive,:crash;cap=2);a.column.=T.([1,2,4,1])
    pol=J.NumericalPolicy(T;pivot_error_tolerance=T(1//2),max_pivot_candidates=2)
    @test modof(tag)._crash_rows!(a.rows,a.w,a.column,pol)==[3]
   end
  end
  for tag in (Val(:original),Val(:B))
   for pv in (T(1//4),-T(1//4))
    a=fixture(T,4,:dense,:positive,:update);a.column[1]=pv;b=merge(a,(tol=T(1//4),))
    @test_throws LinearAlgebra.ZeroPivotException whole(tag,b)
    a.column[1]=pv+sign(pv)*T(1//1024);@test whole(tag,b)===a.f
   end
   a=fixture(T,4,:dense,:positive,:update);resize!(a.column,3)
   @test_throws DimensionMismatch whole(tag,a)
   a=fixture(T,4,:dense,:positive,:update)
   @test_throws BoundsError modof(tag).replace_column!(a.f,a.column,5;zero_tolerance=zero(T))
  end
'''
s=s.replace(needle,extra+needle,1)
(D/'fixtures-ready.jl').write_text(s)
(D/'driver-ready.jl').write_text((D/'driver.jl').read_text().replace('fixtures.jl','fixtures-ready.jl'))
(D/'common_ready.py').write_text((D/'common.py').read_text().replace('contract.json','contract-ready.json').replace('pins.json','pins-ready.json'))
(D/'launch-ready.py').write_text((D/'launch.py').read_text().replace('from common import','from common_ready import').replace('admission.json','admission-ready.json').replace('contract.json','contract-ready.json').replace('pins.json','pins-ready.json'))
(D/'audit-ready.py').write_text((D/'audit.py').read_text().replace('from common import','from common_ready import').replace("'contract.json'","'contract-ready.json'").replace("'pins.json'","'pins-ready.json'").replace("'audit.py'","'audit-ready.py'"))
con=c.read('contract.json');con['command']=[v.replace('driver.jl','driver-ready.jl') for v in con['command']];c.put('contract-ready.json',con)
(D/'SCOPE-ERRATUM.md').write_text('''# Prelaunch scope correction
Initial design/plan and rejected admission remain immutable. The original C sparse fixtures were accidentally dense: fixtures-ready.jl now creates exactly n/4 nonzero direction entries for sparse versus n for dense and asserts the counts. Same grid and all1192cells/21456windows retained, no candidate or numerical launch changed.
Empty residual, PFI dimension/index rejection and signed nonzero pivot cutoff boundaries, and strict crash cutoff boundary are now explicit ordinary assertions. Ties/zero/no-violation/custom views are correctness-only; measured C shapes are positive/negative/mixed with caps1/8. This corrects the broader initial plan wording.
Shared pivot helper: every PFI/HH/triangular/BG call is comparison-only, and BF Markowitz already overrides it separately. The short private numerical comparison measures genuine PFI replace_column! only; direct stored512/ambient64-256/NaNInf/signedzero/threshold tests qualify the helper values, and source audit qualifies comparison-only consumers. No claim of runtime HH/triangular/BG coverage is made in this comparison. Production admission separately requires fresh existing HH precision, triangular scalar and BG update regressions on the accepted stage before any integration. No full-module clone or global overwrite is introduced to expand this diagnostic.
''')
shutil.copyfile(__file__,D/'review-fix.py');c.put('review-fix.json',dict(Julia_executed=False,candidates_unchanged={arm:c.sha(D/(arm+'.jl')) for arm in ['Reference','A','B','C']},old_sparse_selector=old,new_sparse_nonzeros='n/4 vs n asserted',preserved_originals=True,original_pins=c.sha(D/'pins.json'),scope_erratum=c.sha(D/'SCOPE-ERRATUM.md')))
c.put('ready-host.json',c.host());paths=set(c.read('pins.json')['files']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-ready.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[str(D/'grid.toml')],inventory={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=c.sha(p)) for p in sorted(paths)}))
print('ready',len(paths),'pins; old failed admission and all original files unchanged; noJulia')
