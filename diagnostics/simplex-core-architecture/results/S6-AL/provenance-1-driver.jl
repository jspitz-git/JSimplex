using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const RESULT=only(ARGS)
@assert !ispath(RESULT)
const GLOBALS=(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
@assert GLOBALS==(256,RoundNearest,RoundNearest,false) && Threads.nthreads()==BLAS.get_num_threads()==1
# Exact source definitions only: no neighboring testset is evaluated.
function definition(path,name)
    source=read(joinpath(ROOT,path),String)
    found=match(Regex("(?ms)^function "*name*"\\(.*?^end\\n"),source)
    @assert !isnothing(found)
    return found.match
end
const MONITOR=definition("test/primal_perturbation_tests.jl","primal_stalled_monitor")
const HELPER=definition("test/primal_perturbation_integration_tests.jl","shifted_primal_workspace")
include_string(Main,MONITOR,"actual-primal-stalled-monitor.jl")
include_string(Main,HELPER,"actual-shifted-primal-workspace.jl")

# Owned bounded snapshots; no quality, solve or certificate calls. Immutable
# options/policy values are retained; mutable numerical storage is copied.
function capture(ws)
    d=ws.progress.diagnostics; j=ws.scratch.perturbations; p=ws.problem
    bounds=isnothing(j) || isnothing(j.bounds) ? nothing :
        (active=j.bounds.active,original_lower=copy(j.bounds.original_lower),
         original_upper=copy(j.bounds.original_upper),active_lower=copy(j.bounds.active_lower),
         active_upper=copy(j.bounds.active_upper),level=j.bounds.level)
    journal=isnothing(j) ? nothing :
        (owner_match=j.workspace_id==objectid(ws),cost_length_match=length(j.original_costs)==length(ws.costs),
         active=j.active,original_perturbed=j.original_perturbed,
         original_costs=copy(j.original_costs),active_costs=copy(j.active_costs),bounds=bounds)
    model=(colptr=copy(p.A.colptr),rowval=copy(p.A.rowval),nzval=copy(p.A.nzval),
           objective=copy(p.objective),objective_constant=p.objective_constant,
           objective_sense=p.objective_sense,row_lower=copy(p.row_lower),row_upper=copy(p.row_upper),
           column_lower=copy(p.column_lower),column_upper=copy(p.column_upper),
           variable_domains=copy(p.variable_domains),name=p.name)
    return (point=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),rho=copy(ws.scratch.rho),
        lower=copy(ws.lower),upper=copy(ws.upper),basis=copy(ws.basis.basic_indices),states=copy(ws.basis.states),
        perturbed=ws.perturbed,journal=journal,model=model,options=ws.options,policy=ws.progress.numerical_policy,
        start_ns=ws.progress.start_ns,iteration_offset=ws.progress.iteration_offset,
        refactorization_offset=ws.progress.refactorization_offset,iterations=ws.iterations,refactorizations=ws.refactorizations,
        row_scaling=copy(ws.progress.scaling.row_factors),column_scaling=copy(ws.progress.scaling.column_factors),
        event_counts=copy(d.counts),event_ring=copy(d.events),next_event=d.next_event,
        kernel_calls=copy(d.kernel_calls),kernel_nanoseconds=copy(d.kernel_nanoseconds),
        kernel_timing=d.kernel_timing,observer_absent=isnothing(d.observer),factor_type=typeof(ws.factorization))
end
# Encoding runs only after the last numerical call, including exceptional exits.
enc(x::Nothing)="nothing"
enc(x::Bool)=x
enc(x::Integer)=x isa UInt ? string(x) : x
enc(x::Float64)=Dict("bits"=>string(reinterpret(UInt64,x);base=16,pad=16),"exact"=>isfinite(x) ? string(Rational{BigInt}(x)) : string(x))
enc(x::JS.Bound)=Dict("finite"=>isfinite(x),"value"=>isfinite(x) ? enc(JS.bound_value(x)) : "infinite")
enc(x::AbstractString)=x
enc(x::AbstractArray)=[enc(v) for v in x]
enc(x::NamedTuple)=Dict(string(k)=>enc(v) for (k,v) in pairs(x))
enc(x::AbstractDict)=Dict(string(k)=>enc(v) for (k,v) in x)
enc(x::Union{JS.SolverOptions,JS.NumericalPolicy})=Dict(string(k)=>enc(getfield(x,k)) for k in fieldnames(typeof(x)))
enc(x)=string(x)

const entries=Dict("helper"=>0,"initial_optimizer"=>0,"budget_constructor"=>0,"run_from_basis"=>0)
const times=Dict{String,UInt64}()
const snapshots=Dict{String,Any}()
const payloads=Dict{String,Any}()
const metadata=Dict{String,Any}("source"=>pathof(JS),"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"exception"=>"none",
    "monitor_sha256"=>bytes2hex(sha256(MONITOR)),"helper_sha256"=>bytes2hex(sha256(HELPER)))
try
    @testset "Native cleanup provenance original predicates" begin
        entries["helper"]+=1; times["helper_before"]=time_ns()
        ws,setup_policy=shifted_primal_workspace()
        times["helper_after"]=time_ns()
        times["setup_capture_before"]=time_ns();snapshots["setup"]=capture(ws);times["setup_capture_after"]=time_ns()
        ws.progress.diagnostics.kernel_timing=true
        entries["initial_optimizer"]+=1;times["initial_before"]=time_ns()
        terminal=JS._primal_optimize!(ws,()->false)
        times["initial_after"]=time_ns()
        payloads["initial"]=(status=terminal.status,message=terminal.message)
        times["initial_capture_before"]=time_ns();snapshots["initial"]=capture(ws);times["initial_capture_after"]=time_ns()
        @test terminal.status == OPTIMAL
        policy=JS.NumericalPolicy(Float64)
        JS._install_driver_policy!(ws,policy)
        @test JS._original_objective_driver_required(ws)
        entries["budget_constructor"]+=1;budget=JS.SimplexRunBudget(ws)
        payloads["budget_before"]=(start_ns=budget.start_ns,time_limit_seconds=budget.time_limit_seconds,
            iteration_limit=budget.iteration_limit,iterations=budget.iterations,refactorizations=budget.refactorizations)
        times["driver_capture_before"]=time_ns();snapshots["before_driver"]=capture(ws);times["driver_capture_after"]=time_ns()
        entries["run_from_basis"]+=1;times["driver_before"]=time_ns()
        run=JS.run_from_basis!(ws,budget,policy,()->false)
        times["driver_after"]=time_ns()
        times["final_capture_before"]=time_ns();snapshots["final"]=capture(ws);times["final_capture_after"]=time_ns()
        payloads["run"]=(status=run.status,message=run.message,objective=run.objective_value,
            primal=isnothing(run.primal) ? nothing : copy(run.primal),
            basis=isnothing(run.basis) ? nothing : (indices=copy(run.basis.basic_indices),states=copy(run.basis.states)),
            iterations=run.iterations,refactorizations=run.refactorizations)
        payloads["budget_after"]=(start_ns=budget.start_ns,time_limit_seconds=budget.time_limit_seconds,
            iteration_limit=budget.iteration_limit,iterations=budget.iterations,refactorizations=budget.refactorizations)
        @test run.status == OPTIMAL && run.primal == [0.0]
        @test JS._original_bounds_active(ws)
        @test isnothing(ws.scratch.perturbations)
        @test !ws.progress.numerical_policy.feasibility_recovery
    end
catch exception
    metadata["exception"]=sprint(showerror,exception)
    rethrow()
finally
    metadata["globals_before"]=string(GLOBALS)
    metadata["globals_after"]=string((precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals()))
    metadata["globals_preserved"]=metadata["globals_before"]==metadata["globals_after"]
    open(RESULT,"w") do io
        TOML.print(io,Dict("metadata"=>metadata,"entries"=>entries,"times"=>enc(times),
            "snapshots"=>enc(snapshots),"payloads"=>enc(payloads)))
    end
end
