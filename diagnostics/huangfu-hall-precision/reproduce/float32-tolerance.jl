using JSimplex, Test, TOML, SHA
root=dirname(dirname(pathof(JSimplex)))
entry=first(TOML.parsefile(joinpath(root,"diagnostics/basis-selective-preparation/reproduce/external-inputs.toml"))["cases"])
@assert bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
p=read_mps(entry["path"];value_type=Float32)
records=[]
@testset "Float32 afiro with precision-scaled tolerances" begin
    for algorithm in (:primal,:dual), manager in (:pfi,:huangfu_hall)
        tolerance=sqrt(eps(Float32))
        o=SolverOptions(Float32;algorithm,basis_update=manager,verbose=false,time_limit=90.0,
            primal_tolerance=tolerance,dual_tolerance=tolerance)
        r=solve(p;options=o)
        record=Dict("algorithm"=>string(algorithm),"manager"=>string(manager),
            "status"=>string(r.status),"message"=>r.message,"primal_tolerance"=>tolerance,
            "dual_tolerance"=>tolerance,"seconds"=>r.statistics.elapsed_seconds)
        if r.status==OPTIMAL
            record["objective"]=r.objective_value
            record["feasible"]=JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
        end
        push!(records,record)
        open(ARGS[1],"w") do io;TOML.print(io,Dict("records"=>records));end
        println(record);flush(stdout)
        @test r.status==OPTIMAL
        if r.status==OPTIMAL
            @test record["feasible"]
            @test isapprox(r.objective_value,entry["objective"];rtol=1e-5,atol=1e-5)
        end
    end
end
