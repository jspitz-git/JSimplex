using JSimplex, LinearAlgebra, SparseArrays, Serialization, TOML, SHA
const JS=JSimplex
function main(input,manager,backend,out)
    ispath(out) && error("Choose a fresh output directory")
    mkpath(out)
    path=realpath(input)
    lowercase(basename(path)) in ("big.mps","largo.mps","anymod.mps") && error("Excluded input")
    problem=read_mps(path)
    options=SolverOptions(algorithm=:dual,basis_update=Symbol(manager),basis_refactorization=Symbol(backend),
        refactorization_interval=80,pricing=:steepest_edge,simplex_strategy=:legacy,
        partial_pricing=false,time_limit=300.0,iteration_limit=1_000_000,verbose=true)
    root=dirname(dirname(pathof(JS)))
    source_sha256=Dict(relpath(path,root)=>bytes2hex(open(sha256,path))
        for path in [joinpath(root,"Project.toml");
                     [joinpath(dir,name) for (dir,_,files) in walkdir(joinpath(root,"src"))
                      for name in files if endswith(name,".jl")]])
    saved=Ref(0)
    observer=function(reason,ws)
        reason in (:certification,:certification_failed) || return
        saved[]+=1
        n=size(ws.problem.A,2)
        # Store the candidate equations and vectors, not process-local LU pointers.
        dual=JS._original_dual_witness(ws)
        data=(problem=ws.problem,options=ws.options,basis=deepcopy(ws.basis),
            primal=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),
            lower=copy(ws.lower),upper=copy(ws.upper),dual,
            B=JS.basis_matrix(ws),iteration=ws.iterations,reason,
            offset=ws.progress.iteration_offset)
        serialize(joinpath(out,"terminal-$(saved[]).bin"),data)
        println("CAPTURE ",reason," iteration=",ws.iterations," sequence=",saved[]);flush(stdout)
    end
    diag=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    t=@timed JS._solve_diagnosed(problem,diag;options,relax_integrality=true)
    r=t.value
    report=Dict{String,Any}("status"=>string(r.status),"message"=>r.message,
        "iterations"=>r.statistics.iterations,"seconds"=>t.time,"compile_seconds"=>t.compile_time,
        "input_sha256"=>bytes2hex(open(sha256,path)),"manager"=>manager,"backend"=>backend,
        "events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0),
        "snapshots"=>saved[],"source_revision"=>strip(read(`git -C $root rev-parse HEAD`,String)),
        "source_sha256"=>source_sha256)
    if r.status==OPTIMAL
        report["objective"]=r.objective_value
        report["original_primal_feasible"]=JS._original_primal_feasible(problem,r.primal,options.primal_tolerance)
    end
    open(joinpath(out,"result.toml"),"w") do io;TOML.print(io,report;sorted=true);end
    println(report)
end
Base.invokelatest(main,ARGS...)
