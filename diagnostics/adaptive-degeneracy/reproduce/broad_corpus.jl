# Expanded serial verification: identical policies, independent reader order,
# exact model equivalence, native-point certification, and repair coverage.
using JSimplex,JuMP,LinearAlgebra,SparseArrays,Serialization,SHA,TOML,Logging,Random
const MOI=JuMP.MOI
BLAS.set_num_threads(1)
const COUNTERS=Dict{String,Int}()
const COMPONENT_ENABLED=Ref(true)
const CAPTURE_PREFIX=Ref("")
const CAPTURES=String[]
function capture_component(x,B,rhs,policy,cutoff)
    path=CAPTURE_PREFIX[]*"-component-"*string(get(COUNTERS,"component_attempts",0))*".bin"
    serialize(path,(;x=copy(x),B=copy(B),rhs=copy(rhs),policy,cutoff))
    push!(CAPTURES,path)
end
function instrument!()
    path=joinpath(dirname(pathof(JSimplex)),"native_phase_transfer.jl")
    source=read(path,String)
    needle="    stop() && return false\n    trial=copy(x)"
    @assert count(needle,source)==1
    source=replace(source,needle=>"    Main.COUNTERS[\"local_attempts\"] += 1\n    component_trial=false\n"*needle)
    if occursin("        proposed=_native_phase_homogeneous_component!",source)
        needle="        proposed=_native_phase_homogeneous_component!(trial,B,rows,rhs,policy,cutoff,scratch,guard)"
        @assert count(needle,source)==1
        source=replace(source,needle=>"""
        Main.COUNTERS["component_attempts"] += 1
        Main.capture_component(trial,B,rhs,policy,cutoff)
        Main.COMPONENT_ENABLED[] || return false
        proposed=_native_phase_homogeneous_component!(trial,B,rows,rhs,policy,cutoff,scratch,guard)
        proposed && (Main.COUNTERS["component_proposals"] += 1)
        component_trial=proposed""")
        needle="            _native_phase_coupled_rows!(trial,B,rows,rhs,policy,cutoff,scratch,guard) || return false"
        @assert count(needle,source)==1
        source=replace(source,needle=>"""
            component_trial=false
            Main.COUNTERS["coupled_attempts"] += 1
            _native_phase_coupled_rows!(trial,B,rows,rhs,policy,cutoff,scratch,guard) || return false
            Main.COUNTERS["coupled_certified"] += 1""")
    else
    needle="        _native_phase_homogeneous_component!(trial,B,rows,rhs,policy,cutoff,scratch,stop) || return false"
    @assert count(needle,source)==1
    source=replace(source,needle=>"""
        Main.COUNTERS["component_attempts"] += 1
        Main.capture_component(trial,B,rhs,policy,cutoff)
        Main.COMPONENT_ENABLED[] || return false
        _native_phase_homogeneous_component!(trial,B,rows,rhs,policy,cutoff,scratch,stop) || return false
        Main.COUNTERS["component_proposals"] += 1
        component_trial=true""")
    end
    needle="    copyto!(x,trial)\n    return true\nend\n\nfunction _native_phase_primal_solve!"
    @assert count(needle,source)==1
    source=replace(source,needle=>"    component_trial && (Main.COUNTERS[\"component_certified\"] += 1)\n"*needle)
    needle="    _native_phase_transfer_enabled(ws) && !stop() && _finite_workspace(ws) || return false"
    @assert count(needle,source)==1
    source=replace(source,needle=>"    Main.COUNTERS[\"export_attempts\"] += 1\n"*needle)
    Base.include_string(JSimplex,source,"diagnostic_export_coverage.jl")
    hashes=Dict("export_coverage"=>bytes2hex(sha256(source)))
    include(joinpath(@__DIR__,"pricing_isolation.jl"))
    hashes["pricing_isolation"]=Base.invokelatest(()->isolate_pricing_trials!())
    source=read(joinpath(dirname(pathof(JSimplex)),"solver.jl"),String)
    a=first(findfirst("function _retry_original(",source));b=first(findnext("\nfunction ",source,a+1))-1
    body=source[a:b];needle="    time_limit_reached(context) &&"
    @assert count(needle,body)==1
    body=replace(body,needle=>"    Main.COUNTERS[\"original_retry_blocked\"] += 1\n    return previous\n"*needle)
    Base.include_string(JSimplex,body,"diagnostic_no_original_retry.jl")
    hashes["no_original_retry"]=bytes2hex(sha256(body))
    hashes
end
function reset_counters!()
    empty!(COUNTERS);empty!(CAPTURES)
    for name in ("local_attempts","component_attempts","component_proposals","component_certified","export_attempts","original_retry_blocked","coupled_attempts","coupled_certified")
        COUNTERS[name]=0
    end
end
function source_digest()
    root=dirname(dirname(pathof(JSimplex)));h=SHA.SHA2_256_CTX()
    paths=["Project.toml"]
    for (dir,_,names) in walkdir(joinpath(root,"src")),name in names
        endswith(name,".jl") && push!(paths,relpath(joinpath(dir,name),root))
    end
    for path in sort(paths)
        SHA.update!(h,codeunits(path*"\0"));SHA.update!(h,read(joinpath(root,path)))
    end
    bytes2hex(SHA.digest!(h))
end
function policy()
    p=JSimplex.NumericalPolicy(Float64;adaptive_stalling=true,adaptive_pricing=true,
        adaptive_primal_perturbation=true,adaptive_dual_perturbation=true,phase_one=true,refactor_timing=false)
    @assert all(s->getfield(p,s)==(s in (:adaptive_stalling,:adaptive_pricing,
        :adaptive_primal_perturbation,:adaptive_dual_perturbation,:phase_one)),JSimplex.NUMERICAL_SWITCHES)
    p
end
function jump_problem(path)
    model=JuMP.read_from_file(path)
    translation=JSimplex._translate_moi_model(JSimplex.Optimizer(),JuMP.backend(model))
    isnothing(translation.error) || error(translation.error)
    something(translation.problem)
end
function permuted(p,seed)
    rng=MersenneTwister(seed);rows=randperm(rng,size(p.A,1));columns=randperm(rng,size(p.A,2))
    JSimplex.LinearProblem(p.A[rows,columns],p.objective[columns];
        objective_constant=p.objective_constant,objective_sense=p.objective_sense,
        row_lower=p.row_lower[rows],row_upper=p.row_upper[rows],column_lower=p.column_lower[columns],
        column_upper=p.column_upper[columns],variable_domains=p.variable_domains[columns],
        row_names=p.row_names[rows],column_names=p.column_names[columns],name=p.name)
end
function equivalence(p,q)
    @assert size(p.A)==size(q.A)
    rd=Dict(s=>i for (i,s) in enumerate(p.row_names));cd=Dict(s=>i for (i,s) in enumerate(p.column_names))
    @assert length(rd)==length(p.row_names) && length(cd)==length(p.column_names)
    rows=[rd[s] for s in q.row_names];cols=[cd[s] for s in q.column_names]
    @assert length(unique(rows))==length(rows) && length(unique(cols))==length(cols)
    @assert q.A==p.A[rows,cols]
    @assert q.objective==p.objective[cols] && q.objective_constant==p.objective_constant && q.objective_sense==p.objective_sense
    for field in (:row_lower,:row_upper)
        @assert getfield(q,field)==getfield(p,field)[rows]
    end
    for field in (:column_lower,:column_upper,:variable_domains)
        @assert getfield(q,field)==getfield(p,field)[cols]
    end
    Dict("exact_model_match"=>true,"rows_reordered"=>count(i->rows[i]!=i,eachindex(rows)),
         "columns_reordered"=>count(i->cols[i]!=i,eachindex(cols))),cols
end
function detach(ws,path)
    isnothing(ws) && return
    p=ws.progress
    progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=p.start_ns,scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,numerical_policy=p.numerical_policy)
    vals=map(fieldnames(typeof(ws))) do name
        name==:progress ? progress : getfield(ws,name)
    end
    serialize(path,JSimplex.SimplexWorkspace(vals...))
end
function run_case(job,entry,reference,output)
    reset_counters!();COMPONENT_ENABLED[]=get(job,"component_enabled",true)
    CAPTURE_PREFIX[]=output*"-job"*string(get(job,"job_index",0))*"-seed"*string(get(job,"seed",20261001))*"-"*replace(job["id"],"/"=>"-")*"-"*job["reader"]*"-"*job["algorithm"]*"-"*job["manager"]*"-"*string(COMPONENT_ENABLED[])
    row=Dict{String,Any}("id"=>job["id"],"reader"=>job["reader"],"algorithm"=>job["algorithm"],
        "manager"=>job["manager"],"component_enabled"=>COMPONENT_ENABLED[],"input_sha256"=>entry["sha256"],
        "job_index"=>get(job,"job_index",0),"seed"=>get(job,"seed",20261001),
        "time_limit"=>job["seconds"],"reference_objective"=>reference["objective"])
    path=realpath(entry["path"])
    @assert !(lowercase(basename(path)) in ("big.mps","largo.mps","anymod.mps"))
    @assert bytes2hex(open(sha256,path))==entry["sha256"]==reference["sha256"]
    @assert reference["status"]==7
    original=JSimplex.read_mps(path)
    problem=job["reader"]=="native" ? original : job["reader"]=="jump" ? jump_problem(path) : permuted(original,get(job,"seed",20261001))
    match,cols=equivalence(original,problem);merge!(row,match)
    row["rows"],row["columns"]=size(problem.A);row["nonzeros"]=nnz(problem.A)
    zero_steps=Ref(0);steps=Ref(0);last_ws=Ref{Any}(nothing);phases=Dict{String,Any}[]
    observer=(event,ws)->begin
        last_ws[]=ws
        if event==:pivot_completed
            steps[]+=1;iszero(ws.scratch.last_primal_step) && (zero_steps[]+=1)
        elseif event in (:phase_one,:phase_primal,:phase_dual,:phase_cleanup)
            push!(phases,Dict("event"=>string(event),"iteration"=>ws.iterations+ws.progress.iteration_offset))
        end
    end
    diagnostics=JSimplex.SimplexDiagnostics(;observer)
    options=JSimplex.SolverOptions(algorithm=Symbol(job["algorithm"]),basis_update=Symbol(job["manager"]),
        basis_refactorization=:native,refactorization_interval=80,pricing=:steepest_edge,
        simplex_strategy=:adaptive,iteration_limit=1_000_000,time_limit=Float64(job["seconds"]),verbose=false)
    timed=@timed with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,diagnostics;options,numerical_policy=policy(),relax_integrality=true)
    end
    solution=timed.value
    merge!(row,Dict("status"=>string(solution.status),"message"=>solution.message,
        "seconds"=>solution.statistics.elapsed_seconds,"wall_seconds"=>timed.time,
        "iterations"=>solution.statistics.iterations,"refactorizations"=>solution.statistics.refactorizations,
        "allocated_bytes"=>timed.bytes,"compile_seconds"=>get(timed,:compile_time,0.0),"pivot_observations"=>steps[],"zero_primal_steps"=>zero_steps[],
        "events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),
        "coverage"=>copy(COUNTERS),"captures"=>copy(CAPTURES),"phases"=>phases))
    if solution.status==JSimplex.OPTIMAL
        x=solution.primal;mapped=similar(x);mapped[cols]=x
        row["objective"]=solution.objective_value
        row["original_primal_feasible"]=JSimplex._original_primal_feasible(original,mapped,options.primal_tolerance)
        row["reader_primal_feasible"]=JSimplex._original_primal_feasible(problem,x,options.primal_tolerance)
        row["objective_matches"]=isapprox(solution.objective_value,reference["objective"];rtol=1e-8,atol=1e-7)
        row["objective_relative_error"]=abs(solution.objective_value-reference["objective"])/max(1.0,abs(reference["objective"]))
        row["passed"]=row["original_primal_feasible"] && row["reader_primal_feasible"] && row["objective_matches"]
    else
        row["passed"]=false
        row["failure_snapshot"]=CAPTURE_PREFIX[]*"-failure.bin"
        detach(last_ws[],row["failure_snapshot"])
    end
    row
end
function main(args,hashes)
    manifest,refs,jobsfile,output=args
    @assert !isfile(output*".toml")
    entries=Dict(x["id"]=>x for x in TOML.parsefile(manifest)["cases"])
    references=Dict(x["id"]=>x for x in TOML.parsefile(refs)["cases"])
    jobs=TOML.parsefile(jobsfile)["jobs"]
    reset_counters!();CAPTURE_PREFIX[]=output*"-warmup"
    warm=JSimplex.read_mps(joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps"))
    for algorithm in (:primal,:dual)
        with_logger(NullLogger()) do
            JSimplex._solve_diagnosed(warm,nothing;options=JSimplex.SolverOptions(;algorithm,verbose=false,time_limit=120),numerical_policy=policy())
        end
    end
    records=Dict{String,Any}[]
    report=Dict{String,Any}("production_sha256"=>source_digest(),"diagnostic_sha256"=>hashes,
        "julia"=>string(VERSION),"jump"=>string(pkgversion(JuMP)),"julia_threads"=>Threads.nthreads(),
        "blas_threads"=>BLAS.get_num_threads(),"policy"=>Dict(string(s)=>getfield(policy(),s) for s in JSimplex.NUMERICAL_SWITCHES),
        "weak_pivot_preference"=>false,"original_retry_enabled"=>false,"records"=>records)
    for (number,job) in enumerate(jobs)
        job["job_index"]=number
        println("START ",number,"/",length(jobs)," ",job);flush(stdout)
        record=try
            run_case(job,entries[job["id"]],references[job["id"]],output)
        catch e
            Dict{String,Any}("id"=>job["id"],"reader"=>job["reader"],"algorithm"=>job["algorithm"],
                "manager"=>job["manager"],"component_enabled"=>get(job,"component_enabled",true),
                "seed"=>get(job,"seed",20261001),"job_index"=>number,
                "input_sha256"=>entries[job["id"]]["sha256"],"captures"=>copy(CAPTURES),
                "time_limit"=>job["seconds"],"status"=>"EXCEPTION","passed"=>false,
                "exception"=>sprint(showerror,e,catch_backtrace()),"coverage"=>copy(COUNTERS))
        end
        push!(records,record);report["process_peak_rss"]=Sys.maxrss()
        open(output*".toml","w") do io;TOML.print(io,report);end
        println("DONE ",number," ",job["id"]," ",job["reader"]," ",record["status"]," passed=",record["passed"],
            " iterations=",get(record,"iterations",-1)," coverage=",get(record,"coverage",Dict()));flush(stdout)
        GC.gc()
    end
end
hashes=instrument!()
Base.invokelatest(main,ARGS,hashes)
