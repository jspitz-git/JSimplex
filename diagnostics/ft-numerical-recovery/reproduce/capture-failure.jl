using JSimplex, Logging, Serialization, TOML, SHA, Pkg
using JSimplex.LinearAlgebra

# UMFPACK serialization rebuilds its native numeric factor when read back. Save
# explicit factors/permutations as well, so the original numeric state survives.
function capture_snapshot(path, ws; reason, prior_basis=nothing, provenance=(;))
    backend = ws.factorization.base
    native = backend isa JSimplex.UMFPACKBackend ? backend.factorization : nothing
    numeric = isnothing(native) ? nothing :
        (L=native.L, U=native.U, p=native.p, q=native.q, Rs=native.Rs)
    data = (problem=ws.problem, basis=deepcopy(ws.basis), options=ws.options,
        costs=copy(ws.costs), lower=copy(ws.lower), upper=copy(ws.upper),
        primal=copy(ws.primal), prices=copy(ws.reduced_costs), perturbed=ws.perturbed,
        factorization=ws.factorization, native_numeric=numeric,
        pricing_weights=copy(ws.pricing_weights), row=ws.scratch.selected_row,
        entering=ws.scratch.selected_entering, direction=copy(ws.scratch.row_solution),
        rho=copy(ws.scratch.rho), tableau=copy(ws.scratch.tableau_row),
        iteration=ws.iterations, last_step=ws.scratch.last_primal_step,
        event=reason, julia=string(VERSION), architecture=string(Sys.ARCH))
    data = merge(data, provenance)
    isnothing(prior_basis) || (data=merge(data,(;prior_basis)))
    serialize(path, data)
    return path
end
function source_revision()
    root = dirname(dirname(pathof(JSimplex)))
    # Pkg.add installations may have no checkout. Do not identify an unrelated
    # ancestor repository as the loaded package's revision.
    ispath(joinpath(root, ".git")) || return "unavailable"
    try
        return strip(read(`git -C $root rev-parse HEAD`, String))
    catch
        return "unavailable"
    end
end

function capture_environment()
    info = get(Pkg.dependencies(), Base.PkgId(JSimplex).uuid, nothing)
    field(name) = isnothing(info) || isnothing(getproperty(info, name)) ?
        "unavailable" : string(getproperty(info, name))
    # Keep heterogeneous metadata out of a large inferred NamedTuple union.
    return Dict{String,Any}(
        "source_path"=>pathof(JSimplex), "source_revision"=>source_revision(),
        "package_version"=>string(Base.pkgversion(JSimplex)),
        "package_tree_hash"=>field(:tree_hash), "package_git_revision"=>field(:git_revision),
        "active_project"=>something(Base.active_project(), "unavailable"),
        "working_directory"=>pwd(), "julia"=>string(VERSION), "architecture"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(), "blas_threads"=>BLAS.get_num_threads(),
        "blas_config"=>sprint(show, BLAS.get_config()), "cpu_threads"=>Sys.CPU_THREADS)
end

function require_fresh_output(output)
    directory = dirname(abspath(output))
    mkpath(directory)
    prefix = basename(output)
    any(name -> name == prefix || startswith(name, prefix * "."), readdir(directory)) &&
        error("Output prefix already exists; choose a new prefix for this capture run")
    return nothing
end

function main(args=ARGS; warmup=true,
        iteration_limit=parse(Int,get(ENV,"JSIMPLEX_DEBUG_ITERATIONS","1000000")))
    length(args) == 5 || error("Expected: input algorithm basis_update seconds output_prefix")
    path, algorithm, update, seconds, output = args
    lowercase(basename(realpath(path))) in ("big.mps", "largo.mps", "anymod.mps") && error("Excluded large model")
    require_fresh_output(output)
    environment = capture_environment()
    provenance = (input_sha256=bytes2hex(open(sha256,path)),
        source_revision=String(environment["source_revision"]),
        run_id=string(time_ns(),"-",getpid()))
    merge!(environment, Dict(string(k)=>v for (k,v) in pairs(provenance)))
    environment["warmup"] = warmup
    options=SolverOptions(algorithm=Symbol(algorithm),basis_update=Symbol(update),
        basis_refactorization=:native,pricing=:steepest_edge,simplex_strategy=:legacy,
        refactorization_interval=parse(Int,get(ENV,"JSIMPLEX_DEBUG_INTERVAL","80")),time_limit=parse(Float64,seconds),
        iteration_limit=iteration_limit,verbose=true)
    # Persist provenance before the solve, even if the session is interrupted.
    open(output * ".environment.toml", "w") do io
        TOML.print(io, environment)
    end
    println("CAPTURE_ENVIRONMENT ", environment); flush(stdout)
    events=Dict{Symbol,Int}()
    warming=Ref(true)
    marginal_snapshots=Ref(0)
    trace_pivots=get(ENV,"JSIMPLEX_TRACE_PIVOTS","0")=="1"
    previous_basis=Ref{Any}(nothing);small_pivots=Ref(0)
    observer=function(reason,ws)
        warming[] && return
        if reason==:pivot_completed && ws.iterations%5000==0
            println("PROGRESS iter=",ws.iterations," pinf=",JSimplex.primal_infeasibility(ws),
                " dinf=",JSimplex.dual_infeasibility(ws)," refs=",ws.refactorizations)
            flush(stdout)
        end
        if trace_pivots && ws.iterations>=44000 && reason==:pivot_proposed
            previous_basis[]=deepcopy(ws.basis)
            return
        elseif trace_pivots && reason==:pivot_completed && !isnothing(previous_basis[])
            row=ws.scratch.selected_row;entering=ws.scratch.selected_entering
            if row>0
                pivot=ws.scratch.row_solution[row]
                scale=norm(ws.scratch.row_solution,Inf)
                if abs(pivot)<parse(Float64,get(ENV,"JSIMPLEX_TRACE_RELATIVE","1e-8"))*scale && small_pivots[]<parse(Int,get(ENV,"JSIMPLEX_TRACE_LIMIT","10"))
                    small_pivots[]+=1
                    name=output*".accepted_pivot."*string(ws.iterations)*".bin"
                    capture_snapshot(name, ws; reason=:accepted_small_pivot,
                        prior_basis=previous_basis[], provenance)
                    println("SMALL_ACCEPTED_PIVOT iter=",ws.iterations," pivot=",pivot,
                        " direction_norm=",scale," relative_pivot=",abs(pivot)/scale," snapshot=",name);flush(stdout)
                end
            end
            return
        end
        reason in (:refactor_residual,:refactor_pivot,:correction_attempt,:phase_primal,
                   :phase_dual,:phase_one,:phase_auxiliary,:phase_cleanup,:certification_failed) || return
        count=get(events,reason,0)+1;events[reason]=count
        if count<=10 || count%100==0
            row=ws.scratch.selected_row;entering=ws.scratch.selected_entering
            println("EVENT ",reason," count=",count," iter=",ws.iterations,
                " row=",row," entering=",entering,
                " pinf=",JSimplex.primal_infeasibility(ws),
                " dinf=",JSimplex.dual_infeasibility(ws));flush(stdout)
            if reason in (:refactor_residual,:refactor_pivot) && 1<=row<=length(ws.scratch.row_solution) && entering>0
                println("PIVOT stored_forward=",ws.scratch.row_solution[row],
                    " stored_tableau=",ws.scratch.tableau_row[entering],
                    " direction_norm=",norm(ws.scratch.row_solution,Inf),
                    " row_residual_ratio=",JSimplex._dual_row_residual_ratio(ws,ws.scratch.rho,row));flush(stdout)
            end
        end
        marginal=algorithm=="dual" && reason==:correction_attempt && marginal_snapshots[]<3 &&
            ws.options.dual_tolerance<JSimplex.dual_infeasibility(ws)<=64ws.options.dual_tolerance
        failure=reason==:certification_failed
        if (reason==:refactor_residual && count in (1,10)) || marginal || failure
            name=output*"."*string(reason)*"."*string(ws.iterations)*".bin"
            if !isfile(name)
                marginal && (marginal_snapshots[]+=1)
                capture_snapshot(name, ws; reason, provenance)
                println("SNAPSHOT ",name);flush(stdout)
            end
        end
    end
    if warmup
        fixture=joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps")
        with_logger(NullLogger()) do
            JSimplex._solve_diagnosed(read_mps(fixture),JSimplex.SimplexDiagnostics(;observer,kernel_timing=true);
                options,relax_integrality=true)
        end
    end
    warming[]=false
    problem=read_mps(path)
    d=JSimplex.SimplexDiagnostics(;observer,kernel_timing=true)
    timed=@timed JSimplex._solve_diagnosed(problem,d;options,relax_integrality=true)
    result=timed.value
    report=Dict("input"=>realpath(path),"input_sha256"=>provenance.input_sha256,"run_id"=>provenance.run_id,
        "algorithm"=>algorithm,"basis_update"=>update,"interval"=>options.refactorization_interval,"julia"=>string(VERSION),
        "status"=>string(result.status),"message"=>result.message,
        "iterations"=>result.statistics.iterations,"refactorizations"=>result.statistics.refactorizations,
        "seconds"=>result.statistics.elapsed_seconds,"outer_seconds"=>timed.time,
        "source_path"=>pathof(JSimplex),"peak_rss"=>Sys.maxrss(),
        "source_revision"=>provenance.source_revision,
        "architecture"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),
        "blas_threads"=>BLAS.get_num_threads(),"iteration_limit"=>options.iteration_limit,
        "time_limit"=>options.time_limit,
        "counts"=>Dict(string(k)=>v for (k,v) in d.counts if v!=0),
        "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in d.kernel_nanoseconds if v!=0))
    merge!(report, environment)
    if result.status==OPTIMAL
        report["objective"]=result.objective_value
        report["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    end
    open(output,"w") do io;TOML.print(io,report);end
    println(report)
end
abspath(PROGRAM_FILE) == (@__FILE__) && main()
