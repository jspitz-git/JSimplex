# Reuse input validation, source digests, atomic reports and progress logging.
include(joinpath(@__DIR__,"../../huangfu-hall-public/reproduce/external.jl"))
# Flush diagnostics promptly without changing solver options or arithmetic.
struct HHFlushLogger <: AbstractLogger
    inner::HHLogger
end
Logging.min_enabled_level(l::HHFlushLogger)=Logging.min_enabled_level(l.inner)
Logging.shouldlog(l::HHFlushLogger,args...)=Logging.shouldlog(l.inner,args...)
Logging.catch_exceptions(::HHFlushLogger)=false
function Logging.handle_message(l::HHFlushLogger,args...;kwargs...)
    Logging.handle_message(l.inner,args...;kwargs...)
    flush(stderr)
end
function main(backend,selection,out,runtime_seconds=900.0)
backend in (:native,:markowitz) || error("Unknown backend")
selection in ("small","runtime") || error("Unknown selection")
ispath(out) && error("Use a new output directory");mkpath(out)
manifest=joinpath(@__DIR__,"../../basis-selective-preparation/reproduce/external-inputs.toml")
entries=TOML.parsefile(manifest)["cases"]
if selection=="runtime"
    entries=[Dict("id"=>"mps/runtime","path"=>"/home/jspitz/mps/runtime.mps",
        "sha256"=>"d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68",
        "objective"=>51425691.76210457)]
end
opts(algorithm;seconds=900.0,verbose=true)=SolverOptions(;algorithm,
    basis_update=:huangfu_hall,basis_refactorization=backend,
    pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,
    refactorization_interval=80,iteration_limit=1_000_000,time_limit=seconds,verbose)
# Compile using a small instance; runtime remains subject to its own solve limit.
warm=LinearProblem(sparse([1.0 1;-1 1]),[1.0,2];row_lower=[3.0,1],column_lower=[0.0,1])
for algorithm in (:primal,:dual)
    r=solve(warm;options=opts(algorithm;verbose=false));@assert r.status==OPTIMAL
end
passed=true
for entry in entries, algorithm in (selection=="runtime" ? (:dual,) : (:primal,:dual))
    path=allowed_input(entry["path"])
    digest=bytes2hex(open(sha256,path));@assert digest==entry["sha256"]
    p=read_mps(path);o=opts(algorithm;seconds=selection=="runtime" ? runtime_seconds : 180.0)
    logger=HHLogger();GC.gc()
    println("START ",backend," ",entry["id"]," ",algorithm);flush(stdout)
    t=@timed with_logger(HHFlushLogger(logger)) do;solve(p;options=o,relax_integrality=true);end
    r=t.value;optimal=r.status==OPTIMAL
    feasible=optimal && JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
    matched=optimal && isapprox(r.objective_value,entry["objective"];rtol=1e-8,atol=1e-7)
    report=Dict{String,Any}("input"=>entry["id"],"input_sha256"=>digest,
        "algorithm"=>string(algorithm),"basis_refactorization"=>string(backend),"time_limit"=>o.time_limit,
        "status"=>string(r.status),"certified"=>feasible,"objective_matches"=>matched,
        "message"=>r.message,"iterations"=>r.statistics.iterations,
        "refactorizations"=>r.statistics.refactorizations,"restarts"=>logger.restarts,
        "seconds"=>r.statistics.elapsed_seconds,"call_seconds"=>t.time,
        "compile_seconds"=>t.compile_time,"allocated_bytes"=>t.bytes,
        "source_sha256"=>source_digest(),"harness_sha256"=>bytes2hex(sha256(read(@__FILE__))),
        "progress_sha256"=>bytes2hex(sha256(join(logger.progress,"\n"))),
        "julia"=>string(VERSION),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
    if optimal
        report["objective"]=r.objective_value
        report["primal_sha256"]=bytes2hex(sha256(reinterpret(UInt8,r.primal)))
    end
    save_report(joinpath(out,replace(entry["id"],"/"=>"-")*"-"*string(algorithm)*".toml"),report)
    println("DONE ",entry["id"]," ",algorithm," ",r.status," certified=",feasible," matched=",matched);flush(stdout)
    passed &= feasible && matched
end
passed || error("Some external solves were not certified; see all saved reports")
end
main(Symbol(ARGS[1]),ARGS[2],ARGS[3],length(ARGS)>3 ? parse(Float64,ARGS[4]) : 900.0)
