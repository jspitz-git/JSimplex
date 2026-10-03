using JSimplex, SparseArrays, LinearAlgebra, TOML, SHA, Logging
BLAS.set_num_threads(1)
const ROOT = dirname(dirname(pathof(JSimplex)))
function source_digest()
    paths = ["Project.toml"]
    for (dir,_,files) in walkdir(joinpath(ROOT,"src")), name in files
        endswith(name,".jl") && push!(paths,relpath(joinpath(dir,name),ROOT))
    end
    bytes = UInt8[]
    for p in sort(paths)
        append!(bytes,codeunits(p*"\0"));append!(bytes,read(joinpath(ROOT,p)))
    end
    bytes2hex(sha256(bytes))
end
function save_report(path,report)
    open(io->TOML.print(io,report),path*".tmp","w")
    mv(path*".tmp",path;force=true)
end
function allowed_input(path)
    real = realpath(path)
    lowercase(basename(real)) in ("big.mps","largo.mps","anymod.mps") && error("Excluded input")
    real
end
mutable struct HHLogger <: AbstractLogger
    parent::ConsoleLogger
    progress::Vector{String}
    restarts::Int
end
HHLogger()=HHLogger(ConsoleLogger(stderr,Logging.Info),String[],0)
Logging.min_enabled_level(::HHLogger)=Logging.Info
Logging.shouldlog(::HHLogger,level,_module,group,id)=true
Logging.catch_exceptions(::HHLogger)=false
function Logging.handle_message(l::HHLogger,level,message,_module,group,id,file,line;kwargs...)
    msg=string(message)
    startswith(msg,"iter=") && push!(l.progress,first(split(msg," time=")))
    startswith(msg,"Restarting simplex on original LP") && (l.restarts+=1)
    Logging.handle_message(l.parent,level,message,_module,group,id,file,line;kwargs...)
end
function options_for(algorithm;seconds=900.0,verbose=true,interval=80)
    SolverOptions(;algorithm,pricing=:steepest_edge,basis_update=:huangfu_hall,basis_refactorization=:native,
        simplex_strategy=:legacy,partial_pricing=false,refactorization_interval=interval,
        iteration_limit=1_000_000,time_limit=seconds,verbose)
end
function full_run(mode,out,selection)
    ispath(out) && error("Use a new output directory");mkpath(out)
    manifest=joinpath(@__DIR__,"../../basis-selective-preparation/reproduce/external-inputs.toml")
    entries=TOML.parsefile(manifest)["cases"]
    harness=bytes2hex(sha256(vcat(read(@__FILE__),read(joinpath(@__DIR__,"reference.json")),read(manifest))))
    selection=="full" && push!(entries,Dict("id"=>"mps/runtime","path"=>"/home/jspitz/mps/runtime.mps",
        "sha256"=>"d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68","objective"=>51425691.76210457))
    selection in ("smoke","external","full") || error("Unknown selection")
    selection=="smoke" && (entries=entries[1:1])
    if selection=="full"
        # Compile the same solver entry point and certify the warmup first.
        fast=only(filter(e->e["id"]=="mps/fast0507",entries))
        for entry in (first(entries),fast)
            path=allowed_input(entry["path"]);bytes2hex(open(sha256,path))==entry["sha256"] || error("Input digest")
            p=read_mps(path);o=options_for(:dual;seconds=180.0,verbose=false)
            r=solve(p;options=o,relax_integrality=true)
            r.status==OPTIMAL && JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance) &&
                isapprox(r.objective_value,entry["objective"];rtol=1e-8,atol=1e-7) || error("Warmup failed $(r.status)")
        end
        entries=filter(e->e["id"] in ("mps/fast0507","mps/runtime"),entries)
    end
    for entry in entries, algorithm in (selection=="full" ? (:dual,) : (:primal,:dual))
        path=allowed_input(entry["path"]);bytes2hex(open(sha256,path))==entry["sha256"] || error("Input digest")
        p=read_mps(path);o=options_for(algorithm;seconds=occursin("runtime",entry["id"]) ? 900.0 : 180.0,
            interval=selection=="smoke" ? 2 : 80)
        logger=HHLogger();GC.gc();println("START ",mode," ",entry["id"]," ",algorithm);flush(stdout)
        t=@timed with_logger(logger) do;solve(p;options=o,relax_integrality=true);end
        r=t.value;optimal=r.status==OPTIMAL
        certified=optimal && JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
        matched=optimal && isapprox(r.objective_value,entry["objective"];rtol=1e-8,atol=1e-7)
        report=Dict{String,Any}("manager"=>mode,"input"=>entry["id"],"input_sha256"=>entry["sha256"],
            "algorithm"=>string(algorithm),"basis_refactorization"=>"native","simplex_strategy"=>"legacy",
            "pricing"=>"steepest_edge","partial_pricing"=>false,"refactorization_interval"=>o.refactorization_interval,
            "status"=>string(r.status),"message"=>r.message,"certified"=>certified,"objective_matches"=>matched,
            "seconds"=>r.statistics.elapsed_seconds,"call_seconds"=>t.time,"compile_seconds"=>t.compile_time,
            "allocated_bytes"=>t.bytes,"gc_seconds"=>t.gctime,"iterations"=>r.statistics.iterations,
            "refactorizations"=>r.statistics.refactorizations,"restarts"=>logger.restarts,
            "source_sha256"=>source_digest(),"manager_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"src/huangfu_hall_factorization.jl")))),
            "progress_sha256"=>bytes2hex(sha256(join(logger.progress,"\n"))),"julia"=>string(VERSION),
            "harness_sha256"=>harness,"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
        if optimal
            report["objective"]=r.objective_value;report["primal_sha256"]=bytes2hex(sha256(reinterpret(UInt8,r.primal)))
        end
        save_report(joinpath(out,replace(entry["id"],"/"=>"-")*"-"*string(algorithm)*".toml"),report)
        println("DONE ",mode," ",entry["id"]," ",algorithm," ",r.status," certified=",certified," matched=",matched);flush(stdout)
        certified && matched || error("Uncertified full solve: $(r.status) $(r.message)")
    end
end
if abspath(PROGRAM_FILE)==(@__FILE__)
    full_run("huangfu_hall",ARGS...)
end
