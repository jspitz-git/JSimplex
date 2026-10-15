"""New bounded source/saved-data diagnosis; no solver, Julia or old auditor execution."""
from pathlib import Path
from fractions import Fraction as Q
import json,struct,hashlib,tomllib
D=Path(__file__).resolve().parent;R=D.parents[3];A=D.parent/'DIRECT-LU-COST-PREPARATION';B=D.parent/'DIRECT-LU-COST1'
W=R/'.superpowers/direct-lu-markowitz-green-2/candidate'
U=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def q(s):return Q(struct.unpack('>d',bytes.fromhex(s))[0])
def matrix(m):
 rows=[{} for _ in range(m['n'])]
 for j in range(m['n']):
  for z in range(m['colptr'][j]-1,m['colptr'][j+1]-1):rows[m['rowval'][z]-1][j]=q(m['nzval'][z])
 return rows
f=next(f for f in rd(A/'inputs.json')['fixtures'] if f['name']=='sparse96')
w=tomllib.loads((A/'cost1-run/window-13-1.toml').read_text());st=tomllib.loads((A/'cost1-run/started-13.toml').read_text())
rows=[]
for k in range(8):
 M=matrix(f['matrices'][k]);rhs=list(map(q,f['steps'][k]['dse']));x=list(map(q,w['outputs'][3*k+1]));res=[sum(v*x[j] for j,v in row.items())-rhs[i] for i,row in enumerate(M)]
 norms=[sum(abs(v) for v in row.values()) for row in M];pivots=[max(row,key=lambda j:abs(row[j])) for row in M]
 margins=[abs(row[j])-(norms[i]-abs(row[j])) for i,(row,j) in enumerate(zip(M,pivots))]
 bound=Q(128*96,2**52)*max(Q(1),max(norms)*max(map(abs,x)),max(map(abs,rhs)))
 worst=max(range(96),key=lambda i:abs(res[i]))
 rows.append(dict(step=k+1,unique_dominant_columns=len(set(pivots))==96,dominant_all_four=all(M[i][j]==4 for i,j in enumerate(pivots)),min_margin=str(min(margins)),norm_inf=str(max(norms)),inverse_norm_upper=str(1/min(margins)),condition_inf_upper=str(max(norms)/min(margins)),residual_inf=str(abs(res[worst])),worst_row=worst+1,bound=str(bound),ratio=str(abs(res[worst])/bound),backward_scaled=str(abs(res[worst])/max(Q(1),max(norms)*max(map(abs,x)),max(map(abs,rhs)))),norm_x=str(max(map(abs,x))),residual_vector=list(map(str,res))))
M4=matrix(f['matrices'][4]);x5=list(map(q,w['outputs'][13]));rhs5=list(map(q,f['steps'][4]['dse']));i=86
row87=dict(terms=[dict(column=j+1,coefficient=str(v),solution=str(x5[j]),product=str(v*x5[j])) for j,v in M4[i].items()],rhs=str(rhs5[i]))
source_paths=[R/'src'/n for n in ('factorization.jl','triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl','huangfu_hall_factorization.jl')]+[W/'src'/n for n in ('factorization.jl','triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl','JSimplex.jl','factor-export.jl','direct-factor.jl')]+[U,A/'cost.jl',A/'prepare.py']
s={str(p):p.read_text() for p in source_paths};ft=s[str(R/'src/triangular_factorization.jl')];fr=s[str(R/'src/triangular_rows.jl')];be=s[str(R/'src/factorization.jl')];us=s[str(U)];driver=s[str(A/'cost.jl')]
checks={
 'exact_failed_reference':st==dict(fixture='sparse96',manager='FT',backend='native') and w['side']=='reference' and w['correct'] is False and w['inputs_unchanged'] is True,
 'eight_dse_rhs_identical':len({tuple(z['dse']) for z in f['steps']})==1,
 'well_conditioned_by_permuted_dominance':all(z['unique_dominant_columns'] and z['dominant_all_four'] and Q(z['min_margin'])>=Q(103,32) and Q(z['condition_inf_upper'])<=Q(153,103) for z in rows),
 'first_failure_step5':all(Q(z['ratio'])<=1 for z in rows[:4]) and all(Q(z['ratio'])>1 for z in rows[4:]),
 'failed_row87_unchanged_after_step5':all(matrix(f['matrices'][k])[86]==M4[86] for k in range(4,8)),
 'row87_solution_tokens_unchanged_after_step5':all(all(w['outputs'][3*k+1][j]==w['outputs'][13][j] for j in M4[86]) for k in range(4,8)),
 'reference_factory_ordinary':'factory(::Val{:reference},F,B,backend) = F(B,backend)' in driver,
 'refactor_after4_before5':'J.refactorize!(factor,fixture.matrices[5])' in driver and 'if k==4' in driver,
 'distinct_output_allocation':'outputs=[zeros(f.n) for _ in 1:24]' in driver,
 'fresh_first_refactor_native_lu':'candidate = backend.spare\n    if isnothing(candidate)\n        candidate = lu(sparse_basis)' in be and 'UMFPACKBackend(factorization, dimension, nothing, false)' in be,
 'history_cleared':'empty!(factor.updates)' in ft and '_recycle_triangular_updates!(factor)' in ft,
 'maps_identity':'factor.column_order[index] = index' in ft and 'factor.positions[index] = index' in ft,
 'cache_reset':'empty!(cache.operations)' in fr and 'cache.update_count = 0' in fr and 'empty!(cache.active_upper)' in fr and 'cache.upper_dirty = false' in fr,
 'prepared_invalidated':'_invalidate_prepared_spikes!(factor)' in fr,
 'native_ldiv':'ldiv!(destination, backend.factorization, rhs)' in be,
 'fresh_default_control_no_refinement':'control = Vector{Float64}(undef, UMFPACK_CONTROL)' in us and 'control[JL_UMFPACK_IRSTEP] = 0' in us and 'copy(control)' in us,
 'loaded_reference_sources_equal':all((R/'src'/n).read_bytes()==(W/'src'/n).read_bytes() for n in ('factorization.jl','triangular_factorization.jl','triangular_rows.jl','triangular_spikes.jl')),
}
pins=rd(A/'cost1-launch-pins.json')['inventory'];checks['selected_sources_match_launch']=all(str(p) in pins and sha(p)==pins[str(p)] for p in source_paths)
# Installed-source pins are existing launch evidence, never added retroactively.
paths=source_paths+[Path(__file__),A/'inputs.json',A/'cost1-run/window-13-1.toml',A/'cost1-run/started-13.toml',A/'cost1-run/raw.toml',A/'cost1-audit.json',B/'partial-analysis.json',B/'review.json',B/'closure.json',B/'publication.json',D/'host.json',D/'entry-notes.json']
out=dict(scope='Source-supported backend boundary localization and exact saved-vector conditioning; not native-factor cause or new solver run',all_passed=all(checks.values()),checks=checks,dse_steps=rows,row87=row87,sha256={str(p):sha(p) for p in paths})
with (D/'analysis.json').open('x') as o:json.dump(out,o,indent=2);o.write('\n')
if not out['all_passed']:raise ValueError(checks)
print(json.dumps(dict(checks=len(checks),bindings=len(out['sha256']),condition_bound=rows[4]['condition_inf_upper'],margin=rows[4]['min_margin'],row87=row87)))
