from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (Q/'source-check.py').open('xb') as f:f.write(Path(__file__).read_bytes())
p=(C/'panel.jl').read_text();t=(C/'panel-tests.jl').read_text();w=(C/'work-memory-ledger.md').read_text();mapping=json.loads((C/'source-map.json').read_text());entry=json.loads((Q/'entry.json').read_text());first=json.loads((Q/'tests-first.json').read_text())
checks={
'entry_unchanged':all(sha(R/n)==h for n,h in entry['sha256'].items()),
'actual_source_bindings':all(sha(R/n)==h for n,h in mapping['dependencies'].items()),
'first_tests_preserved':first['candidate_absent'] and sha(Q/'panel-tests.first.jl')==first['tests_sha256'],
'four_deliverables':set(x.name for x in C.iterdir())=={'panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json'},
'isolated_module':p.startswith('# UNEXECUTED') and 'module BGBlockedPanel\n' in p and 'import ..JSimplex' in p,
'no_production_overwrite_or_launch':all(x not in p for x in ['@eval','run(', 'ccall(', 'replace_column!(', '@fastmath']),
'fixed_workspace':all(x in p for x in ['values::Matrix{Float64}','present::BitMatrix','touched::BitMatrix','Vector{J.BartelsGolubStep{Float64}}(undef,8)','owner::Union{Nothing,Upper}']),
'policy_and_fma':all(x in p for x in ['J._pivot_magnitude(z)>J._pivot_magnitude(a)','fma(-m,X[j,t],X[j,t+1])','iszero(a) && return reject!']),
'finite_and_zero':all(x in p for x in ['isfinite(v) || return reject!','stored ? v : 0.0','P[j,t] || continue']),
'fresh_commit_arrays':all(x in p for x in ['Vector{Int}(undef,nnew)','Vector{Float64}(undef,nnew)','_bgb_store_budget(planned,h,w) || return reject!']),
'counted_and_uncounted':all(x in p for x in ['BGNoCounts','NTuple{20,Int}','bump!(::BGNoCounts','peak!(c,16*']),
'one_id_pass':p.count('for id in eachindex(inner.positions)')==1,
'failure_propagates':all(x in p for x in ['rethrow()','finally','inner.row_cache.upper_prefix_candidate=false']),
'oracle_independent':all(x in t for x in ['function oracle','D=Dict','abs(z)>abs(a)','fma(-m,D[']),
'coverage_named':all(x in t for x in ['zero_diagonal','store_budget','typemax(Int)','reverse_rows','reverse_columns','subdiagonals','one store']) if False else all(x in t for x in ['zero_diagonal','store_budget','typemax(Int)','reverse_rows','reverse_columns','nextfloat(0.0)','floatmax(Float64)','1153']),
'work_memory_scope':all(x in w for x in ['308480','O(n² log n/b)','131072','Task2','UNEXECUTED','not allocator instrumentation']),
'no_numerical_claim': 'no Julia' in (Q/'AUTHOR-NOTES.md').read_text() or 'No RED/GREEN' in (Q/'AUTHOR-NOTES.md').read_text(),
}
files=list(C.iterdir())+[Q/'AUTHOR-NOTES.md',Q/'source-check.py',Q/'tests-first.json',Q/'panel-tests.first.jl']
j={'all_passed':all(checks.values()),'checks':checks,'sha256':{str(x):sha(x) for x in files},'scope':'Literal/source-hash preparation checks only, not Julia syntax, dispatch, numerical or allocation validation'}
with (Q/'source-check.json').open('x') as f:json.dump(j,f,indent=2)
print(json.dumps(checks))
if not j['all_passed']:raise SystemExit(1)
