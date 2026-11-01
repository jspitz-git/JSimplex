from pathlib import Path
import importlib.util,json,sys,shutil,hashlib,ast
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/measurement';old=D.parent/'task5'
for name in ('run','audit'):shutil.copyfile('/tmp/task6-'+name+'.py',D/(name+'.py'));ast.parse((D/(name+'.py')).read_text())
f=D/'driver.jl';s=f.read_text().replace('    @test mode in ("qualify","compare")','    mode in ("qualify","compare")||throw(ArgumentError("mode"))').replace('    @testset "Task6 $(mode) whole verified solves" begin','    @testset "Task6 $(mode) whole verified solves" begin\n        @test mode in ("qualify","compare")');f.write_text(s)
f=D/'inspection.jl';s=f.read_text().replace('elseif !(x isa Number||x isa Symbol||x isa AbstractString||x isa Function||x isa AbstractArray||x isa AbstractDict||x isa Module||x isa Ptr||x===nothing)','elseif parentmodule(typeof(x))===@__MODULE__ || x isa J.RowAccess || x isa J.Basis')
s=s.replace('for k in (:costs,:lower,:upper,:basis,:primal,:reduced_costs,:pricing_weights,:devex_reference,:scratch);visit','for k in (:costs,:lower,:upper,:basis,:primal,:reduced_costs,:pricing_weights,:devex_reference);visit')
s=s.replace('    probe[label]=data','    for k in fieldnames(typeof(e.ws.scratch))\n        value=getfield(e.ws.scratch,k)\n        value isa Vector&&visit(value,"ws_scratch_"*string(k))\n    end\n    probe[label]=data');f.write_text(s)
# Keep the exact preparation sources as history, never use them as launchers.
for n in ('init','seal'):shutil.copyfile('/tmp/task6-'+n+'.py',D/('prepare-'+n+'.py'))
files=set(json.loads((old/'public-green-pins.json').read_text())['files'])
files|={str(p) for p in (W/'src').rglob('*.jl')};files|={str(p) for p in (W/'experimental/dual_engine').rglob('*.jl')};files|={str(p) for p in D.rglob('*') if p.is_file()}
files.add(str(D/'project/src/JSimplex.jl'))
spec=importlib.util.spec_from_file_location('task6guard',D/'guard/guard_reviewed.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
pins=dict(files=sorted(files),trees=[],inventory=G.inventory(sorted(files),[]))
with (D/'qualify-pins.json').open('x') as f:json.dump(pins,f,indent=2)
runtime=json.loads((D/'runtime.json').read_text());contract=dict(command=runtime['julia_flags']+[str(D/'driver.jl'),'qualify'],exit=0,mode='qualify',common_limit_seconds=1800,ordinary_expected_assertions=236)
# Contract must be launch-pinned too; create then reseal inventory before any review.
(D/'qualify-contract.json').write_text(json.dumps(contract,indent=2));files.add(str(D/'qualify-contract.json'));pins=dict(files=sorted(files),trees=[],inventory=G.inventory(sorted(files),[]));(D/'qualify-pins.json').write_text(json.dumps(pins,indent=2))
print('Qualification pins',len(files),hashlib.sha256((D/'qualify-pins.json').read_bytes()).hexdigest())
