"""New source-only explanation of preserved GREEN failure; never executes Julia."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia')
paths=[R/'diagnostics/direct-lu-markowitz/reproduce/correctness.jl',R/'diagnostics/direct-lu-markowitz/reproduce/fixtures.jl',R/'src/factorization.jl',J/'base/arraymath.jl',J/'stdlib/v1.13/SparseArrays/src/higherorderfns.jl',J/'stdlib/v1.13/SparseArrays/src/sparsematrix.jl',J/'stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl']
test,fixtures,factors,arraymath,higher,sparse,umf=[p.read_text() for p in paths]
checks=dict(test_uses_default_lu='lu!(backend.factorization,sparse(2.0*B))' in test,
    default_symbolic_reuse='check::Bool=true, reuse_symbolic::Bool=true, q=nothing' in umf,
    wrapper_replaces_CSC_before_numeric='F.nzval .= nonzeros(S)\n    return lu!(F; reuse_symbolic, check, q)' in umf,
    stored_zero_fixture='SparseMatrixCSC(4,4,collect(1:4:17),repeat(collect(1:4),4)' in fixtures,
    native_initial_copies_all_stored='copy(nonzeros(S)), 0, UmfpackWS' in umf,
    scalar_broadcast='($f)(A::Number, B::AbstractArray) = broadcast_preserving_zero_d($f, A, B)' in arraymath,
    sparse_scalar_capture='parevalf, passedargstup = capturescalars(f, args)' in higher,
    sparse_map_discards_zero='if isfixed || _isnotzero(Cx)' in higher,
    sparse_copy='sparse(S::AbstractSparseMatrixCSC) = copy(S)' in sparse,
    successful_prefix_count=2*5+2*7+2*7+(2*7+5)+(2*7+1)+2*7+3==89)
result=dict(all_passed=all(checks.values()),checks=checks,
    explanation='Source-derived stored_zeros/native location from fixed order and 89 passes: 16 stored entries including 12 explicit zeros become 4 nonzero entries under scalar sparse broadcast. lu! defaults reuse_symbolic=true and rejects changed pattern. Runtime captured stack/error/counts, not intermediate CSC arrays.',
    next='Separate test-only repair: copy B and scale its nzval privately while retaining colptr/rowval, explicitly qualify unchanged pattern and successful source refactor. No fixture deletion, tolerance change, production fix, current retry or automatic cost continuation.',
    sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Fresh source-read bindings, not retroactive launch pins or a new runtime experiment')
with (D/'source-analysis.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks),indent=2))
if not result['all_passed']:raise SystemExit(1)
