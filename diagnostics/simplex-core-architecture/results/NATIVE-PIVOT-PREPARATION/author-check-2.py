from common import *
a=(R/'src/factorization.jl').read_text();b=(Q/'candidate/src/factorization.jl').read_text()
def section(s,start,end):
 require(s.count(start)==1 and s.count(end)==1,'Bad section anchors')
 return s[s.index(start):s.index(end)]
checks=dict(whole_solve_update_pattern_range=section(a,'function _check_rhs_dimension','function _refactorize_backend(backend::UMFPACKBackend')==section(b,'function _check_rhs_dimension','function _refactorize_backend(backend::UMFPACKBackend'),native_refactor_only_fresh_call=section(a,'function _refactorize_backend(backend::UMFPACKBackend','function _recycle_pfi_updates!')==section(b,'function _refactorize_backend(backend::UMFPACKBackend','function _recycle_pfi_updates!').replace('_native_lu(sparse_basis, backend.pivot_policy)','lu(sparse_basis)'),triangular_all_after_constructors=(R/'src/triangular_factorization.jl').read_text().split('function _check_triangular_dimensions',1)[1]==(Q/'candidate/src/triangular_factorization.jl').read_text().split('function _check_triangular_dimensions',1)[1],source_all_bindings=bindings(rd(Q/'source-check.json')),original_plan_accepted=rd(PREV/'review-final.json')['accepted'] is True and bindings(rd(PREV/'review-final.json')),source_all_checks=rd(Q/'source-check.json')['all_passed'] is True)
paths=list(Q.rglob('*.jl'))+list(Q.glob('*.py'))+[Q/n for n in ['source-check.json','WORK-AND-TEST-LEDGER.md','REPORT.md','continuation-text.md','overlay-manifest.json','inverse.json']]
save(Q/'author-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(f):sha(f) for f in paths},scope='Non-vacuous complete source-range equality, no Julia'))
require(all(checks.values()),'Author check failed');print(dict(all_passed=True,checks=len(checks),bindings=len(paths)))
