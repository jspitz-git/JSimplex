using JSimplex,Test,SparseArrays
root=dirname(dirname(pathof(JSimplex)))
@testset "Shared pipeline and typed HH policies" begin
    include(joinpath(root,"test/hypersparse_pipeline_storage_tests.jl"))
    include(joinpath(root,"test/hypersparse_pipeline_kernel_tests.jl"))
    include(joinpath(root,"test/hypersparse_pipeline_subtraction_tests.jl"))
    for T in (Float16,Float32,BigFloat,Rational{BigInt}), algorithm in (:primal,:dual)
        p=LinearProblem(sparse(T[1 1;-1 1]),T[1,2];row_lower=T[3,1],column_lower=T[0,1])
        o=SolverOptions(T;basis_update=:huangfu_hall,algorithm,verbose=false,presolve=false)
        policy=JSimplex.NumericalPolicy(T;hypersparse=true)
        r=JSimplex._solve_diagnosed(p,nothing;options=o,numerical_policy=policy)
        @test r.status==OPTIMAL
        @test r.objective_value==T(5)
        @test JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
    end
end
