using Test,JSimplex
const ROOT=dirname(dirname(pathof(JSimplex)))
@testset "Compiled working-point and allocation checks" begin
    include(joinpath(ROOT,"test/legacy_primal_perturbed_point_tests.jl"))
    include(joinpath(ROOT,"test/solver_tests.jl")) do expr
        expr isa Expr && expr.head == :macrocall &&
            expr.args[1] == Symbol("@testset") &&
            expr.args[3] != "Solver allocation regression" ? nothing : expr
    end
end
