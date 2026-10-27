from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common as c
c.need(c.read('admission.json')['accepted'] is False,'preserved initial rejection')
s=(D/'fixtures.jl').read_text().replace('function ratio_fixture(', 'isresidual(scope)=scope in (:direction_residual,:row_residual)\nfunction ratio_fixture(')
s=s.replace(':mixedprecision,:alias)',':mixedprecision,:alias,:empty)')
s=s.replace('if variant===:zero;fill!(v.vector,zero(T))','if variant===:empty;empty!(w.basis.basic_indices)\n    elseif variant===:zero;fill!(v.vector,zero(T))')
s=s.replace('first row wins a tie.','largest pivot wins the equal-ratio Harris pass.').replace('x[2]==1&&x[3]===J.AT_LOWER','x[2]==8&&x[3]===J.AT_LOWER')
insert='''  # Exact dyadic tolerated violation, both entering orientations and unsafe snap.
  for unsafe in (false,true),direction in (-one(T),one(T))
   a=fixture(T,2,:dense,:negative,:ratio);b=fixture(T,2,:dense,:negative,:ratio)
   for v in (a,b)
    w=v.w;opts=w.options;tol=T(1//8)
    w.options=typeof(opts)((n===:primal_tolerance ? tol : getfield(opts,n) for n in fieldnames(typeof(opts)))...)
    v.vector[1]=-one(T);v.vector[2]=unsafe ? T(10) : -T(2)
    if direction>0;w.lower[1]=J.Bound(zero(T));else;w.upper[1]=J.Bound(zero(T));end
    for i in eachindex(v.vector);v.vector[i]*=direction;end
    w.upper[2]=J.Bound(one(T));w.primal[2]=T(17//16)
    w.lower[3]=J.Bound(zero(T));w.upper[3]=J.Bound(unsafe ? zero(T) : T(2))
    push!(w.scratch.rejected_rows,2)
   end
   a=merge(a,(orientation=direction,));b=merge(b,(orientation=direction,))
   @test J._primal_bound_snap_feasible(a.w,1,direction,a.vector,1)===!unsafe
   @test !J._primal_step_bounds_feasible(a.w,direction,a.vector,one(T))
   x=checkpair(a,b,:A)
   @test x[1]===:value&&(unsafe ? isnothing(x[2][1])&&x[2][2]==-1 : iszero(x[2][1])&&x[2][2]==1)
  end
'''
s=s.replace('  # Independent known identity direction:',insert+'  # Independent known identity direction:')
# Include full monitor alias topology and input-scalar immutability outside timed windows.
s=s.replace('function checkpair(a,b,arm)','aliaspattern(q)=Bool[q[i]===q[j] for i in eachindex(q),j in eachindex(q)]\nfunction checkpair(a,b,arm)')
s=s.replace('ctx=(precision(BigFloat),rounding(BigFloat))\n x=capture', 'ctx=(precision(BigFloat),rounding(BigFloat))\n scalar_a=a.scope===:progress ? deepcopy(a.values) : ();scalar_b=b.scope===:progress ? deepcopy(b.values) : ()\n x=capture',1)
s=s.replace(' @test intact(a,sa)&&intact(b,sb)',''' if a.scope===:progress
  @test same(a.values,scalar_a)&&same(b.values,scalar_b)
  @test aliaspattern((fields(a.m)...,a.values...))==aliaspattern((fields(b.m)...,b.values...))
 end
 @test intact(a,sa)&&intact(b,sb)''',1)
s=s.replace('   # Multi-window independent', '''   for arm in (:B,:C,:BC),variant in (:positive512,:negative512,:signedzero,:infstep,:negativeinf)
    a=fixture(T,8,:dense,:mixed,:progress,:end);b=fixture(T,8,:dense,:mixed,:progress,:end)
    wide=setprecision(()->BigFloat(3//7),BigFloat,512)
    val=variant===:positive512 ? wide : variant===:negative512 ? -wide : variant===:signedzero ? -zero(T) : variant===:infstep ? T(Inf) : -T(Inf)
    a=merge(a,(values=(a.values[1],a.values[2],a.values[3],val,val),));b=merge(b,(values=(b.values[1],b.values[2],b.values[3],deepcopy(val),deepcopy(val)),))
    # Shared step owners must be mirrored on both sides.
    b=merge(b,(values=(b.values[1],b.values[2],b.values[3],b.values[4],b.values[4]),))
    checkpair(a,b,arm)
   end
   # Multi-window independent''')
(D/'fixtures-reviewed.jl').write_text(s)
(D/'driver-reviewed.jl').write_text((D/'driver.jl').read_text().replace('"fixtures.jl"','"fixtures-reviewed.jl"'))
(D/'common_reviewed.py').write_text((D/'common.py').read_text().replace("'contract.json'","'contract-reviewed.json'").replace("'pins.json'","'pins-reviewed.json'"))
(D/'launch-reviewed.py').write_text((D/'launch.py').read_text().replace('from common import','from common_reviewed import').replace("'contract.json'","'contract-reviewed.json'").replace("'pins.json'","'pins-reviewed.json'").replace("'admission.json'","'admission-reviewed.json'"))
co=c.read('contract.json');co['command']=[v.replace(str(D/'driver.jl'),str(D/'driver-reviewed.jl')) for v in co['command']];c.put('contract-reviewed.json',co)
c.put('review-fix.json',dict(fixes=['missing pure isresidual helper','known equal-step Harris largest-pivot oracle row8','empty basis','dyadic tolerated-negative safe/unsafe both orientations','complete monitor scalar alias topology/input preservation','stored512/signedzero/infinite observation steps'],candidate_unchanged=True,Julia_executed=False,bindings={str(D/n):c.sha(D/n) for n in ['admission.json','fixtures.jl','fixtures-reviewed.jl','driver.jl','driver-reviewed.jl','changes.json','contract-reviewed.json','common_reviewed.py','launch-reviewed.py']}))
shutil.copyfile(__file__,D/'review-fix.py')
paths=set(c.read('pins.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-reviewed.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_reviewed as cc;cc.unchanged();cc.put('reviewed-host.json',cc.host());print('reviewed fixtures sealed',len(paths),'pins; noJulia')
