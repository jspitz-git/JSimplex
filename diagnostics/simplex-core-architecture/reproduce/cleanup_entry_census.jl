# Diagnostic-only paired census. Production function bodies are parsed unchanged.
using JSimplex, SparseArrays, LinearAlgebra, Logging, SHA, TOML
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
scalar(x::BigFloat)=isfinite(x) ? string(Rational{BigInt}(x),"@",precision(x)) : string(x)
scalar(x)=string(x)
values(x)=scalar.(x)
basisstate(b)=Dict("basic"=>copy(b.basic_indices),"states"=>string.(b.states))
function snapshot(ws)
    Dict("basis"=>basisstate(ws.basis),"primal"=>values(ws.primal),
      "costs"=>values(ws.costs),"prices"=>values(ws.reduced_costs),
      "weights"=>values(ws.pricing_weights),"lower"=>values(ws.lower),"upper"=>values(ws.upper),
      "iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,
      "algorithm"=>string(ws.options.algorithm),
      "checkpoints"=>[Dict("basis"=>basisstate(c.basis),"costs"=>values(c.costs),
        "lower"=>values(c.lower),"upper"=>values(c.upper)) for c in ws.scratch.checkpoints])
end
struct CensusLogger <: AbstractLogger
    exception::Exception
end
Logging.min_enabled_level(::CensusLogger)=Logging.Info
Logging.shouldlog(::CensusLogger,args...)=true
Logging.catch_exceptions(::CensusLogger)=false
function Logging.handle_message(l::CensusLogger,level,message,args...;kwargs...)
    message=="Refactorizing basis" && throw(l.exception)
end
function fixture(T,singular)
    if singular
        p=LinearProblem(sparse(T[1 0]),T[1,0];row_lower=T[1],column_lower=T[0,0])
        b=JS.Basis([2],JS.VariableState[JS.AT_LOWER,JS.BASIC,JS.AT_LOWER])
        return p,b,nothing
    end
    p=LinearProblem(sparse(T[1 1 0;0 0 1]),T[-1,0,-1];row_lower=[nothing,T(0)],
        row_upper=T[10,10],column_lower=T[0,4,0],column_upper=[nothing,T(8),nothing])
    b=JS.Basis([2,3],JS.VariableState[JS.AT_LOWER,JS.BASIC,JS.BASIC,JS.AT_UPPER,JS.AT_LOWER])
    return p,b,T[6,4,5]
end
function run_case(T,algorithm,backend,profile,mode)
    p,b,target=fixture(T,mode==:singular)
    initial_basis=basisstate(b)
    opts=SolverOptions(T;algorithm,basis_update=:huangfu_hall,basis_refactorization=backend,
        simplex_strategy=:legacy,verbose=false,log_level=Logging.Info,iteration_limit=40,scaling=:off)
    policy=JS.NumericalPolicy(T;numerical_profile=profile,simplex_strategy=:legacy)
    events=Any[];exception=SingularException(713)
    observer=(reason,ws)->begin
        push!(events,Dict("reason"=>string(reason),"state"=>snapshot(ws)))
        mode==:observer_throw && reason==:refactor_initial && throw(exception)
    end
    diagnostics=mode==:unobserved ? nothing : JS.SimplexDiagnostics(;observer)
    context=JS.SolveContext(time_ns(),mode==:expired ? 0.0 : Inf,diagnostics,policy)
    supplied=mode==:project ? target : mode==:bad_hint ? T[0] : nothing
    result=nothing;caught=nothing
    try
        result=with_logger(mode==:logger_throw ? CensusLogger(exception) : NullLogger()) do
            JS.cleanup_original(p,b,opts,context,7,3;target_primal=supplied)
        end
    catch e;caught=e;end
    @assert basisstate(b)==initial_basis
    row=Dict{String,Any}("key"=>join(string.((T,algorithm,backend,profile,mode)),"/"),
      "type"=>string(T),"algorithm"=>string(algorithm),"backend"=>string(backend),
      "profile"=>string(profile),"mode"=>string(mode),"events"=>events,
      "restored_basis_unchanged"=>true,"recovery_enabled"=>policy.recovery)
    if caught!==nothing
        @assert mode in (:observer_throw,:logger_throw)
        @assert mode==:logger_throw ? caught===exception : caught isa JS.DiagnosticObserverFailure
        row["exception"]=string(typeof(caught));row["caller_exception_preserved"]=
            caught===exception || any(x->x===exception,[getfield(caught,k) for k in fieldnames(typeof(caught))])
        @assert row["caller_exception_preserved"]
    else
        @assert !(mode in (:observer_throw,:logger_throw))
        row["status"]=string(result.status);row["objective"]=scalar(result.objective_value)
        row["primal"]=isnothing(result.primal) ? String[] : values(result.primal)
        row["iterations"]=result.iterations;row["refactorizations"]=result.refactorizations
        row["basis"]=isnothing(result.basis) ? Dict{String,Any}() : basisstate(result.basis)
        row["original_feasible"]=!isnothing(result.primal) && JS._original_primal_feasible(p,result.primal,opts.primal_tolerance)
        if mode==:expired
            @assert result.status==TIME_LIMIT && result.iterations==7 && result.refactorizations==3
        elseif mode==:singular
            @assert result.status==NUMERICAL_ERROR
        else
            @assert result.status==OPTIMAL && result.objective_value==T(-16) && row["original_feasible"]
        end
    end
    row
end
const LABELS=("ftran_requests","btran_requests","pricing_reconstructions","basis_validations","checkpoint_attempts","checkpoint_publications","refactor_attempts")
function parsed(file,prefix)
    src=read(joinpath(ROOT,"src",file),String);pos=findall(prefix,src)
    @assert length(pos)==1
    ex,_=Meta.parse(src,first(only(pos)));@assert ex.head==:function;ex
end
function install!()
    Core.eval(JS,:(const _ce_counts=zeros(Int,7)))
    Core.eval(JS,:(const _ce_rows=Any[]))
    Core.eval(JS,:(const _ce_initial=Ref(false)))
    Core.eval(JS,:(const _ce_snapshot=$snapshot))
    hooks=[("simplex_recovery.jl","function _checked_basis_solve!",:( _ce_counts[1+Int(transposed)]+=1 )),
      ("simplex.jl","function _recompute_reduced_costs!",:(_ce_counts[3]+=1)),
      ("simplex.jl","function _validate_basis(",:(_ce_counts[4]+=1)),
      ("simplex_recovery.jl","function _remember_verified_basis!",:(_ce_counts[5]+=1)),
      ("simplex_recovery.jl","function _store_basis_checkpoint!",:(_ce_counts[6]+=1))]
    for (file,prefix,probe) in hooks
        ex=parsed(file,prefix);body=ex.args[2];ex.args[2]=quote $probe; $body end;Core.eval(JS,ex)
    end
    ex=parsed("simplex.jl","function _finish_workspace_initialization!");body=ex.args[2]
    ex.args[2]=quote
        saved=_ce_initial[];_ce_initial[]=true
        try;return (() -> begin $body end)();finally;_ce_initial[]=saved;end
    end
    Core.eval(JS,ex)
    ex=parsed("simplex.jl","function recompute!(workspace::SimplexWorkspace{T};");body=ex.args[2]
    ex.args[2]=quote
        counts_before=copy(_ce_counts);state_before=_ce_snapshot(workspace)
        initial=_ce_initial[];completed=false
        refactorize && (_ce_counts[7]+=1)
        try
            result=(() -> begin $body end)();completed=true;return result
        finally
            push!(_ce_rows,Dict("initial"=>initial,"refactor_requested"=>refactorize,
              "completed"=>completed,"before"=>state_before,"after"=>_ce_snapshot(workspace),
              "counts"=>_ce_counts-counts_before,"rows"=>size(workspace.problem.A,1),
              "columns"=>size(workspace.problem.A,2),"nnz"=>nnz(workspace.problem.A)))
        end
    end
    Core.eval(JS,ex)
end
function main(out)
    @assert !ispath(out)
    cases=[(T,a,b,p,m) for T in (Float32,Float64,BigFloat,Rational{BigInt})
      for a in (:primal,:dual) for b in (:native,:markowitz) for p in (:native,:checked)
      for m in (:unobserved,:observed,:expired,:project,:bad_hint)]
    append!(cases,[(Float64,a,b,p,m) for a in (:primal,:dual) for b in (:native,:markowitz)
      for p in (:native,:checked) for m in (:singular,:observer_throw,:logger_throw)])
    controls=[run_case(c...) for c in cases]
    install!();rows=Any[]
    for (c,control) in zip(cases,controls)
        fill!(JS._ce_counts,0);empty!(JS._ce_rows)
        counted=Base.invokelatest(run_case,c...)
        @assert isequal(control,counted) "instrumentation changed $(control["key"])"
        records=deepcopy(JS._ce_rows)
        @assert count(r->r["initial"],records)==1
        initial=only(filter(r->r["initial"],records))
        @assert initial["completed"] && initial["counts"][1:3]==[1,1,1]
        @assert initial["counts"][7]==0
        if c[5] in (:expired,:observer_throw)
            @assert length(records)==1
        else
            @assert length(records)>=2 && records[2]["refactor_requested"]
        end
        push!(rows,Dict("control"=>control,"exact_pair"=>true,"recomputations"=>records,
            "total_counts"=>copy(JS._ce_counts)))
    end
    report=Dict("source"=>pathof(JS),"source_sha256"=>bytes2hex(sha256(read(pathof(JS)))),
      "script_sha256"=>bytes2hex(sha256(read(@__FILE__))),"labels"=>collect(LABELS),
      "case_count"=>length(rows),"cases"=>rows,"timing_claim"=>"none; counted requests are not raw refinement solves")
    open(out,"w") do io;TOML.print(io,report);end
    println("CLEANUP_ENTRY_CENSUS_PASS cases=",length(rows))
end
main(only(ARGS))
