"""Continue only after the owned dispatcher's whole-suite job has completed."""
from pathlib import Path
import subprocess,json,time
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'.superpowers/simplex-data-movement';runner=Path(__file__).with_name('run.py')
while not (OUT/'project-suite/process.json').exists():time.sleep(2)
suite=json.loads((OUT/'project-suite/process.json').read_text());assert suite['sources_unchanged']
jobs=[
 ('prepared-final-bench',300,['-O2','diagnostics/simplex-data-movement/reproduce/prepared-production-bench.jl',str(OUT/'prepared-final-bench/results.toml')]),
 ('certificate-bench-final',300,['-O2','diagnostics/simplex-data-movement/reproduce/certificate-bench.jl',str(OUT/'certificate-bench-final/results.toml')]),
 ('final-budget',300,['-O2','diagnostics/simplex-data-movement/reproduce/prepared-budget.jl']),
 ('manager-regressions',600,['--compile=min','-e','using JSimplex,Test,LinearAlgebra,SparseArrays; @testset "Manager semantic regressions" begin; for f in ("huangfu_hall_tests.jl","huangfu_hall_precision_tests.jl","huangfu_hall_markowitz_tests.jl","triangular_prepared_spike_tests.jl","triangular_selective_preparation_tests.jl"); include(joinpath("test",f)); end; end']),
 ('semantic-final',600,['--compile=min','diagnostics/primal-row-memory/reproduce/semantic.jl']),
 ('external',1800,['-O2','diagnostics/simplex-data-movement/reproduce/external.jl','diagnostics/basis-selective-preparation/reproduce/external-inputs.toml',str(OUT/'external/results.toml')]),
 ('cleanup-pair-final',1200,['-O2','diagnostics/simplex-data-movement/reproduce/cleanup-pair-final.jl',str(OUT/'cleanup-pair-final/results.toml'),str(OUT/'cleanup-pair/results.toml')]),
 ('runtime-final',1500,['-O2','diagnostics/simplex-data-movement/reproduce/runtime-final.jl',str(OUT/'runtime-final/solve')])]
records=[]
for name,seconds,args in jobs:
 (OUT/'final-current.json').write_text(json.dumps(dict(job=name,started=time.time()))+'\n')
 p=subprocess.run(['python3',str(runner),str(OUT/name),str(seconds),*args],cwd=ROOT,capture_output=True,text=True)
 records.append(dict(job=name,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(OUT/'final.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:break
(OUT/'final-current.json').write_text(json.dumps(dict(stopped=True,ended=time.time()))+'\n')
