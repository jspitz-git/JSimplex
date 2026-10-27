from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');sys.path.insert(0,str(D));import common as c
s=(D/'extra-tests-final.jl').read_text().replace('# A reliable tiny pivot must still fail the finite reciprocal gate.','# A reliable tiny pivot crosses the reciprocal range boundary. Directed\n   # rounding may cap overflow at floatmax; require the original decision.')
a='   z=checkpair(a,b);@test z[1]===:value&&z[2]===:reject_candidate'
b='''   for v in (a,b)
    B=J._basis_matrix!(v.w);p=v.proposal.column[1];pol=v.w.progress.numerical_policy
    @test J.solve_quality!(J.SolveQualityScratch(BigFloat,1),B,v.proposal.column,[BigFloat(2)*p],pol).reliable
    @test J.solve_quality!(J.SolveQualityScratch(BigFloat,1),B,v.proposal.rho,[BigFloat(1)],pol;transposed=true).reliable
   end
   z=checkpair(a,b);@test z[1]===:value
   !isfinite(inv(a.proposal.column[1]))&&@test z[2]===:reject_candidate'''
c.need(s.count(a)==1,'one reciprocal oracle correction');s=s.replace(a,b);(D/'extra-tests-ready.jl').write_text(s)
s=(D/'driver-final.jl').read_text().replace('extra-tests-final.jl','extra-tests-ready.jl');(D/'driver-ready.jl').write_text(s)
co=c.read('contract-final.json');co['command']=[v.replace('/driver-final.jl','/driver-ready.jl') for v in co['command']];c.put('contract-ready.json',co)
for src,dst in [('common_final.py','common_ready.py'),('launch-final.py','launch-ready.py'),('audit-final.py','audit-ready.py')]:
 s=(D/src).read_text().replace('contract-final.json','contract-ready.json').replace('pins-final.json','pins-ready.json').replace('common_final','common_ready').replace('audit-final.py','audit-ready.py');(D/dst).write_text(s)
(D/'RECIPROCAL-ORACLE.md').write_text('Pre-execution reviewer correction: reciprocal overflow under RoundDown/ToZero may cap at finite floatmax. Both prerequisite quality certificates must be reliable. Preserve whole-call original/candidate parity, require rejection when reciprocal is nonfinite; finite capped reciprocal may continue original checks. No tolerance/precision/candidate/runtime tuning. Original unconditional expectation and all manifests remain unexecuted/preserved. All other amendment obligations remain.\n')
shutil.copyfile(__file__,D/'reciprocal-prepare.py')
pins=c.read('pins-final.json');paths=set(pins['inventory']);paths.update(str(D/n) for n in ['extra-tests-ready.jl','driver-ready.jl','contract-ready.json','common_ready.py','launch-ready.py','audit-ready.py','RECIPROCAL-ORACLE.md','reciprocal-prepare.py','pins-final.json'])
c.put('pins-ready.json',dict(files=sorted(paths),trees=pins['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_ready as f;f.unchanged();f.put('ready-author-host.json',f.host());print(len(paths),'ready pins noJulia')
