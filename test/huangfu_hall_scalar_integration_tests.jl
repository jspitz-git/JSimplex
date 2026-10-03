using Test, JSimplex, SparseArrays
import MathOptInterface as MOI

for T in (Float32, BigFloat, Rational{BigInt}, Rational{Int})
@testset "Huangfu-Hall public solves $T" begin
    upper = LinearProblem(sparse(T[1.0 1; 1 0; 0 1]), T[-3.0, -2.0]; row_upper=T[4.0, 2.0, 3.0])
    lower = LinearProblem(sparse(T[1.0 1; -1 1]), T[1.0, 2.0]; row_lower=T[3.0, 1.0], column_lower=T[0.0, 1.0])
    for algorithm in (:primal, :dual), strategy in (:legacy, :adaptive), presolve in (false, true)
        options = SolverOptions(T; algorithm, basis_update=:huangfu_hall,
            simplex_strategy=strategy, presolve, verbose=false, refactorization_interval=2)
        for (problem, objective) in ((upper, -10.0), (lower, 5.0))
            result = solve(problem; options)
            @test result.status == OPTIMAL
            @test result.objective_value ≈ objective
            @test JSimplex._original_primal_feasible(problem, result.primal, options.primal_tolerance)
        end
    end
    for algorithm in (:primal, :dual)
        source = MOI.Utilities.Model{T}()
        x = MOI.add_variables(source, 2)
        for v in x; MOI.add_constraint(source, v, MOI.GreaterThan(zero(T))); end
        affine(a) = MOI.ScalarAffineFunction(MOI.ScalarAffineTerm.(T.(a), x), zero(T))
        MOI.add_constraint(source, affine([1.0, 1.0]), MOI.GreaterThan(T(3)))
        MOI.add_constraint(source, affine([-1.0, 1.0]), MOI.GreaterThan(one(T)))
        objective = affine([1.0, 2.0])
        MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
        MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
        optimizer = JSimplex.Optimizer{T}()
        MOI.set(optimizer, MOI.RawOptimizerAttribute("basis_update"), :huangfu_hall)
        MOI.set(optimizer, MOI.RawOptimizerAttribute("algorithm"), algorithm)
        MOI.set(optimizer, MOI.RawOptimizerAttribute("presolve"), false)
        MOI.set(optimizer, MOI.Silent(), true)
        indices, _ = MOI.optimize!(optimizer, source)
        @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
        @test MOI.get(optimizer, MOI.ObjectiveValue()) ≈ 5.0
        @test [MOI.get(optimizer, MOI.VariablePrimal(), indices[v]) for v in x] ≈ [1.0, 2.0]
    end
end

end

@testset "Huangfu-Hall working precision transfer" begin
    for (T,S,bits) in ((Float32,Float64,53),(Float64,BigFloat,128),(BigFloat,BigFloat,512))
        Int !== Int64 && (T === Float64 || S === Float64) && continue
        p=LinearProblem(sparse(T[2 1;1 3]),T[1,2];row_lower=T[2,1],row_upper=T[2,1])
        options=SolverOptions(T;basis_update=:huangfu_hall,verbose=false,presolve=false)
        policy=JSimplex.NumericalPolicy(T;precision_boosting=true)
        basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        ws=JSimplex.initialize_from_basis(p,basis,options;policy)
        budget=JSimplex.SimplexRunBudget(ws)
        fresh=JSimplex.transfer_precision(ws,S,bits,budget,policy)
        @test fresh isa JSimplex.SimplexWorkspace{S}
        @test fresh.factorization isa JSimplex.HuangfuHallFactorization{S}
        @test fresh.basis.basic_indices==basis.basic_indices
        @test eltype(fresh.factorization.base.lower)===S
        @test JSimplex._recomputed_basis_reliable(fresh)
        rhs=S[3,4]
        @test JSimplex.basis_matrix(fresh)*JSimplex.forward_solve(fresh.factorization,rhs) ≈ rhs
        @test eltype(ws.factorization.base.lower)===T
    end
end
