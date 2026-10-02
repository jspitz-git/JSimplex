# Production-only replay of the captured pricing dead end.
using JSimplex,Serialization,LinearAlgebra,Test,TOML
BLAS.set_num_threads(1)
prefix,output=ARGS
ws=deserialize(prefix*"-rejected.bin")
@testset "Captured native direction-price recovery" begin
    @test ws.iterations==272
    @test JSimplex._legacy_primal_point_certified(ws)
    basis=copy(ws.basis.basic_indices);point=copy(ws.primal);costs=copy(ws.costs)
    terminal=JSimplex._primal_iteration!(ws,()->false,0.0)
    @test !isnothing(terminal) && terminal.status==OPTIMAL
    @test ws.iterations==272
    @test ws.basis.basic_indices==basis && ws.primal==point && ws.costs==costs
    @test isempty(ws.scratch.rejected_entering)
    @test JSimplex._legacy_primal_point_certified(ws)
end
open(output,"w") do io;TOML.print(io,Dict("accepted"=>true,"iteration"=>ws.iterations));end
