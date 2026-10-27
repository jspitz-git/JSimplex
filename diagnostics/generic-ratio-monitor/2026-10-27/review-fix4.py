from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures-ready.jl').read_text();old='(x,fields(v.state.monitor),v.state.last_iteration,v.state.cost_scale,v.state.value_scale)';new='(x,fields(v.w.scratch.stagnation.monitor),v.w.scratch.stagnation.last_iteration,v.w.scratch.stagnation.cost_scale,v.w.scratch.stagnation.value_scale)';assert s.count(old)==1;s=s.replace(old,new)
extra='''   # Unequal stored512 operands whose normalized divisions round equally in all modes.
   near1=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
   near2=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-299);end
   @test near1!=near2
   for mod in (RMReference,RMC,RMBC)
    scale=BigFloat(2);a=mod._stagnation_improvement(near1,near2,scale);b=mod._stagnation_improvement(near1,near2,scale)
    @test iszero(a)&&iszero(b)&&a!==b
    @test a!==near1&&a!==near2&&a!==scale&&precision(a)==precision(BigFloat)
   end
'''
s=s.replace('   # Multi-window independent',extra+'   # Multi-window independent')
(D/'fixtures-complete.jl').write_text(s)
(D/'driver-complete.jl').write_text((D/'driver-ready.jl').read_text().replace('fixtures-ready.jl','fixtures-complete.jl'))
(D/'common_complete.py').write_text((D/'common_ready.py').read_text().replace('contract-ready.json','contract-complete.json').replace('pins-ready.json','pins-complete.json'))
(D/'launch-complete.py').write_text((D/'launch-ready.py').read_text().replace('common_ready','common_complete').replace('contract-ready.json','contract-complete.json').replace('pins-ready.json','pins-complete.json').replace('admission-ready.json','admission-complete.json'))
co=c.read('contract-ready.json');co['command']=[v.replace('driver-ready.jl','driver-complete.jl') for v in co['command']];c.put('contract-complete.json',co)
c.put('review-fix4.json',dict(fixes=['read actual replacement workspace monitor state, not stale retained pre-call state','independent unequal512 rounded-equal zero branch for every mode'],candidate_unchanged=True,Julia_executed=False,bindings={str(D/n):c.sha(D/n) for n in ['fixtures-ready.jl','fixtures-complete.jl','driver-complete.jl','changes.json','contract-complete.json','common_complete.py','launch-complete.py']}))
shutil.copyfile(__file__,D/'review-fix4.py')
paths=set(c.read('pins-ready.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-complete.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_complete as cc;cc.unchanged();cc.put('complete-host.json',cc.host());print('COMPLETE',len(paths),'pins; noJulia')
