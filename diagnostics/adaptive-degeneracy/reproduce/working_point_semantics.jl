using Test,JSimplex
const ROOT=dirname(dirname(pathof(JSimplex)))
@testset "Working-bound and original-certificate regressions" begin
    for name in ("legacy_primal_perturbed_point","legacy_primal_point","legacy_primal_equation_point",
        "legacy_primal_point_recovery","simplex_strategy_separation","primal_perturbation",
        "primal_perturbation_integration","simplex_phase_one_state","simplex_phase_one_completion",
        "simplex_precision_activity","regression")
        println("CHECK ",name);flush(stdout)
        include(joinpath(ROOT,"test",name*"_tests.jl"))
    end
    # solver_tests shares this logger with the workspace suite.
    helpers = first(split(read(joinpath(ROOT,"test/simplex_workspace_tests.jl"),String),
                          "function test_workspace_type"))
    include_string(Main,helpers,"workspace_logger_helpers.jl")
    # Allocation assertions require normal compilation; run that one separately.
    include(joinpath(ROOT,"test/solver_tests.jl")) do expr
        expr isa Expr && expr.head == :macrocall &&
            expr.args[1] == Symbol("@testset") &&
            expr.args[3] == "Solver allocation regression" ? nothing : expr
    end
    include(joinpath(ROOT,"diagnostics/adaptive-degeneracy/reproduce/phase_one_interactions.jl"))
end
