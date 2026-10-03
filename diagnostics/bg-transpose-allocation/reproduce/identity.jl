using Test, JSimplex, SparseArrays, LinearAlgebra
# Compare the exact pre-fix public method, without loading a second package or
# changing any numerical kernel. The pinned commit must exist in the clone.
root = normpath(joinpath(@__DIR__, "../../.."))
source = read(`git -C $root show 084a74920a3c752acef50666331f11cbea473daa:src/triangular_factorization.jl`, String)
start = first(findfirst("function transpose_solve!(destination::Vector{T},\n", source))
stop = first(findnext("\nfunction transpose_solve(factor::", source, start))
method = replace(source[start:prevind(source, stop)],
                 "function transpose_solve!" => "function baseline_transpose_solve!"; count=1)
Base.include_string(JSimplex, method, "baseline-084a749.jl")
@testset "BTRAN arithmetic agrees with 084a749" begin
    for Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization), backend in (:native, :markowitz),
        T in (Float32, Float64, BigFloat, Rational{BigInt}), n in (0, 8)
        f = Factor(spdiagm(0 => ones(T, n)), Val(backend))
        rhs = T.(1:n)
        old = similar(rhs); new = similar(rhs)
        for step in 0:8
            if n > 0 && step > 0
                direction = fill(T(1)/8, n)
                direction[step] = T(2)
                JSimplex.replace_column!(f, direction, step)
            end
            for mode in (:separate, :inplace, :work)
                old_source = mode === :work ? f.work : mode === :inplace ? old : copy(rhs)
                copyto!(old_source, rhs)
                JSimplex.baseline_transpose_solve!(old, f, old_source)
                new_source = mode === :work ? f.work : mode === :inplace ? new : copy(rhs)
                copyto!(new_source, rhs)
                JSimplex.transpose_solve!(new, f, new_source)
                @test isequal(old, new)
            end
        end
    end
end
