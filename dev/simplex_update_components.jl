module JSimplexUpdateComponents
using JSimplex,LinearAlgebra,SparseArrays

function checked_solve(factor,reference,values,transposed,mode)
    n = length(values)
    rhs,dest = JSimplex.IndexedVector{Float64}(n),JSimplex.IndexedVector{Float64}(n)
    JSimplex.load_indexed!(rhs,values)
    operation = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
    measured = @timed operation(dest,factor,rhs;kernel_mode=mode)
    expected = transposed ? transpose(reference) \ BigFloat.(values) : reference \ BigFloat.(values)
    residual = maximum(abs,BigFloat.(dest.values)-expected;init=BigFloat(0))
    allowance = 512eps(Float64)*max(BigFloat(1),maximum(abs,expected;init=BigFloat(0)))
    residual <= allowance || error("Bounded update chain failed its independent reference")
    Set(dest.indices) == Set(findall(!iszero,dest.values)) || error("Update support is inconsistent")
    return Dict("transposed"=>transposed,"kernel_mode"=>string(mode),
        "rhs_support"=>count(!iszero,values),"result_support"=>length(dest.indices),
        "seconds"=>measured.time,"allocated_bytes"=>measured.bytes,"reference_verified"=>true)
end

"""Exercise only an already constructed synthetic basis of at most 32x32."""
function _probe(B0::SparseMatrixCSC{Float64,Int})
    n,m = size(B0)
    n == m || throw(DimensionMismatch("Update component must be square"))
    n <= 32 || throw(ArgumentError("Update component exceeds 32x32"))
    all(isfinite,nonzeros(B0)) || throw(ArgumentError("Update component must be finite"))
    sequence = Tuple{Int,Vector{Float64}}[]
    for pivot in 1:min(2,n)
        forward,inverse = zeros(n),zeros(n)
        forward[pivot],inverse[pivot] = 2.0,0.5
        if n > 1
            neighbor = mod(pivot,n)+1
            forward[neighbor],inverse[neighbor] = 0.25,-0.125
        end
        push!(sequence,(pivot,forward)); push!(sequence,(pivot,inverse))
    end
    methods = Dict{String,Any}[]
    for (name,Factor) in (("pfi",JSimplex.PFIFactorization),
                         ("forrest_tomlin",JSimplex.ForrestTomlinFactorization),
                         ("suhl_suhl",JSimplex.SuhlSuhlFactorization),
                         ("bartels_golub",JSimplex.BartelsGolubFactorization)),
        backend in (:native,:markowitz)
        B = Matrix(B0)
        constructed = @timed Factor(sparse(B),Val(backend))
        factor = constructed.value
        unit = zeros(n); n > 0 && (unit[1] = 1.0)
        original_reference = lu(Matrix{BigFloat}(B))
        initial = checked_solve(factor,original_reference,unit,false,:sparse)
        saved = @timed JSimplex.copy_basis_factorization(factor)
        checkpoint = saved.value
        profiles = Dict{String,Any}[]
        update_seconds,update_bytes = 0.0,0
        for (pivot,tableau) in sequence
            replacement = B*tableau
            measured = @timed JSimplex.replace_column!(factor,tableau,pivot)
            update_seconds += measured.time; update_bytes += measured.bytes
            B[:,pivot] = replacement
            reference = lu(Matrix{BigFloat}(B))
            for values in (unit,ones(n)), transposed in (false,true)
                mode = values === unit ? :sparse : :auto
                push!(profiles,checked_solve(factor,reference,values,transposed,mode))
            end
        end
        cache_bytes = Base.summarysize(factor.sparse)
        base_builds,upper_rebuilds,dense_fallbacks = factor.sparse.base_builds,
            factor.sparse.upper_rebuilds,factor.sparse.dense_fallbacks
        factor_entries = JSimplex._factor_storage_count(factor)
        checked_solve(checkpoint,original_reference,unit,true,:sparse)
        refactored = @timed JSimplex.refactorize!(factor,sparse(B))
        isnothing(factor.sparse) || error("Refactorization retained stale indexed scratch")
        reference = lu(Matrix{BigFloat}(B))
        checked_solve(factor,reference,unit,false,:sparse)
        checked_solve(factor,reference,unit,true,:sparse)
        checked_solve(checkpoint,original_reference,unit,false,:sparse)
        push!(methods,Dict("basis_update"=>name,"backend"=>string(backend),
            "steps"=>length(sequence),"construction_seconds"=>constructed.time,
            "construction_allocated_bytes"=>constructed.bytes,"initial_indexed_solve"=>initial,
            "update_seconds"=>update_seconds,"update_allocated_bytes"=>update_bytes,
            "checkpoint_seconds"=>saved.time,"checkpoint_allocated_bytes"=>saved.bytes,
            "refactor_seconds"=>refactored.time,"refactor_allocated_bytes"=>refactored.bytes,
            "cache_storage_bytes"=>cache_bytes,"factor_storage_entries"=>factor_entries,
            "base_builds"=>base_builds,"upper_rebuilds"=>upper_rebuilds,
            "dense_fallbacks"=>dense_fallbacks,"profiles"=>profiles,
            "reference_verified"=>true,"checkpoint_verified"=>true,"refactor_reset_verified"=>true))
    end
    return Dict("basis_dimension"=>n,"basis_nonzeros"=>nnz(B0),
        "sequence_recipe"=>"Up to two pivot columns, each dyadic replacement followed by its inverse tableau",
        "simplex_solve"=>false,"full_sized_factorization"=>false,"methods"=>methods)
end

probe(B0::SparseMatrixCSC{Float64,Int}) = setprecision(()->_probe(B0),BigFloat,256)
end
