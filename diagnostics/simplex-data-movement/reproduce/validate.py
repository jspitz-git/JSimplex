from pathlib import Path
import subprocess,json,time
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-shared-work/JSimplex.jl');OUT=ROOT/'.superpowers/simplex-data-movement';runner=ROOT/'diagnostics/simplex-data-movement/reproduce/run.py'
jobs=[
 ('prepared-production-bench',300,['-O2','diagnostics/simplex-data-movement/reproduce/prepared-production-bench.jl',str(OUT/'prepared-production-bench/results.toml')]),
 ('prepared-budget-green-v2',300,['-O2','diagnostics/simplex-data-movement/reproduce/prepared-budget.jl']),
 ('prepared-tests-v2',600,['-O2','-e','using JSimplex,Test; for f in ("prepared_handoff_validation_tests.jl","triangular_prepared_spike_tests.jl","triangular_selective_preparation_tests.jl"); include(joinpath("test",f)); end']),
 ('certificate-green-v2',300,['-O2','-e','using JSimplex,Test,SparseArrays; include("test/primal_point_storage_tests.jl")']),
 ('certificate-bench-v2',300,['-O2','diagnostics/simplex-data-movement/reproduce/certificate-bench.jl',str(OUT/'certificate-bench-v2/results.toml')]),
 ('targeted',600,['--compile=min','-e','using JSimplex,Test,SparseArrays,LinearAlgebra; for f in ("legacy_primal_balanced_point_tests.jl","legacy_primal_perturbed_point_tests.jl","legacy_primal_equation_point_tests.jl","legacy_primal_joint_point_tests.jl"); include(joinpath("test",f)); end']),
 ('semantic',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('cleanup-pair',1800,['-O2','diagnostics/simplex-data-movement/reproduce/cleanup-pair.jl',str(OUT/'cleanup-pair/results.toml')]),
 ('runtime-after',1500,['-O2','diagnostics/simplex-data-movement/reproduce/runtime-after.jl',str(OUT/'runtime-after/solve')]),
 ('project-suite',300,['-O2','test/runtests.jl'])]
records=[]
for name,seconds,args in jobs:
 (OUT/'validation-v2-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(seconds),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(OUT/'validation-v2.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode and name!='project-suite':break
(OUT/'validation-v2-current.json').write_text(json.dumps(dict(stopped=True,ended=time.time()))+'\n')
