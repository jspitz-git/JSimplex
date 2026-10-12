using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const C=Float64[1,1,0,0,0,0]
const BAD=Float64[1,1,2.0^-40,0,0,0]
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/legacy_primal_direction_price_tests.jl")
const SOURCE=read(FILE,String)
const TITLE="A repeated price disagreement cannot renew the recovery budget"
const ORIGINAL="@testset \""*TITLE*"\" begin"*first(split(split(SOURCE,"@testset \""*TITLE*"\" begin";limit=2)[2],"\n@testset";limit=2))
const ASSERTIONS=join(filter(l->startswith(strip(l),"@test "),split(ORIGINAL,'\n')),"\n")
@assert count("@test ",ASSERTIONS)==5
Base.include_string(@__MODULE__,"function original_oracle(ws,result,diagnostics)\n"*ASSERTIONS*"\nend",FILE)
mutable struct PriceBoundaryFactor{F}
    inner::F
    armed::Bool
    hits::Int
    calls::Vector{Dict}
end
Base.getproperty(f::PriceBoundaryFactor,n::Symbol)=n in fieldnames(typeof(f)) ? getfield(f,n) : getproperty(getfield(f,:inner),n)
function JS.transpose_solve!(dest::Vector{Float64},f::PriceBoundaryFactor,rhs::AbstractVector)
    input=collect(rhs)
    JS.transpose_solve!(dest,f.inner,rhs)
    raw=copy(dest)
    cost=input==C
    injected=f.armed && cost
    if injected
        f.armed=false;f.hits+=1;copyto!(dest,BAD)
    end
    push!(f.calls,Dict("kind"=>"btran","cost_rhs"=>cost,"rhs"=>input,"raw"=>raw,"output"=>copy(dest),"injected"=>injected))
    dest
end
function JS.forward_solve!(dest::Vector{Float64},f::PriceBoundaryFactor,rhs::AbstractVector)
    input=collect(rhs);JS.forward_solve!(dest,f.inner,rhs)
    push!(f.calls,Dict("kind"=>"ftran","rhs"=>input,"output"=>copy(dest)));dest
end
function JS._ordinary_forward_solve!(dest::Vector{Float64},f::PriceBoundaryFactor,rhs::AbstractVector)
    input=collect(rhs);JS._ordinary_forward_solve!(dest,f.inner,rhs)
    push!(f.calls,Dict("kind"=>"ordinary_ftran","rhs"=>input,"output"=>copy(dest)));dest
end
JS._invalidate_prepared_destination!(f::PriceBoundaryFactor,dest)=JS._invalidate_prepared_destination!(f.inner,dest)
JS._finite_updated_factor(f::PriceBoundaryFactor)=JS._finite_updated_factor(f.inner)
JS.refactorize!(f::PriceBoundaryFactor,B::AbstractMatrix)=JS.refactorize!(f.inner,B)
JS.replace_column!(f::PriceBoundaryFactor,direction::AbstractVector,row::Integer;kwargs...)=JS.replace_column!(f.inner,direction,row;kwargs...)
JS.copy_basis_factorization(f::PriceBoundaryFactor)=PriceBoundaryFactor(JS.copy_basis_factorization(f.inner),f.armed,f.hits,deepcopy(f.calls))
function snapshot(ws)
    ws isa JS.SimplexWorkspace || return Dict("workspace"=>false,"type"=>string(typeof(ws)))
    Dict("workspace"=>true,"primal"=>copy(ws.primal),"costs"=>copy(ws.costs),"prices"=>copy(ws.reduced_costs),"rho"=>copy(ws.scratch.rho),"basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,"updates"=>length(ws.factorization.updates),"rejected"=>copy(ws.scratch.rejected_entering),"selected_row"=>ws.scratch.selected_row,"selected_entering"=>ws.scratch.selected_entering)
end
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
function fixture(manager,mode,d)
    B=Matrix{Float64}(I,6,6);unit=B[:,3:6]
    A=sparse(hcat(B,unit,-unit,zeros(6)))
    costs=vcat(C,zeros(9));rhs=ones(6)
    p=LinearProblem(A,costs;row_lower=rhs,row_upper=rhs,column_upper=vcat(fill(Bound{Float64}(nothing),14),Bound(1.0)))
    options=SolverOptions(Float64;algorithm=:primal,basis_update=manager,verbose=false)
    policy=JS.NumericalPolicy(Float64;max_refinements=3)
    ws=JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
    ws.basis=JS.Basis(collect(1:6),vcat(fill(JS.BASIC,6),fill(JS.AT_LOWER,15)))
    JS.recompute!(ws;refactorize=true)
    ws.primal.=vcat(ones(6),zeros(9),rhs)
    if mode!=:exact
        copyto!(ws.scratch.rho,BAD)
        JS._recompute_reduced_costs!(ws.reduced_costs,ws,BAD)
        JS._pipeline_changed!(ws,ws.scratch.rho)
        JS._invalidate_pricing_pool!(ws;basis=false)
    end
    @assert !policy.hypersparse
    f=PriceBoundaryFactor(ws.factorization,mode==:subject,0,Dict[])
    wrapped=JS.SimplexWorkspace((name==:factorization ? f : getfield(ws,name) for name in fieldnames(typeof(ws)))...)
    return wrapped,A
end
function counts(f)
    b=filter(c->c["kind"]=="btran",f.calls)
    Dict("cost"=>count(c->c["cost_rhs"],b),"correction"=>count(c->!c["cost_rhs"],b),"btran"=>length(b),"ftran"=>count(c->c["kind"] in ("ftran","ordinary_ftran"),f.calls),"hits"=>f.hits)
end
budget(c)=c["cost"]==1 && c["correction"]==1 && c["btran"]==2
old_values(ws,result,d)=[!isnothing(result)&&result.status==NUMERICAL_ERROR,JS.event_count(d,:primal_prices_corrected)==1,JS.event_count(d,:correction_attempt)==1,ws.iterations==0,isempty(ws.scratch.rejected_entering)]
records=Dict[];initial_precision=precision(BigFloat);initial_rounding=rounding(BigFloat)
@assert !ispath(only(ARGS))
try
 @testset "Price boundary qualification" begin
  for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), mode in (:exact,:seed,:subject)
    events=Dict[]
    d=JS.SimplexDiagnostics(;kernel_timing=true,observer=(event,ws)->begin
        push!(events,Dict("event"=>string(event),"boundary"=>"before_injection","state"=>snapshot(ws)))
        event==:primal_prices_corrected && (ws.reduced_costs[7]=-1.0)
        event==:primal_prices_corrected && push!(events,Dict("event"=>string(event),"boundary"=>"after_injection","state"=>snapshot(ws)))
        nothing
    end)
    ws,A=fixture(manager,mode,d);before=snapshot(ws);start_event=length(events);kernels=copy(d.kernel_calls)
    result=JS._primal_iteration!(ws,()->false,0.0)
    after=snapshot(ws);c=counts(ws.factorization)
    rec=Dict("manager"=>string(manager),"mode"=>string(mode),"before"=>before,"after"=>after,"A_rows"=>[collect(A[i,:]) for i in axes(A,1)],"options"=>fields(ws.options),"policy"=>fields(ws.progress.numerical_policy),"status"=>string(result.status),"message"=>result.message,"calls"=>deepcopy(ws.factorization.calls),"work"=>c,"events"=>deepcopy(events[start_event+1:end]),"counts"=>Dict(string(k)=>v for (k,v) in d.counts),"kernels"=>Dict(string(k)=>v-kernels[k] for (k,v) in d.kernel_calls),"old_oracle"=>old_values(ws,result,d))
    push!(records,rec)
    @test all(before[k]==after[k] for k in ("primal","costs","basis","states","iterations","refactorizations","updates"))
    @test all(call["rhs"]==get(call,"raw",call["output"]) for call in rec["calls"])
    @test isempty(ws.scratch.rejected_entering)
    if mode==:subject
        original_oracle(ws,result,d)
        @test budget(c)
        @test c["hits"]==1
        @test after["rho"]==C
        @test only(filter(call->call["kind"]=="btran"&&!call["cost_rhs"],rec["calls"]))["rhs"]==C-BAD
        # Deliberately call the exhausted recovery boundary after immutable subject
        # snapshots. This is NOT another iteration or a production budget mutation.
        event_count=length(events);old=old_values(ws,result,d)
        extra=JS._try_native_primal_price_recovery!(ws,()->false)
        nc=counts(ws.factorization)
        rec["negative"]=Dict("extra_return"=>extra,"work"=>nc,"old_oracle"=>old_values(ws,result,d),"new_budget_oracle"=>budget(nc),"calls"=>deepcopy(ws.factorization.calls),"after"=>snapshot(ws),"new_events"=>length(events)-event_count)
        @test !extra
        @test old_values(ws,result,d)==old && all(old)
        @test !budget(nc)
        @test nc["cost"]==2 && nc["correction"]==1 && nc["btran"]==3 && nc["hits"]==1
        @test snapshot(ws)==after && length(events)==event_count
    else
        @test result.status==(mode==:exact ? OPTIMAL : NUMERICAL_ERROR)
        @test c["cost"]==(mode==:exact ? 0 : 1)
        @test c["correction"]==c["hits"]==0
        @test JS.event_count(d,:correction_attempt)==JS.event_count(d,:primal_prices_corrected)==0
    end
  end
 end
finally
 open(only(ARGS),"w") do io
    TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),"original_source"=>ORIGINAL,"original_assertions"=>ASSERTIONS,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>precision(BigFloat)==initial_precision&&rounding(BigFloat)==initial_rounding,"records"=>records))
 end
end
