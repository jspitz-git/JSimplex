using Test, JSimplex, SparseArrays, Serialization, TOML
include(joinpath(@__DIR__, "capture_basis_failure.jl"))
const D = RuntimeBasisFailure
const J = JSimplex
@testset "basis-failure diagnostic" begin
    source = read(joinpath(dirname(pathof(J)), "simplex_driver.jl"), String)
    @test D.checked_verifier(source) isa Expr
    @test_throws ErrorException D.checked_verifier(replace(source,
        "_finite_workspace(ws) || return false" => "_finite_workspace(ws) || return true"))
    mktempdir() do dir
        problem = LinearProblem(sparse(reshape([1.0],1,1)), [1.0];
            row_lower=[0.0], row_upper=[2.0], column_lower=[1.0])
        options = SolverOptions(basis_update=:huangfu_hall, basis_refactorization=:native)
        ws = J.initialize_workspace(problem, options)
        input = joinpath(dir,"small.bin")
        serialize(input, (;problem,basis=ws.basis,options,target_primal=[1.0],
            iterations=0,refactorizations=0))
        prefix = joinpath(dir,"reliable")
        @test D.main(input,prefix,60.0) == 2
        @test TOML.parsefile(prefix*".run.toml")["outcome"] == "no_failure_captured"
        @test !isfile(prefix*".basis-failure.bin")
        @test_throws ErrorException D.main(input,prefix,60.0)
        D.output_prefix[] = joinpath(dir,"failure")
        ws.costs[1] = NaN
        @test_throws D.Captured Base.invokelatest(J._verify_driver_basis!,ws,J._guard_stop_callback(()->false))
        snapshot = deserialize(D.output_prefix[]*".basis-failure.bin")
        @test snapshot.failure.kind == "returned_false"
        @test isnan(snapshot.costs[1])
        @test snapshot.rho == ws.scratch.rho
        @test snapshot.factorization isa typeof(ws.factorization)
        @test snapshot.factorization.refactor_workspace === nothing
        @test ws.factorization.refactor_workspace !== nothing
        @test snapshot.factorization.base.lower == ws.factorization.base.lower
        @test snapshot.factorization.base.upper == ws.factorization.base.upper
        @test D.equations(snapshot)[2] == J._basis_primal_rhs(ws)
        @test !iszero(only(D.equations(snapshot)[2]))
        report = TOML.parsefile(D.output_prefix[]*".basis-failure.toml")
        @test !report["finite_workspace"]
        replay = D.summarize(snapshot)
        @test replay["primal"]["reliable"]
        @test !replay["finite_workspace"]
        D.output_prefix[] = joinpath(dir,"exception")
        original = ErrorException("original callback exception")
        caught = try
            Base.invokelatest(J._verify_driver_basis!,ws,
                J._guard_stop_callback(()->throw(original)))
            nothing
        catch exception
            exception
        end
        @test caught === original
        exceptional = deserialize(D.output_prefix[]*".basis-failure.bin")
        @test exceptional.failure.kind == "exception"
        @test occursin("original callback exception",exceptional.failure.exception)
        # A solver-internal numerical exception must escape the actual driver's
        # recovery handlers after capture, without a second snapshot attempt.
        policy = J.NumericalPolicy(Float64; numerical_profile=:checked,
            simplex_strategy=:adaptive)
        broken = J.initialize_workspace(problem,options;
            progress=J.SimplexProgressContext(problem;numerical_policy=policy))
        broken.factorization.base.upper.nzval .= 0.0
        D.output_prefix[] = joinpath(dir,"numerical-exception")
        guard = J._guard_stop_callback(()->false)
        @test_throws J._UnreliableBasisSolve Base.invokelatest(J._run_basis_terminal!,
            broken,J.SimplexRunBudget(broken),policy,guard)
        numerical = deserialize(D.output_prefix[]*".basis-failure.bin")
        @test numerical.failure.kind == "exception"
        @test numerical.failure.exception_type == "JSimplex._UnreliableBasisSolve"
        @test guard.exception isa J._UnreliableBasisSolve
    end
end
