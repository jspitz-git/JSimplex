using Test, JSimplex, Logging, TOML
include(joinpath(@__DIR__, "..", "iteration_allocations.jl"))
using .JSimplexIterationAllocations

@testset "Iteration allocation audit preserves prepared states" begin
    audit = JSimplexIterationAllocations
    path = joinpath(@__DIR__, "..", "..", "test", "fixtures", "solver", "afiro.mps")
    problem = read_mps(path)
    original = deepcopy(problem)
    for method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), algorithm in (:dual,:primal)
        workspace, metadata, terminal = with_logger(NullLogger()) do
            audit.prepare_workspace(problem, algorithm, method, :steepest_edge, 3)
        end
        @test isnothing(terminal)
        @test metadata["completed_steps"] == 3
        @test metadata["updates"] > 0
        @test algorithm == :dual || metadata["phase"] == "primal_phase_two_with_fixed_artificials"
        saved, _, _ = with_logger(NullLogger()) do
            audit.prepare_workspace(problem, algorithm, method, :steepest_edge, 3)
        end
        @test isequal(saved.problem.A, workspace.problem.A)
        @test saved.basis.basic_indices !== workspace.basis.basic_indices
        @test saved.scratch.row_rhs !== workspace.scratch.row_rhs
        @test saved.factorization.updates !== workspace.factorization.updates
        @test saved.factorization.work !== workspace.factorization.work
        B = JSimplex.basis_matrix(workspace)
        rhs = collect(1.0:size(B,1))
        @test B*JSimplex.forward_solve(saved.factorization,rhs) ≈ rhs
        @test transpose(B)*JSimplex.transpose_solve(saved.factorization,rhs) ≈ rhs
        before = (copy(workspace.primal),copy(workspace.reduced_costs),copy(workspace.basis.basic_indices),length(workspace.factorization.updates))
        with_logger(NullLogger()) do
            JSimplex.recompute!(saved;refactorize=true)
        end
        @test isequal(before,(workspace.primal,workspace.reduced_costs,workspace.basis.basic_indices,length(workspace.factorization.updates)))
        @test isequal(problem.A,original.A) && isequal(problem.objective,original.objective)
        @test isequal(problem.column_upper,original.column_upper) && isequal(problem.row_lower,original.row_lower)
    end
end

@testset "Iteration audit distinguishes kernels and pricing caches" begin
    path = joinpath(@__DIR__, "..", "..", "test", "fixtures", "solver", "afiro.mps")
    problem = read_mps(path)
    results = audit_iterations(problem;samples=1,steps=(0,3),methods=(:pfi,:forrest_tomlin),pricings=(:dantzig,:steepest_edge))
    @test length(results)==16
    for snapshot in results
        @test snapshot["preparation_status"]=="READY"
        @test snapshot["completed_steps"]==snapshot["requested_steps"]
        @test snapshot["pivot_available"]
        stages=Dict(row["stage"]=>row for row in snapshot["stages"])
        @test all(haskey(stages,name) for name in ("basis_matrix","recompute","refactorize","forward_solve","transpose_solve","replace_column","iteration"))
        if snapshot["algorithm"]=="dual"
            @test all(haskey(stages,name) for name in ("dual_edge_selection","price","dual_ratio","bound_flipping_ratio"))
        else
            @test all(haskey(stages,name) for name in ("primal_pricing_before_probe","primal_pricing","primal_ratio"))
        end
        @test all(row["samples"]==1 && row["compile_seconds"]==0 && row["allocations"]>=0 && row["bytes"]>=0 for row in values(stages))
        @test stages["recompute"]["allocations"]==0
        @test stages["forward_solve"]["allocations"]==0 && stages["transpose_solve"]["allocations"]==0
        @test stages["iteration"]["status"]=="CONTINUE"
        @test stages["iteration"]["completed_steps"]==1
    end
    @test_throws ArgumentError audit_iterations(problem;samples=0)
    @test_throws ArgumentError audit_iterations(problem;steps=(-1,))
    @test_throws ArgumentError iteration_allocation_main(["--unknown"])
    @test_throws ArgumentError iteration_allocation_main(["--samples=0"])
    @test_throws ArgumentError iteration_allocation_main(["--steps=-1"])
    mktemp() do path,io
        close(io)
        @test iteration_allocation_main(["afiro","--samples=1","--steps=0","--pricing=dantzig","--output=$path"];io=devnull)==0
        report=TOML.parsefile(path)
        @test report["presolve"]==false && report["scaling"]=="off"
        @test report["state_setup"]=="deterministic_replay_outside_measurement"
        @test length(report["datasets"]["afiro"])==2
    end
end
