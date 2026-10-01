# Fresh whole-MPS runs under the established isolated adaptive policy.
# Reuse reader equivalence, policy isolation, coverage and snapshot helpers.
source=read(joinpath(@__DIR__,"broad_corpus.jl"),String)
marker="hashes=instrument!()\nBase.invokelatest(main,ARGS,hashes)"
@assert count(marker,source)==1
Base.include_string(Main,replace(source,marker=>""),joinpath(@__DIR__,"broad_corpus.jl"))

function runtime_full(args,hashes)
    reader,method,seconds_text,output=args
    @assert reader in ("native","jump") && method in ("primal","dual")
    @assert !isfile(output*".toml")
    path="/home/jspitz/mps/runtime.mps"
    digest="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    @assert bytes2hex(open(sha256,path))==digest
    @assert source_digest()=="40d6fa0140556827f9e353987417296ef513e64c0618ea4afa3fcc8bddcb3718"
    reset_counters!();CAPTURE_PREFIX[]=output*"-warmup"
    options=SolverOptions(;algorithm=Symbol(method),pricing=:steepest_edge,basis_update=:pfi,
        basis_refactorization=:native,refactorization_interval=80,simplex_strategy=:adaptive,
        iteration_limit=1_000_000,time_limit=parse(Float64,seconds_text),verbose=false)
    with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(read_mps(joinpath(dirname(dirname(pathof(JSimplex))),
            "test/fixtures/solver/afiro.mps")),nothing;options,numerical_policy=policy(),relax_integrality=true)
    end
    reset_counters!();CAPTURE_PREFIX[]=output
    original=read_mps(path)
    problem=reader=="native" ? original : jump_problem(path)
    match,cols=equivalence(original,problem)
    println("INPUT reader=",reader," algorithm=",method," shape=",size(problem.A),
        " nnz=",nnz(problem.A)," equivalence=",match);flush(stdout)
    records=Dict{String,Any}[];last_ws=Ref{Any}(nothing)
    transitions=Set((:phase_one,:phase_auxiliary,:phase_primal,:phase_dual,:phase_cleanup,
        :pricing_dantzig,:pricing_steepest_edge,:pricing_progress_return,:pricing_trial_expired,
        :pricing_phase_reset,:perturbation,:restore_perturbations,:stagnation_stalled,:stagnation_cost_rebase))
    observer=(event,ws)->begin
        last_ws[]=ws
        if event in transitions || event==:final_observed_workspace ||
                (event==:pivot_completed && ws.iterations%1000==0)
            ps,pc=JSimplex.primal_infeasibility_summary(ws)
            ds,dc=JSimplex.dual_infeasibility_summary(ws)
            state=ws.scratch.pricing
            active=isnothing(state) || state.algorithm==:none ? ws.options.algorithm : state.algorithm
            row=Dict{String,Any}("event"=>string(event),"iteration"=>ws.iterations,
                "total_iterations"=>ws.iterations+ws.progress.iteration_offset,
                "rows"=>size(ws.problem.A,1),"columns"=>size(ws.problem.A,2),
                "working_objective"=>dot(ws.costs,ws.primal),"pinf"=>ps,"pinf_count"=>pc,
                "dinf"=>ds,"dinf_count"=>dc,"active_algorithm"=>string(active),
                "pricing"=>string(JSimplex._effective_pricing(ws,active)),
                "seconds"=>(time_ns()-ws.progress.start_ns)/1e9)
            push!(records,row)
            println("TRACE ",row);flush(stdout)
        end
    end
    diagnostics=JSimplex.SimplexDiagnostics(;observer)
    timed=@timed with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,diagnostics;options,numerical_policy=policy(),relax_integrality=true)
    end
    result=timed.value
    isnothing(last_ws[]) || observer(:final_observed_workspace,last_ws[])
    report=Dict{String,Any}("input"=>path,"input_sha256"=>digest,"reader"=>reader,"algorithm"=>method,
        "production_sha256"=>source_digest(),"diagnostic_sha256"=>hashes,
        "julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),"jump"=>string(pkgversion(JuMP)),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "status"=>string(result.status),"message"=>result.message,"iterations"=>result.statistics.iterations,
        "refactorizations"=>result.statistics.refactorizations,"seconds"=>result.statistics.elapsed_seconds,
        "wall_seconds"=>timed.time,"compile_seconds"=>get(timed,:compile_time,0.0),
        "allocated_bytes"=>timed.bytes,"process_peak_rss"=>Sys.maxrss(),"records"=>records,
        "time_limit"=>options.time_limit,"iteration_limit"=>options.iteration_limit,
        "basis_update"=>"pfi","basis_refactorization"=>"native","refactorization_interval"=>80,
        "pricing"=>"steepest_edge","simplex_strategy"=>"adaptive","relax_integrality"=>true,
        "primal_tolerance"=>options.primal_tolerance,"dual_tolerance"=>options.dual_tolerance,
        "zero_tolerance"=>options.zero_tolerance,"scaling"=>string(options.scaling),"presolve"=>options.presolve,
        "weak_pivot_preference"=>false,"original_retry_enabled"=>false,
        "policy"=>Dict(string(s)=>getfield(policy(),s) for s in JSimplex.NUMERICAL_SWITCHES),
        "events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),
        "coverage"=>copy(COUNTERS),"captures"=>copy(CAPTURES),"passed"=>false)
    merge!(report,match)
    if result.status==JSimplex.OPTIMAL
        x=result.primal;mapped=similar(x);mapped[cols]=x
        reference=51425691.762103125
        report["objective"]=result.objective_value
        report["reference_objective"]=reference
        report["reference_source"]="diagnostics/native-primal-completion/results/runtime-dual.toml"
        report["reader_primal_feasible"]=JSimplex._original_primal_feasible(problem,x,options.primal_tolerance)
        report["original_primal_feasible"]=JSimplex._original_primal_feasible(original,mapped,options.primal_tolerance)
        report["objective_relative_error"]=abs(result.objective_value-reference)/abs(reference)
        report["objective_matches"]=isapprox(result.objective_value,reference;rtol=1e-9,atol=1e-7)
        report["passed"]=report["reader_primal_feasible"] && report["original_primal_feasible"] && report["objective_matches"]
        serialize(output*"-primal.bin",(;reader,primal=x,native_primal=mapped))
    end
    open(output*".toml","w") do io;TOML.print(io,report);end
    detach(last_ws[],output*"-final.bin")
    println("RESULT reader=",reader," algorithm=",method," status=",result.status,
        " passed=",report["passed"]," iterations=",result.statistics.iterations,
        " seconds=",result.statistics.elapsed_seconds);flush(stdout)
end
hashes=instrument!()
Base.invokelatest(runtime_full,ARGS,hashes)
