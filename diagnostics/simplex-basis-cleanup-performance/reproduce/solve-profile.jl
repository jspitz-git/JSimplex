using JSimplex, Logging, TOML, SHA, Profile
function main()
    path, algorithm, interval, seconds, output = ARGS[1:5]
    lowercase(basename(realpath(path))) in ("big.mps", "largo.mps", "anymod.mps") && error("Excluded large model")
    options = SolverOptions(algorithm=Symbol(algorithm), basis_update=:bartels_golub,
        basis_refactorization=:native, pricing=:steepest_edge, simplex_strategy=:legacy,
        refactorization_interval=parse(Int,interval),time_limit=parse(Float64,seconds),
        iteration_limit=parse(Int,get(ARGS,6,"1000000")),verbose=true)
    warm=SolverOptions(algorithm=Symbol(algorithm),basis_update=:bartels_golub,verbose=false)
    with_logger(NullLogger()) do
        solve(read_mps(joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps"));options=warm)
    end
    problem=read_mps(path)
    d=JSimplex.SimplexDiagnostics(;kernel_timing=true)
    Profile.init(n=5_000_000,delay=0.01)
    timed=@timed @profile JSimplex._solve_diagnosed(problem,d;options,relax_integrality=true)
    r=timed.value
    report=Dict("input"=>path,"input_sha256"=>bytes2hex(open(sha256,path)),
        "source"=>pathof(JSimplex),"algorithm"=>algorithm,"interval"=>parse(Int,interval),
        "julia"=>string(VERSION),"status"=>string(r.status),"message"=>r.message,
        "seconds"=>r.statistics.elapsed_seconds,"iterations"=>r.statistics.iterations,
        "refactorizations"=>r.statistics.refactorizations,"outer_seconds"=>timed.time,
        "allocated_bytes"=>timed.bytes,"peak_rss"=>Sys.maxrss(),
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts if v!=0),
        "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in d.kernel_nanoseconds if v!=0))
    if r.status==OPTIMAL
        report["objective"]=r.objective_value
        report["original_primal_certified"]=JSimplex._original_primal_feasible(problem,r.primal,options.primal_tolerance)
    end
    open(output,"w") do io; TOML.print(io,report); end
    open(output*".profile","w") do io; Profile.print(io;format=:flat,sortedby=:count,mincount=20); end
    println(report)
end
main()
