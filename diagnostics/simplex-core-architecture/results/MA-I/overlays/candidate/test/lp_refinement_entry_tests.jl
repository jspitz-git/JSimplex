using Test, JSimplex, SparseArrays

@testset "Public simplex entries use LP refinement before precision boosting" begin
    for T in (Float32,Float64), algorithm in (:primal,:dual), sense in (MIN_SENSE,MAX_SENSE),
        scaling in (:off,:on), presolve in (false,true)
        p=LinearProblem(sparse(reshape(T[8],1,1)),T[sense==MIN_SENSE ? 1 : -1];
            objective_constant=T(7),objective_sense=sense,column_lower=T[0],
            row_lower=T[8],row_upper=T[16])
        for enabled in (false,true)
            injected=Ref(false)
            diagnostics=JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
                if reason==:certification && size(ws.problem.A,1)>0 && !injected[]
                    ws.factorization=JSimplex._basis_factorization(2*JSimplex._basis_matrix!(ws),ws.options)
                    injected[]=true
                end
            end)
            policy=JSimplex.NumericalPolicy(T;lp_refinement=enabled,solve_refinement=false,
                recovery=false,refactor_timing=false)
            options=SolverOptions(T;algorithm,scaling,presolve,verbose=false)
            solution=JSimplex._solve_diagnosed(p,diagnostics;options,numerical_policy=policy)
            @test injected[]
            @test solution isa Solution{T}
            # Postsolve has an independent fresh-basis retry, which can repair
            # the one-shot fault even when LP refinement is disabled.
            @test solution.status==((enabled || presolve) ? OPTIMAL : NUMERICAL_ERROR)
            if enabled
                @test solution.primal==T[1]
                @test solution.objective_value==T(sense==MIN_SENSE ? 8 : 6)
                @test diagnostics.counts[:lp_refinement]>=1
                @test diagnostics.counts[:precision_boost]==0
                @test JSimplex._original_primal_feasible(p,solution.primal,options.primal_tolerance)
            elseif presolve
                @test solution.primal==T[1]
                @test diagnostics.counts[:lp_refinement]==0
            else
                @test isnothing(solution.primal)
            end
            @test p.A.nzval==T[8] && p.objective_constant==7
        end
    end
end
