using JSimplex, Logging, LinearAlgebra, SparseArrays, SHA, TOML
BLAS.set_num_threads(1)

# The production adaptive_pricing flag also enables a separate primal
# weak-pivot preference. Disable only that preference in this diagnostic process
# so it cannot confound the pricing lifecycle experiment. All numerical checks
# and the bounded rejection/retry machinery retain their exact source.
function isolate_pricing_trials!()
    source = read(joinpath(dirname(pathof(JSimplex)),"primal_simplex.jl"),String)
    first_index = first(findfirst("function _legacy_primal_iteration!",source))
    last_index = first(findnext("\nfunction ",source,first_index+1))-1
    original = source[first_index:last_index]
    expression = "defer_weak = workspace.progress.numerical_policy.adaptive_pricing"
    @assert count(expression,original) == 1
    isolated = replace(original,expression=>"defer_weak = false")
    Base.include_string(JSimplex,isolated,"diagnostic_pricing_only.jl")
    return bytes2hex(sha256(isolated))
end

const ISOLATED_METHOD_SHA256 = isolate_pricing_trials!()

function main()
    name, method, seconds_text, output = ARGS
    name in ("runtime", "medium") || error("Unsupported model")
    algorithm = Symbol(method)
    algorithm in (:primal,:dual) || error("Unsupported algorithm")
    path = "/home/jspitz/mps/" * name * ".mps"
    digest = bytes2hex(open(sha256,path))
    @assert digest == (name == "runtime" ?
        "d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68" :
        "79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0")
    policy = JSimplex.NumericalPolicy(Float64;adaptive_stalling=true,adaptive_pricing=true,
        refactor_timing=false)
    @assert all(s -> getfield(policy,s) == (s in (:adaptive_stalling,:adaptive_pricing)),
        JSimplex.NUMERICAL_SWITCHES)
    probe = LinearProblem(sparse([1e-10 -1.0;1.0 0.0]),[-2.0,-1.0];
        row_upper=[0.0,Inf],column_upper=[1.0,1.0])
    check = JSimplex.initialize_workspace(probe,SolverOptions(algorithm=:primal,pricing=:dantzig,verbose=false);
        progress=JSimplex.SimplexProgressContext(probe;numerical_policy=policy))
    @assert isnothing(JSimplex._primal_iteration!(check,()->false,check.options.dual_tolerance))
    @assert check.basis.basic_indices == [1,4]
    options = SolverOptions(;algorithm,pricing=:steepest_edge,basis_update=:pfi,
        basis_refactorization=:native,refactorization_interval=80,
        iteration_limit=1_000_000,time_limit=parse(Float64,seconds_text),verbose=false)
    # Compile common solve paths separately. Timings are diagnostic, not a benchmark.
    with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(read_mps("test/fixtures/solver/afiro.mps"),nothing;
            options,numerical_policy=policy,relax_integrality=true)
    end
    problem = read_mps(path)
    records = Dict{String,Any}[]
    last = Ref{Any}(nothing)
    transitions = Set((:pricing_dantzig,:pricing_steepest_edge,:pricing_devex,
        :pricing_progress_return,:pricing_trial_expired,:pricing_phase_reset,
        :phase_one,:phase_auxiliary,:phase_primal,:phase_dual))
    observer = function(event,ws)
        if event in transitions || (event == :pivot_completed && ws.iterations % 2000 == 0)
            state = ws.scratch.pricing
            active_algorithm = isnothing(state) || state.algorithm == :none ? algorithm : state.algorithm
            mode = JSimplex._effective_pricing(ws,active_algorithm)
            ps,pc = JSimplex.primal_infeasibility_summary(ws)
            ds,dc = JSimplex.dual_infeasibility_summary(ws)
            record = Dict{String,Any}("event"=>string(event),"iteration"=>ws.iterations,
                "objective"=>dot(ws.costs,ws.primal),"pinf"=>ps,"pinf_count"=>pc,
                "dinf"=>ds,"dinf_count"=>dc,"pricing"=>string(mode),
                "active_algorithm"=>string(active_algorithm),
                "seconds"=>(time_ns()-ws.progress.start_ns)/1e9)
            if !isnothing(state)
                record["temporary"] = state.temporary
                record["return_mode"] = string(state.return_mode)
                record["transition"] = string(state.last_transition)
                record["observations"] = state.observations
                record["trial_until"] = state.trial_until
                @assert !state.temporary || state.framework_valid
                @assert !state.temporary || state.observations <= state.trial_until
                event == :pricing_phase_reset && @assert !state.temporary && state.observations == 0
            end
            push!(records,record)
            println("TRACE ",record); flush(stdout)
            last[] = record
        end
    end
    d = JSimplex.SimplexDiagnostics(;observer)
    timed = @timed with_logger(NullLogger()) do
        JSimplex._solve_diagnosed(problem,d;options,numerical_policy=policy,relax_integrality=true)
    end
    result = timed.value
    report = Dict{String,Any}("input"=>path,"input_sha256"=>digest,"algorithm"=>method,
        "weak_pivot_preference"=>false,"diagnostic_method_sha256"=>ISOLATED_METHOD_SHA256,
        "julia"=>string(VERSION),"architecture"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "time_limit"=>options.time_limit,"status"=>string(result.status),
        "message"=>result.message,"iterations"=>result.statistics.iterations,
        "refactorizations"=>result.statistics.refactorizations,
        "seconds"=>result.statistics.elapsed_seconds,"allocated_bytes"=>timed.bytes,
        "peak_rss"=>Sys.maxrss(),"records"=>records,
        "policy"=>Dict(string(s)=>getfield(policy,s) for s in JSimplex.NUMERICAL_SWITCHES),
        "events"=>Dict(string(k)=>v for (k,v) in d.counts if v != 0))
    h = SHA.SHA2_256_CTX()
    root = dirname(dirname(pathof(JSimplex)))
    files = ["Project.toml"]
    for (dir,_,names) in walkdir(joinpath(root,"src")), file in names
        endswith(file,".jl") && push!(files,relpath(joinpath(dir,file),root))
    end
    for file in sort(files)
        SHA.update!(h,codeunits(file*"\0"))
        SHA.update!(h,read(joinpath(root,file)))
    end
    report["production_sha256"] = bytes2hex(SHA.digest!(h))
    if result.status == OPTIMAL
        report["objective"] = result.objective_value
        report["original_primal_feasible"] = JSimplex._original_primal_feasible(problem,
            result.primal,options.primal_tolerance)
        @assert report["original_primal_feasible"]
    end
    open(output,"w") do io
        TOML.print(io,report)
    end
    println("RESULT ",name," ",method," ",result.status," iterations=",result.statistics.iterations,
        " seconds=",result.statistics.elapsed_seconds); flush(stdout)
end

main()
