using Test,JSimplex,SparseArrays,LinearAlgebra

@testset "Modern phase-one interfaces" begin
    @test isdefined(JSimplex,:PhaseOneMap)
    @test isdefined(JSimplex,:run_phase_one!)
    @test isdefined(JSimplex,:remove_artificials!)
end

if isdefined(JSimplex,:PhaseOneMap) && isdefined(JSimplex,:run_phase_one!)
    @testset "General-basis phase one appends signed basic columns" begin
        for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}), sign in (-1,1)
            lower = sign == 1 ? zeros(T,2) : T[2,0]
            upper = [sign == 1 ? Bound(one(T)/T(2)) : Bound{T}(nothing),Bound{T}(nothing)]
            p = LinearProblem(sparse(T[2 1;1 3]),T[1,2];
                column_lower=lower,column_upper=upper,row_lower=T[2,0])
            original = deepcopy(p)
            options = SolverOptions(T;verbose=false,algorithm=:primal)
            policy = JSimplex.NumericalPolicy(T;phase_one=true)
            basis = JSimplex.Basis([1,4],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.BASIC])
            ws = JSimplex.initialize_from_basis(p,basis,options;policy)
            phase,map = JSimplex._phase_one_workspace(ws,policy,()->false)
            @test length(map.artificial_columns) == 1
            @test map.original_to_phase == [1,2,4,5]
            @test map.phase_to_original == [1,2,0,3,4]
            @test phase.problem.A[:,3] == sign*p.A[:,1]
            @test phase.basis.basic_indices[1] == 3
            @test phase.primal[3] == (sign == 1 ? one(T)/T(2) : one(T))
            @test iszero(JSimplex.primal_infeasibility(phase))
            @test JSimplex._recomputed_basis_reliable(phase)
            @test ws.basis.basic_indices == [1,4]
            @test p.A == original.A && p.objective == original.objective
            @test p.column_lower == original.column_lower && p.column_upper == original.column_upper
        end
    end

    @testset "Phase one restores an original-dimension owned workspace" begin
        for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
            method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),backend in (:native,:markowitz)
            p = LinearProblem(sparse(T[1 1]),T[2,1];row_lower=T[1])
            saved = deepcopy(p)
            options = SolverOptions(T;verbose=false,algorithm=:primal,
                basis_update=method,basis_refactorization=backend)
            policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true)
            ws = JSimplex.initialize_workspace(p,options;
                progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
            budget = JSimplex.SimplexRunBudget(ws)
            result = JSimplex.run_phase_one!(ws,budget,policy,()->false)
            @test result.status == OPTIMAL
            # This internal status establishes a feasible start, not original
            # optimality. The original objective must still be optimized.
            @test isnothing(result.objective_value) && isnothing(result.primal)
            @test length(ws.basis.states) == 3
            @test all(1 .<= ws.basis.basic_indices .<= 3)
            @test ws.problem === p
            @test ws.costs == T[2,1,0]
            @test JSimplex._original_bounds_active(ws)
            @test iszero(JSimplex.primal_infeasibility(ws))
            @test JSimplex._recomputed_basis_reliable(ws)
            original = JSimplex.run_from_basis!(ws,budget,policy,()->false)
            @test original.status == OPTIMAL
            @test original.objective_value ≈ one(T)
            @test p.A == saved.A && p.objective == saved.objective
            @test p.row_lower == saved.row_lower && p.row_upper == saved.row_upper
        end
    end

    @testset "Zero basic artificials leave through verified exchanges" begin
        for T in (Float64,Rational{BigInt})
            p = LinearProblem(sparse(reshape(T[1,1],2,1)),T[1];row_lower=T[1,1],row_upper=T[1,1])
            policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true)
            d = JSimplex.SimplexDiagnostics()
            options = SolverOptions(T;verbose=false,algorithm=:primal)
            ws = JSimplex.initialize_workspace(p,options;
                progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
            result = JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
            @test result.status == OPTIMAL
            @test JSimplex.event_count(d,:artificial_removed) >= 1
            @test ws.iterations >= 2
            @test length(ws.basis.states) == 3
            @test ws.primal[1] == one(T)
            @test JSimplex._recomputed_basis_reliable(ws)
        end
    end
end
