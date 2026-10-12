"""Exclusive offline S4-M preparation. No Julia or old script execution."""
from pathlib import Path
from fractions import Fraction as Q
import json,hashlib,struct,subprocess,shutil,time
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-M';raw=r/'.superpowers/simplex-core-architecture/S4-M';raw.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((d/'results/S4-K/preflight.json').read_text());prior=json.loads((d/'results/S4-K/nonfinite-1-pins.json').read_text());L=json.loads((d/'results/S4-L/source-contract.json').read_text())
assert all(sha(p)==h for p,h in old['user_hashes'].items());assert all(sha(p)==h for p,h in old['native_libraries'].items());assert not subprocess.check_output(['git','diff','master','--','src','test','.github'])
shutil.copyfile('/tmp/s4-m-host.json',o/'host-before-preparation.json');shutil.copyfile(d/'results/S4-K/native-libraries.toml',o/'native-libraries.toml')
s=(r/'src/huangfu_hall_factorization.jl').read_text();production=s[s.index('_hh_refactor_lu!(F::Float64UMFPACK'):s.index('function copy_basis_factorization(f::HuangfuHall')]
clone=production.replace('_hh_refactor_lu!','_s4m_refactor_lu!').replace('_hh_refactor_backend','_s4m_refactor_backend').replace('function refactorize!','function _s4m_refactorize!').replace('reuse_symbolic=false','reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))')
cp=d/'reproduce/hh_symbolic_cost_clone.jl';cp.write_text(clone)
back=clone.replace('_s4m_refactor_lu!','_hh_refactor_lu!').replace('_s4m_refactor_backend','_hh_refactor_backend').replace('function _s4m_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false');assert back==production
(o/'production-refactor.txt').write_text(production)
fixtures=[];toml=[]
for kind in ['sparse','dense']:
 for phase in [0,1]:
  n=96;M=[[Q(8)+Q(i%7,64)+Q(phase,8) if i==j else Q((-1)**(i+j)*(8+phase),8192) if kind=='dense' or abs(i-j)<=2 else Q(0) for j in range(1,n+1)] for i in range(1,n+1)]
  zf=[Q((-1)**i) for i in range(1,n+1)];zb=[Q(i%3-1) for i in range(1,n+1)]
  bf=[sum(x*z for x,z in zip(row,zf)) for row in M];bb=[sum(M[k][i]*zb[k] for k in range(n)) for i in range(n)]
  colptr=[1];rowval=[];vals=[]
  for j in range(n):
   for i in range(n):
    if M[i][j]:rowval.append(i+1);vals.append(M[i][j])
   colptr.append(len(vals)+1)
  bits=lambda vs:[struct.pack('>d',float(x)).hex() for x in vs]
  assert all(Q.from_float(float(x))==x for x in vals+bf+bb)
  c={'kind':kind,'phase':phase,'dimension':n,'nnz':len(vals),'colptr':colptr,'rowval':rowval,'nzval_bits':bits(vals),'rhs_forward_bits':bits(bf),'rhs_transpose_bits':bits(bb),'rhs_forward_rational':list(map(str,bf)),'rhs_transpose_rational':list(map(str,bb)),'minimum_dominance_margin':str(min(M[i][i]-sum(abs(M[i][k]) for k in range(n) if k!=i) for i in range(n)))}
  lc=next(x for x in L['fixture_contract'] if x['kind']==kind and x['phase']==phase)
  assert hashlib.sha256(b''.join(struct.pack('<d',float(x)) for x in vals)).hexdigest()==lc['nzval_sha256_le_f64']
  assert c['rhs_forward_bits']==lc['rhs_forward_bits'] and c['rhs_transpose_bits']==lc['rhs_transpose_bits']
  fixtures.append(c);toml.append('['+kind+str(phase)+']')
  for key in ['nnz','colptr','rowval','nzval_bits','rhs_forward_bits','rhs_transpose_bits']:toml.append(key+' = '+json.dumps(c[key]))
(o/'inputs.toml').write_text('\n'.join(toml)+'\n')
(o/'exact-inputs.json').write_text(json.dumps({'fixtures':fixtures,'oracle':'exact ||M*z-b||inf <= 64*2^-52*max(1,||M||inf*||z||inf,||b||inf)','prior_L_input_bits_match':True,'count_budget':{'constructors':4,'warmup_refactors':128,'measured_refactors':512,'FTRAN':44,'BTRAN':44},'phases':[0,0,1,1,0,0,1,1]},indent=2))
driver=d/'reproduce/hh_symbolic_cost.jl';plan=r/'docs/superpowers/plans/2026-10-12-hh-symbolic-cost-measurement.md';guard=d/'reproduce/guarded_run.py';out=raw/'cost-1';pins=raw/'cost-1-pins.json'
launcher='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
command=['/usr/bin/python3',str(guard),'run',str(pins),str(out),'--seconds','600','--','bash',launcher,'--heap-size-hint=2G','--project='+str(r),str(driver),str(out/'report.toml'),str(o/'native-libraries.toml'),str(cp),str(o/'inputs.toml')]
(o/'launch-command.json').write_text(json.dumps(command,indent=2))
pre={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'master':subprocess.check_output(['git','rev-parse','master'],text=True).strip(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'user_hashes':old['user_hashes'],'native_libraries':old['native_libraries'],'driver_sha256':sha(driver),'clone_sha256':sha(cp),'inverse_equal':True,'input_sha256':sha(o/'inputs.toml'),'oracle_sha256':sha(o/'exact-inputs.json'),'scope':'prelaunch; no Julia; exact L inputs matched','time_ns':time.time_ns()}
(o/'preflight.json').write_text(json.dumps(pre,indent=2))
files=[p for p in prior['files'] if '/diagnostics/simplex-core-architecture/' not in p and '/docs/superpowers/' not in p and not p.startswith('/tmp/')]
files += [str(guard),str(driver),str(cp),str(plan),str(Path(__file__).resolve()),*old['user_hashes']]
files += [p for p in L['hashes'] if '/share/julia/' in p]
files += [str(o/name) for name in ['production-refactor.txt','exact-inputs.json','inputs.toml','native-libraries.toml','preflight.json','launch-command.json']]
args=['/usr/bin/python3',str(guard),'freeze',str(pins)]
for p in sorted(set(files)):args+=['--file',p]
for p in prior['trees']:args+=['--tree',p]
args+=['--input',str(o/'inputs.toml')]
for name in ['big','largo','AnyMOD']:args+=['--forbidden','/home/jspitz/mps/'+name+'.mps']
subprocess.run(args,check=True);shutil.copyfile(pins,o/'cost-1-pins.json')
print({'pins':len(json.loads(pins.read_text())['inventory']),'inverse_equal':True,'exact_L_inputs_match':True,'budget':pre['scope']})
