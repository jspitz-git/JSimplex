using JSimplex, Profile, Logging, TOML, LinearAlgebra
BLAS.set_num_threads(1)
const JS = JSimplex
path, algorithm, interval, limit, output = ARGS[1:5]
problem = read_mps(path)
options = SolverOptions(algorithm=Symbol(algorithm), refactorization_interval=parse(Int,interval),
    time_limit=parse(Float64,limit), verbose=false, log_level=Logging.Debug,
    simplex_strategy=Symbol(get(ARGS,6,"legacy")))
run() = with_logger(NullLogger()) do
    solve(problem; options, relax_integrality=true)
end
println("Loaded ",path," ",size(problem.A)," nnz=",length(problem.A.nzval)); flush(stdout)
warm = run()
println("Warmup ",warm.status," ",warm.statistics); flush(stdout)
GC.gc()
Profile.clear(); Profile.init(n=20_000_000,delay=parse(Float64,get(ARGS,7,"0.01")))
measured = @timed @profile run()
solution = measured.value
open(output*".profile", "w") do io
    Profile.print(io;format=:flat,sortedby=:count,mincount=20,C=false)
end
record=Dict("input"=>path,"algorithm"=>algorithm,"interval"=>parse(Int,interval),
    "status"=>string(solution.status),"message"=>solution.message,
    "seconds"=>measured.time,"solve_seconds"=>solution.statistics.elapsed_seconds,
    "strategy"=>string(options.simplex_strategy),"bytes"=>measured.bytes,"gc_seconds"=>measured.gctime,
    "iterations"=>solution.statistics.iterations,"refactorizations"=>solution.statistics.refactorizations,
    "objective"=>something(solution.objective_value,NaN),"precision"=>53,
    "warmup_status"=>string(warm.status),"warmup_seconds"=>warm.statistics.elapsed_seconds)
open(output*".toml","w") do io; TOML.print(io,record); end
println(record); flush(stdout)
