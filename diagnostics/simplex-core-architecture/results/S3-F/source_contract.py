from pathlib import Path
import hashlib, json, subprocess, datetime
R=Path.cwd(); D=R/'diagnostics/simplex-core-architecture/results/S3-F'
def run(*args): return subprocess.check_output(args,text=True).strip()
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
 with (D/name).open('x') as f: json.dump(obj,f,indent=2); f.write('\n')
def require(ok,msg):
 if not ok: raise RuntimeError(msg)
refs={k:run('git','rev-parse',k) for k in ['HEAD','master','origin/master']}
require(refs['HEAD']=='f820f2404f76fbe4fcd2cd4b99fb43f6e0cf6511','unexpected HEAD')
require(refs['master']==refs['origin/master']=='d02416c108f06fcd41d58e0a1980b70a51fef9ef','unexpected master')
groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746,84681,84689,89395,89399,90313,90323,128482,128483}
matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  s=(p/'stat').read_text(); tail=s[s.rfind(')')+2:].split(); comm=(p/'comm').read_text().strip()
  if int(tail[2]) in groups or int(tail[3]) in groups or comm.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(tail[2]),sid=int(tail[3]),start_ticks=int(tail[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError,PermissionError): pass
save('host.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),refs=refs,groups_and_sessions=sorted(groups),matches=matches,remote_refs=run('git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=run('git','status','--short')))
require(not matches,'host not quiescent')
require(not run('git','diff','master','--','src','test','.github'),'production/test/CI differs from master')
status=R/'diagnostics/simplex-core-architecture/STATUS.md'; roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for p,n in [(status,'STATUS.md.before-S3-F'),(roadmap,'roadmap.md.before-S3-F')]:
 with (D/n).open('xb') as f: f.write(p.read_bytes())
old={}
for name in ['closure-final.json','publication-final.json']:
 p=R/'diagnostics/simplex-core-architecture/results/S2-E'/name; d=json.loads(p.read_text())
 require(d['all_passed'] and all(d['checks'].values()),'old final gate failed')
 old[name]={str(x.relative_to(R)):d['sha256'][str(x)] for x in [status,roadmap]}
 require(all(digest(R/k)==v for k,v in old[name].items()),'old continuation hash mismatch')
dual=(R/'src/dual_simplex.jl').read_text(); pipe=(R/'src/hypersparse_pipeline.jl').read_text()
def block(s,a,b): return s[s.index(a):s.index(b,s.index(a))]
u=block(dual,'function update_duals!','function update_primals!'); v=block(dual,'function update_primals!','function update_dse!')
flip=block(dual,'function _apply_bound_flips!','function price!'); residual=block(dual,'function _dual_direction_residual_ok!','# The entering direction')
access=block(pipe,'function _pipeline_vector!','function _pipeline_changed!')
partial=(R/'test/partial_pricing_integration_tests.jl').read_text(); numeric=(R/'src/numeric.jl').read_text()
checks={
 'dual_full_loop_and_repair': all(x in u for x in ['eachindex(workspace.reduced_costs)','workspace.costs[index] -= reduced_cost','changed_costs && _invalidate_pricing_pool!']),
 'dual_basic_entering_skip_then_explicit_assignments': all(x in u for x in ['(state == BASIC || index == entering_index) && continue','workspace.reduced_costs[leaving_index] = -dual_step','workspace.reduced_costs[entering_index] = zero(T)']),
 'primal_dense_basis_order': 'for (row, index) in enumerate(workspace.basis.basic_indices)' in v and 'workspace.primal[index] -= primal_step * tableau_column[row]' in v,
 'primal_entering_add_after_loop': v.index('workspace.primal[entering_index] += primal_step')>v.index('workspace.primal[index] -='),
 'ordinary_call_order': dual.index('    update_duals!(workspace, tableau_row, leaving_index, entering_index, dual_step)')<dual.index('    update_primals!(workspace, tableau_column, entering_index, leaving_row, primal_step)')<dual.index('    _replace_pivot_column!(workspace, tableau_column, leaving_row;'),
 'direction_owner': '_pipeline_basis_solve!(workspace.scratch.row_solution,workspace,column;prepare_update=true)' in dual,
 'direction_residual_other_scratch': 'residual = workspace.scratch.tau' in residual and 'scale = workspace.scratch.row_rhs' in residual and 'direction[basis_row]' in residual,
 'flips_other_output_and_observer': '_pipeline_basis_solve!(workspace.scratch.tau,workspace,rhs;operation=:bfrt)' in flip and '_simplex_event!(workspace, :bound_flipped)' in flip,
 'consumer_accessor_can_rebuild_or_compact': '_rebuild_pipeline_support!(cache,i)' in access and 'compact_support!(cache.buffers[i])' in access,
 'zero_row_repair_test_exists': 'JSimplex.update_duals!(ws,zeros(length(ws.costs)),130,1,0.0)' in partial and '@test ws.costs[2] == 1.0' in partial and '@test pool.cost_generation > generation' in partial,
 'exact_trait_is_broader_than_bigint': '_is_exact(::Type{<:Rational}) = Val(true)' in numeric,
 'no_production_test_ci_diff': not run('git','diff','master','--','src','test','.github'),
}
files=['src/dual_simplex.jl','src/hypersparse_pipeline.jl','src/hypersparse_pipeline_types.jl','src/indexed_vector.jl','src/numeric.jl','src/simplex_numerics.jl','test/partial_pricing_integration_tests.jl','test/dual_stagnation_cost_tests.jl','test/hypersparse_pipeline_tests.jl','diagnostics/simplex-core-architecture/S3-INVENTORY-NOTES.md','diagnostics/simplex-core-architecture/S3-SUPPORT.md','diagnostics/simplex-core-architecture/S3-DSE-COUNTER-SEAM-LIMIT.md','docs/superpowers/specs/2026-10-11-simplex-core-architecture-design.md']
files += [str(p.relative_to(R)) for p in D.iterdir() if p.is_file()]
save('source-contract.json',dict(checks=checks,all_passed=all(checks.values()),sha256={n:digest(R/n) for n in sorted(files)},previous_continuation_hashes=old,scope='Literal source checks only; existing tests read, not executed. No Julia or arithmetic experiment.'))
require(all(checks.values()),'source checks failed')
print(json.dumps({'checks':len(checks),'hashes':len(files),'all_passed':True}))
