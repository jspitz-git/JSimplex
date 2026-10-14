using JSimplex, SparseArrays, Test, TOML
const D=@__DIR__
Base.include(JSimplex,joinpath(D,"probe-original.jl"))
p=LinearProblem(sparse([2.0 3.0;4.0 0.0]),[0.0,2.0];objective_constant=7.0,
    row_lower=[4.0,nothing],row_upper=[4.0,20.0],column_lower=[nothing,nothing],column_upper=[nothing,nothing])
original=deepcopy(p)
r=JSimplex.zero_conversion_probe(p)
count=JSimplex.zero_conversion_count[]
correct=size(r.problem.A)==(1,1) && r.problem.A[1,1]==-6.0 && JSimplex.bound_value(r.problem.row_upper[1])==12.0
preserved=p.A==original.A && p.row_upper==original.row_upper && p.row_lower==original.row_lower
open(joinpath(ARGS[1],"raw.toml"),"w") do io
 TOML.print(io,Dict("expected_red"=>true,"zero_conversions"=>count,"correct"=>correct,"preserved"=>preserved,"loaded_path"=>pathof(JSimplex)))
end
@testset "Missing zero matrix entries avoid exact-zero conversion" begin
 @test correct
 @test preserved
 @test count==0
end
