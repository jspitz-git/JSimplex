using JSimplex,Test,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
@testset "Presolve tolerance, certificates, and solver regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("presolve_tolerance","presolve_dispatch","retry_dispatch","benchmark_regression")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
    include(joinpath(@__DIR__,"dual_pivot_semantics.jl"))
end
