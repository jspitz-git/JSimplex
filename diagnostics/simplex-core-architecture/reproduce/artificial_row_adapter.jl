using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const TESTFILE=joinpath(ROOT,"test/native_artificial_row_tests.jl")
const SOURCE=read(TESTFILE,String)
const TITLE="Artificial-row recovery respects budgets and preserves the original on cancellation"
# Load only the unchanged fixture definition. Preserve the original oracle node.
Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),TESTFILE)
const NODE=only(filter(x->x isa Expr && x.head==:macrocall &&
    x.args[1]==Symbol("@testset") && TITLE in x.args,Meta.parseall(SOURCE).args))
# Test-only adapter: real factor ownership remains private to the phase workspace.
mutable struct S6RowFactor{F}
    inner::F
    armed::Bool
    exact::Bool
    hits::Int
    calls::Int
end
Base.getproperty(f::S6RowFactor,name::Symbol)=name in fieldnames(typeof(f)) ?
    getfield(f,name) : getproperty(getfield(f,:inner),name)
const BAD_ROW=Float64[0.9999999999999981,0.9999999999999987,
    6.289736151548563e-17,1.2231357997302227e-16,-2.4643934028723657e-16,-4.478701551351629e-17]
function JS.transpose_solve!(dest::Vector{Float64},f::S6RowFactor,rhs::AbstractVector)
    f.calls+=1
    JS.transpose_solve!(dest,f.inner,rhs)
    if f.armed
        @assert length(rhs)==6 && rhs==[1.0,0.0,0.0,0.0,0.0,0.0]
        f.armed=false;f.hits+=1
        copyto!(dest,f.exact ? [1.0,1.0,0.0,0.0,0.0,0.0] : BAD_ROW)
    end
    dest
end
JS.forward_solve!(dest::Vector{Float64},f::S6RowFactor,rhs::AbstractVector)=JS.forward_solve!(dest,f.inner,rhs)
JS._ordinary_forward_solve!(dest::Vector{Float64},f::S6RowFactor,rhs::AbstractVector)=JS._ordinary_forward_solve!(dest,f.inner,rhs)
JS._invalidate_prepared_destination!(f::S6RowFactor,dest)=JS._invalidate_prepared_destination!(f.inner,dest)
JS._finite_updated_factor(f::S6RowFactor)=JS._finite_updated_factor(f.inner)
JS.refactorize!(f::S6RowFactor,B::AbstractMatrix)=JS.refactorize!(f.inner,B)
JS.replace_column!(f::S6RowFactor,direction::AbstractVector,row::Integer;kwargs...)=JS.replace_column!(f.inner,direction,row;kwargs...)
function wrap_phase(ws;armed=false,exact=false)
    @assert !ws.progress.numerical_policy.hypersparse
    factor=S6RowFactor(ws.factorization,armed,exact,0,0)
    # Phase owns all fields; reconstruct only its concrete factor type. Never
    # wrap original: final adoption assigns a fresh ordinary original factor.
    JS.SimplexWorkspace((name==:factorization ? factor : getfield(ws,name)
        for name in fieldnames(typeof(ws)))...)
end
function controlled_fixture(args...;kwargs...)
    phase,map,original,policy=artificial_row_roundoff_fixture(args...;kwargs...)
    return wrap_phase(phase;armed=true),map,original,policy
end

function snapshot(ws)
    Dict("basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),
      "primal"=>copy(ws.primal),"costs"=>copy(ws.costs),"prices"=>copy(ws.reduced_costs),
      "lower"=>string.(ws.lower),"upper"=>string.(ws.upper),
      "iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations)
end
function observe(manager,mode;record_events=false,adapter_mode=:none)
    correcting=Ref(false);events=String[]
    # Both twins retain the original behavior-driving observer. Only passive
    # event recording differs; cancellation/exception semantics must be identical.
    diagnostics=JS.SimplexDiagnostics(;observer=(event,ws)->begin
        event==:correction_attempt && (correcting[]=true)
        record_events && push!(events,string(event))
    end)
    phase,mapping,original,policy=artificial_row_roundoff_fixture(Float64,manager;
        diagnostics,infeasible_original=mode==:point,max_refinements=mode==:budget ? 0 : 3,
        pivot_validation=mode==:checked,
        pivot_error_tolerance=mode==:pivot ? eps(Float64)^2 : sqrt(eps(Float64)))
    adapter_mode!=:none && (phase=wrap_phase(phase;armed=adapter_mode==:enabled,exact=mode==:reliable))
    mode==:dual && (phase.options=JS._phase_options(phase.options,:dual))
    before=snapshot(original)
    failure=SingularException(927)
    stop=()->begin
        correcting[] && mode==:exception && throw(failure)
        correcting[] && mode==:cancel
    end
    result=try JS.remove_artificials!(phase,mapping,original,policy,stop) catch e; e end
    after=snapshot(original)
    record=Dict("manager"=>string(manager),"mode"=>string(mode),
        "result"=>string(result),"same_callback_exception"=>result===failure,
        "correcting"=>correcting[],"before"=>before,"original"=>after,
        "phase"=>snapshot(phase),"events"=>events,
        "artificial_removed"=>JS.event_count(diagnostics,:artificial_removed),
        "numerical_state_unchanged"=>all(isequal(before[k],after[k]) for k in
             ("basis","states","primal","costs","prices","lower","upper")))
    # Post-state feasibility probe only; it cannot influence the recorded attempt.
    record["original_feasible"]=JS._original_primal_feasible(original,original.primal[1:6])
    record["adapter"]=Dict("hits"=>adapter_mode==:none ? 0 : phase.factorization.hits,
        "btran_calls"=>adapter_mode==:none ? 0 : phase.factorization.calls,
        "armed"=>adapter_mode==:none ? false : phase.factorization.armed)
    return record
end
function initial_row_probe(manager,mode)
    # Independent fresh fixture, after both twins. Never modifies either attempt.
    phase,map,original,policy=artificial_row_roundoff_fixture(Float64,manager;
        infeasible_original=mode==:point,max_refinements=mode==:budget ? 0 : 3,
        pivot_validation=mode==:checked,
        pivot_error_tolerance=mode==:pivot ? eps(Float64)^2 : sqrt(eps(Float64)))
    mode==:dual && (phase.options=JS._phase_options(phase.options,:dual))
    unit=zeros(6);unit[1]=1;rho=zeros(6)
    JS._checked_basis_solve!(rho,phase,unit,()->false;transposed=true)
    copyto!(rho,mode==:reliable ? [1.0,1.0,0.0,0.0,0.0,0.0] : BAD_ROW)
    B=JS._basis_matrix!(phase)
    q=JS.solve_quality!(JS._pivot_quality_buffers(phase).row,B,rho,unit,policy;transposed=true)
    Dict("rho"=>rho,"absolute_error"=>q.absolute_error,
        "relative_error"=>isnothing(q.relative_error) ? "nothing" : string(q.relative_error),
        "finite"=>q.finite,"reliable"=>q.reliable,
        "native_enabled"=>JS._native_phase_transfer_enabled(phase),
        "max_refinements"=>policy.max_refinements)
end
records=Dict[]
@testset "Controlled row adapter qualification" begin
for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
    mode in (:budget,:checked,:dual,:cancel,:exception,:pivot,:point,:success,:reliable)
    control=observe(manager,mode)
    disabled=observe(manager,mode;record_events=true,adapter_mode=:disabled)
    enabled=observe(manager,mode;record_events=true,adapter_mode=:enabled)
    equal=all(isequal(control[k],disabled[k]) for k in keys(control) if !(k in ("events","adapter")))
    @test equal
    @test disabled["adapter"]["hits"]==0
    @test enabled["adapter"]["hits"]==1 && !enabled["adapter"]["armed"]
    q=initial_row_probe(manager,mode)
    @test q["reliable"] == (mode==:reliable)
    @test enabled["correcting"] == !(mode in (:budget,:checked,:dual,:reliable))
    @test enabled["result"] == (mode in (:success,:reliable) ? "true" : mode==:exception ? "SingularException(927)" : "false")
    @test enabled["same_callback_exception"] == (mode==:exception)
    @test enabled["original"]["iterations"] == (mode in (:point,:success,:reliable) ? 1 : 0)
    @test enabled["artificial_removed"] == (mode in (:point,:success,:reliable) ? 1 : 0)
    @test enabled["numerical_state_unchanged"] == !(mode in (:success,:reliable))
    @test enabled["original_feasible"] == (mode!=:point)
    push!(records,Dict("control"=>control,"disabled"=>disabled,"enabled"=>enabled,
        "disabled_equal"=>equal,"injected_quality"=>q))
end
end
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
    "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"records"=>records))
end
# Original assertions unchanged, only the fixture constructor gains the adapter.
const REDIRECTS=Ref(0)
function redirect_fixture!(ex)
    ex isa Expr || return
    for i in eachindex(ex.args)
        if ex.args[i]===:artificial_row_roundoff_fixture
            ex.args[i]=:controlled_fixture;REDIRECTS[]+=1
        else
            redirect_fixture!(ex.args[i])
        end
    end
end
redirect_fixture!(NODE);@assert REDIRECTS[]==1
Core.eval(@__MODULE__,NODE)
