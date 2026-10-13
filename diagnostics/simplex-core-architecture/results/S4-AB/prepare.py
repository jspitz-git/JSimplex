"""One-use offline preparation of one Markowitz row-count fusion candidate."""
from pathlib import Path
import hashlib,json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S4-AB'
def require(x,m):
 if not x:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=(R/'src/markowitz_factorization.jl').read_text()
a=s.index('function _construct_markowitz(');b=s.index('\nfunction _backend_forward_solve!',a)
original=s[a:b]
old='    nonzeros = sum(length, rows)\n'
oldrow='    for row in 1:n\n        length(rows[row]) == 1 && push!(singleton_rows,row)\n    end\n'
newrow='    for row in 1:n\n        row_count = length(rows[row])\n        nonzeros += row_count\n        row_count == 1 && push!(singleton_rows,row)\n    end\n'
require(original.count(old)==1 and original.count(oldrow)==1,'unique change sites')
candidate=original.replace(old,'    nonzeros = 0\n').replace(oldrow,newrow)
require(candidate.replace('    nonzeros = 0\n',old,1).replace(newrow,oldrow)==original,'exact constructor inverse')
full=s[:a]+candidate+s[b:]
for name,text in [('original-construct.jl',original),('candidate-source.jl',full)]:
 with (D/name).open('x') as f:f.write(text)
# Only two new private method names; no existing method overwritten, no HH/module clone.
ca=candidate.replace('function _construct_markowitz(','function _s4ab_construct_markowitz(',1)
a=s.index('function _refactorize_backend(backend::MarkowitzBackend');b=s.index('\nfunction refactorize!',a)
ref=s[a:b];cr=ref.replace('function _refactorize_backend(','function _s4ab_refactorize_backend(',1).replace('_construct_markowitz(B,backend.workspace,D,backend.spare)','_s4ab_construct_markowitz(B,backend.workspace,D,backend.spare)')
require(cr.replace('_s4ab_refactorize_backend','_refactorize_backend').replace('_s4ab_construct_markowitz','_construct_markowitz')==ref,'refactor inverse')
with (D/'candidate-methods.jl').open('x') as f:f.write(ca+'\n'+cr)
checks={
 'whole_source_inverse':full.replace('    nonzeros = 0\n',old,1).replace(newrow,oldrow)==s,
 'no_new_workspace_field':full[:full.index('mutable struct MarkowitzBackend')]==s[:s.index('mutable struct MarkowitzBackend')],
 'all_tail_dictionaries_still_cleared':'foreach(empty!,workspace.rows)\n    foreach(empty!,workspace.columns)' in full,
 'dense_branches_before_reset':original.index('if B isa StridedMatrix')<original.index('_reset_markowitz_workspace!') and original.index('if 2 * count(!iszero, sparse_basis.nzval)')<original.index('_reset_markowitz_workspace!'),
 'zero_skip_fill_and_scatter_unchanged':candidate[:candidate.index('    nonzeros = 0')]==original[:original.index(old)],
 'column_setup_pivot_loop_unchanged':candidate[candidate.index('    for column in 1:n\n        length(columns[column])'):]==original[original.index('    for column in 1:n\n        length(columns[column])'):],
 'row_order_and_singleton_condition_preserved':'row_count == 1 && push!(singleton_rows,row)' in candidate,
 'no_new_full_scan_or_buffer':'@view' not in candidate and candidate.count('for row in 1:n')==original.count('for row in 1:n'),
 'refactor_inverse':cr.replace('_s4ab_refactorize_backend','_refactorize_backend').replace('_s4ab_construct_markowitz','_construct_markowitz')==ref,
 'no_actual_production_edit':(R/'src/markowitz_factorization.jl').read_text()==s}
require(all(checks.values()),'source checks')
paths=[R/'src/markowitz_factorization.jl',R/'test/markowitz_workspace_reuse_allocation_tests.jl',R/'test/runtime_markowitz_cache_tests.jl',R/'test/markowitz_tests.jl',R/'diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-QUALIFICATION.md',D/'prepare.py',D/'candidate-source.jl',D/'original-construct.jl',D/'candidate-methods.jl']
with (D/'source-checks.json').open('x') as f:json.dump({'all_passed':True,'checks':checks,'sha256':{str(p):sha(p) for p in paths},'scope':'Source only; no Julia syntax/runtime/cost qualification.'},f,indent=2);f.write('\n')
print({'source_checks':len(checks),'readtime_hashes':len(paths),'candidate_unexecuted':True})
