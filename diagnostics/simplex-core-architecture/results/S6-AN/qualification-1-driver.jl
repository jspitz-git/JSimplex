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
        (identity=objectid(j),owner=j.workspace_id,owner_match=j.workspace_id==objectid(ws),
         lower_alias=ws.lower===j.bounds.active_lower,upper_alias=ws.upper===j.bounds.active_upper,
         lower_identity=objectid(ws.lower),upper_identity=objectid(ws.upper),cost_length_match=length(j.original_costs)==length(ws.costs),
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


# Each gate records an assertion and stops the qualification immediately on failure.
function gate(ok)
    @test ok
    ok || error("qualification gate failed; no further lifecycle is authorized")
end
budget_snapshot(b)=(start_ns=b.start_ns,time_limit_seconds=b.time_limit_seconds,
    iteration_limit=b.iteration_limit,iterations=b.iterations,refactorizations=b.refactorizations)
const records=Dict{String,Any}()
const metadata=Dict{String,Any}("source"=>pathof(JS),"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"exception"=>"none",
    "monitor_sha256"=>bytes2hex(sha256(MONITOR)),"helper_sha256"=>bytes2hex(sha256(HELPER)))
function qualify(mode)
    entries=Dict("helper"=>0,"initial_optimizer"=>0,"budget_constructor"=>0,"run_from_basis"=>0)
    times=Dict{String,UInt64}(); snapshots=Dict{String,Any}(); payloads=Dict{String,Any}()
    record=Dict("entries"=>entries,"times"=>times,"snapshots"=>snapshots,"payloads"=>payloads)
    records[string(mode)]=record
    @testset "Native entry $mode" begin
        entries["helper"]+=1;times["helper_before"]=time_ns()
        ws,setup_policy=shifted_primal_workspace()
        times["helper_after"]=time_ns()
        snapshots["setup"]=capture(ws)
        ws.progress.diagnostics.kernel_timing=true
        entries["initial_optimizer"]+=1;times["initial_before"]=time_ns()
        terminal=JS._primal_optimize!(ws,()->false)
        times["initial_after"]=time_ns()
        payloads["initial"]=(status=terminal.status,message=terminal.message)
        snapshots["initial"]=capture(ws)
        gate(terminal.status==OPTIMAL)
        a=snapshots["setup"]; i=snapshots["initial"]
        gate(all(i.kernel_calls[k]-a.kernel_calls[k]==get(Dict(:ftran=>2,:btran=>3,:pricing=>2),k,0) for k in keys(a.kernel_calls)))
        gate(all(reinterpret(UInt64,x)==0xbeae32f0ee144531 for x in i.point) && i.basis==[2] && i.states==[JS.AT_LOWER,JS.BASIC])
        policy=JS.NumericalPolicy(Float64)
        JS._install_driver_policy!(ws,policy)
        entries["budget_constructor"]+=1;budget=JS.SimplexRunBudget(ws)
        payloads["budget_before"]=budget_snapshot(budget)
        snapshots["before_driver"]=capture(ws)
        before=snapshots["before_driver"]
        calls=Ref(0); sentinel=SingularException(29)
        stop=()->begin
            calls[]+=1
            mode==:throw && throw(sentinel)
            true
        end
        run=nothing; caught=nothing
        entries["run_from_basis"]+=1;times["driver_before"]=time_ns()
        try
            run=JS.run_from_basis!(ws,budget,policy,stop)
        catch exception
            caught=exception
        finally
            times["driver_after"]=time_ns()
            payloads["callback_calls"]=calls[]
        end
        snapshots["final"]=capture(ws); after=snapshots["final"]
        payloads["budget_after"]=budget_snapshot(budget)
        payloads["caught"]=(type=typeof(caught),same_sentinel=caught===sentinel,
            message=isnothing(caught) ? "none" : sprint(showerror,caught))
        payloads["run"]=isnothing(run) ? nothing : (status=run.status,message=run.message,
            primal=isnothing(run.primal) ? nothing : copy(run.primal),objective=run.objective_value,
            basis=isnothing(run.basis) ? nothing : copy(run.basis.basic_indices))
        gate(calls[]==1)
        gate(before.kernel_calls==after.kernel_calls)
        for field in (:point,:costs,:prices,:rho,:lower,:upper,:basis,:states,:perturbed,:journal,:model,
                      :options,:policy,:start_ns,:iteration_offset,:refactorization_offset,:iterations,:refactorizations,
                      :row_scaling,:column_scaling,:factor_type,:observer_absent)
            gate(isequal(getproperty(before,field),getproperty(after,field)))
        end
        gate(before.journal.owner_match && before.journal.bounds.active)
        gate(payloads["budget_before"]==payloads["budget_after"] && budget.start_ns==ws.progress.start_ns)
        gate(budget.iterations==ws.iterations && budget.refactorizations==ws.refactorizations)
        if mode==:stop
            gate(isnothing(caught) && !isnothing(run))
            gate(run.status==TIME_LIMIT && run.message=="time limit reached during feasibility recovery")
            gate(isnothing(run.primal) && isnothing(run.objective_value) && isnothing(run.basis))
        else
            gate(caught===sentinel && isnothing(run))
        end
        expected=mode==:stop ? [:checkpoint] : Symbol[]
        gate(after.event_ring==vcat(before.event_ring,expected))
        gate(after.next_event==before.next_event+length(expected))
        gate(all(after.event_counts[k]-before.event_counts[k]==(mode==:stop && k==:checkpoint ? 1 : 0) for k in keys(before.event_counts)))
    end
end
try
    qualify(:stop)
    qualify(:throw)
catch exception
    metadata["exception"]=sprint(showerror,exception)
    rethrow()
finally
    metadata["globals_before"]=string(GLOBALS)
    metadata["globals_after"]=string((precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals()))
    metadata["globals_preserved"]=metadata["globals_before"]==metadata["globals_after"]
    open(RESULT,"w") do io
        TOML.print(io,Dict("metadata"=>metadata,"cases"=>enc(records)))
    end
end
