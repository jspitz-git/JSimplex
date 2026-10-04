using JSimplex,Test,TOML,SHA
root=dirname(dirname(pathof(JSimplex)))
entries=TOML.parsefile(joinpath(root,"diagnostics/basis-selective-preparation/reproduce/external-inputs.toml"))["cases"][1:2]
records=[]
@testset "Markowitz HH external scalars" begin
    for T in (Float32,BigFloat,Rational{BigInt}), entry in (T===Float32 ? entries[1:1] : entries), algorithm in (:primal,:dual)
        path=realpath(entry["path"])
        @assert !(lowercase(basename(path)) in ("big.mps","largo.mps","anymod.mps"))
        @assert bytes2hex(open(sha256,path))==entry["sha256"]
        p=read_mps(path;value_type=T)
        # The previously measured Float32 default-tolerance limitation is separate
        # from backend support. Predeclare the same precision-scaled control here.
        tolerances=T===Float32 ? (;primal_tolerance=sqrt(eps(T)),dual_tolerance=sqrt(eps(T))) : (;)
        o=SolverOptions(T;basis_update=:huangfu_hall,basis_refactorization=:markowitz,
            algorithm,verbose=false,time_limit=90.0,tolerances...)
        r=solve(p;options=o,relax_integrality=true)
        feasible=r.status==OPTIMAL && JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
        matched=r.status==OPTIMAL && isapprox(r.objective_value,T(entry["objective"]);rtol=T(1//100000),atol=T(1//100000))
        record=Dict("type"=>string(T),"input"=>entry["id"],"input_sha256"=>entry["sha256"],
            "algorithm"=>string(algorithm),"status"=>string(r.status),"certified"=>feasible,
            "objective_matches"=>matched,"seconds"=>r.statistics.elapsed_seconds,
            "iterations"=>r.statistics.iterations,"primal_tolerance"=>string(o.primal_tolerance),
            "dual_tolerance"=>string(o.dual_tolerance))
        r.status==OPTIMAL && (record["objective"]=string(r.objective_value))
        push!(records,record)
        open(ARGS[1],"w") do io;TOML.print(io,Dict("records"=>records));end
        println(record);flush(stdout)
        @test r.status==OPTIMAL
        @test feasible
        @test matched
    end
end
