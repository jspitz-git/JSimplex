using JSimplex, Logging, TOML, SHA, Serialization, LinearAlgebra
include(joinpath(@__DIR__,"..","..","ft-numerical-recovery","reproduce","capture-failure.jl"))
function capture_primal(args)
    length(args)==4 || error("Expected: input manager seconds output_prefix")
    input,manager,seconds,output=args
    lowercase(basename(realpath(input))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded model")
    require_fresh_output(output)
    options=SolverOptions(algorithm=:primal,basis_update=Symbol(manager),basis_refactorization=:native,
        pricing=:steepest_edge,simplex_strategy=:legacy,refactorization_interval=80,
        iteration_limit=1_000_000,time_limit=parse(Float64,seconds),verbose=true)
    environment=capture_environment();environment["input_sha256"]=bytes2hex(open(sha256,input))
    environment["source_sha256"]=Dict(name=>bytes2hex(open(sha256,joinpath(dirname(pathof(JSimplex)),name)))
        for name in ("legacy_primal_pivot.jl","primal_simplex.jl","legacy_primal_point.jl","simplex_numerics.jl"))
    environment["time_limit"]=options.time_limit
    environment["interval"]=options.refactorization_interval
    environment["algorithm"]="primal";environment["pricing"]="steepest_edge"
    environment["strategy"]="legacy";environment["backend"]="native"
    open(output*".environment.toml","w") do io;TOML.print(io,environment);end
    with_logger(NullLogger()) do
        solve(read_mps("test/fixtures/solver/afiro.mps");options,relax_integrality=true)
    end
    latest=Ref{Any}(nothing);snapshots=String[];phases=Dict{String,Any}[]
    previous_basis=Ref{Any}(nothing);weak_count=Ref(0)
    phase_one=Ref(false);zero_steps=Ref(0);artificial_entries=Ref(0)
    trace=get(ENV,"JSIMPLEX_PRIMAL_TRACE","false")=="true"
    function save(ws,reason;prior_basis=nothing)
        length(snapshots)>=6 && return
        name=output*"."*string(length(snapshots)+1)*"."*string(reason)*".bin"
        capture_snapshot(name,ws;reason,prior_basis,provenance=(input_sha256=environment["input_sha256"],source_revision=source_revision()))
        push!(snapshots,name);println("SNAPSHOT ",name);flush(stdout)
    end
    observer=function(reason,ws)
        old=latest[]
        if !isnothing(old) && old !== ws && old.iterations>0
            save(old,:before_workspace_change)
        end
        if reason in (:phase_primal,:phase_one,:phase_cleanup)
            phase_one[]=reason==:phase_one
            row=Dict{String,Any}("phase"=>string(reason),"iteration"=>ws.iterations,
                "rows"=>size(ws.problem.A,1),"columns"=>size(ws.problem.A,2))
            push!(phases,row);println("PHASE ",row);flush(stdout)
        elseif reason==:pivot_completed && ws.iterations%1000==0
            println("PROGRESS iter=",ws.iterations," refs=",ws.refactorizations,
                " pinf=",JSimplex.primal_infeasibility(ws),
                " working_objective=",dot(ws.costs,ws.primal));flush(stdout)
        end
        if reason in (:pivot_completed,:flip_completed)
            iszero(ws.scratch.last_primal_step) && (zero_steps[]+=1)
            entering=ws.scratch.selected_entering
            if phase_one[] && entering>0 && ws.costs[entering]>0
                artificial_entries[]+=1
            end
        end
        if trace && reason==:pivot_proposed
            previous_basis[]=deepcopy(ws.basis)
        elseif trace && reason==:pivot_completed && ws.scratch.selected_row>0
            pivot=ws.scratch.row_solution[ws.scratch.selected_row]
            scale=maximum(abs,ws.scratch.row_solution;init=0.0)
            if abs(pivot)<=eps(Float64)*scale
                weak_count[]+=1
                if weak_count[]<=3
                    println("ROUNDING_SCALE_PIVOT iter=",ws.iterations," pivot=",pivot,
                        " norm=",scale," row_pivot=",ws.scratch.tableau_row[ws.scratch.selected_entering])
                    save(ws,:rounding_scale_pivot;prior_basis=previous_basis[])
                end
            end
        end
        latest[]=ws
    end
    problem=read_mps(input)
    diagnostics=JSimplex.SimplexDiagnostics(;observer,kernel_timing=true)
    result=JSimplex._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
    if result.status in (NUMERICAL_ERROR,TIME_LIMIT) && !isnothing(latest[])
        save(latest[],result.status==NUMERICAL_ERROR ? :numerical_error : :time_limit)
    end
    report=merge(environment,Dict{String,Any}("manager"=>manager,"status"=>string(result.status),
        "message"=>result.message,"iterations"=>result.statistics.iterations,"seconds"=>result.statistics.elapsed_seconds,
        "refactorizations"=>result.statistics.refactorizations,"phases"=>phases,"snapshots"=>snapshots,
        "rounding_scale_pivots"=>weak_count[],"trace_enabled"=>trace,
        "zero_steps"=>zero_steps[],"phase_one_artificial_entries"=>artificial_entries[],
        "kernel_calls"=>Dict(string(k)=>v for (k,v) in diagnostics.kernel_calls if v!=0),
        "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in diagnostics.kernel_nanoseconds if v!=0),
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0)))
    if result.status==OPTIMAL
        report["objective"]=result.objective_value
        report["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
        if environment["input_sha256"]=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
            report["objective_matches"]=isapprox(result.objective_value,51425691.76210457;rtol=1e-8)
        end
    end
    if !isnothing(latest[])
        ws=latest[];report["last_primal_infeasibility"]=JSimplex.primal_infeasibility(ws)
        report["last_step"]=ws.scratch.last_primal_step
        report["last_working_objective"]=dot(ws.costs,ws.primal)
    end
    open(output,"w") do io;TOML.print(io,report);end
    println("FINAL ",report);flush(stdout)
end
abspath(PROGRAM_FILE)==(@__FILE__) && capture_primal(ARGS)
