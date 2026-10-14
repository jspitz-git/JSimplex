# UNEXECUTED; original backend methods, renamed only. No candidate auto-load.
module MADenseProbe
using LinearAlgebra
using Base: require_one_based_indexing, @lazy_str
import MutableArithmetics
import JSimplex
using LinearAlgebra: _ustrip
const MA = MutableArithmetics
const LA = LinearAlgebra
const DenseLUBackend = JSimplex.DenseLUBackend
const Float32LUBackend = JSimplex.Float32LUBackend
function reference_forward!(destination::Vector, backend::Union{DenseLUBackend,Float32LUBackend},
                                 rhs::AbstractVector)
    ldiv!(destination, backend.factorization, rhs)
    return destination
end

function reference_transpose!(destination::Vector, backend::Union{DenseLUBackend,Float32LUBackend},
                                   rhs::AbstractVector)
    ldiv!(destination, transpose(backend.factorization), rhs)
    return destination
end

end # MADenseProbe
