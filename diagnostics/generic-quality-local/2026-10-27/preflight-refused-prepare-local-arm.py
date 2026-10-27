from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];O=R/'diagnostics/generic-quality-devex/2026-10-27';arm=sys.argv[1]
if arm not in ['RED','GREEN','MASTER']:raise RuntimeError('arm')
Q=D/(arm+'-run');Q.mkdir();stage=M if arm=='MASTER' else D/arm;base='ca64312f7f74b1d7bec047718399f229674b3e1d';target=json.loads((D/'production-commit.json').read_text())['commit'] if arm=='MASTER' else base
s=(D/'common.py').read_text().replace("TARGET='"+base+"'","TARGET='"+target+"'")
if arm=='MASTER':s=s.replace("git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET","git(['rev-parse','HEAD'])==git(['rev-parse','master'])==TARGET and git(['rev-parse','origin/master'])=='"+base+"'")
(Q/'common.py').write_text(s)
for n in ['environment.json','protected-before.json']:shutil.copyfile(D/n,Q/n)
last=D/'comparison-2' if arm=='RED' else D/('RED-run' if arm=='GREEN' else 'GREEN-run');shutil.copyfile(last/'audit-host.json',Q/'host-seed.json');sys.path.insert(0,str(Q));import common as c
if arm=='MASTER':
 j=c.read('protected-before.json');j['indexes']={n:c.sha(n) for n in j['indexes']};(Q/'protected-before.json').write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
h=c.host();h['diagnostic_head']=c.git(['rev-parse','HEAD'],R);c.put('host-before.json',h)
files=['generic_quality_local_tests.jl'] if arm=='RED' else ['generic_quality_local_tests.jl',*json.loads((O/'GREEN-run/contract.json').read_text())['files']];c.need(len(set(files))==len(files),'unique wholefiles')
(Q/'tests.jl').write_text('''using Test,JSimplex,LinearAlgebra
const ROOT="'''+str(stage)+'''"
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("LOCAL_QUALITY_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Local quality '''+arm+'''" begin
 for file in '''+json.dumps(files)+'''
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("LOCAL_QUALITY_COMPLETED '''+arm+'''");flush(stdout)
''')
shutil.copytree(D/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(Q/'launch.py').write_text((O/'GREEN-run/launch.py').read_text().replace('1792','2392').replace('1800','2400'))
(Q/'audit.py').write_text((O/'GREEN-run/audit.py').read_text().replace('1792','2392').replace('1800','2400').replace('QUALITY_DEVEX','LOCAL_QUALITY').replace('Quality Devex ','Local quality '))
oldcontract=json.loads((O/'GREEN-run/contract.json').read_text());command=[v.replace(str(O/'GREEN-run'),str(Q)).replace('--project='+oldcontract['source_root'],'--project='+str(stage)) for v in oldcontract['command']]
locations=[[str(stage/'test/generic_quality_local_tests.jl'),i] for i,line in enumerate((stage/'test/generic_quality_local_tests.jl').read_text().splitlines(),1) if '# RED whole-call cost gate' in line];c.need(len(locations)==1,'one gate location')
c.put('contract.json',dict(arm=arm,source_root=str(stage),command=command,files=files,attempts=1,expected_exit=1 if arm=='RED' else 0,expected_failures=4 if arm=='RED' else 0,expected_failure_locations=locations*4 if arm=='RED' else [],minimum_total=1000,expected_total=c.read('../GREEN-run/audit.json')['total'] if arm=='MASTER' else None,guard_limit_seconds=2392,shared_limit_seconds=2400))
paths={n for n in json.loads((D/'pins.json').read_text())['inventory'] if not Path(n).is_relative_to(R/'diagnostics')};paths.update(str(p) for root in [M/'src',M/'test',stage/'src',stage/'test'] for p in root.rglob('*') if p.is_file());paths.update(str(stage/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in Q.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for root,names in [(D,['PLAN.md','WORK-MEMORY.md','changes.json','baseline-tree.json','Reference.jl','CandidateA.jl','CandidateB.jl','CandidateAB.jl','CandidateC.jl','pins.json','new-test.jl','source-inverse.json','production-review.json','production-commit.json','commit-review.json']),(D/'comparison-2',['PLAN-AMENDMENT.md','fixtures.jl','audit.json','result-review.json','RESULT-REVIEW.md']),(last,['audit.json','result-review.json'])]:
 for n in names:
  if (root/n).exists():paths.add(str(root/n))
shutil.copyfile(__file__,Q/'prepare.py');paths.add(str(Q/'prepare.py'));c.put('pins.json',dict(files=sorted(paths),trees=sorted({str(M/'src'),str(M/'test'),str(stage/'src'),str(stage/'test')}),inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}));c.unchanged();c.put('author-host.json',c.host());print(arm,len(files),'files',len(paths),'pins;noJulia')
