from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');O=D.parents[1]/'generic-ratio-monitor/2026-10-27';sys.path.insert(0,str(D));import common as c
s=(D/'fixtures.jl').read_text();shutil.copyfile(D/'fixtures.jl',D/'fixtures.before-author-check.jl')
s=s.replace('sink(x::Bool)=Int(x)','sink(x::Bool)=Int(x)\nsink(x::Rational)=Int(x>0)')
s=s.replace('one=whole(Val(:B),b);two=whole(Val(:B),b);@test one[2]!==two[2]','result1=whole(Val(:B),b);result2=whole(Val(:B),b);@test result1[2]!==result2[2]')
(D/'fixtures.jl').write_text(s)
c.put('author-preseal-check.json',dict(fixes=['Rational returned norm/solve scalar sink','avoid local variable one shadowing Base.one throughout correctness function'],before=c.sha(D/'fixtures.before-author-check.jl'),after=c.sha(D/'fixtures.jl'),Julia_executed=False,candidates_unchanged=True))
old=json.loads((O/'contract-complete.json').read_text());cmd=old['command'][:];cmd=[v.replace(str(O/'driver-complete.jl'),str(D/'driver.jl')).replace(str(O/'output/results.toml'),str(D/'output/results.toml')) for v in cmd]
c.put('contract.json',dict(command=cmd,attempts=1,contexts=19,cases=1632,measured_windows=29376,expected_exit=0,shared_limit_seconds=600,guard_limit_seconds=592,baseline=c.TARGET,ordinary_Test=True))
shutil.copyfile(__file__,D/'seal.py')
paths={n for n in json.loads((O/'MASTER-run/pins.json').read_text())['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
for root in (c.M/'src',c.M/'test',D/'baseline'):paths.update(str(p) for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print('sealed',len(paths),'pins; noJulia')
