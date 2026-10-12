"""Exclusive S4-H source/evidence contract. No Julia or old parser execution."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,subprocess,re,shutil
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-H';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=(r/'src/simplex.jl').read_text();rec=(r/'src/simplex_recovery.jl').read_text();pol=(r/'src/simplex_numerics.jl').read_text();diag=(r/'src/simplex_diagnostics.jl').read_text();pipe=(r/'src/hypersparse_pipeline.jl').read_text();test=(r/'test/basis_matrix_reuse_allocation_tests.jl').read_text();hh=(r/'src/huangfu_hall_factorization.jl').read_text();pricing=(r/'src/simplex_pricing.jl').read_text();rp=(r/'src/refactorization_policy.jl').read_text();host=json.loads(Path('/tmp/s4-h-host.json').read_text());pre=json.loads((d/'results/S4-G/preflight.json').read_text())
files=['src/simplex.jl','src/huangfu_hall_factorization.jl','src/refactorization_policy.jl','src/simplex_recovery.jl','src/hypersparse_pipeline.jl','src/simplex_pricing.jl','src/simplex_numerics.jl','src/simplex_diagnostics.jl','test/basis_matrix_reuse_allocation_tests.jl','test/huangfu_hall_integration_tests.jl']
comparisons=[]
for ref in ['4914cbb','b720674']:
 for p in files:
  b=subprocess.check_output(['git','show',ref+':'+p]);comparisons.append({'ref':ref,'path':p,'current':sha(r/p),'historical':hashlib.sha256(b).hexdigest(),'equal':b==(r/p).read_bytes()})
labels=['Repeated refactorization reuses basis assembly storage','Borrowed assembly preserves saved factors and public matrices','Basis assembly keeps capacity across sparser bases','Borrowed assembly handles no rows and preserves stored precision']
logs={};logpaths=[]
for run in ['38142752357','38149970679']:
 p=r/f'.superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{run}-failed.log';logpaths.append(p);rows=[]
 for no,line in enumerate(p.read_text().splitlines(),1):
  text=re.sub(r'\x1b\[[0-9;]*m','',line)
  if any(label in text for label in labels):rows.append({'line':no,'text':text})
 logs[run]=rows
c_pin=r/'.superpowers/simplex-core-architecture/S4-C/triplet-focused-1-pins.json';cp=json.loads(c_pin.read_text())['inventory'];cf=d/'reproduce/hh_scratch_focused_tests.jl';cl=d/'results/S4-C/triplet-focused-1-run.log';ccompare={p:cp[str(r/p)]['sha256']==sha(r/p) for p in files if str(r/p) in cp}
recompute=s[s.index('function recompute!(workspace::'):s.index('recompute!(workspace::SimplexWorkspace, refactorize::Bool)')]
order=['_validate_basis(workspace)','_invalidate_pricing_pool!(workspace)','@logmsg','B = _basis_matrix!(workspace)','_before_basis_refactor!','_measure_basis_factorization!','refactorize!(workspace.factorization, B)','_after_basis_refactor!','workspace.refactorizations += 1','_simplex_event!','basic_primal = _checked_basis_solve!','dual = _checked_basis_solve!','_recompute_reduced_costs!']
checks={
'expected_refs':host['refs'].splitlines()==['df2a96f445970056152165092bda21f34f88002e','0eb75c3190096946b0e91e5360230ccd7166f298'],
'host_clear':not host['old_identities'] and not host['group_members'] and not host['julia'],
'source_test_ci_master_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
'users_preserved':all(sha(p)==v for p,v in pre['user_hashes'].items()),
'initial_slack_factor_once':'initial_basis = spdiagm(0 => fill(-one(T), row_count))' in s and 'factorization = _basis_factorization(initial_basis, typed_options)' in s,
'initial_scratch_alias':'scratch.basis_matrix = initial_basis' in s,
'initial_finish_recompute':'function _finish_workspace_initialization!(workspace)\n    recompute!(workspace)\n    _simplex_event!(workspace, :refactor_initial)' in s,
'borrowed_validation_first':'function _basis_matrix!(workspace::SimplexWorkspace)\n    _validate_basis(workspace)' in s,
'capacity_reuse':'rows = resize!(storage.rowval, nonzero_count)' in s and 'values = resize!(storage.nzval, nonzero_count)' in s,
'stored_zero_kept':'A.colptr[variable_index + 1] - A.colptr[variable_index]' in s,
'public_owned':'return _assemble_basis_matrix(workspace, nothing)' in s,
'recompute_order':all(recompute.index(a)<recompute.index(b) for a,b in zip(order,order[1:])),
'checked_two_entries':recompute.count('_checked_basis_solve!(')==2,
'native_quality_shortcircuit':'policy.solve_refinement || return true' in rec and 'solve_refinement::Bool=(numerical_profile == :checked)' in pol,
'native_recovery_disabled':'recovery::Bool=(numerical_profile == :checked)' in pol,
'dense_ordinary_forward':'_ordinary_forward_solve!(destination,ws.factorization,rhs)' in pipe,
'failure_kernel_finally':'finally\n        diagnostics.kernel_nanoseconds[reason]' in diag and 'diagnostics.kernel_calls[reason] += 1' in diag,
'pricing_invalidates_if_present':'isnothing(pool) && return nothing' in pricing and 'pool.valid = false' in pricing,
'factor_abort_native_noop':'function _abort_basis_refactor!(ws)\n    ws.progress.numerical_policy.adaptive_refactor || return nothing' in rp,
'assembly_test_excludes_HH':':huangfu_hall' not in test and test.count('(:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)')==2,
'historical_contract9of10each':all(sum(x['equal'] for x in comparisons if x['ref']==ref)==9 for ref in ['4914cbb','b720674']),
'historical_four_rows_each':all(len(rows)==4 and [list(map(int,re.findall(r'\d+',x['text'].split('|')[1])))[:2] for x in rows]==[[16,16],[2280,2280],[3,3],[12,12]] for rows in logs.values()),
'C_focused_HH_execution':'"huangfu_hall_integration_tests.jl"' in cf.read_text() and 'Starting huangfu_hall_integration_tests.jl' in cl.read_text() and ccompare['test/huangfu_hall_integration_tests.jl'] and ccompare['src/huangfu_hall_factorization.jl'],
'C_assembly_not_execution':'basis_matrix_reuse_allocation_tests.jl' not in cf.read_text(),
'production_symbolic_disabled':'reuse_symbolic=false' in hh,
}
selected=[*files,'src/options.jl','diagnostics/simplex-core-architecture/S4-SYMBOLIC-PUBLICATION.md','diagnostics/simplex-core-architecture/S4-SYMBOLIC-PUBLICATION-REVIEW.md','docs/superpowers/plans/2026-10-12-hh-borrowed-assembly-contract.md']
paths=set(r/p for p in selected)|set(logpaths)|{c_pin,cf,cl,Path(__file__)}|set(map(Path,pre['user_hashes']))
for tree in ['src','test']:paths.update(p for p in (r/tree).rglob('*') if p.is_file())
hashes={str(p.resolve()):sha(p) for p in sorted(paths)}
A=[[4,1,7,1,2],[1,3,1,2,4]];matrices={'initial': [[-1,0],[0,-1]],'first':[[4,1],[1,3]],'same_pattern':[[7,1],[1,3]],'shrink':[[-1,0],[0,-1]],'singular':[[1,2],[2,4]]};recipes={}
for name,B in matrices.items():
 det=B[0][0]*B[1][1]-B[0][1]*B[1][0];v={'matrix':B,'determinant':det}
 if det:v['rhs12_solution']=[str(Q(B[1][1]-2*B[0][1],det)),str(Q(2*B[0][0]-B[1][0],det))]
 recipes[name]=v
result={'checks':checks,'all_passed':all(checks.values()),'hashes':hashes,'historical_comparisons':comparisons,'historical_log_rows':logs,'C_focused_comparisons':ccompare,'declared_coverage':{'historical_assembly':'four non-HH testsets executed separately in each failed whole-suite run;2311pass each,not full suite success','C_focused':'HH integration test executed; assembly file only pinned not included; source matched','G':'direct HH lifecycle, not workspace'},'future_recipe':{'A':A,'basis_order':[[1,2],[3,2],[6,7],[4,5]],'matrices':recipes},'scope':'source/evidence and Python exact arithmetic only; zero Julia calls'}
with (o/'source-contract.json').open('x') as f:json.dump(result,f,indent=2)
shutil.copyfile('/tmp/s4-h-host.json',o/'host-preflight.json');print({'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'hashes':len(hashes),'comparisons':len(comparisons),'C_matches':ccompare});assert result['all_passed']
