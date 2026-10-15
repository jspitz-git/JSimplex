"""One offline freeze. Does not seal/reserve/launch a numerical attempt."""
from control import *
import guard
from evidence import validate_predecessor
extra=validate_predecessor('accuracy');req(not Q.exists(),'Future stage already exists')
report=R/'diagnostics/simplex-core-architecture/NATIVE-ACCURACY-PREPARATION.md'
required=sorted({str(p) for p in D.iterdir() if p.is_file()}|{str(report)}|{str(p) for p in extra}|set(rd(D/'source-check.json')['sha256']))
# Snapshot this exact completed artifact set ONCE before review; review output files
# and mutable continuation/publication tools are intentionally outside membership.
save(D/'required-paths.json',required)
J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu');S=J/'share/julia/stdlib/v1.13'
runtime=[J/'bin/julia',J/'lib/julia/sys.so']+[p for p in (J/'lib').rglob('*') if p.is_file() and '.so' in p.name]
source=[p for root in [J/'share/julia/base']+[S/n for n in ('SparseArrays','LinearAlgebra','TOML','SuiteSparse_jll','OpenBLAS_jll','libblastrampoline_jll','CompilerSupportLibraries_jll','Libdl','Artifacts','Serialization','Random','SHA','Dates','Printf','Unicode')] for p in root.rglob('*') if p.is_file() and (p.suffix=='.jl' or p.name in ('Project.toml','Manifest.toml','LocalPreferences.toml'))]
wrapper=Path(expected_config('accuracy')['command'][1]);transitive=wrapper.parents[3]/'.superpowers/basis-chain-cost/julia.sh'
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];req(all(sha(R/n)==h for n,h in base.items()),'Baseline changed')
files=sorted(set(required)|{str(D/'required-paths.json'),str(wrapper),str(transitive),'/bin/bash',sys.executable,str(Path(sys.executable).resolve())}|{str(p) for p in runtime+source}|{str(R/n) for n in base}|{str(R/n) for n in ('Project.toml','Manifest.toml','LocalPreferences.toml')})
pins=dict(files=files,trees=[],inventory=guard.inventory(files,[]),inputs=[str(D/'inputs.toml')],created=time.time(),scope='Offline component preparation; runtime/stdlibrary/native paths pinned, no full observed loader/cache closure and no stage admission')
save(D/'preparation-pins.json',pins);print(json.dumps(dict(required=len(required),files=len(files),inventory=len(pins['inventory']))))
