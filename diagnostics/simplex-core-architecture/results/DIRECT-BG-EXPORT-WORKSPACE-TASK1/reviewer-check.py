"""Independent OFFLINE read-time integrity review. No Julia, parsing or imports of old checkers."""
from pathlib import Path
import hashlib,json,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=Path(__file__).resolve().parent
C=R/'diagnostics/direct-bg-export-workspace/reproduce'
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while True:
            block=f.read(1024*1024)
            if not block: break
            h.update(block)
    return h.hexdigest()
def read(path): return Path(path).read_text()
author=json.loads(read(E/'source-check.json'))
manifest=json.loads(read(C/'source-manifest.json'))
inverse=json.loads(read(C/'source-inverse.json'))
seal=json.loads(read(manifest['seal']))
stage=Path(manifest['stage'])
recorded=author['readtime_sha256']
actual={p:digest(p) for p in recorded}
selected={p:entry['sha256'] for p,entry in seal['inventory'].items() if p.startswith(str(stage)+'/') or '/.julia/' in p}
seal_comparison={p:actual.get(p)==h for p,h in selected.items()}
checks={
'author_readtime_count_702':len(actual)==702,
'all_702_author_readtime_hashes_match':actual==recorded,
'original_selected_count_679':len(selected)==679,
'all_selected_match_original_seal':all(seal_comparison.values()),
'manifest_readtime_exact_selected_seal':manifest['original_readtime_sha256']==selected,
'manifest_comparison_exact_recomputed':manifest['original_comparison']==seal_comparison,
'stage_75_paths':sum(p.startswith(str(stage)+'/') for p in selected)==75,
'installed_runtime_dependency_604_paths':sum('/.julia/' in p for p in selected)==604,
'whole_stage_set_matches':{str(p) for p in stage.rglob('*') if p.is_file()}=={p for p in selected if p.startswith(str(stage)+'/')},
'author_27_checks_reported_pass':len(author['checks'])==27 and all(v is True for v in author['checks'].values()) and author['all_passed'] is True,
'inverse_source_hashes_match':all(digest(p)==h for p,h in inverse['source_sha256'].items()),
'inverse_historical_triangular_matches':digest(stage/'src/triangular_factorization.jl')==inverse['historical_triangular_sha256'],
'inverse_live_triangular_matches':digest(R/'src/triangular_factorization.jl')==inverse['live_triangular_sha256'],
'historical_and_live_triangular_differ':inverse['historical_triangular_sha256']!=inverse['live_triangular_sha256'],
'root_additions_declared':manifest['root_additions']==['workspace.jl','export.jl','import.jl'],
'no_task2_or_task3_candidate':not (C/'factor.jl').exists() and not (C/'driver.jl').exists(),
}
# Compare exact original numerical lines, independently stripping only prescribed
# wrapper/acquisition regions. This is text comparison, not a Julia parser.
export=read(C/'export.jl')
original=read(stage/'src/factor-export.jl')
start=export.index('        n=size(L,1)')
end=export.index('\n    catch',start)
checked='\n'.join(line[4:] for line in export[start:end].splitlines()).replace('seen=_bgx_scratch!(owner,:seen,n,nnz(L),nnz(U);allocate)','seen=falses(n)')
ostart=original.index('    n=size(L,1)',original.index('function _checked_basis_lu'))
oend=original.index('\nend',ostart)
checks['independent_validation_body_exact']=checked==original[ostart:oend]
scale=export.split('function _bgx_scale_mode(',1)[1].split('\n_bgx_export(',1)[0]
scale=scale.split('\n    try\n',1)[1].split('\n    catch',1)[0]
lines=[line[4:] for line in scale.splitlines()]
first=lines.index('    b=_bgx_budget(n,l,u);w=_bgx_prepare!(owner,n,b)')
last=next(i for i,line in enumerate(lines) if line.startswith('    fill!(work'))
del lines[first:last]
first=next(i for i,line in enumerate(lines) if line.startswith('    permuted=isnothing(group)'))
last=next(i for i,line in enumerate(lines) if line.startswith('    for i in eachindex(permuted)'))
lines[first:last]=['    permuted=Vector{Float64}(undef,n);transformed=similar(permuted)']
restored='\n'.join(lines).replace('return _bgx_drop!(owner)','return nothing')
hh=read(stage/'src/huangfu_hall_factorization.jl')
original_scale=hh.split('function _hh_scale_mode(F,L,U,p,q,scaling,work,auxiliary)\n',1)[1].split('\nend\n\nfunction _hh_extract_parts',1)[0]
checks['independent_orientation_body_exact']=restored==original_scale
checks['raw_extract_call_sites_preserved']=export.count('_hh_extract_parts(')==2 and export.count('HHExtractWorkspace()')==2
workspace=read(C/'workspace.jl');imports=read(C/'import.jl')
tests=read(C/'workspace-tests.jl')+read(C/'import-tests.jl')
assertion_sites=len(re.findall(r'@test(?:_throws)?\b',tests))
checks['70_static_sites_not_runtime_total']=assertion_sites==70 and author['static_test_assertion_sites']==70
checks['seven_named_testsets']=len(re.findall(r'@testset\s',tests))==7
checks['test_only_solve_dispatch']=('f::OrientationSolve' in tests and 'struct OrientationSolve' in tests)
checks['no_automatic_test_entry_call']=not re.search(r'^run_(workspace|import)_tests\(\)',tests,re.M)
checks['tests_preparation_mtime_precedes_candidate']=(E/'prepare-tests.py').stat().st_mtime<(E/'prepare-candidate.py').stat().st_mtime
# Source-level counts only, not executed counters or allocation-event evidence.
checks['normalization_and_raw_recovery_store_sites']=imports.count('values[k]=value\n')==1 and imports.count('values[k]=U.nzval[first+k-1]')==1 and imports.count('ids[k]=row')==1
checks['no_raw_upper_mutation_or_normalization_temp']='copyto!(U.nzval' not in imports and 'similar(U.nzval)' not in imports
extra=[E/'source-check.json',Path(__file__).resolve(),R/'diagnostics/direct-lu-policy-adapters/reproduce/lifecycle-tests.jl',R/'diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl']
actual.update({str(p):digest(p) for p in extra})
result={'all_passed':all(checks.values()),'checks':checks,'author_binding_count':len(recorded),'original_seal_comparison':seal_comparison,'author_readtime_comparison':{p:actual[p]==h for p,h in recorded.items()},'static_assertion_sites':assertion_sites,'readtime_sha256':actual,'scope':'OFFLINE hashes and literal source comparison only; author checker not run/imported; Julia not parsed/loaded/executed; no numerical or performance result'}
with (E/'reviewer-check.json').open('x') as f: json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'author_bindings':len(recorded),'original_seal_bindings':len(selected),'static_assertion_sites':assertion_sites,'failed':[k for k,v in checks.items() if not v]}))
if not result['all_passed']:raise SystemExit(1)
