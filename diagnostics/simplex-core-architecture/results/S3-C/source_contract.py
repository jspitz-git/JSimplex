import hashlib,json
from pathlib import Path
r=Path.cwd(); d=r/'diagnostics/simplex-core-architecture'; out=d/'results/S3-C'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
s={n:(r/'src'/n).read_text() for n in ['dual_simplex.jl','hypersparse_pipeline.jl','hypersparse_pipeline_types.jl','triangular_factorization.jl','triangular_spikes.jl','huangfu_hall_factorization.jl','simplex_recovery.jl','hypersparse_updates.jl']}
a=s['dual_simplex.jl']; body=a[a.index('function update_dse!'):a.index('function _switch_dual_pricing_to_devex!')]
checks={'dse_dense_basis_order':'enumerate(workspace.basis.basic_indices)' in body,'dse_typed_floor':'_typed_ratio(T, 1, 10^4)' in body,'weight_checked_ftran':'_checked_basis_solve!(workspace.scratch.tau,workspace,rho;operation=:weight_ftran)' in body,'no_support_loop_in_dse':'indices' not in body.replace('basic_indices',''),'weight_before_replace':a.index('update_dual_pricing_weights!(workspace, rho, tableau_row, tableau_column,')<a.index('_replace_pivot_column!(workspace, tableau_column, leaving_row;'),'finite_wrapper_retained':'if !_finite_workspace(workspace)' in a,'accepted_refinement_invalidates':'_pipeline_changed!(ws,destination)' in s['simplex_recovery.jl'],'six_owned_buffers':'(:row_rhs,:row_solution,:rho,:tau,:tableau_row,:pricing_row)' in s['hypersparse_pipeline_types.jl'],'exact_nonzero_support':'if !iszero(value)' in s['hypersparse_pipeline.jl'],'canonical_local_only':'mode in (:sparse,:empty)' in s['hypersparse_pipeline.jl'],'ordinary_only_nonhypersparse':'return prepare_update ? forward_solve!' in s['hypersparse_pipeline.jl'],'hh_dense_prepares':'forward_solve!(destination, factor, rhs)' in s['hypersparse_pipeline.jl'],'triangular_eviction_ordinary':'entry = _begin_prepared_spike!(factor, destination)' in s['triangular_factorization.jl'],'triangular_identity_values':'entry.destination === direction && isequal(entry.direction, direction)' in s['triangular_spikes.jl'],'hh_value_match':'isequal(direction,f.prepared_direction)' in s['huangfu_hall_factorization.jl'],'indexed_destination_invalidation':'_invalidate_prepared_destination!(factor,dest.values)' in s['hypersparse_updates.jl']}
assert all(checks.values())
files=[r/'src'/n for n in s]+list((r/'src').glob('*factorization*.jl'))+[r/'src/indexed_vector.jl']
files=[p for p in files if p.exists()]
files += [r/'test'/n for n in ['hypersparse_pipeline_solver_tests.jl','dual_weight_validation_tests.jl','triangular_selective_preparation_tests.jl','triangular_prepared_spike_tests.jl','huangfu_hall_tests.jl','hypersparse_pipeline_kernel_tests.jl','hypersparse_boundary_invalidation_tests.jl']]
files += [d/n for n in ['S3-BOUNDARIES.md','S3-SUPPORT.md','S3-INVENTORY-NOTES.md','reproduce/pipeline_support_focused.jl','reproduce/pipeline_support_hh_tests.jl','reproduce/pipeline_support_trajectory.jl','results/S3-B/support-focused-1-run.log','results/S3-B/support-focused-1-process.json','results/S3-B/support-trajectory-1-run.log','results/S3-B/support-trajectory-1-process.json','results/S3-B/support-trajectory-1-trajectory.toml']]
files += [r/'.superpowers/simplex-core-architecture/S3-B'/n for n in ['support-focused-1-pins.json','support-trajectory-1-pins.json']]
files += [r/'docs/superpowers/plans/2026-10-12-dse-support-consumer-contract.md',r/'Project.toml']
host=json.loads((out/'host-before.json').read_text());files+=list(map(Path,host['user_hashes']))
x=json.loads((d/'results/S4-X/source-contract.json').read_text())['sha256']
files += [Path(p) for p in x if '/.julia/' in p and (p.endswith('/bin/julia') or '/lib/julia/' in p or p.endswith('/solvers/umfpack.jl'))]
pins={str(p):sha(p) for p in sorted(set(files))}
comparisons=[]
for attempt in ['support-focused-1','support-trajectory-1']:
 inv=json.loads((r/'.superpowers/simplex-core-architecture/S3-B'/f'{attempt}-pins.json').read_text())['inventory']
 for p in files:
  if str(p).startswith(str(r/'src')) or p.name in ['hypersparse_pipeline_solver_tests.jl','pipeline_support_hh_tests.jl','pipeline_support_trajectory.jl']:
   old=inv.get(str(p));comparisons.append({'attempt':attempt,'path':str(p),'historical_sha256':old and old['sha256'],'current_sha256':sha(p),'matches':old is not None and old['sha256']==sha(p)})
ex=[]
for n,lo,hi in [('dual_simplex.jl',602,692),('dual_simplex.jl',1429,1443),('hypersparse_pipeline.jl',345,384),('hypersparse_pipeline.jl',406,510),('simplex_recovery.jl',457,493),('triangular_factorization.jl',710,760),('triangular_spikes.jl',1,116),('huangfu_hall_factorization.jl',385,408),('huangfu_hall_factorization.jl',482,537)]:
 lines=(r/'src'/n).read_text().splitlines(keepends=True);ex.append({'file':'src/'+n,'first_line':lo,'last_line':hi,'text':''.join(lines[lo-1:hi])})
for name,value in [('source-contract.json',{'checks':checks,'all_passed':True,'sha256':pins,'historical_comparisons':comparisons,'scope':'Read-time hashes and literal source checks, not execution coverage or a launch permit'}),('source-excerpts.json',ex)]:
 with (out/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'comparisons':len(comparisons),'excerpts':len(ex)}))
