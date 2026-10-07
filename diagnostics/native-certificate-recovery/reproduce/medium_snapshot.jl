using JSimplex, LinearAlgebra, SparseArrays, Serialization, SHA, TOML
const JS=JSimplex

function restore_workspace(d,diagnostics)
    progress=JS.SimplexProgressContext(d.problem;diagnostics,
        numerical_policy=JS.NumericalPolicy(Float64,d.options))
    ws=JS._initialize_workspace_state(d.problem,d.options;progress)
    m=size(d.problem.A,1)
    ws.factorization=typeof(ws.factorization)(d.factor_base,copy(d.factor_updates),
        zeros(m),zeros(m),zeros(m),zeros(m),false,nothing,JS.HHUnitWorkspace(m,Float64),
        length(d.factor_updates),JS.HHPool(Float64),JS.HHPool(Float64),JS.HHExtractWorkspace())
    ws.basis=d.basis
    ws.primal.=d.primal
    ws.reduced_costs.=d.prices
    ws.costs.=d.costs
    ws.lower.=d.lower
    ws.upper.=d.upper
    ws.pricing_weights.=d.pricing_weights
    ws.iterations=d.iteration
    ws.refactorizations=d.refactorizations
    ws.perturbed=d.perturbed
    return ws
end

function main(snapshot,output,mode="cleanup")
    ispath(output) && error("Use a fresh report path")
    input="/home/jspitz/mps/medium.mps"
    @assert bytes2hex(open(sha256,input))=="79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0"
    d=deserialize(snapshot)
    @assert d.iteration_offset==0
    diag=JS.SimplexDiagnostics()
    ws=restore_workspace(d,diag)
    run=JS._internal_solution(ws,OPTIMAL,"saved terminal candidate")
    println("STAGE saved certificate: ",run.status);flush(stdout)
    @assert run.status==OPTIMAL
    @assert JS.event_count(diag,:certificate_corrected)==1
    report=Dict{String,Any}("algorithm"=>string(d.options.algorithm),
        "snapshot_sha256"=>bytes2hex(open(sha256,snapshot)),
        "saved_iteration"=>run.iterations,"saved_certificate_status"=>string(run.status),
        "source_revision"=>strip(read(`git -C $(dirname(dirname(pathof(JS)))) rev-parse HEAD`,String)),
        "source_path"=>dirname(dirname(pathof(JS))),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
    println("STAGE rebuild presolve");flush(stdout)
    root=dirname(dirname(pathof(JS)))
    bytes=IOBuffer()
    files=String[joinpath(root,"Project.toml")]
    for (dir,_,names) in walkdir(joinpath(root,"src")), name in names
        endswith(name,".jl") && push!(files,joinpath(dir,name))
    end
    for file in sort(files);write(bytes,relpath(file,root),'\0',read(file));end
    report["source_sha256"]=bytes2hex(sha256(take!(bytes)))
    original=read_mps(input)
    continuous=JS.relax_integrality(original)
    presolved=JS._presolve_for_solve(continuous,d.options.primal_tolerance;verbose=false)
    @assert !(presolved isa JS.PresolveFailure)
    scaled,scaling=JS.scale_problem(presolved.problem)
    working=JS._minimization_problem(scaled)
    n=size(working.A,2)
    @assert d.problem.A[:,1:n]==working.A
    @assert d.problem.objective[1:n]==working.objective
    # The artificial-column workspace is created with a zero constant and
    # retains it in phase II; the public driver evaluates the original point.
    augmented=d.options.algorithm==:primal && size(d.problem.A,2)>n
    @assert d.problem.objective_constant==(augmented ? 0.0 : working.objective_constant)
    report["working_objective_constant"]=working.objective_constant
    report["saved_objective_constant"]=d.problem.objective_constant
    @assert d.problem.row_lower==working.row_lower && d.problem.row_upper==working.row_upper
    @assert d.problem.column_lower[1:n]==working.column_lower && d.problem.column_upper[1:n]==working.column_upper
    @assert all(getfield(scaling,f)==getfield(d.scaling,f) for f in fieldnames(typeof(scaling)))
    basis=if d.options.algorithm==:primal
        JS._primal_original_basis(ws,n,size(d.problem.A,2)-n)
    else
        run.basis
    end
    @assert !isnothing(basis)
    println("STAGE postsolve primal");flush(stdout)
    target=JS.postsolve_primal(presolved,JS.unscale_primal(scaling,run.primal[1:n]))
    println("STAGE restore basis");flush(stdout)
    restored=JS.restore_basis(presolved,basis)
    options=d.options
    if mode=="handoff"
        serialize(output,(problem=continuous,basis=restored,target_primal=target,options,
            iterations=run.iterations,refactorizations=run.refactorizations,provenance=report))
        println("HANDOFF saved");flush(stdout)
        return
    end
    iterations,refactorizations=run.iterations,run.refactorizations
    # Only the terminal state is reconstructed. The public cleanup then creates
    # its own fresh workspace; this is not a claimed mid-iteration checkpoint.
    ws=nothing;d=nothing;run=nothing;presolved=nothing;scaled=nothing;working=nothing
    GC.gc(true)
    println("STAGE original cleanup");flush(stdout)
    context=JS.SolveContext(time_ns(),600.0,diag,JS.NumericalPolicy(Float64,options))
    timed=@timed Base.invokelatest(JS.cleanup_original,continuous,restored,options,context,
        iterations,refactorizations;target_primal=target)
    result=timed.value
    merge!(report,Dict("cleanup_status"=>string(result.status),"message"=>result.message,
        "cleanup_seconds"=>timed.time,"cleanup_compile_seconds"=>timed.compile_time,
        "iterations"=>result.iterations,"refactorizations"=>result.refactorizations,
        "original_primal_feasible"=>result.status==OPTIMAL &&
            JS._original_primal_feasible(continuous,result.primal,options.primal_tolerance),
        "events"=>Dict(string(k)=>v for (k,v) in diag.counts if v!=0)))
    if result.status==OPTIMAL
        obj=JS._restored_objective(original,result.primal)
        report["original_objective_evaluable"]=!isnothing(obj)
        !isnothing(obj) && (report["objective"]=obj)
    end
    open(output,"w") do io;TOML.print(io,report;sorted=true);end
    println(report);flush(stdout)
    @assert result.status==OPTIMAL && report["original_primal_feasible"] && report["original_objective_evaluable"]
end
Base.invokelatest(main,ARGS...)
