using Test,JSimplex,SparseArrays

@testset "Transfer never lowers an already wider working precision" begin
    p,options,progress,basis=setprecision(BigFloat,512) do
        p=LinearProblem(sparse(BigFloat[2 1;1 3]),BigFloat[1,2];
            row_lower=BigFloat[2,0],row_upper=BigFloat[2,0])
        options=SolverOptions(BigFloat;verbose=false,pricing=:devex)
        progress=JSimplex.SimplexProgressContext(p)
        basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        (p,options,progress,basis)
    end
    ws=setprecision(BigFloat,1024) do
        JSimplex.initialize_from_basis(p,basis,options;progress,policy=progress.numerical_policy)
    end
    @test minimum(precision,ws.primal[1:2])>=1024
    fresh=setprecision(BigFloat,64) do
        JSimplex.transfer_precision(ws,BigFloat,128,JSimplex.SimplexRunBudget(ws),progress.numerical_policy)
    end
    @test minimum(precision,fresh.primal[1:2])>=1024
    @test minimum(precision,fresh.factorization.base.factorization.factors)>=1024
end
