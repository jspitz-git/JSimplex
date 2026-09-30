using JSimplex, Serialization, LinearAlgebra, Test, SHA, TOML
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
include(joinpath(@__DIR__,"joint_point_probe.jl"))
root=joinpath(dirname(dirname(pathof(JSimplex))),".superpowers/adaptive-degeneracy")
records=Dict{String,Any}[]
@testset "Joint recovery on captured mathematical points" begin
    for relative in ("runtime-point/runtime-point.bin","coupled-point/runtime-coupled.bin",
                     "coupled-point/runtime-coupled-candidate.bin","joint-point/runtime-joint.bin")
        path=joinpath(root,relative);ws=point_workspace(path)
        original=copy(ws.primal);basic=ws.basis.states.==JSimplex.BASIC
        @test !JSimplex._legacy_primal_point_certified(ws)
        accepted=JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test accepted
        @test JSimplex._legacy_primal_point_certified(ws)
        @test isequal(ws.primal[.!basic],original[.!basic])
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
        push!(records,Dict("snapshot"=>relative,"kind"=>"mathematical point",
            "sha256"=>bytes2hex(open(sha256,path)),"accepted"=>accepted,"certified"=>true,
            "nonbasic_unchanged"=>true,"maximum_change"=>maximum(abs.(ws.primal-original))))
    end
end
@testset "Actual captured pivots complete with a certified point" begin
    for (relative,iteration) in (("runtime-point/runtime-point",6799),
                                 ("coupled-point/runtime-coupled",8464))
        prefix=joinpath(root,relative)
        ws=deserialize(prefix*"-before.bin")
        ws.scratch.perturbations.workspace_id=objectid(ws)
        terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
        failed=deserialize(prefix*".bin")
        @test isnothing(terminal)
        @test ws.iterations==iteration
        @test ws.basis.basic_indices==failed.basis.basic_indices
        @test ws.basis.states==failed.basis.states
        nonbasic=ws.basis.states.!=JSimplex.BASIC
        @test isequal(ws.primal[nonbasic],failed.primal[nonbasic])
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
        push!(records,Dict("snapshot"=>relative,"kind"=>"one pivot",
            "sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),"iteration"=>iteration,
            "accepted"=>isnothing(terminal),"certified"=>true,"nonbasic_unchanged"=>true))
    end
end
open(only(ARGS),"w") do io
    TOML.print(io,Dict("records"=>records,"scope"=>"Point and one-pivot checks, not driver continuation"))
end
