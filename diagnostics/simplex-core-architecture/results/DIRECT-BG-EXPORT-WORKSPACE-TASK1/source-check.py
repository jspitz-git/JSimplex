from pathlib import Path
import json,hashlib,re,difflib
R=Path.cwd();C=R/'diagnostics/direct-bg-export-workspace/reproduce';E=Path(__file__).resolve().parent
old=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-PLAN'
seal=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/runs/cost1-300/sealed.json'
x=json.loads(seal.read_text());stage=Path(x['config']['stage'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
bindings={};comparison={}
for n,d in x['inventory'].items():
 if n.startswith(str(stage)+'/') or '/.julia/' in n:
  h=sha(Path(n));bindings[n]=h;comparison[n]=h==d['sha256']
export=(C/'export.jl').read_text();work=(C/'workspace.jl').read_text();imp=(C/'import.jl').read_text()
origexport=(stage/'src/factor-export.jl').read_text();hh=(stage/'src/huangfu_hall_factorization.jl').read_text()
a=export[export.index('function _bgx_checked_basis_lu('):export.index('\nfunction _bgx_scale_mode(')].strip()
a=a.replace('_bgx_checked_basis_lu(','_checked_basis_lu(').replace('divide::Bool,owner;allocate=_bgx_allocate)','divide::Bool)')
a=a.replace('    try\n','',1);a=a[:a.rindex('\n    catch')]+ '\nend'
a='\n'.join(s[4:] if i>=2 and s.startswith('        ') else s for i,s in enumerate(a.splitlines()))
a=a.replace('seen=_bgx_scratch!(owner,:seen,n,nnz(L),nnz(U);allocate)','seen=falses(n)')
origchecked=origexport[origexport.index('function _checked_basis_lu('):origexport.index('\n_export_basis_lu(backend)')].strip()
scale=export[export.index('function _bgx_scale_mode('):export.index('\n_bgx_export(backend,')].strip();lines=scale.splitlines();body='\n'.join(s[4:] for s in lines[2:lines.index('    catch')])
acq='''    b=_bgx_budget(n,l,u);w=_bgx_prepare!(owner,n,b)
    group=isnothing(w) ? nothing : w.orientation
    work=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[1]
    auxiliary=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[2]
'''
body=body.replace(acq,'')
later='''    permuted=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[3]
    transformed=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[4]
    if isnothing(group) && b.keep_orientation
        complete=(work,auxiliary,permuted,transformed)
        if isnothing(w)
            w=BGExportWorkspace(nothing,complete,n,512+b.orientation_bytes)
            owner.workspace=w
        else
            w.orientation=complete;w.charged_bytes=_bgx_charge(w)
        end
    end'''
body=body.replace(later,'    permuted=Vector{Float64}(undef,n);transformed=similar(permuted)').replace('return _bgx_drop!(owner)','return nothing')
restored='function _hh_scale_mode(F,L,U,p,q,scaling,work,auxiliary)\n'+body+'\nend'
origscale=hh[hh.index('function _hh_scale_mode('):hh.index('\nfunction _hh_extract_parts(F::LinearAlgebra.LU')].strip()
tests=(C/'workspace-tests.jl').read_text()+(C/'import-tests.jl').read_text()
checks=dict(full_stage_count=sum(n.startswith(str(stage)+'/') for n in bindings)==75,dependency_count=sum('/.julia/' in n for n in bindings)==604,all_selected_sealed_hashes=all(comparison.values()),stage_complete={str(p) for p in stage.rglob('*') if p.is_file()}=={n for n in bindings if n.startswith(str(stage)+'/')},validation_inverse=a==origchecked,orientation_inverse=restored==origscale,raw_extraction_calls_unchanged=export.count('_hh_extract_parts(')==2 and export.count('HHExtractWorkspace()')==2,no_old_definition_overwrite=not re.search(r'^function (_hh_|_direct_|_check_export)',export,re.M),stable_output_type='Vector{PackedUpperColumn{Float64,UpperRowIndices}}' in imp,no_u_normalization_temp='similar(U.nzval)' not in imp and 'copyto!(U.nzval' not in imp,normalized_store_one_site=imp.count('values[k]=value\n')==1,index_copy_one_site=imp.count('ids[k]=row')==1,rejected_divisions_stop='!isnothing(D) && !rejected' in imp,raw_recovery_one_site=imp.count('values[k]=U.nzval[first+k-1]')==1,checked_budget='Base.Checked.checked_add' in work and 'Base.Checked.checked_mul' in work,only_seen_role='role===:seen || throw' in work,atomic_tuple='complete=(work,auxiliary,permuted,transformed)' in export,no_candidate_driver=not (C/'factor.jl').exists() and not (C/'driver.jl').exists(),testsets=len(re.findall(r'@testset ',tests))==7,tests_no_autorun=not re.search(r'^run_(workspace|import)_tests\(\)',tests,re.M),real_fixture_and_policies='export_fixtures()' in tests and 'X._NATIVE_PIVOT_ONE' in tests and 'X._NATIVE_PIVOT_DEFAULT' in tests,core_negative_witness='@test !export_identity(B,wrong)' in tests,staged_failure_control='for failed in 1:4' in tests and '(:throw,:zero,:nonfinite)' in tests,first_middle_last_eligible='for bad in (2,4,5)' in tests,budget_and_shrink='scratch_reuse_and_shrink' in tests and '487,488,489' in tests,raw_input_bits='snapshot(U)==before' in tests,saved_tests_first=(E/'prepare-tests.py').stat().st_mtime< (E/'prepare-candidate.py').stat().st_mtime)
# Complete files and literal inverse diffs; no Julia parser or checker imported.
inverse=dict(scope='Exact two body inverses plus explicit whole-file delta classification; UNEXECUTED Julia',validation_equal=checks['validation_inverse'],orientation_equal=checks['orientation_inverse'],validation_diff=list(difflib.unified_diff(origchecked.splitlines(),a.splitlines())),orientation_diff=list(difflib.unified_diff(origscale.splitlines(),restored.splitlines())),files={'workspace.jl':'new private bounded cache and allocation seam','export.jl':'existing raw extract calls; validation/scale bodies exact after recorded substitutions; added drop-on-exception/fallback','import.jl':'new fused loop replacing old normalization temporary+copyback+packed value copy; preserves D lookup/division/guards and raw fallback','workspace-tests.jl':'new UNEXECUTED synthetic structural boundary tests','import-tests.jl':'new UNEXECUTED differential tests and original fixtures/core negative witness'},historical_triangular_sha256=sha(stage/'src/triangular_factorization.jl'),live_triangular_sha256=sha(R/'src/triangular_factorization.jl'),source_sha256={str(q):sha(q) for q in [stage/'src/factor-export.jl',stage/'src/direct-factor.jl',stage/'src/huangfu_hall_factorization.jl']})
save(C/'source-inverse.json',inverse)
manifest=dict(scope='Readtime original stage/runtime/dependency binding ONLY, not launch pins or loader closure',stage=str(stage),seal=str(seal),original_comparison=comparison,original_readtime_sha256=bindings,root_additions=['workspace.jl','export.jl','import.jl'],root_rule='Append these includes after original definitions before final module end; no root edited now',test_order=['workspace-tests.jl','import-tests.jl'],test_entry_points=['BGExportWorkspaceTests.run_workspace_tests','BGExportImportTests.run_import_tests'])
save(C/'source-manifest.json',manifest)
paths=list(C.iterdir())+[E/'host.json',E/'REPORT.md',E/'progress.md',E/'prepare-tests.py',E/'prepare-candidate.py',E/'prepare-docs.py',Path(__file__).resolve(),R/'AGENTS.md',seal,R/'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md',R/'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md',old/'amendment-review.json',old/'amendment-review.md',R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl',R/'src/triangular_factorization.jl']
bindings.update({str(p):sha(p) for p in paths})
result=dict(all_passed=all(checks.values()),checks=checks,readtime_sha256=bindings,static_test_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',tests)),scope='Offline source and provenance only; no Julia/parse/dispatch/numerics')
save(E/'source-check.json',result);print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),bindings=len(bindings),assertion_sites=result['static_test_assertion_sites'],failed=[k for k,v in checks.items() if not v])))
if not result['all_passed']:raise SystemExit(1)
