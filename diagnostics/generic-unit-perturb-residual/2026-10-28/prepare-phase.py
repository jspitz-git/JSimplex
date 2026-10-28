from pathlib import Path
import os,json,sys,shutil,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common as c
arm=sys.argv[1];c.need(arm in ['RED','GREEN','MASTER'],'phase');P=D/(arm+'-run');P.mkdir();O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28'
root=c.M if arm=='MASTER' else D/arm
base=c.TARGET;target=c.read('production-commit.json')['commit'] if arm=='MASTER' else base
files=['generic_unit_perturb_residual_tests.jl'] if arm=='RED' else ['generic_unit_perturb_residual_tests.jl']+json.loads((O/'GREEN-run/contract.json').read_text())['files']
if arm!='RED':
 for extra_file in ['simplex_perturbation_tests.jl','primal_perturbation_tests.jl','primal_perturbation_integration_tests.jl','lp_refinement_tests.jl','simplex_perturbation_integration_tests.jl','lp_refinement_diagnostic_tests.jl','lp_refinement_entry_tests.jl','lp_refinement_factor_tests.jl','lp_refinement_limit_tests.jl','lp_refinement_precision_tests.jl','lp_refinement_projection_tests.jl','lp_refinement_recovery_tests.jl','lp_refinement_state_tests.jl','lp_refinement_terminal_tests.jl']:
  if extra_file not in files:files.append(extra_file)
expected=c.read('test-gates.json')['expected_RED_failures'] if arm=='RED' else 0
cmd=c.read('contract-reviewed.json')['command'][:-2]+[str(P/'tests.jl')]
cmd=[x.replace('--project='+str(c.M),'--project='+str(root)) for x in cmd]
body='''using Test,JSimplex,LinearAlgebra
const ROOT=ROOT_VALUE
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("UPR_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Unit perturb residual ARM" begin
 for file in FILES_VALUE
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("UPR_COMPLETED ARM");flush(stdout)
'''.replace('ROOT_VALUE',json.dumps(str(root))).replace('FILES_VALUE',json.dumps(files)).replace('ARM',arm)
(P/'tests.jl').write_text(body)
shutil.copytree(D/'guard',P/'guard',ignore=shutil.ignore_patterns('__pycache__'))
common=(D/'common_reviewed.py').read_text().replace('contract-reviewed.json','contract.json').replace('pins-reviewed.json','pins.json')
if arm=='MASTER':
 common=common.replace("TARGET='"+base+"'","TARGET='"+target+"'").replace("==git(['rev-parse','origin/master'])==TARGET","==TARGET and git(['rev-parse','origin/master'])=='"+base+"'")
(P/'common.py').write_text(common)
launch=(D/'launch-reviewed.py').read_text().replace('from common_reviewed import','from common import').replace('contract-reviewed.json','contract.json').replace('pins-reviewed.json','pins.json').replace('admission-reviewed.json','admission.json').replace('892','3592').replace('900','3600')
(P/'launch.py').write_text(launch)
extra=set(c.read('host-seed.json')['groups'])
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
h=c.host(extra);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);c.put(str(P/'host-before.json'),h);c.put(str(P/'host-seed.json'),h)
c.put(str(P/'protected-before.json'),{k:{n:c.sha(n) for n in v} for k,v in c.read('protected-before.json').items()});shutil.copyfile(D/'environment.json',P/'environment.json')
line=c.read('test-gates.json')['failure_line'];locations=[[str(root/'test/generic_unit_perturb_residual_tests.jl'),line]]*expected if arm=='RED' else []
c.put(str(P/'contract.json'),dict(arm=arm,command=cmd,attempts=1,source_root=str(root),files=files,expected_exit=1 if arm=='RED' else 0,expected_failures=expected,expected_failure_locations=locations,shared_limit_seconds=3600,guard_limit_seconds=3592,expected_total=c.read('GREEN-run/audit.json')['total'] if arm=='MASTER' else None,minimum_total=1000))
# Current pins are fresh; older benchmark pins remain as frozen provenance with explicit baseline maps after integration.
paths={n for n in c.read('pins-reviewed.json')['inventory'] if not Path(n).is_relative_to(c.M/'src') and not Path(n).is_relative_to(c.M/'test') and not Path(n).is_relative_to(D)}
roots=[c.M/'src',c.M/'test',root/'src',root/'test']
for tree in roots:paths.update(str(p) for p in tree.rglob('*') if p.is_file())
for directory in [D,P]:paths.update(str(p) for p in directory.iterdir() if p.is_file() and p.suffix in ['.py','.jl','.json','.md'])
paths.update(str(p) for p in (P/'guard').rglob('*') if p.is_file())
for pathroot in [root,c.M]:paths.update(str(pathroot/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml'])
paths.add(str(P/'tests.jl'))
c.put(str(P/'pins.json'),dict(files=sorted(paths),trees=sorted({str(v) for v in roots}),inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
shutil.copyfile(__file__,P/'prepare.py')
sys.path.insert(0,str(P));import importlib.util
sp=importlib.util.spec_from_file_location('phase_common',P/'common.py');pc=importlib.util.module_from_spec(sp);sp.loader.exec_module(pc);pc.unchanged();pc.put('author-host.json',pc.host())
print(arm,'prepared',len(paths),'pins',len(files),'whole files')
