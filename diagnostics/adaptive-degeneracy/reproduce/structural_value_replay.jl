using JSimplex,Serialization,Test,SHA,TOML,LinearAlgebra
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"));isolate_pricing_trials!()
include(joinpath(@__DIR__,"joint_point_probe.jl"))
root=joinpath(dirname(dirname(pathof(JSimplex))),".superpowers/adaptive-degeneracy")
records=Dict{String,Any}[]
@testset "Earlier mathematical points remain recoverable" begin
    for name in ("runtime-point/runtime-point.bin","coupled-point/runtime-coupled.bin",
                 "coupled-point/runtime-coupled-candidate.bin","joint-point/runtime-joint.bin","joint-point/runtime-joint-native.bin")
        path=joinpath(root,name);ws=point_workspace(path);before=copy(ws.primal)
        @test JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test JSimplex._legacy_primal_point_certified(ws)
        nonbasic=ws.basis.states.!=JSimplex.BASIC
        @test isequal(ws.primal[nonbasic],before[nonbasic])
        push!(records,Dict("snapshot"=>name,"sha256"=>bytes2hex(open(sha256,path)),
            "kind"=>"mathematical point","certified"=>true))
    end
end
@testset "Captured pivots finish with certified points" begin
    for (name,iteration) in (("runtime-point/runtime-point",6799),("coupled-point/runtime-coupled",8464),
        ("representable-point/runtime-representable-capture",14186),("extended-runtime/runtime-extended-capture",19222))
        prefix=joinpath(root,name);ws=deserialize(prefix*"-before.bin")
        ws.scratch.perturbations.workspace_id=objectid(ws)
        before=copy(ws.primal);failed=deserialize(prefix*".bin")
        @test JSimplex._legacy_primal_point_certified(ws)
        terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
        @test isnothing(terminal)
        @test ws.iterations==iteration
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
        same_basis=ws.basis.basic_indices==failed.basis.basic_indices && ws.basis.states==failed.basis.states
        if iteration==19222
            @test same_basis
            @test isequal(ws.primal,before)
            @test ws.primal[8504]==before[8504]<0
        end
        push!(records,Dict("snapshot"=>name,"sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),
            "kind"=>"one pivot","iteration"=>iteration,"certified"=>true,"completed"=>isnothing(terminal),
            "same_captured_basis"=>same_basis,"same_prepoint"=>isequal(ws.primal,before),
            "maximum_change"=>maximum(abs.(ws.primal-before))))
    end
end
open(only(ARGS),"w") do io
    TOML.print(io,Dict("scope"=>"Native production recovery and one-pivot replays; not driver continuation","records"=>records))
end
