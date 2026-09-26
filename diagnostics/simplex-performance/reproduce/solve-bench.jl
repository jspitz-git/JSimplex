using JSimplex, Logging, TOML, SHA, LinearAlgebra
BLAS.set_num_threads(1)
function main()
    path,algorithm,strategy,limit_text,sample_text,output = ARGS[1:6]
    mode = get(ARGS,7,"default")
    warmup_mode = get(ARGS,8,"full")
    options=SolverOptions(algorithm=Symbol(algorithm),simplex_strategy=Symbol(strategy),
        time_limit=parse(Float64,limit_text),iteration_limit=1_000_000,verbose=false)
    problem=read_mps(path)
    policy=if mode=="selected"
        JSimplex.NumericalPolicy(Float64;stable_ratio=true,incremental_primal=true,
            incremental_primal_pivots=true,sparse_pricing=true)
    else
        nothing
    end
    run()=with_logger(NullLogger()) do
        isnothing(policy) ? solve(problem;options,relax_integrality=true) :
            JSimplex._solve_diagnosed(problem,nothing;options,relax_integrality=true,numerical_policy=policy)
    end
    report=Dict{String,Any}("input"=>path,"source"=>pathof(JSimplex),"source_sha256"=>bytes2hex(open(sha256,path)),
        "algorithm"=>algorithm,"strategy"=>strategy,"policy_mode"=>mode,"threads"=>1,
        "iteration_limit"=>1_000_000,"time_limit"=>options.time_limit,"warmups"=>[],"samples"=>[])
    h=SHA.SHA2_256_CTX()
    root=dirname(dirname(pathof(JSimplex)))
    files=["Project.toml"]
    for (dir,_,names) in walkdir(joinpath(root,"src")),name in names
        endswith(name,".jl") && push!(files,relpath(joinpath(dir,name),root))
    end
    for name in sort(files);SHA.update!(h,codeunits(name*"\0"));SHA.update!(h,read(joinpath(root,name)));end
    report["production_sha256"]=bytes2hex(SHA.digest!(h))
    report["warmup_mode"]=warmup_mode
    report["harness_sha256"]=bytes2hex(open(sha256,@__FILE__))
    if warmup_mode=="afiro"
        warm_problem=read_mps(joinpath(root,"test/fixtures/solver/afiro.mps"))
        warm=with_logger(NullLogger()) do;solve(warm_problem;options,relax_integrality=true);end
        report["compilation_warmup"]=Dict("input"=>"test/fixtures/solver/afiro.mps","status"=>string(warm.status),"seconds"=>warm.statistics.elapsed_seconds)
    end
    for repetition in (warmup_mode=="full" ? 0 : 1):parse(Int,sample_text)
        GC.gc()
        timed=@timed run()
        result=timed.value
        sample=Dict{String,Any}("status"=>string(result.status),"message"=>result.message,
            "seconds"=>result.statistics.elapsed_seconds,"outer_seconds"=>timed.time,
            "iterations"=>result.statistics.iterations,"refactorizations"=>result.statistics.refactorizations,
            "allocated_bytes"=>timed.bytes,"gc_seconds"=>timed.gctime,"process_peak_rss"=>Sys.maxrss())
        if result.status==OPTIMAL
            sample["objective"]=result.objective_value
            sample["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
        end
        push!(report[repetition==0 ? "warmups" : "samples"],sample)
        open(output,"w") do io;TOML.print(io,report);end
        println(basename(path)," ",algorithm," ",strategy," ",mode," repetition=",repetition," ",sample);flush(stdout)
    end
end
main()
