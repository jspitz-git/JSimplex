using Test, JSimplex, SHA
@testset "Legacy primal phase transition solves degen3" begin
    path="/home/jspitz/NetLib/degen3.mps"
    @test bytes2hex(open(sha256,path))=="7a149f601961000bc365c3431276d52d1e13e04ae459f98177d6b459d9a65475"
    p=read_mps(path)
    options=SolverOptions(;algorithm=:primal,basis_update=:pfi,basis_refactorization=:native,
        refactorization_interval=80,pricing=:steepest_edge,simplex_strategy=:legacy,
        partial_pricing=false,time_limit=150.0,iteration_limit=1_000_000,verbose=false)
    r=solve(p;options,relax_integrality=true)
    @test r.status==OPTIMAL
    if r.status==OPTIMAL
        @test JSimplex._original_primal_feasible(p,r.primal,options.primal_tolerance)
        @test isapprox(r.objective_value,-987.294;atol=1e-6,rtol=0)
    end
end
