using JSimplex,Test,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
@testset "Presolve tolerance and allocation regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    for name in ("presolve_tolerance","presolve","presolve_dispatch","presolve_allocation",
                 "basic_presolve_allocation","singleton_bounds_allocation","propagation_bounds_allocation")
        println("CHECK ",name);flush(stdout)
        include(joinpath(root,"test",name*"_tests.jl"))
    end
    include(joinpath(root,"test/solver_tests.jl")) do expr
        expr isa Expr && expr.head == :macrocall && expr.args[1] == Symbol("@testset") &&
            expr.args[3] != "Solver allocation regression" ? nothing : expr
    end
end
