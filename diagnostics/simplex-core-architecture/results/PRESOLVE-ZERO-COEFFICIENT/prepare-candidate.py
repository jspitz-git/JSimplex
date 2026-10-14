from pathlib import Path
import shutil,json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/PRESOLVE-ZERO-COEFFICIENT';O=R/'.superpowers/presolve-zero-coefficient/candidate'
if not json.loads((D/'red2-audit.json').read_text())['all_passed']:raise ValueError('RED not accepted')
source=(R/'src/presolve_aggregation.jl').read_text()
old='''                    old_value = get(matrix_updates, key) do
                        _exact_rational(A[other_row, other])
                    end'''
new='''                    old_value = if T === Float64
                        staged_value = get(matrix_updates, key, nothing)
                        if isnothing(staged_value)
                            stored_value = A[other_row, other]
                            # A missing zero will be discarded by the nonzero update.
                            iszero(stored_value) && !iszero(multiplier) ? nothing :
                                _exact_rational(stored_value)
                        else
                            staged_value
                        end
                    else
                        get(matrix_updates, key) do
                            _exact_rational(A[other_row, other])
                        end
                    end'''
old2='''                        iszero(old_value) ? -product :''';new2='''                        (isnothing(old_value) || iszero(old_value)) ? -product :'''
if source.count(old)!=1 or source.count(old2)!=1:raise ValueError('source scope')
candidate=source.replace(old,new).replace(old2,new2)
if candidate.replace(new,old).replace(new2,old2)!=source:raise ValueError('inverse')
(D/'candidate-source.jl').write_text(candidate)
shutil.copytree(R/'.superpowers/presolve-exact-cache/reference',O)
(O/'src/presolve_aggregation.jl').write_text(candidate)
orig=(D/'original-function.jl').read_text();ref=orig.replace('function aggregate_sparse_equalities(','function zero_reference_aggregate(')
s=(R/'src/presolve_dispatch.jl').read_text();a=s.index('function _dispatch_presolve_pass!');b=s.index('\n# Split the finite record',a);dispatch=s[a:b]
ref+=dispatch.replace('_dispatch_presolve_pass!','zero_reference_dispatch!').replace('aggregate_sparse_equalities,','zero_reference_aggregate,')
s=(R/'src/presolve.jl').read_text();a=s.index('function presolve_problem(');b=s.index('\nfunction restore_basis(step::PresolveMap',a);pipeline=s[a:b]
ref+=pipeline.replace('function presolve_problem(','function zero_reference_presolve(').replace('_dispatch_presolve_pass!','zero_reference_dispatch!')
(D/'reference-functions.jl').write_text(ref)
start=candidate.index('function aggregate_sparse_equalities(');end=candidate.index('\nfunction postsolve_primal(step::SparseEqualityStep',start)
probe=candidate[start:end].replace('function aggregate_sparse_equalities(','function zero_candidate_probe(').replace('_exact_rational(stored_value)','zero_probe_convert(stored_value)').replace('_exact_rational(A[other_row, other])','zero_probe_convert(A[other_row, other])')
(D/'probe-candidate.jl').write_text(probe)
(D/'candidate-inverse.json').write_text(json.dumps(dict(exact_inverse=True,substitutions=2,scope='Float64 only; all other T retain original lookup and exact conversion',original_sha256=hashlib.sha256(source.encode()).hexdigest(),candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),overlay=str(O),unchanged_files=[str(p.relative_to(O)) for p in O.rglob('*') if p.is_file() and p.name!='presolve_aggregation.jl']),indent=2)+'\n')
