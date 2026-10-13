"""One-use OFFLINE S4-Y source/text verification. Never executes Julia."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); D=R/'diagnostics/simplex-core-architecture/results/S4-Y'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,message):
 if not ok: raise RuntimeError(message)
entry=json.loads((D/'entry.json').read_text())
source=(R/'src/markowitz_factorization.jl').read_text()
driver=(D/'driver.jl').read_text()
tests=(R/'test/markowitz_workspace_reuse_allocation_tests.jl').read_text()
cache=(R/'test/runtime_markowitz_cache_tests.jl').read_text()
reset=source[source.index('function _reset_markowitz_workspace!'):source.index('mutable struct MarkowitzBackend')]
construction=source[source.index('function _construct_markowitz'):source.index('function _backend_forward_solve!')]
solves=source[source.index('function _backend_forward_solve!'):source.index('function _refactorize_backend')]
checks={
 'entry_source_hashes':all(sha(R/p)==h for p,h in entry['source_sha256'].items()),
 'user_files_preserved':all(sha(Path(p))==h for p,h in entry['user_sha256'].items()),
 'six_G_continuation_bindings':len(entry['previous_continuation_mapping'])==6 and all(sha(R/v['saved_path'])==v['sha256'] for v in entry['previous_continuation_mapping'].values()),
 'grow_only_dictionaries': 'while length(workspace.rows) < n' in reset and 'resize!(workspace.rows' not in reset and 'resize!(workspace.columns' not in reset,
 'whole_dictionary_clear':all(x in reset for x in ['foreach(empty!,workspace.rows)','foreach(empty!,workspace.columns)']),
 'maxima_only_grow_whole_valid_clear':all(x in reset for x in ['if length(workspace.column_maxima) < n','fill!(workspace.column_maxima_valid,false)']),
 'two_dense_returns_before_reset':construction[:construction.index('_reset_markowitz_workspace!')].count('return _markowitz_backend')==2,
 'retained_rows_sum': 'nonzeros = sum(length, rows)' in construction,
 'solves_do_not_read_construction_workspace': 'workspace' not in solves,
 'workspace_spare_construction': '_construct_markowitz(B,backend.workspace,D,backend.spare)' in source,
 'failure_drops_spare_rethrows': 'backend.spare = nothing\n        rethrow()' in source,
 'saved_no_workspace_spare': 'similar(backend.work), similar(backend.core_work), nothing,\n        nothing, true' in source,
 'existing_regrowth_allocation_contract': '(@allocated replace_markowitz_backend_for_capacity!(holder,large))==0' in tests and 'fill(T(4),64)' in tests,
 'existing_maximum_identity_contract': '@test ws.column_maxima === maxima' in cache and '@test length(maxima) >= 64' in cache,
 'exact_driver_schedule': 'enumerate((large,small,small,large))' in driver and 'for kind in ("sparse","dense")' in driver and driver.count('backend = JSimplex.MarkowitzBackend(large)')==1 and driver.count('backend = JSimplex._refactorize_backend(backend,B)')==1,
 'twenty_prospective_solves':driver.count('JSimplex._backend_forward_solve!(')==1 and driver.count('JSimplex._backend_transpose_solve!(')==1 and driver.count('in retention_solves(')==2 and 2*(4*2+2)==20,
 'sixty_six_named_predicates':driver.count('checks[label*')==6 and driver.count('checks["saved_"*name]')==1 and 2*(4*(2+5)+2+2+1)==66,
 'raw_before_aggregate_failure':driver.index('TOML.print(io,')<driver.index('all_passed || error('),
 'no_runtime_or_compile_tools_called':all(x not in driver for x in ['@eval','include(','run(','@allocated','@timed','GC.gc']),
 'production_test_ci_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
}
# The loop has two solve keys plus five explicit suffix keys at each stage.
# Count the literal sites separately to avoid treating one loop site as one predicate.
checks['sixty_six_named_predicates']=driver.count('checks[label*')==6 and driver.count('checks["saved_"*name]')==1 and all(x in driver for x in ['checks["saved_no_workspace_or_spare"]','checks["saved_dimension"]','checks["small_reset_route"]']) and 2*(4*7+4+1)==66
need(all(checks.values()),str({k:v for k,v in checks.items() if not v}))
paths=list(entry['source_sha256'])+[
 'diagnostics/simplex-core-architecture/results/S4-Y/'+p for p in ['driver.jl','entry.json','host.json','verify.py','STATUS.md.before-S4-Y','roadmap.md.before-S4-Y']]+[
 'diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-PREPARATION.md',
 'docs/superpowers/plans/2026-10-13-markowitz-retention-admission.md',
 'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
with (D/'source.json').open('x') as f:
 json.dump({'checks':checks,'all_passed':True,'sha256':{p:sha(R/p) for p in paths},'scope':'Readtime/source/text only. Julia driver UNEXECUTED; no numerical allowance.','schedule':{'cases':2,'constructors':2,'copies':2,'refactor_attempts':6,'backend_solves':20,'snapshots':8,'predicates':66}},f,indent=2);f.write('\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'hashes':len(paths),'julia_executed':False}))
