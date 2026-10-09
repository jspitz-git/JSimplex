# Count actual whole-workspace checks without changing their predicate.
using JSimplex,SparseArrays,Test
const JS=JSimplex
s=read(joinpath(dirname(pathof(JS)),"dual_simplex.jl"),String)
ex,_=Meta.parse(s,first(findfirst("function _finite_workspace(",s)))
ex.args[1].args[1].args[1]=:_finite_budget_original
Core.eval(JS,ex)
@eval JS begin
    const _finite_budget_count=Ref(0)
    function _finite_workspace(ws::SimplexWorkspace{T}) where T
        _finite_budget_count[]+=1
        _finite_budget_original(ws)
    end
end
function main()
    @testset "Successful DSE update checks the unchanged workspace once" begin
        for T in (Float32,Float64,BigFloat)
            p=LinearProblem(sparse(T[1 0; -1 1]),T[1,1];row_lower=T[1,1])
            ws=JS.initialize_workspace(p,SolverOptions(verbose=false))
            JS._finite_budget_count[]=0
            @test JS.update_dual_pricing_weights!(ws,T[1,0],T[1,0,-1,0],T[1,0],1,one(T),one(T),()->false)
            @test JS._finite_budget_count[]==1
            @test !ws.dual_devex_fallback
        end
    end
end
Base.invokelatest(main)
