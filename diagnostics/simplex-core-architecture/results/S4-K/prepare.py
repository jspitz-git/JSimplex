"""S4-K offline preparation, no Julia execution."""
from pathlib import Path
import json,hashlib,subprocess,time,shutil
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-K';raw=r/'.superpowers/simplex-core-architecture/S4-K';raw.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=json.loads((d/'results/S4-I/preflight.json').read_text());ip=json.loads((d/'results/S4-I/assembly-1-pins.json').read_text());driver=d/'reproduce/hh_nonfinite_reuse.jl';clone=d/'reproduce/hh_nonfinite_reuse_clone.jl'
assert all(sha(k)==v for k,v in old['user_hashes'].items())
assert all(sha(k)==v for k,v in old['native_libraries'].items())
assert not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True)
s=(r/'src/huangfu_hall_factorization.jl').read_text();production=s[s.index('_hh_refactor_lu!(F::Float64UMFPACK'):s.index('function copy_basis_factorization(f::HuangfuHall')]
back=clone.read_text().replace('_s4k_refactor_lu!','_hh_refactor_lu!').replace('_s4k_refactor_backend','_hh_refactor_backend').replace('function _s4k_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false');assert back==production==(o/'production-refactor.txt').read_text()
shutil.copyfile(d/'results/S4-I/native-libraries.toml',o/'native-libraries.toml')
ldd=subprocess.check_output(['ldd',next(k for k in old['native_libraries'] if 'libumfpack' in k)],text=True)
pre={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'master':subprocess.check_output(['git','rev-parse','master'],text=True).strip(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'time_ns':time.time_ns(),'user_hashes':old['user_hashes'],'native_libraries':old['native_libraries'],'ldd':ldd,'driver_sha256':sha(driver),'clone_sha256':sha(clone),'inverse_equal':back==production,'oracle_sha256':sha(o/'exact-inputs.json'),'source_test_CI_unchanged':True,'scope':'prelaunch offline; J residual formula resolved before outputs'}
(o/'preflight.json').write_text(json.dumps(pre,indent=2))
launcher='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh';guard=d/'reproduce/guarded_run.py';pins=raw/'nonfinite-1-pins.json';out=raw/'nonfinite-1'
command=['/usr/bin/python3',str(guard),'run',str(pins),str(out),'--seconds','600','--','bash',launcher,'--heap-size-hint=2G','--project='+str(r),str(driver),str(out/'report.toml'),str(o/'native-libraries.toml'),str(clone)]
(o/'launch-command.json').write_text(json.dumps(command,indent=2))
files=[p for p in ip['files'] if '/diagnostics/simplex-core-architecture/' not in p and '/docs/superpowers/' not in p and not p.startswith('/tmp/')]
files += [str(guard),str(driver),str(clone),str(r/'docs/superpowers/plans/2026-10-12-hh-nonfinite-reuse-boundary.md'),str(Path(__file__).resolve()),*old['user_hashes']]
files += [str(o/n) for n in ['exact-inputs.json','clone-source.json','production-refactor.txt','native-libraries.toml','preflight.json','launch-command.json']]
args=['/usr/bin/python3',str(guard),'freeze',str(pins)]
for p in sorted(set(files)):args+=['--file',p]
for p in ip['trees']:args+=['--tree',p]
args+=['--input',str(o/'exact-inputs.json')]
for n in ['big','largo','AnyMOD']:args+=['--forbidden','/home/jspitz/mps/'+n+'.mps']
subprocess.run(args,check=True);shutil.copyfile(pins,o/'nonfinite-1-pins.json');print({'pins':len(json.loads(pins.read_text())['inventory']),'inverse_equal':True,'user6':True,'native13':True,'oracle_frozen':True})
