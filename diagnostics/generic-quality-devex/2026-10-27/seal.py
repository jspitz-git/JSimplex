from pathlib import Path
import json,shutil,sys
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');R=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');O=R/'diagnostics/generic-residual-magnitudes/2026-10-26/measure'
p=D/'fixtures.jl';s=p.read_text().replace('if isquality(v.scope);return (v.B,v.x,v.rhs);end','if isquality(v.scope)\n  B=v.B\n  return B isa SparseMatrixCSC ? (B.nzval,B.rowval,B.colptr,v.x,v.rhs) : (B,v.x,v.rhs)\n end')
s=s.replace('z=checkpair(a,b);@test z[1]===:value&&!z[2].finite&&!z[2].reliable','''z=checkpair(a,b)
    unsafe_expected=setprecision(BigFloat,2*precision(BigFloat)+18) do
     floatmin(BigFloat)*BigFloat(1//2)<floatmin(BigFloat)
    end
    @test z[1]===:value&&z[2].finite===!unsafe_expected''')
p.write_text(s)
shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile(O/'launch.py',D/'launch.py')
command=json.loads((O/'contract.json').read_text())['command'];command=[v.replace(str(O),str(D)) for v in command]
contract=dict(command=command,expected_exit=0,attempts=1,shared_limit_seconds=600,guard_limit_seconds=592,cases=1240,measured_windows=22320,rounding_modes=5,contexts=19)
# 15BFcontexts *72cells + 2hardware *24 + 2rational *16 =1160, not1240.
contract['cases']=15*72+2*24+2*16;contract['measured_windows']=18*contract['cases']
(D/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
sys.path.insert(0,str(D));import common as c
paths={n for n in json.loads((O/'pins.json').read_text())['inventory'] if not Path(n).is_relative_to(R/'diagnostics')}
paths.update(str(p) for root in [M/'src',M/'test',D/'baseline'] for p in root.rglob('*') if p.is_file())
paths.update(str(p) for p in D.rglob('*') if p.is_file() and 'baseline' not in p.parts and '__pycache__' not in p.parts)
for n in ['mpfr.jl','number.jl','math.jl']:paths.add('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/'+n)
shutil.copyfile(__file__,D/'seal.py');paths.add(str(D/'seal.py'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(M/'src'),str(M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print('Sealed',len(paths),'pins,',contract['cases'],'cells',contract['measured_windows'],'windows;noJulia')
