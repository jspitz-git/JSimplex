# Private optimizer qualification. Setup, plain time and counted validation are separate.
using JSimplex,LinearAlgebra,SparseArrays,TOML,SHA,Logging
include("primal_flip_prototype.jl")
const FA=PrimalFlipPrototype
const JS=JSimplex
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const OUTPUT=only(ARGS)
struct CostContext{C}
    core::C
    reject_all::Bool
end
Base.getproperty(c::CostContext,s::Symbol)=s in (:core,:reject_all) ? getfield(c,s) : getproperty(getfield(c,:core),s)
Base.setproperty!(c::CostContext,s::Symbol,v)=setproperty!(getfield(c,:core),s,v)
function FA._flip_certificate(c::CostContext,ws)
    passed=FA._flip_certificate(c.core,ws)
    return passed && !c.reject_all
end
function fixture(T,kind,history,counted,reject_all)
    m=kind==:sparse ? 256 : 64
    flips=64;k=history
    A=spzeros(T,m,k+flips)
    for j in 1:k
        A[j,j]=one(T)
        # Nontrivial lower coupling in each actual pivot update.
        A[k+j,j]=T(1//8)
    end
    for j in 1:flips
        if kind==:dense
            for i in 1:m; A[i,k+j]=T(1+mod(i+3j,4))/T(1024);end
        else
            for i in unique((1+mod(j-1,m),1+mod(7j,m),1+mod(j-1,max(k,1))))
                A[i,k+j]=T(1//1024)
            end
        end
    end
    costs=vcat(fill(-one(T),k),-T.(flips:-1:1))
    p=JS.LinearProblem(A,costs;row_upper=vcat(fill(T(10),k),fill(T(1000),m-k)),
        column_upper=vcat(fill(nothing,k),fill(one(T),flips)))
    options=JS.SolverOptions(T;algorithm=:primal,pricing=:dantzig,simplex_strategy=:legacy,
        presolve=false,partial_pricing=false,basis_update=:pfi,basis_refactorization=:native,
        refactorization_interval=160,iteration_limit=1000,verbose=false)
    policy=JS.NumericalPolicy(T,options)
    d=counted ? JS.SimplexDiagnostics(;kernel_timing=true) : nothing
    ws=JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
    stop=FA.PF.deadline(ws,d)
    # Owned preparation only: seed real updates before restoring the final costs.
    if k>0
        ws.costs[k+1:k+flips].=zero(T)
        JS.recompute!(ws)
        for j in 1:k
            @assert isnothing(JS._primal_iteration!(ws,stop,options.dual_tolerance))
        end
        @assert length(ws.factorization.updates)==k
        @assert all(i in ws.basis.basic_indices for i in 1:k)
        ws.costs[1:k+flips].=costs
        JS.recompute!(ws)
    end
    @assert FA.eligible_run(ws) && JS._primal_feasible(ws)
    if counted
        for key in keys(d.kernel_calls);d.kernel_calls[key]=0;d.kernel_nanoseconds[key]=0;end
        for key in keys(d.counts);d.counts[key]=0;end
        empty!(d.events);d.next_event=1
    end
    ctx=CostContext(FA.FlipAuditContext(ws),reject_all)
    return (;p,ws,d,stop,ctx,flips,k,initial_iteration=ws.iterations,
        basis=copy(ws.basis.basic_indices),prices=copy(ws.reduced_costs))
end
function optimize(f,::Val{candidate}) where candidate
    candidate ? FA._flip_optimize!(f.ctx,f.ws,f.stop,f.ws.options.dual_tolerance;perturb_degenerate=false) :
        JS._primal_optimize!(f.ws,f.stop,f.ws.options.dual_tolerance;perturb_degenerate=false)
end
function validate(f,terminal,candidate)
    retained_after=Base.summarysize(f.ws.scratch.primal_point_buffers)
    calls=isnothing(f.d) ? Dict{String,Int}() : Dict(string(k)=>v for (k,v) in f.d.kernel_calls)
    @assert terminal.status==JS.OPTIMAL
    @assert f.ws.iterations-f.initial_iteration==f.flips
    @assert f.ws.basis.basic_indices==f.basis && f.ws.reduced_costs==f.prices
    @assert length(f.ws.factorization.updates)==f.k
    @assert all(==(one(eltype(f.ws.primal))),f.ws.primal[f.k+1:f.k+f.flips])
    @assert !candidate || (!f.ctx.dirty && f.ctx.applied==f.flips && f.ctx.audits==f.flips)
    run=JS._internal_solution(f.ws,terminal)
    @assert run.status==JS.OPTIMAL && JS._original_primal_feasible(f.p,run.primal,f.ws.options.primal_tolerance)
    @assert JS._legacy_primal_point_certified(f.ws)
    expected=candidate && !f.ctx.reject_all ? 1 : f.flips
    if !isnothing(f.d)
        @assert calls["ftran"]==f.flips+expected && calls["btran"]==expected
        @assert JS.event_count(f.d,:flip_completed)==f.flips
        @assert JS.event_count(f.d,:pivot_completed)==0
    end
    return Dict{String,Any}("primal_hash"=>bytes2hex(sha256(reinterpret(UInt8,run.primal))),
        "objective"=>Float64(run.objective_value),"kernel_calls"=>calls,"flips"=>f.flips,
        "audits"=>f.ctx.audits,"skips"=>f.ctx.skips,"fallbacks"=>f.ctx.fallbacks,
        "direct_recomputations"=>f.ctx.direct_recomputations,"candidate_copies"=>f.ctx.candidate_copies,
        "endpoint_refreshes"=>f.ctx.endpoint_refreshes,
        "point_buffer_retained_bytes"=>retained_after)
end
metric(m)=Dict{String,Any}("seconds"=>m.time,"bytes"=>m.bytes,"allocations"=>Base.gc_alloc_count(m.gcstats),
    "compile_seconds"=>m.compile_time,"gc_seconds"=>m.gctime)
function sample(T,kind,k,reject,candidate,counted)
    setup=@timed fixture(T,kind,k,counted,reject)
    f=setup.value
    retained_before=Base.summarysize(f.ws.scratch.primal_point_buffers)
    GC.gc(true)
    measured=@timed optimize(f,Val(candidate))
    # Numerical hashes, certificates and allocation traversal are outside the timed region.
    evidence=validate(f,measured.value,candidate)
    merge!(evidence,Dict("setup"=>metric(setup),"optimizer"=>metric(measured),
        "point_buffer_before_bytes"=>retained_before,"type"=>string(T),"matrix"=>string(kind),
        "rows"=>size(f.p.A,1),"columns"=>size(f.p.A,2),"nnz"=>nnz(f.p.A),
        "history"=>k,"reject_all"=>reject,"variant"=>candidate ? "candidate" : "control","counted"=>counted))
    return evidence
end
function main()
    samples=Dict[];warmups=Dict[]
    try
        with_logger(NullLogger()) do
            for T in (Float32,Float64),kind in (:sparse,:dense),k in (0,8),reject in (false,true)
                # Compile both variants and diagnostics shapes; keep these separate.
                for counted in (false,true),candidate in (false,true)
                    push!(warmups,sample(T,kind,k,reject,candidate,counted))
                end
                for pair in 1:3
                    order=isodd(pair) ? (false,true) : (true,false)
                    for candidate in order
                        row=sample(T,kind,k,reject,candidate,false);row["pair"]=pair;push!(samples,row)
                    end
                end
                # Counted workload is distinct from plain elapsed, one paired observation.
                for candidate in (false,true)
                    row=sample(T,kind,k,reject,candidate,true);row["pair"]=0;push!(samples,row)
                end
                println("Qualified ",T," ",kind," history=",k," reject=",reject);flush(stdout)
            end
        end
    finally
        open(io->TOML.print(io,Dict("samples"=>samples,"warmups"=>warmups,
            "source_hashes"=>FA.SOURCE_HASHES,"rewritten_hashes"=>FA.REWRITTEN_HASHES,
            "semantics"=>"setup separate; 3 interleaved plain pairs; counted pair separate; certificates and hashes outside timing; fixed 64-flip workload")),OUTPUT,"w")
    end
end
main()
