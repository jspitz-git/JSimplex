"""Exclusive S4-L source/evidence audit; no Julia or old diagnostic execution."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,struct,subprocess,time,re
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-L'
j=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia')
u=j/'stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl';w=u.with_name('wrappers.jl');a=j/'base/abstractarray.jl';s=j/'stdlib/v1.13/SparseArrays/src/sparsematrix.jl'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={};check=lambda name,value:checks.__setitem__(name,bool(value))
U=u.read_text();W=w.read_text();H=(r/'src/huangfu_hall_factorization.jl').read_text();F=(r/'src/factorization.jl').read_text();header=(o/'upstream-umfpack-v7.10.1.h').read_text()
check('production_reuse_disabled','reuse_symbolic=false' in H)
check('identity_convert','convert(::Type{T}, a::T) where {T<:AbstractArray} = a' in a.read_text())
check('constructor_distinct_copy','SparseMatrixCSC{Tv,Ti}(S::AbstractSparseMatrixCSC{Tv,Ti}) where {Tv,Ti} = copy(S)' in s.read_text())
pattern=F[F.index('function _same_umfpack_pattern'):F.index('function _refactorize_backend(backend::UMFPACKBackend')]
check('pattern_two_index_loops','eachindex(B.colptr)' in pattern and 'eachindex(B.rowval)' in pattern and 'nzval' not in pattern)
check('native_finalizers','umfpack_free_numeric(num, Tv, Ti)' in U and 'umfpack_free_symbolic(sym, Tv, Ti)' in U)
check('reference_drops_symbolic','F.symbolic = Symbolic{Tv, Ti}(C_NULL)' in U)
check('numeric_replaced_after_call',U.index('status = $num_r(')<U.index('U.numeric = Numeric{Float64, $itype}(tmp[])'))
check('symbolic_early_return','_isnotnull(U.symbolic) && return U' in U)
check('info_show_mutates_control','control[1] = Float64(level)' in U)
constants={'SIZE_OF_UNIT':3,'SYMBOLIC_PEAK_MEMORY':13,'SYMBOLIC_SIZE':14,'NUMERIC_SIZE_ESTIMATE':20,'PEAK_MEMORY_ESTIMATE':21,'NUMERIC_SIZE':40,'PEAK_MEMORY':41,'VARIABLE_PEAK':46}
check('installed_info_indices',all(re.search(r'const UMFPACK_'+k+r' = '+str(v)+r'\b',W) for k,v in constants.items()))
check('installed_header_version',all(f'const UMFPACK_{k}_VERSION = {v}' in W for k,v in [('MAIN',6),('SUB',3),('SUBSUB',5)]))
check('upstream_unit_documentation','the number of bytes in a Unit' in header)
check('upstream_variable_peak_not_malloc','not the space\n            allocated via UMF_malloc' in header)
check('upstream_estimate_not_upper_bound','but this is not\n            guaranteed' in header)
prov=json.loads((o/'upstream-umfpack-v7.10.1.provenance.json').read_text());check('upstream_hash',sha(o/'upstream-umfpack-v7.10.1.h')==prov['sha256'])
old=json.loads((d/'results/S4-K/preflight.json').read_text())
check('six_user_hashes',len(old['user_hashes'])==6 and all(sha(p)==v for p,v in old['user_hashes'].items()))
check('native13_hashes',len(old['native_libraries'])==13 and all(sha(p)==v for p,v in old['native_libraries'].items()))
check('source_test_ci_master_equal',not subprocess.check_output(['git','diff','master','--','src','test','.github']))
check('expected_refs',subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines()==['457d4c08adbfd0401608ed85349d15c6a6d6fa94','0eb75c3190096946b0e91e5360230ccd7166f298'])
check('preflight_groups_absent',json.loads((o/'host-preflight.json').read_text())['matches']==[])
fixtures=[]
for kind in ['sparse','dense']:
 for phase in [0,1]:
  n=96;M=[[Q(8)+Q(i%7,64)+Q(phase,8) if i==k else Q((-1)**(i+k)*(8+phase),8192) if kind=='dense' or abs(i-k)<=2 else Q(0) for k in range(1,n+1)] for i in range(1,n+1)]
  zf=[Q((-1)**i) for i in range(1,n+1)];zb=[Q(i%3-1) for i in range(1,n+1)]
  bf=[sum((x*z for x,z in zip(row,zf)),Q(0)) for row in M];bb=[sum((M[k][i]*zb[k] for k in range(n)),Q(0)) for i in range(n)]
  nnz=sum(x!=0 for row in M for x in row);margin=min(abs(M[i][i])-sum(abs(M[i][k]) for k in range(n) if i!=k) for i in range(n))
  vals=[M[i][k] for k in range(n) for i in range(n) if M[i][k]!=0]
  check(f'{kind}{phase}_nnz_dominance',nnz==(474 if kind=='sparse' else 9216) and margin>0)
  check(f'{kind}{phase}_exact_binary64',all(Q.from_float(float(x))==x for x in vals+bf+bb))
  check(f'{kind}{phase}_symmetric',all(M[i][k]==M[k][i] for i in range(n) for k in range(n)))
  fixtures.append({'kind':kind,'phase':phase,'dimension':n,'nnz':nnz,'minimum_dominance_margin':str(margin),'nzval_sha256_le_f64':hashlib.sha256(b''.join(struct.pack('<d',float(x)) for x in vals)).hexdigest(),'rhs_forward_rational':list(map(str,bf)),'rhs_transpose_rational':list(map(str,bb)),'rhs_forward_bits':[struct.pack('>d',float(x)).hex() for x in bf],'rhs_transpose_bits':[struct.pack('>d',float(x)).hex() for x in bb]})
check('work_totals',4*2*16==128 and 8*4*16==512 and 4+128+512==644 and 2*(4+8+32)==88 and 2*(1+160)==322)
plan=r/'docs/superpowers/plans/2026-10-12-hh-symbolic-cost-measurement.md';P=plan.read_text()
check('frozen_compile_stop','compile_time==0 and recompile_time==0' in P and 'do not subtract' in P)
check('native_retention_open','Full native-retention acceptance remains OPEN' in P)
check('exact_scale_frozen','64*2^-52*max(1, ||M||inf*||z||inf, ||b||inf)' in P)
files=list((r/'src').rglob('*.jl'))+list((r/'test').rglob('*.jl'))+[u,w,a,s,r/'Project.toml',Path(__file__).resolve(),plan,r/'docs/superpowers/plans/2026-10-12-hh-symbolic-cost-contract.md',o/'upstream-umfpack-v7.10.1.h',o/'upstream-umfpack-v7.10.1.provenance.json',o/'host-preflight.json']
files += [Path(p) for p in [*old['user_hashes'],*old['native_libraries']]]
files += [d/p for p in ['S4-COMPONENTS.md','S4-TRIPLETS.md','reproduce/hh_component_attribution.jl','reproduce/hh_triplet_cost.jl','reproduce/hh_scalar_components.jl','results/S4-D/scalar-components-1-audit.json','results/S4-D/scalar-components-1-initial-audit.json']]
result={'scope':'source/evidence only; no Julia; read-time hashes not numerical launch pins','checks':checks,'all_passed':all(checks.values()),'hashes':{str(p):sha(p) for p in sorted(set(files))},'constants_c_zero_based':constants,'fixture_contract':fixtures,'user_hashes':old['user_hashes'],'time_ns':time.time_ns()}
with (o/'source-contract.json').open('x') as f:json.dump(result,f,indent=2)
print({'checks':len(checks),'passed':sum(checks.values()),'hashes':len(result['hashes']),'failed':[k for k,v in checks.items() if not v]})
raise SystemExit(0 if result['all_passed'] else 1)
