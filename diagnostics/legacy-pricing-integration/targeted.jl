using JSimplex, Test, SparseArrays, LinearAlgebra
const root=dirname(dirname(@__DIR__))
@testset "Integrated fixed pricing and original safeguards" begin
    for file in ("dual_check_reuse_tests.jl","dual_fixed_pricing_check_reuse_tests.jl",
                 "dual_weight_validation_tests.jl","dual_small_pivot_retry_tests.jl",
                 "dual_small_pivot_price_tests.jl","pivot_retry_tests.jl","pivot_atomicity_tests.jl")
        include(joinpath(root,"test",file))
    end
end
function gate(source)
    s=read(source,String);p=first(findfirst("function _can_reuse_dual_checks(",s))
    first(Meta.parse(s,p))
end
const old=gate(joinpath(@__DIR__,"reference-gate.jl"))
const current=gate(joinpath(root,"src/dual_simplex.jl"))
@testset "Integrated whole small LP exact against original gate" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall), pricing in (:dantzig,:steepest_edge), input in ("afiro","sc50a")
        lp=read_mps(joinpath(@__DIR__,input*".mps"))
        opts=SolverOptions(algorithm=:dual,pricing=pricing,basis_update=manager,simplex_strategy=:legacy,presolve=false,verbose=false,time_limit=Inf)
        Core.eval(JSimplex,old); r=Base.invokelatest(solve,lp;options=opts)
        Core.eval(JSimplex,current); c=Base.invokelatest(solve,lp;options=opts)
        @test r.status==c.status==OPTIMAL
        @test JSimplex._original_primal_feasible(lp,r.primal,1e-7) && JSimplex._original_primal_feasible(lp,c.primal,1e-7)
        @test reinterpret(UInt64,r.objective_value)==reinterpret(UInt64,c.objective_value)
        @test isequal(r.primal,c.primal)
        @test r.statistics.iterations==c.statistics.iterations && r.statistics.refactorizations==c.statistics.refactorizations
    end
end
