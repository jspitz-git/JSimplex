using JSimplex, Test, TOML, SHA
root=normpath(joinpath(@__DIR__,"../../.."))
manifest=TOML.parsefile(joinpath(root,"diagnostics/basis-selective-preparation/reproduce/external-inputs.toml"))["cases"]
records=Dict{String,Any}[]
@testset "External HH scalar controls" begin
    for T in (Float32,BigFloat,Rational{BigInt}), entry in manifest[1:4], algorithm in (:primal,:dual)
        path=realpath(entry["path"])
        @assert !(lowercase(basename(path)) in ("big.mps","largo.mps","anymod.mps"))
        @assert bytes2hex(open(sha256,path))==entry["sha256"]
        p=read_mps(path;value_type=T)
        results=[]
        for manager in (:pfi,:huangfu_hall)
            o=SolverOptions(T;algorithm,basis_update=manager,presolve=true,verbose=false,
                time_limit=90.0,iteration_limit=100_000,refactorization_interval=80)
            println("START ",T," ",entry["id"]," ",algorithm," ",manager);flush(stdout)
            r=solve(p;options=o,relax_integrality=true)
            feasible=r.status==OPTIMAL && JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
            reference=r.status==OPTIMAL && isapprox(Float64(r.objective_value),entry["objective"];rtol=1e-5,atol=1e-5)
            record=Dict{String,Any}("type"=>string(T),"input"=>entry["id"],"input_sha256"=>entry["sha256"],
                "algorithm"=>string(algorithm),"manager"=>string(manager),"status"=>string(r.status),
                "feasible"=>feasible,"reference"=>reference,"iterations"=>r.statistics.iterations,
                "seconds"=>r.statistics.elapsed_seconds,"message"=>r.message)
            r.status==OPTIMAL && (record["objective"]=string(r.objective_value))
            push!(records,record);push!(results,r)
            open(ARGS[1],"w") do io;TOML.print(io,Dict("records"=>records));end
            println("DONE ",record);flush(stdout)
            @test feasible
            @test reference
        end
        if all(r->r.status==OPTIMAL,results)
            @test T <: Rational ? results[1].objective_value == results[2].objective_value :
                isapprox(results[1].objective_value,results[2].objective_value;rtol=T(1//100000),atol=T(1//100000))
        end
    end
end
