from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];O=R/'diagnostics/generic-residual-magnitudes/2026-10-26';arm=sys.argv[1]
if arm not in ['RED','GREEN','MASTER']:raise RuntimeError('arm')
Q=D/(arm+'-run');Q.mkdir();stage=M if arm=='MASTER' else D/arm
base='7e306e24f064a8aa214bc88379e059def77661ab';target=json.loads((D/'production-commit.json').read_text())['commit'] if arm=='MASTER' else base
s=(D/'common.py').read_text().replace("TARGET='"+base+"'","TARGET='"+target+"'")
if arm=='MASTER':s=s.replace("git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET","git(['rev-parse','HEAD'])==git(['rev-parse','master'])==TARGET and git(['rev-parse','origin/master'])=='"+base+"'")
(Q/'common.py').write_text(s)
for n in ['environment.json','protected-before.json']:shutil.copyfile(D/n,Q/n)
last=D if arm=='RED' else D/('RED-run' if arm=='GREEN' else 'GREEN-run');shutil.copyfile(last/'audit-host.json',Q/'host-seed.json')
sys.path.insert(0,str(Q));import common as c
if arm=='MASTER':
 j=c.read('protected-before.json');j['indexes']={n:c.sha(n) for n in j['indexes']};(Q/'protected-before.json').write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
h=c.host();h['diagnostic_head']=c.git(['rev-parse','HEAD'],R);c.put('host-before.json',h)
files=['generic_quality_devex_tests.jl'] if arm=='RED' else ['generic_quality_devex_tests.jl',*json.loads((O/'GREEN-run/contract.json').read_text())['files'],'simplex_numerics_tests.jl','primal_simplex_tests.jl']
(Q/'tests.jl').write_text('''using Test,JSimplex,LinearAlgebra
const ROOT="'''+str(stage)+'''"
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("QUALITY_DEVEX_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Quality Devex '''+arm+'''" begin
 for file in '''+json.dumps(files)+'''
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("QUALITY_DEVEX_COMPLETED '''+arm+'''");flush(stdout)
''')
shutil.copytree(D/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile(O/'GREEN-run/launch.py',Q/'launch.py')
(Q/'audit.py').write_text((O/'GREEN-run/audit.py').read_text().replace('RESIDUAL_MAGNITUDES','QUALITY_DEVEX').replace('Residual magnitudes ','Quality Devex '))
command=[v.replace(str(O/'GREEN-run'),str(Q)).replace('--project='+str(json.loads((O/'GREEN-run/contract.json').read_text())['source_root']),'--project='+str(stage)) for v in json.loads((O/'GREEN-run/contract.json').read_text())['command']]
locations=[[str(stage/'test/generic_quality_devex_tests.jl'),i] for i,line in enumerate((stage/'test/generic_quality_devex_tests.jl').read_text().splitlines(),1) if '# RED whole-call cost gate' in line];c.need(len(locations)==1,'gate location')
c.put('contract.json',dict(arm=arm,source_root=str(stage),command=command,files=files,attempts=1,expected_exit=1 if arm=='RED' else 0,expected_failures=6 if arm=='RED' else 0,expected_failure_locations=locations*6 if arm=='RED' else [],minimum_total=1000,expected_total=c.read('../GREEN-run/audit.json')['total'] if arm=='MASTER' else None,guard_limit_seconds=1792,shared_limit_seconds=1800))
paths={n for n in json.loads((D/'pins.json').read_text())['inventory'] if not Path(n).is_relative_to(R/'diagnostics')}
paths.update(str(p) for root in [M/'src',M/'test',stage/'src',stage/'test'] for p in root.rglob('*') if p.is_file());paths.update(str(stage/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in Q.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for n in ['PLAN.md','WORK-MEMORY.md','changes.json','baseline-tree.json','reference.jl','candidate.jl','fixtures.jl','driver.jl','pins.json','audit.json','result-review.json','new-test.jl','source-inverse.json','production-review.json','production-commit.json','commit-review.json']:
 if (D/n).exists():paths.add(str(D/n))
for n in ['audit.json','result-review.json']:
 if (last/n).exists():paths.add(str(last/n))
shutil.copyfile(__file__,Q/'prepare.py');paths.add(str(Q/'prepare.py'))
c.put('pins.json',dict(files=sorted(paths),trees=sorted({str(M/'src'),str(M/'test'),str(stage/'src'),str(stage/'test')}),inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print(arm,len(files),'files',len(paths),'pins;noJulia')
