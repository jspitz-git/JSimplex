# Fresh-process diagnostic; see README_basis_failure.md. No production files change.
include(joinpath(@__DIR__, "capture.jl"))
module RuntimeBasisFailure
using JSimplex, Serialization, SparseArrays, LinearAlgebra, TOML
using ..RuntimePrimalCapture: environment, write_report
const JS = JSimplex
const output_prefix = Ref("")
const installed = Ref(false)
const captured = Ref(false)
struct Captured <: Exception
    budget_expired::Bool
end

# Fail closed if this private function changes. The executing body is cloned
# from the installed source, never a separately maintained solver implementation.
const expected_verifier = raw"""
function _verify_driver_basis!(ws,stop;refactorize::Bool=false)
    stop() && return false
    state = ws.scratch.pricing
    algorithm = isnothing(state) ? ws.options.algorithm : state.algorithm
    _prepare_auto_pricing!(ws,algorithm;stop) || return false
    return _with_recovery_precision(ws,ws) do
        recompute!(ws;refactorize,caller_guard=stop)
        stop() && return false
        _finite_workspace(ws) || return false
        _recomputed_basis_reliable(ws) && return true
        return _try_native_cleanup_recompute!(ws,stop)
    end
end
"""
function checked_verifier(source)
    parsed = Meta.parseall(source)
    matches = filter(parsed.args) do expression
        expression isa Expr && expression.head == :function &&
            expression.args[1] isa Expr && expression.args[1].head == :call &&
            expression.args[1].args[1] == :_verify_driver_basis!
    end
    length(matches) == 1 || error("Expected exactly one driver verifier; instrumentation refused")
    actual = deepcopy(only(matches))
    Base.remove_linenums!(deepcopy(actual)) ==
        Base.remove_linenums!(Meta.parse(expected_verifier)) ||
        error("Driver verifier source shape changed; instrumentation refused")
    return actual
end

function install!()
    installed[] && return
    method = checked_verifier(read(joinpath(dirname(pathof(JS)), "simplex_driver.jl"), String))
    method.args[1].args[1] = :_diagnostic_original_verify_driver_basis!
    Core.eval(JS,method)
    callback = GlobalRef(@__MODULE__, :verify!)
    Core.eval(JS, quote
        function _verify_driver_basis!(ws,stop;refactorize::Bool=false)
            return $callback(ws,stop;refactorize)
        end
    end)
    installed[] = true
end

function atomic_serialize(path,data)
    ispath(path) && error("Refusing to overwrite " * path)
    temporary = path * ".partial"
    ispath(temporary) && error("Refusing to overwrite " * temporary)
    open(temporary,"w") do io
        serialize(io,data)
        flush(io)
    end
    mv(temporary,path)
end

# Preserve the exact active factors and updates without process-local backend
# scratch. HH owns its extracted L/U; refactor_workspace is disposable and may
# contain UMFPACK pointers even with basis_refactorization=:native.
function portable_factorization(f::JS.HuangfuHallFactorization)
    return typeof(f)((name == :refactor_workspace ? nothing : getfield(f,name)
        for name in fieldnames(typeof(f)))...)
end

# Serialize before assembling residuals or attempting any additional solve.
function save_failure(ws, failure)
    prefix = output_prefix[]
    data = (;format_version=1, problem=ws.problem, options=ws.options,
        policy=ws.progress.numerical_policy, basis=ws.basis, primal=ws.primal,
        costs=ws.costs, lower=ws.lower, upper=ws.upper, rho=ws.scratch.rho,
        reduced_costs=ws.reduced_costs, factorization=portable_factorization(ws.factorization),
        omitted_refactor_workspace_type=string(typeof(ws.factorization.refactor_workspace)),
        refactorization_state=ws.scratch.refactorization, pricing=ws.scratch.pricing,
        perturbations=ws.scratch.perturbations, perturbed=ws.perturbed,
        iterations=ws.iterations, refactorizations=ws.refactorizations,
        iteration_offset=ws.progress.iteration_offset,
        phase_generation=ws.scratch.phase_generation,
        finite_workspace=JS._finite_workspace(ws), failure)
    atomic_serialize(prefix*".basis-failure.bin", data)
    captured[] = true
    println("Saved first failed verification state: ",prefix*".basis-failure.bin")
    flush(stdout)
    # A report failure never hides the primary artifact or original exception.
    try
        write_report(prefix*".basis-failure.toml",summarize(data))
    catch exception
        write_report(prefix*".analysis-error.toml",Dict("error"=>sprint(showerror,exception,catch_backtrace())))
        @warn "Snapshot saved, but residual analysis failed" exception
    end
    return nothing
end

function verify!(ws,stop;refactorize::Bool=false)
    result = try
        JS._diagnostic_original_verify_driver_basis!(ws,stop;refactorize)
    catch exception
        failure = (;kind="exception",refactorize,
            exception_type=string(typeof(exception)),
            exception=sprint(showerror,exception,catch_backtrace()))
        try
            save_failure(ws,failure)
        catch saving_exception
            @error "Could not save failure snapshot; original exception follows" saving_exception
        end
        # Preserve this diagnostic stop through the solver's numerical-error
        # handlers. They relay guard provenance through nested driver/cleanup
        # calls; without it they may consume the exception and resume recovery.
        stop isa JS._StopCallback && (stop.exception = exception)
        rethrow() # Preserve the original exception and stack, never substitute Captured.
    end
    result && return true
    # No extra stop() calls: caller callbacks can be stateful. The CLI supplies
    # only the solver's time guard; an expired budget is explicitly identified.
    budget_expired = isfinite(ws.options.time_limit) &&
        (time_ns()-ws.progress.start_ns)/1e9 >= ws.options.time_limit
    save_failure(ws,(;kind="returned_false",refactorize,budget_expired,
        exception_type="",exception=""))
    throw(Captured(budget_expired))
end

scalar(x) = x isa Union{Bool,Integer,Float32,Float64,AbstractString} ? x : string(x)
function quality_report(B,x,rhs,policy;transposed=false)
    T = eltype(x)
    scratch = JS.SolveQualityScratch(T,length(rhs))
    quality = JS.solve_quality!(scratch,B,x,rhs,policy;transposed)
    report = Dict{String,Any}(string(name)=>scalar(getfield(quality,name))
        for name in fieldnames(typeof(quality)))
    # Report actual componentwise equations, including tiny homogeneous rows.
    residual = copy(scratch.residual)
    scales = abs.(rhs) + (transposed ? abs.(transpose(B))*abs.(x) : abs.(B)*abs.(x))
    errors = [iszero(scales[i]) ? (iszero(residual[i]) ? zero(T) : T(Inf)) :
        abs(residual[i])/scales[i] for i in eachindex(rhs)]
    indices = sortperm(errors;rev=true)[1:min(10,length(errors))]
    report["worst_equations"] = [Dict("equation"=>i,"rhs"=>scalar(rhs[i]),
        "residual"=>scalar(residual[i]),"scale"=>scalar(scales[i]),
        "componentwise_ratio"=>scalar(errors[i])) for i in indices]
    report["note"] = "Ratios are descriptive; reliable is the solver's unchanged roundoff-aware test."
    return report
end

function equations(d)
    T = eltype(d.primal)
    m,n = size(d.problem.A)
    full = hcat(d.problem.A,spdiagm(0=>fill(-one(T),m)))
    B = full[:,d.basis.basic_indices]
    rhs = zeros(T,m)
    # The saved published nonbasic values are exactly those installed by
    # recompute!. A verification exception may instead represent a partial state.
    for j in eachindex(d.basis.states)
        d.basis.states[j] == JS.BASIC && continue
        for p in nzrange(full,j)
            rhs[full.rowval[p]] -= full.nzval[p]*d.primal[j]
        end
    end
    return B,rhs
end

function summarize(d)
    B,rhs = equations(d)
    report = Dict{String,Any}(
        "format_version"=>d.format_version,"iterations"=>d.iterations,
        "iteration_offset"=>d.iteration_offset,"refactorizations"=>d.refactorizations,
        "failure"=>Dict(string(k)=>scalar(v) for (k,v) in pairs(d.failure)),
        "rows"=>size(d.problem.A,1),"columns"=>size(d.problem.A,2),
        "basis_nonzeros"=>nnz(B),"factorization_type"=>string(typeof(d.factorization)),
        "update_count"=>length(d.factorization.updates),
        "finite_workspace"=>d.finite_workspace,
        "solve_tolerance"=>scalar(d.policy.solve_tolerance),
        "primal_tolerance"=>scalar(d.options.primal_tolerance),
        "dual_tolerance"=>scalar(d.options.dual_tolerance),
        "primal"=>quality_report(B,d.primal[d.basis.basic_indices],rhs,d.policy),
        "transpose"=>quality_report(B,d.rho,d.costs[d.basis.basic_indices],d.policy;transposed=true),
        "scope"=>"Published state after the first failed verification; native cleanup's rejected private trials are not published.",
    )
    return report
end

function main(input,prefix,seconds=600.0)
    seconds > 0 && isfinite(seconds) || error("Seconds must be finite and positive")
    output_prefix[] = abspath(prefix)
    captured[] = false
    for suffix in (".environment.toml",".basis-failure.bin",".basis-failure.bin.partial",
                   ".basis-failure.toml",".analysis-error.toml",".run.toml")
        ispath(output_prefix[]*suffix) && error("Use a fresh output prefix: "*prefix)
    end
    mkpath(dirname(output_prefix[]))
    data = deserialize(input)
    data.options.basis_update == :huangfu_hall &&
        data.options.basis_refactorization == :native ||
        error("This portable snapshot requires basis_update=:huangfu_hall and basis_refactorization=:native")
    write_report(output_prefix[]*".environment.toml",environment(input))
    install!()
    options = JS._remaining_options(data.options;iterations=0,time_limit=Float64(seconds))
    started = time_ns()
    report = Dict{String,Any}("input"=>abspath(input),"budget_seconds"=>seconds,
        "mode"=>"restored_basis_without_target_primal")
    code = 0
    try
        result = Base.invokelatest(JS.cleanup_original,data.problem,data.basis,options,
            JS.SolveContext(time_ns(),Float64(seconds)),data.iterations,data.refactorizations)
        report["outcome"] = "no_failure_captured"
        report["solver_status"] = string(result.status)
        report["solver_message"] = result.message
        report["iterations"] = result.iterations
        code = 2
    catch exception
        if exception isa Captured
            expired = exception.budget_expired
            report["outcome"] = expired ? "verification_stopped_at_time_budget" : "failure_captured"
            code = expired ? 3 : 0
        else
            report["outcome"] = captured[] ? "exception_captured" : "exception_without_capture"
            report["exception"] = sprint(showerror,exception,catch_backtrace())
            rethrow()
        end
    finally
        report["snapshot_saved"] = captured[]
        report["seconds_including_compilation_and_capture"] = (time_ns()-started)/1e9
        write_report(output_prefix[]*".run.toml",report)
        println(report)
    end
    return code
end
end
if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) in (2,3) || error("Expected: handoff.bin output_prefix [seconds=600]")
    exit(RuntimeBasisFailure.main(ARGS[1],ARGS[2],length(ARGS)==3 ? parse(Float64,ARGS[3]) : 600.0))
end
