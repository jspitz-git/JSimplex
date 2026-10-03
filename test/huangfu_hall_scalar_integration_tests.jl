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
        policy=JSimplex.NumericalPolicy(T;precision_boosting=true,hypersparse=true)
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

@testset "BigFloat HH hypersparse policy uses a precision-safe dense fallback" begin
    for wider in (:base,:update,:rhs)
        bits=wider === :base ? 256 : 64
        ws,B=setprecision(BigFloat,bits) do
            alpha=wider === :base ? 1+BigFloat(2)^(-180) : BigFloat(1)
            B=BigFloat[1 alpha;0 1]
            p=LinearProblem(sparse(B),BigFloat[1,2];row_lower=BigFloat[2,1],row_upper=BigFloat[2,1])
            o=SolverOptions(BigFloat;basis_update=:huangfu_hall,verbose=false,presolve=false)
            policy=JSimplex.NumericalPolicy(BigFloat;hypersparse=true)
            basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
            ws=try
                JSimplex.initialize_from_basis(p,basis,o;policy)
            catch err
                err
            end
            ws,B
        end
        @test ws isa JSimplex.SimplexWorkspace{BigFloat}
        ws isa JSimplex.SimplexWorkspace{BigFloat} || continue
        setprecision(BigFloat,256) do
            if wider === :update
                delta=BigFloat(2)^(-180)
                direction=BigFloat[1+2delta,delta]
                JSimplex.replace_column!(ws.factorization,direction,1)
                B[:,1]=B*direction
            end
            rhs=setprecision(BigFloat,wider === :rhs ? 256 : 64) do
                wider === :rhs ? BigFloat[1+BigFloat(2)^(-180),1] : BigFloat[1,1]
            end
            for transposed in (false,true), mode in (:auto,:sparse,:dense), alias in (false,true)
                expected=transposed ? transpose(B)\rhs : B\rhs
                actual=copy(rhs)
                setprecision(BigFloat,64) do
                    JSimplex._pipeline_basis_solve!(actual,ws,alias ? actual : rhs;
                        transposed,kernel_mode=mode)
                    @test precision(BigFloat)==64
                end
                @test actual ≈ expected rtol=8eps(BigFloat) atol=8eps(BigFloat)
                @test all(v->precision(v)>=256,actual)
            end
        end
    end
end
