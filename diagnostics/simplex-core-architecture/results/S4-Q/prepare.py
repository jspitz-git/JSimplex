from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-Q';raw=R/'.superpowers/simplex-core-architecture/S4-Q';raw.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=D/'results/S4-P/exact-inputs.json';assert sha(P)=='85874a35de281a9de4ce4d49c7f17f176d37a1597fc557ae64469202fcfd9b06';x=json.loads(P.read_text());out=[]
for f in x['fixtures']:
 k=f['name']
 for s in f['states']:
  out.append('['+k+str(s['stage'])+']')
  for field in ['nnz','colptr','rowval','nzval_bits','rhsF_bits','rhsB_bits']:out.append(field+' = '+json.dumps(s[field]))
 for t in f['transitions']:
  out.append('['+k+'incoming'+str(t['step'])+']');out.append('bits = '+json.dumps(t['incoming_bits']))
(E/'inputs.toml').write_text('\n'.join(out)+'\n')
s=(R/'src/huangfu_hall_factorization.jl').read_text();production=s[s.index('_hh_refactor_lu!(F::Float64UMFPACK'):s.index('function copy_basis_factorization(f::HuangfuHall')]
clone=production.replace('_hh_refactor_lu!','_s4q_refactor_lu!').replace('_hh_refactor_backend','_s4q_refactor_backend').replace('function refactorize!','function _s4q_refactorize!').replace('reuse_symbolic=false','reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))')
cp=D/'reproduce/hh_history_cost_clone.jl';cp.write_text(clone)
back=clone.replace('_s4q_refactor_lu!','_hh_refactor_lu!').replace('_s4q_refactor_backend','_hh_refactor_backend').replace('function _s4q_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false');assert back==production
(E/'production-refactor.txt').write_text(production)
old=json.loads((D/'results/S4-M/cost-1-pins.json').read_text());h=json.loads((E/'host-before.json').read_text());mpre=json.loads((D/'results/S4-M/preflight.json').read_text())
assert all(sha(p)==v['sha256'] for p,v in old['inventory'].items());assert all(sha(p)==v for p,v in h['user_hashes'].items());assert all(sha(p)==v for p,v in mpre['native_libraries'].items());assert not subprocess.check_output(['git','diff','master','--','src','test','.github'])
shutil.copyfile(D/'results/S4-M/native-libraries.toml',E/'native-libraries.toml')
lib='/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/lib/julia/libjulia-internal.so.1.13.0'
for name in ['jl_cumulative_compile_timing_enable','jl_cumulative_compile_timing_disable']:
 body=subprocess.check_output(['objdump','-d','--disassemble='+name,lib],text=True);(E/(name+'.asm.txt')).write_text(body);assert ('add' if name.endswith('enable') else 'sub') in body and '#0x1' in body
plan=R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-measurement.md';driver=D/'reproduce/hh_history_cost.jl';guard=D/'reproduce/guarded_run.py';pins=raw/'cost-1-pins.json';dest=raw/'cost-1';launcher='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
command=['/usr/bin/python3',str(guard),'run',str(pins),str(dest),'--seconds','600','--','bash',launcher,'--heap-size-hint=2G','--project='+str(R),str(driver),str(dest/'report.toml'),str(E/'native-libraries.toml'),str(cp),str(E/'inputs.toml')];(E/'launch-command.json').write_text(json.dumps(command,indent=2)+'\n')
pre=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),master=subprocess.check_output(['git','rev-parse','master'],text=True).strip(),user_hashes=h['user_hashes'],native_libraries=mpre['native_libraries'],driver_sha256=sha(driver),clone_sha256=sha(cp),inverse_equal=True,exact_P_input_sha256=sha(P),input_toml_sha256=sha(E/'inputs.toml'),source_sha256=sha(R/'src/huangfu_hall_factorization.jl'),plan_sha256=sha(plan),scope='Q prelaunch, one new numerical attempt only; nested compile instrumentation has installed atomic add/sub1')
(E/'preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
files=[p for p in old['files'] if '/diagnostics/simplex-core-architecture/' not in p and '/docs/superpowers/' not in p and not p.startswith('/tmp/')]
files += [str(guard),str(driver),str(cp),str(plan),str(P),str(Path(__file__).resolve()),*h['user_hashes'],lib,'/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/timing.jl']
files += [str(E/n) for n in ['production-refactor.txt','inputs.toml','native-libraries.toml','preflight.json','launch-command.json','jl_cumulative_compile_timing_enable.asm.txt','jl_cumulative_compile_timing_disable.asm.txt']]
args=['/usr/bin/python3',str(guard),'freeze',str(pins)]
for p in sorted(set(files)):args+=['--file',p]
for p in old['trees']:args+=['--tree',p]
args+=['--input',str(E/'inputs.toml')]
for n in ['big','largo','AnyMOD']:args+=['--forbidden','/home/jspitz/mps/'+n+'.mps']
subprocess.run(args,check=True);shutil.copyfile(pins,E/'cost-1-pins.json');print('PRELAUNCH',len(json.loads(pins.read_text())['inventory']),'pins')
