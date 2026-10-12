using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const INPUT=joinpath(ROOT,"diagnostics/simplex-core-architecture/results/S6-AE/inputs.toml")
const DATA=TOML.parsefile(INPUT)
rat(s)=begin p=split(s,"/");parse(BigInt,p[1])//(length(p)==1 ? big(1) : parse(BigInt,p[2])) end
readfloat(s)=begin q=rat(s);x=Float64(q);@assert Rational{BigInt}(x)==q;x end
ex(x)=string(Rational{BigInt}(x))
vecx(x)=ex.(vec(x))
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
const B=sparse(reduce(vcat,permutedims.(map(row->readfloat.(row),DATA["B"]))))
const UNIT=readfloat.(DATA["unit_rhs"])
const RHO=readfloat.(DATA["exact_rho"])
const BAD=readfloat.(DATA["declared_rho"])
const DUP=readfloat.(DATA["duplicate_rhs"])
const CORR=readfloat.(DATA["correction_rhs"])
const CORROUT=readfloat.(DATA["correction"])
const DIR=readfloat.(DATA["direction"])
const PRIMAL=-Vector(B[:,2])
const KEYS=(:ftran,:prepared,:ordinary,:btran,:unit,:correction,:cost,:metadata,:invalidate,:refactor,:update,:copy,:hits)
mutable struct DualBoundaryFactor{F}
    inner::F
    counts::Dict{Symbol,Int}
    calls::Vector{Dict{String,Any}}
end
DualBoundaryFactor(f)=DualBoundaryFactor(f,Dict(k=>0 for k in KEYS),Dict{String,Any}[])
Base.getproperty(f::DualBoundaryFactor,k::Symbol)=k in fieldnames(typeof(f)) ? getfield(f,k) : getproperty(getfield(f,:inner),k)
bump(f,k)=(f.counts[k]+=1)
counts(f)=Dict(string(k)=>v for (k,v) in f.counts)
function saved!(f,kind,rhs,out;declared=out)
    push!(f.calls,Dict("kind"=>kind,"rhs"=>vecx(rhs),"real_output"=>vecx(out),"declared_output"=>vecx(declared),"rhs_type"=>string(typeof(rhs)),"counts"=>counts(f)))
end
function JS._unit_transpose_rhs(f::DualBoundaryFactor,rhs,row::Int)
    bump(f,:metadata);@assert row==2 && rhs==UNIT
    return JS._unit_transpose_rhs(f.inner,rhs,row)
end
function JS.transpose_solve!(d::Vector{Float64},f::DualBoundaryFactor,r::AbstractVector)
    bump(f,:btran)
    kind=r==UNIT ? :unit : r==CORR ? :correction : all(iszero,r) ? :cost : :unexpected
    kind==:unexpected && error("Unexpected BTRAN RHS")
    bump(f,kind)
    JS.transpose_solve!(d,f.inner,r)
    real=copy(d)
    if kind==:unit
        @assert d==RHO
        if f.counts[:hits]<2
            copyto!(d,BAD);bump(f,:hits)
        end
    elseif kind==:correction
        @assert d==CORROUT
    else
        @assert all(iszero,d)
    end
    saved!(f,string(kind),r,real;declared=d)
    return d
end
function forward!(d,f,r,prepared)
    bump(f,:ftran);bump(f,prepared ? :prepared : :ordinary)
    @assert r==(prepared ? DUP : PRIMAL)
    prepared ? JS.forward_solve!(d,f.inner,r) : JS._ordinary_forward_solve!(d,f.inner,r)
    @assert d==(prepared ? DIR : -UNIT)
    saved!(f,prepared ? "prepared" : "ordinary",r,d)
    return d
end
JS.forward_solve!(d::Vector{Float64},f::DualBoundaryFactor,r::AbstractVector)=forward!(d,f,r,true)
JS._ordinary_forward_solve!(d::Vector{Float64},f::DualBoundaryFactor,r::AbstractVector)=forward!(d,f,r,false)
function JS._invalidate_prepared_destination!(f::DualBoundaryFactor,d)
    bump(f,:invalidate);JS._invalidate_prepared_destination!(f.inner,d)
end
JS._finite_updated_factor(f::DualBoundaryFactor)=JS._finite_updated_factor(f.inner)
function JS.refactorize!(f::DualBoundaryFactor,A::AbstractMatrix)
    bump(f,:refactor);@assert A==B
    JS.refactorize!(f.inner,A)
    return f
end
function JS.replace_column!(f::DualBoundaryFactor,d::AbstractVector,row::Integer;kwargs...)
    bump(f,:update);error("Unexpected factor update")
end
function JS.copy_basis_factorization(f::DualBoundaryFactor)
    bump(f,:copy);error("Unexpected factor copy")
end
function fixture(manager,policy,diagnostics;wrapped=true)
    p=LinearProblem(sparse(hcat(B,B[:,1])),zeros(5);row_lower=PRIMAL,row_upper=PRIMAL)
    options=SolverOptions(algorithm=:dual,simplex_strategy=:legacy,basis_update=manager,pricing=:dantzig,verbose=false)
    ws=JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis.basic_indices .= 1:4
    ws.basis.states[1:4] .= JS.BASIC
    ws.basis.states[6:9] .= JS.AT_LOWER
    JS.recompute!(ws;refactorize=true)
    @assert ws.primal==vcat(-UNIT,0.0,PRIMAL) && all(iszero,ws.reduced_costs)
    if wrapped
        factor=DualBoundaryFactor(ws.factorization)
        ws=JS.SimplexWorkspace((k==:factorization ? factor : getfield(ws,k) for k in fieldnames(typeof(ws)))...)
    end
    return ws
end
function snapshot(ws)
    Dict("primal"=>vecx(ws.primal),"costs"=>vecx(ws.costs),"prices"=>vecx(ws.reduced_costs),
      "basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"iterations"=>ws.iterations,
      "refactorizations"=>ws.refactorizations,"rejected_rows"=>copy(ws.scratch.rejected_rows),
      "rejected_entering"=>copy(ws.scratch.rejected_entering),"updates"=>length(ws.factorization.updates))
end
kernels(d)=Dict(string(k)=>get(d.kernel_calls,k,0) for k in (:ftran,:btran,:refactorization))
delta(after,before)=Dict(k=>after[k]-before[k] for k in keys(before))
function expected(mode)
    refresh=mode==:after_refresh
    Dict("ftran"=>2+refresh,"prepared"=>2,"ordinary"=>Int(refresh),"btran"=>3+refresh,
      "unit"=>2,"correction"=>1,"cost"=>Int(refresh),"metadata"=>2,"invalidate"=>4+2refresh,
      "refactor"=>Int(refresh),"update"=>0,"copy"=>0,"hits"=>2)
end
const RECORDS=Dict{String,Any}[]
const GLOBALS=(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
@assert GLOBALS==(256,RoundNearest,RoundNearest,false) && Threads.nthreads()==BLAS.get_num_threads()==1
@assert !ispath(only(ARGS))
function run_case(manager,mode)
    rejected=Ref(0);cancelled=Ref(false);live=Ref{Any}(nothing);events=Dict{String,Any}[]
    observer=(event,ws)->begin
        if !isnothing(live[])
            push!(events,Dict("event"=>string(event),"snapshot"=>snapshot(ws),
                "same_factor"=>ws.factorization===live[].factorization,
                "staged"=>JS._is_staged_workspace(ws),
                "counts"=>mode==:control ? Dict{String,Int}() : counts(ws.factorization)))
            if mode==:after_refresh
                event==:refactor_pivot && (cancelled[]=true)
            elseif event==:pivot_rejected
                rejected[]+=1
                mode==:cancelled && (cancelled[]=true)
                mode==:callback_error && error("rejected pivot observer")
                mode==:numerical_callback_error && throw(SingularException(7))
            end
        end
        nothing
    end
    policy=mode in (:control,:after_refresh) ? JS.NumericalPolicy(Float64) :
        JS.NumericalPolicy(Float64;max_pivot_candidates=mode==:cancelled ? 2 : 1,max_recovery_rounds=0)
    @assert !policy.hypersparse && !policy.solve_refinement && !policy.recovery && !policy.pivot_validation
    diagnostics=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    ws=fixture(manager,policy,diagnostics;wrapped=mode!=:control);live[]=ws
    before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),copy(ws.basis.states),
            copy(ws.basis.basic_indices),ws.iterations,ws.refactorizations)
    before_refresh=before[1:5]
    refs=ws.refactorizations
    initial=snapshot(ws);setup=kernels(diagnostics);factor=ws.factorization
    model_before=fields(ws.problem)
    rec=Dict{String,Any}("manager"=>string(manager),"mode"=>string(mode),"before"=>initial,
      "options"=>fields(ws.options),"policy"=>fields(policy),"setup_kernels"=>setup,"events"=>events,"error"=>"none")
    push!(RECORDS,rec)
    # This is the public production entry; observer exceptions are retained as values
    # so every original assertion can be evaluated with a single iteration per case.
    result=try JS.dual_iteration!(ws,()->cancelled[]) catch e; e end
    rec["after"]=snapshot(ws);rec["kernels"]=delta(kernels(diagnostics),setup)
    rec["status"]=result isa JS.DualTermination ? string(result.status) : "none"
    rec["result_type"]=string(typeof(result));rec["message"]=result isa Exception ? sprint(showerror,result) : result isa JS.DualTermination ? result.message : "nothing"
    rec["rejected"]=rejected[];rec["factor_identity"]=ws.factorization===factor
    rec["counts"]=mode==:control ? Dict{String,Int}() : counts(factor)
    rec["calls"]=mode==:control ? Dict{String,Any}[] : factor.calls
    rec["cancelled"]=cancelled[]
    rec["model_preserved"]=fields(ws.problem)==model_before && ws.problem.A==hcat(B,B[:,1])
    rec["row_lower"]=string.(ws.problem.row_lower);rec["row_upper"]=string.(ws.problem.row_upper)
    @testset "$manager $mode" begin
        if mode==:control
            @test result isa JS.DualTermination && result.status==JS.INFEASIBLE
            @test ws.basis.basic_indices==collect(1:4) && ws.primal==vcat(-UNIT,0.0,PRIMAL)
            @test ws.iterations==0 && ws.refactorizations==refs+1
            @test rejected[]==0 && get(diagnostics.counts,:pivot_completed,0)==0
            @test rec["kernels"]==Dict("ftran"=>1,"btran"=>3,"refactorization"=>1)
        elseif mode==:after_refresh
            terminal=result
            @test terminal.status==JSimplex.TIME_LIMIT
            @test before_refresh==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,ws.basis.basic_indices)
            @test ws.iterations==0
            @test ws.refactorizations==refs+1
            @test get(diagnostics.counts,:pivot_completed,0)==0
            @test get(diagnostics.counts,:bound_flipped,0)==0
            @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
        else
            if mode==:callback_error
                @test_throws JSimplex.DiagnosticObserverFailure{ErrorException} (result isa Exception ? throw(result) : result)
            elseif mode==:numerical_callback_error
                @test_throws JSimplex.DiagnosticObserverFailure{SingularException} (result isa Exception ? throw(result) : result)
            else
                terminal=result
                @test terminal.status==(mode==:cancelled ? JSimplex.TIME_LIMIT : JSimplex.NUMERICAL_ERROR)
            end
            @test rejected[]==1
            @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,
                           ws.basis.basic_indices,ws.iterations,ws.refactorizations)
            @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
            @test isempty(ws.factorization.updates)
        end
        if mode!=:control
            @test rec["counts"]==expected(mode)
            @test rec["kernels"]==Dict("ftran"=>expected(mode)["ftran"],"btran"=>expected(mode)["btran"],"refactorization"=>expected(mode)["refactor"])
            @test all(e["same_factor"] for e in events) && any(e["staged"] for e in events)
            @test rec["factor_identity"] && ws.primal==vcat(-UNIT,0.0,PRIMAL) && ws.basis.basic_indices==collect(1:4)
            @test count(e->e["event"]=="correction_attempt",events)==1 && count(e->e["event"]=="pivot_rejected",events)==1
            @test [c["kind"] for c in factor.calls]==(mode==:after_refresh ? ["unit","prepared","unit","prepared","correction","ordinary","cost"] : ["unit","prepared","unit","prepared","correction"])
            negative=copy(rec["counts"]);negative["unit"]+=1;negative["btran"]+=1
            rec["negative_counts"]=negative
            @test negative!=expected(mode) && negative["hits"]==rec["counts"]["hits"]
        end
    end
end
try
    @testset "Public dual dyadic boundary qualification" begin
        for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
            run_case(manager,:control)
        end
        for mode in (:exhausted,:cancelled,:callback_error,:numerical_callback_error,:after_refresh),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
            run_case(manager,mode)
        end
        @test (precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())==GLOBALS
    end
finally
    open(only(ARGS),"w") do io
        TOML.print(io,Dict("source"=>pathof(JS),"input_sha256"=>bytes2hex(sha256(read(INPUT))),"input"=>DATA,
          "test_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"test/dual_pivot_consistency_tests.jl")))),
          "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
          "globals_preserved"=>(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())==GLOBALS,
          "records"=>RECORDS))
    end
end
