using Test
using JET
using JSimplex
using JuMP

include("hypersparse_pipeline_jet_tests.jl")
include("simplex_start_jet_tests.jl")
include("simplex_phase_one_jet_tests.jl")
include("simplex_precision_jet_tests.jl")
include("simplex_precision_recovery_jet_tests.jl")
include("lp_refinement_jet_tests.jl")

@testset "JET indexed basis update kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
            factor = Factor(JSimplex.spdiagm(0=>ones(T,4)),Val(:markowitz))
            JSimplex.replace_column!(factor,T[1,2,0,0],1)
            rhs,dest = JSimplex.IndexedVector{T}(4),JSimplex.IndexedVector{T}(4)
            JSimplex.set_entry!(rhs,1,one(T))
            JET.@test_opt target_modules=(JSimplex,) JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
            JET.@test_opt target_modules=(JSimplex,) JSimplex.transpose_solve!(dest,factor,rhs;kernel_mode=:auto)
            JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
            JET.@test_opt target_modules=(JSimplex,) JSimplex.copy_basis_factorization(factor)
        end
    end
end

@testset "JET hypersparse base solve kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        B = JSimplex.sparse(T[2 0 0;1 3 0;0 0 4])
        for kind in (T == Float64 ? (:markowitz,:native) : (:markowitz,))
            view = JSimplex.sparse_solve_view(JSimplex._factorize_basis(B,Val(kind)))
            rhs,dest = JSimplex.IndexedVector{T}(3),JSimplex.IndexedVector{T}(3)
            JSimplex.set_entry!(rhs,1,one(T))
            JET.@test_opt target_modules=(JSimplex,) JSimplex.reachability_order(view.lower,rhs.indices)
            JET.@test_opt target_modules=(JSimplex,) JSimplex.hypersparse_forward_solve!(dest,view,rhs)
            JET.@test_opt target_modules=(JSimplex,) JSimplex.hypersparse_transpose_solve!(dest,view,rhs)
        end
    end
end

const MOI = JuMP.MOI

@testset "JET incremental primal updates" begin
    for T in (Float64, Rational{BigInt})
        p = LinearProblem(JSimplex.sparse(reshape(T[1], 1, 1)), T[-1];
            row_upper=T[2], column_upper=T[1])
        w = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.apply_primal_flip!(w, 1, one(T), T[-1])
        JET.@test_opt target_modules=(JSimplex,) JSimplex.audit_primal_values!(w)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.update_reduced_costs!(T[-2,3,0],T[-1,2,1],1,3,-one(T))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.apply_primal_pivot!(w,1,1,one(T),T[-1],T[-1,1];leaving_state=JSimplex.AT_UPPER)
    end
end

@testset "JET typed solver kernels" begin
    float_problem = LinearProblem(JSimplex.SparseArrays.sparse([1.0 1.0]),
                                  [-1.0, -2.0]; row_upper=[3.0])
    rational_problem = LinearProblem(
        JSimplex.SparseArrays.sparse(Rational{BigInt}[1 1]),
        Rational{BigInt}[-1, -2]; row_upper=Rational{BigInt}[3],
    )
    float_workspace = JSimplex.initialize_workspace(float_problem, SolverOptions(Float64))
    rational_workspace = JSimplex.initialize_workspace(
        rational_problem, SolverOptions(Rational{BigInt}),
    )

    JET.@test_opt target_modules=(JSimplex,) JSimplex.recompute!(float_workspace)
    JET.@test_opt target_modules=(JSimplex,) JSimplex.recompute!(rational_workspace)
    JET.@test_opt target_modules=(JSimplex,) JSimplex.presolve_problem(float_problem)
    JET.@test_opt target_modules=(JSimplex,) JSimplex.presolve_problem(rational_problem)
    report = JET.report_opt(solve, (typeof(float_problem),); target_modules=(JSimplex,))
    @test isempty(unexpected_precision_reports(report))
    @test Base.infer_return_type(solve, Tuple{typeof(float_problem)}) === Solution{Float64}
    JET.@test_opt target_modules=(JSimplex,) solve(rational_problem)
end

@testset "JET typed MOI adapter helpers" begin
    float_optimizer = JSimplex.Optimizer{Float32}()
    float_source = MOI.Utilities.Model{Float32}()
    float_x = MOI.add_variable(float_source)
    MOI.add_constraint(float_source, float_x, MOI.GreaterThan(Float32(1)))
    float_evaluation = JSimplex.MOIScalarEvaluation(
        Int[1], Float32[2], Float32(3),
    )
    rational_evaluation = JSimplex.MOIScalarEvaluation(
        Int[1], Rational{BigInt}[2//3], Rational{BigInt}(1//3),
    )

    # Basis strategies are mutable MOI attributes, so their value parameters
    # cannot be inferred from Optimizer{Float32} alone. The scalar type must be.
    @test Base.infer_return_type(JSimplex._solver_options,
        Tuple{typeof(float_optimizer)}) <: SolverOptions{Float32}
    @test JSimplex._solver_options(float_optimizer) isa SolverOptions{Float32,:pfi,:native}
    MOI.set(float_optimizer,MOI.RawOptimizerAttribute("basis_update"),:suhl_suhl)
    MOI.set(float_optimizer,MOI.RawOptimizerAttribute("basis_refactorization"),:markowitz)
    @test JSimplex._solver_options(float_optimizer) isa SolverOptions{Float32,:suhl_suhl,:markowitz}
    @test @inferred(JSimplex._evaluate_moi_function(
        float_evaluation,
        Float32[4],
    )) === Float32(11)
    @test @inferred(JSimplex._evaluate_moi_function(
        rational_evaluation,
        Rational{BigInt}[3],
    )) == Rational{BigInt}(7//3)
    JET.@test_opt target_modules=(JSimplex,) JSimplex._solver_options(float_optimizer)
end

@testset "JET retry dispatch retains concrete runtime options" begin
    for T in (Float64,Rational{BigInt}), diagnostics in (nothing,JSimplex.SimplexDiagnostics()),
        policy in (nothing,JSimplex.NumericalPolicy(T))
        # Analyze concrete runtime observer/policy types, including the backward
        # compatible constructor, rather than unspecified UnionAll parameters.
        context_type = typeof(JSimplex.SolveContext(UInt64(0),Inf,diagnostics,policy))
        report=JET.report_opt(JSimplex._retry_original,
            (LinearProblem{T},SolverOptions{T,:pfi,:native},
             context_type,JSimplex.DualRunResult{T});target_modules=(JSimplex,))
        @test isempty(unexpected_precision_reports(report))
    end
end

@testset "JET sparse basis update and cached Markowitz kernels" begin
    for T in (Float32,Float64)
        B = JSimplex.SparseArrays.spdiagm(0=>ones(T,32))
        for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization)
            factor = Factor(B)
            JET.@test_opt target_modules=(JSimplex,) JSimplex.replace_column!(factor,ones(T,32),1)
        end
        factor = JSimplex.PFIFactorization(B,Val(:markowitz))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.refactorize!(factor,B)
    end
end

@testset "JET adaptive dual perturbation kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        p = LinearProblem(JSimplex.sparse(ones(T,1,2)),zeros(T,2);row_lower=T[1])
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,stagnation_window=1)
        w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        for _ in 1:2
            w.iterations += 1
            JSimplex._observe_stagnation!(w,:dual,zero(T),zero(T))
        end
        JET.@test_opt target_modules=(JSimplex,) JSimplex._maybe_perturb_dual_costs!(w,()->false)
        journal = JSimplex.PerturbationJournal(w)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.restore_perturbations!(w,journal)
    end
end

@testset "JET adaptive primal bound perturbation kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        p=LinearProblem(JSimplex.sparse(T[1 -1]),T[-1,0];row_upper=T[0])
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,stagnation_window=1)
        w=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        for _ in 1:2
            w.iterations+=1
            JSimplex._observe_stagnation!(w,:primal,zero(T),zero(T))
        end
        JET.@test_opt target_modules=(JSimplex,) JSimplex._maybe_perturb_primal_bounds!(w,()->false)
        journal=JSimplex.PerturbationJournal(w)
        journal.bounds=JSimplex.BoundPerturbationState(w)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.restore_perturbations!(w,journal)
    end
end

@testset "JET automatic pricing and owned state kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        p=LinearProblem(JSimplex.sparse(T[1 2;1 1]),T[-3,-4];row_upper=T[4,3])
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,stagnation_window=2)
        w=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,pricing=:auto,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        JSimplex._prepare_auto_pricing!(w,:primal)
        JSimplex._primal_entering(w,w.options.dual_tolerance)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._prepare_auto_pricing!(w,:primal)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._validate_primal_edge!(w,1,T[-1,-1])
        JET.@test_opt target_modules=(JSimplex,) JSimplex._validate_dual_edge!(w,3,T[-1,0])
        JET.@test_opt target_modules=(JSimplex,) JSimplex.dual_edge_selection(w)
        trial=JSimplex._candidate_workspace(w)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._copy_pivot_state!(trial,w)
        for _ in 1:4
            w.iterations+=1
            JSimplex._observe_stagnation!(w,:primal,zero(T),zero(T))
        end
        JET.@test_opt target_modules=(JSimplex,) JSimplex._observe_auto_pricing!(w,:primal)
    end
end

@testset "JET owned partial pricing kernels" begin
    for T in (Float32,Float64,Rational{BigInt}), algorithm in (:primal,:dual)
        problem = algorithm == :primal ?
            LinearProblem(JSimplex.spzeros(T,1,129),fill(-one(T),129);row_upper=T[1],column_upper=ones(T,129)) :
            LinearProblem(JSimplex.spzeros(T,129,1),T[0];row_lower=ones(T,129))
        options = SolverOptions(T;algorithm,pricing=:auto,simplex_strategy=:adaptive,verbose=false)
        ws = JSimplex.initialize_workspace(problem,options)
        pool = JSimplex._pricing_pool!(ws,algorithm)
        policy = ws.progress.numerical_policy
        JET.@test_opt target_modules=(JSimplex,) JSimplex.select_pricing_candidate!(ws,pool,policy)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._select_workspace_pool!(ws,algorithm)
        destination = JSimplex._candidate_workspace(ws)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._copy_pricing_pool!(destination,ws)
    end
end

@testset "JET indexed sparse pricing kernels" begin
    for T in (Float32,Float64,Rational{BigInt})
        A = JSimplex.sparse(T[1 2;3 4])
        rows = JSimplex.RowAccess(A)
        rho,out = JSimplex.IndexedVector{T}(2),JSimplex.IndexedVector{T}(4)
        JSimplex.add_entry!(rho,2,T(2))
        ordered = Int[]
        JET.@test_opt target_modules=(JSimplex,) JSimplex.add_entry!(rho,1,one(T))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.clear!(rho)
        JET.@test_opt target_modules=(JSimplex,) JSimplex.sparse_price!(out,A,rho,rows;ordered_rows=ordered)
        problem = LinearProblem(A,T[1,3];row_lower=T[1,2])
        policy = JSimplex.NumericalPolicy(T;sparse_pricing=true)
        ws = JSimplex.initialize_workspace(problem,SolverOptions(T;verbose=false);
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
        JET.@test_opt target_modules=(JSimplex,) JSimplex.price!(zeros(T,4),ws,T[0,2])
        candidate = JSimplex._candidate_workspace(ws)
        JET.@test_opt target_modules=(JSimplex,) JSimplex._copy_sparse_pricing_cache!(candidate,ws)
    end
end
