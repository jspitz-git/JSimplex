using Test, LinearAlgebra, SparseArrays, Serialization, SHA, TOML, Libdl, Profile
using JSimplex
include(joinpath(@__DIR__,"vendor/KLU/src/KLU.jl"))
include(joinpath(@__DIR__,"export.jl"))
include(joinpath(@__DIR__,"ftran.jl"))
include(joinpath(@__DIR__,"candidate.jl"))
include(joinpath(@__DIR__,"consumer.jl"))
const D=@__DIR__
function digestarrays(a...)
    io=IOBuffer();for v in a;write(io,Int(length(v)));write(io,v);end;bytes2hex(sha256(take!(io)))
end
matrixhash(B)=digestarrays(B.colptr,B.rowval,B.nzval)
function assemble(A,basis)
    n,m=size(A);ptr=Int[1];rows=Int[];vals=Float64[]
    for e in basis
        if e<=m
            for k in nzrange(A,e);push!(rows,A.rowval[k]);push!(vals,A.nzval[k]);end
        else
            1<=e-m<=n || error("artificial basis column");push!(rows,e-m);push!(vals,-1.)
        end
        push!(ptr,length(rows)+1)
    end
    SparseMatrixCSC(n,n,ptr,rows,vals)
end
function stat(t)
    Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
mutable struct StopProbe
    calls::Int
    limit::Int
    error::Union{Nothing,Exception}
end
function (s::StopProbe)()
    s.calls+=1
    if s.calls>=s.limit
        isnothing(s.error)||throw(s.error)
        return true
    end
    false
end
function trial_for(problem,basis,ctx)
    n,N=size(problem.A);options=JSimplex.SolverOptions(Float64;algorithm=:dual,pricing=:steepest_edge,simplex_strategy=:legacy,verbose=false,time_limit=Inf)
    progress=JSimplex.SimplexProgressContext(problem;numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    states=fill(JSimplex.FREE_NONBASIC,n+N);states[basis].=JSimplex.BASIC
    factor=WeightFactor(ctx,JSimplex.PackedEta{Float64}[],0)
    JSimplex.SimplexWorkspace(problem,options,progress,zeros(n+N),vcat(problem.column_lower,problem.row_lower),vcat(problem.column_upper,problem.row_upper),JSimplex.Basis(basis,states),zeros(n+N),zeros(n+N),ones(n+N),falses(n+N),factor,JSimplex.SimplexScratch(Float64,n,n+N),0,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
end
function model_for(A)
    # Only an algebraic workspace holder: original captured matrix, no optimization/LP trajectory.
    JSimplex.LinearProblem(A,zeros(size(A,2));column_lower=fill(nothing,size(A,2)),name="captured-basis-weight-harness")
end
partshash(b)=b.forward isa GraphContext ? digestarrays(values(b.forward.parts)...) : "native-only"
function indexhash(b)
    digestarrays(b.inverseQ,b.rowptr,b.positions,b.columns,b.weights)
end
function memory(b)
    c=b.forward
    shared=c isa GraphContext ? sum(sizeof,values(c.parts))+sum(sizeof,(c.rowpos,c.block,c.weights,c.work,c.marks,c.heap,c.rhs)) : sizeof(c.rhs)
    reverse=sum(sizeof,(b.inverseQ,b.rowptr,b.positions,b.columns,b.weights,b.paths))
    Dict("shared_export_scratch_payload_bytes"=>shared,"transpose_index_payload_bytes"=>reverse,"context_julia_graph_bytes"=>Base.summarysize(b),"native_reported_bytes"=>Int(c.native.common.memusage),"graph_eligible"=>c isa GraphContext)
end
function reset_probe!(trial,stop)
    stop.calls=0;trial.factorization.generic_calls=0;fill!(trial.factorization.ctx.paths,0)
end
function kernels!(dest,rhs,b,rows,mode)
    checksum=0.
    for row in rows
        unit_btran!(dest,b,rhs,row,mode);checksum+=dest[row]
    end
    checksum
end
function residual(B,x,rhs,bnorm)
    all(isfinite,x)||return Inf
    norm(transpose(B)*x-rhs,Inf)/max(1.0,bnorm*norm(x,Inf),norm(rhs,Inf))
end
function microtests()
    n=40;B=spdiagm(0=>[2.0+mod(i,3) for i in 1:n],1=>fill(.125,n-1))
    b,_=prepare_staged(B;minimum_dimension=0);r,_=prepare_staged(B;minimum_dimension=typemax(Int));x=zeros(n);y=zeros(n);z=zeros(n);rhs=zeros(n);other=zeros(n)
    @test b.forward isa GraphContext
    unit_btran!(x,b,rhs,1,Val(:local));@test b.forward.last_path==4 && b.forward.last_blocks>0
    unit_btran!(x,b,rhs,n,Val(:local));@test b.forward.last_path==1 && b.forward.last_blocks==1
    @test x[n]==1/B[n,n]
    unit_btran!(y,b,other,n,Val(:full));@test x==y
    before=partshash(b);ih=indexhash(b);b.forward.epoch=typemax(UInt32)
    unit_btran!(x,b,rhs,n,Val(:local));@test b.forward.epoch==1
    column_ftran!(x,b.forward,B,n,Val(:local));@test norm(B*x-Vector(B[:,n]),Inf)<1e-12
    unit_btran!(x,b,rhs,n,Val(:local));unit_btran!(y,r,other,n,Val(:native));@test x==y
    @test before==partshash(b) && ih==indexhash(b)
    @test_throws ArgumentError unit_btran!(b.forward.work,b,rhs,n,Val(:local))
    @test_throws ArgumentError unit_btran!(x,b,b.forward.rhs,n,Val(:local))
    @test_throws ArgumentError unit_btran!(x,b,x,n,Val(:local))
    owner=ones(n+1)
    GC.@preserve owner begin
        a=unsafe_wrap(Vector{Float64},pointer(owner),n;own=false);d=unsafe_wrap(Vector{Float64},pointer(owner)+8,n;own=false)
        @test_throws ArgumentError unit_btran!(d,b,a,n,Val(:local));@test all(==(1.0),owner)
    end
    @test_throws BoundsError unit_btran!(x,b,rhs,0,Val(:local))
    @test_throws SingularException replace_bbase!(b,spzeros(n,n))
    @test b.valid && b.forward.valid && before==partshash(b)
    replace_bbase!(b,2B);unit_btran!(x,b,rhs,n,Val(:local));@test b.forward.last_path==6 && x[n]==.5/B[n,n]
    b2,_=prepare_staged(B;minimum_dimension=0);@test !overlaps(b.forward.work,b2.forward.work)
    generic_btran!(x,b2,ones(n));generic_btran!(y,r,ones(n));@test all(isapprox.(x,y;rtol=1e-12,atol=1e-12)) && b2.forward.last_path==3
    bad=copy(x);bad[1]+=1;@test residual(B,bad,ones(n),opnorm(B,1))>1e-5
    for value in (Inf,NaN)
        q=zeros(n);q[1]=value;generic_btran!(x,b2,q);generic_btran!(y,r,q);@test all(isequal.(x,y))
    end
    tiny=spdiagm(0=>fill(1e-308,n));tb,_=prepare_staged(tiny;minimum_dimension=0)
    unit_btran!(x,tb,rhs,n,Val(:local));@test isfinite(x[n]) && x[n]>1e307
    overflowB=spdiagm(0=>fill(1e-309,n));ob,_=prepare_staged(overflowB;minimum_dimension=0);orr,_=prepare_staged(overflowB;minimum_dimension=typemax(Int))
    unit_btran!(x,ob,rhs,n,Val(:local));unit_btran!(y,orr,other,n,Val(:native));@test ob.forward.last_path==5 && all(isequal.(x,y))
    problem=model_for(B);basis=collect(1:n);tr=trial_for(problem,basis,r);tc=trial_for(problem,basis,b2);s=StopProbe(0,typemax(Int),nothing)
    @test original_weights!(tr,s);original_calls=s.calls;s.calls=0
    @test weights!(tc,1:n,s,Val(:local));@test s.calls==original_calls
    @test all(isapprox.(tr.pricing_weights[basis],tc.pricing_weights[basis];rtol=1e-10,atol=1e-12))
    for trial in (tr,tc)
        fill!(trial.pricing_weights,-1.0);stop=StopProbe(0,2,nothing)
        @test !weights!(trial,1:n,stop,Val(:local));@test trial.pricing_weights[1]>0 && trial.pricing_weights[2]==-1.0 && stop.calls==2
        sentinel=ErrorException("weight-stop-sentinel");stop=StopProbe(0,1,sentinel);caught=nothing
        try;weights!(trial,1:n,stop,Val(:local));catch e;caught=e;end
        @test caught===sentinel && stop.calls==1
    end
end
function prep_samples!(B,id,result,minimum)
    for round in 1:5
        for arm in mod1.(collect(1:3).+round,3)
            if arm==1
                t=@timed prepare_staged(B;minimum_dimension=typemax(Int));b,stages=t.value;name="native-staged"
            elseif arm==2
                t=@timed prepare_staged(B;minimum_dimension=minimum);b,stages=t.value;name="shared-staged"
            else
                t=@timed prepare(B;minimum_dimension=minimum);b=t.value;stages=(;);name="original-FTRAN-unsplit"
            end
            if round>2
                record=merge(stat(t),Dict("case"=>id,"arm"=>name,"round"=>round-2,"stages"=>Dict(string(k)=>stat(v) for (k,v) in pairs(stages))))
                push!(result["setup"],record)
            end
        end
        GC.gc()
    end
end
function inclusive!(problem,basis,rows,minimum,mode)
    B=assemble(problem.A,basis)
    b,_=prepare_staged(B;minimum_dimension=minimum)
    trial=trial_for(problem,basis,b);stop=StopProbe(0,typemax(Int),nothing)
    ok=weights!(trial,rows,stop,mode)
    (ok=ok,stop_calls=stop.calls,paths=copy(b.paths),generic_calls=trial.factorization.generic_calls,weights=trial.pricing_weights[basis[rows]])
end
function qualify_case(B,A,basis,id,result;minimum=4096)
    n=size(B,1);rows=unique([1+fld(i*(n-1),min(n,128)-1) for i in 0:min(n,128)-1]);ah=matrixhash(A);bh=matrixhash(B)
    mt=@timed model_for(A);problem=mt.value
    push!(result["preparation"],merge(stat(mt),Dict("case"=>id,"stage"=>"algebraic-model-holder")))
    r,_=prepare_staged(B;minimum_dimension=typemax(Int));f,_=prepare_staged(B;minimum_dimension=minimum);l,_=prepare_staged(B;minimum_dimension=minimum)
    original=prepare(B;minimum_dimension=minimum)
    @test (original isa NativeOnly)==(l.forward isa NativeOnly)
    if original isa GraphContext
        @test digestarrays(values(original.parts)...)==partshash(l)
        @test original.block==l.forward.block && original.weights==l.forward.weights && original.rowpos==l.forward.rowpos
    end
    original=nothing
    @test !overlaps(r.forward.rhs,l.forward.rhs) && !overlaps(f.forward.rhs,l.forward.rhs)
    if l.forward isa GraphContext
        p=l.forward.parts
        @test p.Q[l.inverseQ]==collect(1:n) && sum(l.weights)==l.forward.fullweight
        @test l.rowptr[1]==1 && l.rowptr[end]==length(p.Fi)+1
        @test sort(l.positions)==collect(1:length(p.Fi))
        @test all(p.Fi[l.positions[k]]==i && p.Fp[l.columns[k]]<=l.positions[k]<p.Fp[l.columns[k]+1] for i in 1:n for k in l.rowptr[i]:l.rowptr[i+1]-1)
    end
    wt=@timed (trial_for(problem,basis,r),trial_for(problem,basis,f),trial_for(problem,basis,l));trials=wt.value
    push!(result["preparation"],merge(stat(wt),Dict("case"=>id,"stage"=>"three-independent-weight-workspaces")))
    contexts=(r,f,l);modes=(Val(:native),Val(:full),Val(:local));names=("native","full","local")
    partbefore=[partshash(c) for c in contexts];indexbefore=[indexhash(c) for c in contexts]
    x=zeros(n);y=zeros(n);z=zeros(n);rhs=zeros(n);r2=zeros(n);r3=zeros(n);tol=min(1e-10,128*n*eps(Float64));bnorm=opnorm(B,1);maxres=0.0;maxdelta=0.0;signs=0
    reference=lu(B);directchecks=0
    for (cycle,row) in Iterators.product(1:2,rows)
        unit_btran!(x,r,rhs,row,Val(:native));unit_btran!(y,f,r2,row,Val(:full));unit_btran!(z,l,r3,row,Val(:local))
        for v in (x,y,z);q=residual(B,v,rhs,bnorm);@test q<=tol;maxres=max(maxres,q);end
        delta=norm(x-z,Inf)/max(1.0,norm(x,Inf));@test delta<=1e-6;maxdelta=max(maxdelta,delta)
        if l.forward.last_path==1
            @test all((iszero(a)&&iszero(b))||isequal(a,b) for (a,b) in zip(y,z))
            signs+=count(i->iszero(y[i])&&iszero(z[i])&&signbit(y[i])!=signbit(z[i]),1:n)
        end
        if cycle==1 && row in (rows[1],rows[cld(length(rows),2)],rows[end])
            direct=transpose(reference)\rhs
            @test residual(B,direct,rhs,bnorm)<=tol
            @test norm(x-direct,Inf)/max(1.0,norm(direct,Inf))<=1e-6;directchecks+=1
        end
    end
    reference=nothing;GC.gc()
    stopper=StopProbe(0,typemax(Int),nothing);coldweights=Vector{Vector{Float64}}();coldstops=Int[];coldpaths=Vector{Vector{Int}}()
    for (trial,mode) in zip(trials,modes)
        reset_probe!(trial,stopper);@test weights!(trial,rows,stopper,mode)
        push!(coldweights,copy(trial.pricing_weights[basis[rows]]));push!(coldstops,stopper.calls);push!(coldpaths,copy(trial.factorization.ctx.paths))
        @test all(v->isfinite(v)&&v>0,coldweights[end])
    end
    @test all(isapprox.(coldweights[1],coldweights[2];rtol=1e-6,atol=1e-12))
    @test all(isapprox.(coldweights[1],coldweights[3];rtol=1e-6,atol=1e-12))
    @test coldstops[1]==coldstops[2]==coldstops[3]
    record=Dict("id"=>id,"n"=>n,"columns"=>size(A,2),"B_nnz"=>nnz(B),"matrix_hash"=>bh,"rows"=>rows,"sample_rows"=>length(rows),"scope"=>"sampled whole weight handling, not full rebuild","tolerance"=>tol,"max_scaled_residual"=>maxres,"max_native_relative_difference"=>maxdelta,"signed_zero_differences"=>signs,"direct_UMFPACK_checks"=>directchecks,"cold_weights"=>coldweights,"cold_stops"=>coldstops,"cold_paths"=>coldpaths,"memory"=>Dict(names[i]=>memory(contexts[i]) for i in 1:3),"policy"=>Dict(string(k)=>getfield(trials[1].progress.numerical_policy,k) for k in fieldnames(typeof(trials[1].progress.numerical_policy))),"samples"=>Any[],"kernel_samples"=>Any[],"inclusive_samples"=>Any[])
    for round in 1:7
        for arm in mod1.(collect(1:3).+round,3)
            trial=trials[arm];mode=modes[arm];b=contexts[arm];reset_probe!(trial,stopper)
            t=@timed weights!(trial,rows,stopper,mode);@test t.value
            if round>2
                @test t.compile_time==0 && t.recompile_time==0
                @test all(isapprox.(coldweights[1],trial.pricing_weights[basis[rows]];rtol=1e-6,atol=1e-12))
                push!(record["samples"],merge(stat(t),Dict("arm"=>names[arm],"round"=>round-2,"unit_calls"=>length(rows),"stop_calls"=>stopper.calls,"paths"=>copy(b.paths),"generic_correction_calls"=>trial.factorization.generic_calls)))
            end
            fill!(b.paths,0);kt=@timed kernels!(x,rhs,b,rows,mode)
            if round>2
                @test kt.compile_time==0 && kt.recompile_time==0
                push!(record["kernel_samples"],merge(stat(kt),Dict("arm"=>names[arm],"round"=>round-2,"unit_calls"=>length(rows),"checksum"=>kt.value,"paths"=>copy(b.paths))))
            end
        end
        round==2&&GC.gc()
    end
    for round in 1:4
        for arm in mod1.(collect(1:3).+round,3)
            limit=arm==1 ? typemax(Int) : minimum
            t=@timed inclusive!(problem,basis,rows,limit,modes[arm]);@test t.value.ok
            @test all(isapprox.(coldweights[1],t.value.weights;rtol=1e-6,atol=1e-12))
            if round>1
                @test t.compile_time==0 && t.recompile_time==0
                push!(record["inclusive_samples"],merge(stat(t),Dict("arm"=>names[arm],"round"=>round-1,"unit_calls"=>length(rows),"stop_calls"=>t.value.stop_calls,"paths"=>t.value.paths,"generic_correction_calls"=>t.value.generic_calls)))
            end
        end
        GC.gc()
    end
    prep_samples!(B,id,result,minimum)
    @test matrixhash(A)==ah && matrixhash(B)==bh && matrixhash(problem.A)==ah
    selected=falses(length(trials[1].pricing_weights));selected[basis[rows]].=true
    for trial in trials
        @test trial.basis.basic_indices==basis
        @test all(trial.pricing_weights[i]==1.0 for i in eachindex(selected) if !selected[i])
        @test all(iszero,trial.primal) && all(iszero,trial.reduced_costs) && all(iszero,trial.costs)
        @test trial.progress.numerical_policy==trials[1].progress.numerical_policy
    end
    @test [partshash(c) for c in contexts]==partbefore && [indexhash(c) for c in contexts]==indexbefore
    push!(result["cases"],record)
    println(id," completed; sample=",length(rows)," coldpaths=",coldpaths);flush(stdout)
end
function allocation_profile(B,out)
    # Warm the exact original first; profiler is outside all timings and stage comparisons.
    prepare(B);prepare_staged(B);GC.gc()
    Profile.Allocs.@profile sample_rate=0.01 nothing
    Profile.Allocs.fetch();Profile.Allocs.clear()
    records=Any[]
    for (which,work) in (("original-FTRAN-unsplit",()->prepare(B)),("shared-staged",()->prepare_staged(B)))
        warm=work();warm=nothing;GC.gc()
        Profile.Allocs.clear();value=Profile.Allocs.@profile sample_rate=0.01 work();data=Profile.Allocs.fetch()
        groups=Dict{Tuple{String,String},Tuple{Int,Int}}();traces=Dict{Tuple{String,String},Vector{String}}()
        for alloc in data.allocs
            localframes=[string(fr.func," @ ",fr.file,":",fr.line) for fr in alloc.stacktrace if occursin("klu-weight-btran",String(fr.file))]
            key=(string(alloc.type),isempty(localframes) ? "outside-diagnostic" : first(localframes));num,bytes=get(groups,key,(0,0));groups[key]=(num+1,bytes+alloc.size);traces[key]=localframes[1:min(end,8)]
        end
        detail=[Dict("type"=>k[1],"first_diagnostic_frame"=>k[2],"sampled_events"=>v[1],"sampled_bytes"=>v[2],"diagnostic_stack"=>traces[k]) for (k,v) in groups]
        sort!(detail;by=q->q["sampled_events"],rev=true)
        push!(records,Dict("arm"=>which,"sample_rate"=>0.01,"sampled_events"=>length(data.allocs),"sampled_bytes"=>sum(a.size for a in data.allocs;init=0),"groups"=>detail,"scope"=>"statistical Julia allocation-stack attribution; not complete aggregate/native allocation ledger"))
        value=nothing;data=nothing;Profile.Allocs.clear();GC.gc()
    end
    open(out,"w") do  io;TOML.print(io,Dict("profiles"=>records));end
end
function main(out)
    @assert sizeof(Int)==8 && Threads.nthreads()==1 && BLAS.get_num_threads()==1
    result=Dict{String,Any}("cases"=>Any[],"setup"=>Any[],"preparation"=>Any[],"completed"=>false,"scope"=>"isolated fixed captured matrices, sampled complete weight handling; no LP solve/production integration")
    @testset "Shared KLU unit transpose and weight handling" begin
        microtests()
        for entry in TOML.parsefile(joinpath(D,"inputs.toml"))["cases"]
            entry["structural_only"]&&continue
            @test bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
            load=@timed deserialize(entry["path"]);data=load.value;A=data.A;basis=copy(data.basis);initial=copy(basis);ah=matrixhash(A)
            @test data.input_sha256==entry["input_sha256"] && length(data.steps)>=161
            push!(result["preparation"],merge(stat(load),Dict("case"=>entry["id"],"stage"=>"deserialize")))
            for anchor in (0,80,160)
                if anchor>0;for state in anchor-79:anchor;row,enter=data.steps[state];basis[row]=enter;end;end
                assembly=@timed assemble(A,basis);B=assembly.value
                push!(result["preparation"],merge(stat(assembly),Dict("case"=>entry["id"]*"-B"*string(anchor),"stage"=>"assemble-initial-B")))
                qualify_case(B,A,basis,entry["id"]*"-B"*string(anchor),result)
                if entry["id"]=="runtime-30000"&&anchor==0;allocation_profile(B,joinpath(D,"allocation-profile.toml"));end
                open(out,"w") do  io;TOML.print(io,result);end
                GC.gc()
            end
            @test matrixhash(A)==ah && data.basis==initial
            data=nothing;GC.gc()
        end
        n=64;B=spdiagm(0=>fill(4.0,n),1=>fill(.25,n-1));qualify_case(B,B,collect(1:n),"coupled64-forced",result;minimum=0)
        B=sparse([i==j ? 4.0 : .01/(1+abs(i-j)) for i in 1:n,j in 1:n]);qualify_case(B,B,collect(1:n),"dense64-native-only",result)
        B=spdiagm(0=>fill(4.0,n),1=>fill(.125,n-1),-1=>fill(.125,n-1));qualify_case(B,B,collect(1:n),"irreducible64-native-only",result)
        @test length(result["cases"])==12 && sum(c["sample_rows"] for c in result["cases"])==1344
        @test length(result["setup"])==108
        result["loaded_libraries"]=[realpath(p) for p in Libdl.dllist() if  any(s->occursin(s,basename(p)),("libklu.","libbtf.","libumfpack.","libamd.","libcolamd.","libsuitesparseconfig."))]
        expected=TOML.parsefile(joinpath(D,"library-pins.toml"))["libraries"]
        @test all(p->haskey(expected,p)&&bytes2hex(open(sha256,p))==expected[p],result["loaded_libraries"])
        result["completed"]=true
        open(out,"w") do  io;TOML.print(io,result);end
    end
end
main(abspath(ARGS[1]))
