from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures-reviewed.jl').read_text().replace('variant===:negative512 ? -wide :','variant===:negative512 ? setprecision(()->BigFloat(-3//7),BigFloat,512) :')
marker='   # Multi-window independent state transitions and fresh result owners.'
extra='''   widepositive=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
   widenegative=setprecision(()->-widepositive,BigFloat,512)
   @test precision(widepositive)==precision(widenegative)==512
   for arm in (:B,:C,:BC),wide in (widepositive,widenegative)
    a=fixture(T,8,:dense,:mixed,:progress,:end);b=fixture(T,8,:dense,:mixed,:progress,:end)
    for v in (a,b)
     v.m.best_objective=deepcopy(wide);v.m.best_primal=deepcopy(widepositive);v.m.best_dual=deepcopy(widepositive)
    end
    a=merge(a,(seed=fields(a.m),values=(wide,deepcopy(widepositive),deepcopy(widepositive),a.values[4],a.values[5]),))
    b=merge(b,(seed=fields(b.m),values=(deepcopy(wide),deepcopy(widepositive),deepcopy(widepositive),b.values[4],b.values[5]),))
    checkpair(a,b,arm)
    a=fixture(T,8,:dense,:mixed,:workspace);b=fixture(T,8,:dense,:mixed,:workspace)
    for v in (a,b)
     v.w.costs[1]=deepcopy(wide);v.w.lower[1]=J.Bound(deepcopy(widenegative));v.w.upper[1]=J.Bound(deepcopy(widepositive))
    end
    checkpair(a,b,arm)
   end
   for mod in (RMReference,RMC,RMBC),(a,b) in ((BigFloat(1),BigFloat(1)),(widepositive,BigFloat(1)))
    scale=BigFloat(1);z=mod._stagnation_improvement(a,b,scale);q=mod._stagnation_improvement(a,b,scale)
    @test iszero(z)&&iszero(q)&&z!==q
    @test z!==a&&z!==b&&z!==scale
    @test precision(z)==precision(BigFloat)
   end
'''
assert marker in s;s=s.replace(marker,extra+marker)
(D/'fixtures-final.jl').write_text(s)
(D/'driver-final.jl').write_text((D/'driver-reviewed.jl').read_text().replace('fixtures-reviewed.jl','fixtures-final.jl'))
(D/'common_final.py').write_text((D/'common_reviewed.py').read_text().replace('contract-reviewed.json','contract-final.json').replace('pins-reviewed.json','pins-final.json'))
(D/'launch-final.py').write_text((D/'launch-reviewed.py').read_text().replace('common_reviewed','common_final').replace('contract-reviewed.json','contract-final.json').replace('pins-reviewed.json','pins-final.json').replace('admission-reviewed.json','admission-final.json'))
co=c.read('contract-reviewed.json');co['command']=[v.replace('driver-reviewed.jl','driver-final.jl') for v in co['command']];c.put('contract-final.json',co)
c.put('review-fix2.json',dict(fixes=['actual stored512 negative step','stored512 objective/violation/anchor progress and full workspace observers','fresh zero C equality and rounded-equal branch'],candidate_unchanged=True,bindings={str(D/n):c.sha(D/n) for n in ['fixtures-reviewed.jl','fixtures-final.jl','driver-final.jl','changes.json','contract-final.json','common_final.py','launch-final.py']}))
shutil.copyfile(__file__,D/'review-fix2.py')
paths=set(c.read('pins-reviewed.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-final.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_final as cc;cc.unchanged();cc.put('final-ready-host.json',cc.host());print('final fixtures sealed',len(paths),'pins; noJulia')
