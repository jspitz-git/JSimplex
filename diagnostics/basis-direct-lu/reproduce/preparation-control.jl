# Isolate the selective-preparation cache lifecycle from the fused kernels.
# Advance/evict the same preparation slot as the original public FTRAN, while
# omitting the auxiliary spike/direction payload copies.
using JSimplex, TOML, SHA
@eval JSimplex function _ordinary_forward_solve!(destination::Vector{T},
        factor::AbstractTriangularBasisFactorization{T},rhs::AbstractVector) where T
    destination===factor.work && throw(ArgumentError("destination aliases work"))
    _check_triangular_dimensions(factor,destination,rhs)
    _begin_prepared_spike!(factor,destination)
    return _triangular_forward_solve!(destination,factor,rhs,false)
end
ARGS[4]=="correction" || error("This control requires correction mode")
include(joinpath(@__DIR__,"solve.jl"))
report=TOML.parsefile(ARGS[7])
report["preparation_policy"]="original slot lifecycle, auxiliary payload copies omitted"
report["control_sha256"]=bytes2hex(open(sha256,@__FILE__))
open(ARGS[7],"w") do io;TOML.print(io,report);end
