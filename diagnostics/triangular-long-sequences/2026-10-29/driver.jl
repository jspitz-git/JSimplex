using JSimplex,Test,LinearAlgebra,SparseArrays,Statistics,TOML,SHA
const J=JSimplex
const D=@__DIR__
@assert realpath(pathof(J))=="/home/jspitz/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
@assert !isdefined(J,:DirectLowerBackend)
Base.include(J,joinpath(D,"factor-export.jl"))
Base.include(J,joinpath(D,"direct-factor.jl"))

policy(::Val{:native})=J._NATIVE_PIVOT_ONE
policy(::Val{:markowitz})=J._NATIVE_PIVOT_DEFAULT
const MANAGERS=(J.ForrestTomlinFactorization,J.SuhlSuhlFactorization,J.BartelsGolubFactorization)
const LABELS=("FT","SS","BG")
function makecase(kind,n=64)
    pool=Vector{Float64}[];nz=Vector{Int}[]
    for variant in 0:2,j in 1:n
        col=zeros(n);col[j]=8
        for i in 1:n
            i==j && continue
            keep=kind=="band" ? abs(i-j)<=2+variant :
                 kind=="blocks" ? (div(i-1,8)==div(j-1,8) || (j%16==1 && i%8==mod(variant,8))) :
                 kind=="sparse" ? mod(i*17+j*29+variant*31,61)<7 : true
            k=mod(i*11+j*5+variant*13,7)-3
            keep && k!=0 && (col[i]=k/512)
        end
        push!(pool,col);push!(nz,findall(!iszero,col))
    end
    active=collect(1:n);steps=Tuple{Int,Int}[];undo=Tuple{Int,Int}[]
    for t in 1:128
        j=1+mod(37*(t-1),n);v=1+div(t-1,n)
        push!(undo,(j,active[j]));push!(steps,(j,v*n+j));active[j]=v*n+j
    end
    middle=sparse(hcat(pool[active]...))
    append!(steps,reverse(undo))
    initial=sparse(hcat(pool[1:n]...));active=collect(1:n)
    norms=Tuple{Float64,Float64}[];nnzs=Int[]
    function record_input()
        rows=zeros(n);column_max=0.;entries=0
        for j in 1:n
            idx=active[j];s=0.
            for i in nz[idx];a=abs(pool[idx][i]);rows[i]+=a;s+=a;entries+=1;end
            column_max=max(column_max,s)
        end
        push!(norms,(maximum(rows),column_max));push!(nnzs,entries)
    end
    record_input()
    for (j,idx) in steps;active[j]=idx;record_input();end
    @test active==collect(1:n)
    @test all(x->8<=x[1]<9 && 8<=x[2]<9,norms)
    bp=setprecision(BigFloat,256)do;[BigFloat.(c)for c in pool];end
    rhs=[(-1.)^i*(mod(i,11)+1)/16 for i in 1:n]
    rhs2=[(-1.)^(i+1)*(mod(i,7)+1)/32 for i in 1:n]
    return (name=kind,n=n,pool=pool,nz=nz,bp=bp,steps=steps,initial=initial,middle=middle,norms=norms,nnzs=nnzs,rhs=rhs,rhs2=rhs2)
end
function inputhash(c)
    io=IOBuffer()
    for v in c.pool;write(io,v);end
    for A in (c.initial,c.middle);write(io,A.colptr);write(io,A.rowval);write(io,A.nzval);end
    write(io,c.rhs);write(io,c.rhs2)
    for (j,idx) in c.steps;write(io,j,idx);end
    for x in c.norms;write(io,x[1],x[2]);end
    write(io,c.nnzs)
    for x in c.nz;write(io,length(x));write(io,x);end
    bytes2hex(sha256(take!(io)))
end
# Independent enclosure from the explicit chosen input columns. Every Float64
# token converts exactly; directed sums enclose even severe cancellation.
function oracle(c,state,x,rhs,norms,transposed=false)
    all(isfinite,x)||return false
    setprecision(BigFloat,256) do
        bx=BigFloat.(x);br=BigFloat.(rhs)
        bounds=map((RoundDown,RoundUp)) do mode
            setrounding(BigFloat,mode)do
                r=[-v for v in br]
                for j in 1:c.n
                    idx=state[j]
                    for i in c.nz[idx]
                        target,source=transposed ? (j,i) : (i,j)
                        r[target]=r[target]+c.bp[idx][i]*bx[source]
                    end
                end
                r
            end
        end
        residual=maximum(max(abs(bounds[1][i]),abs(bounds[2][i]))for i in 1:c.n)
        # Input norms are exact integer/512 sums. Downward bound computation
        # cannot relax the historical128*n*eps normwise acceptance threshold.
        bound=setrounding(BigFloat,RoundDown)do
            BigFloat(128*c.n)*BigFloat(eps(Float64))*max(BigFloat(1),BigFloat(norms[transposed ? 2 : 1])*maximum(abs,bx),maximum(abs,br))
        end
        residual<=bound
    end
end
function digest_factor(f;initial=false)
    io=IOBuffer();L=f.base.lower
    for a in (L.colptr,L.rowval,L.nzval,f.base.row_order,f.base.scaling,f.base.diagonal,f.column_order)
        a===nothing ? write(io,Int(-1)) : (write(io,length(a));write(io,a))
    end
    write(io,UInt8(f.base.divide_scaling))
    for col in f.upper
        write(io,length(col.values));write(io,collect(col.indices));write(io,col.values)
    end
    if !initial
        for u in f.updates
            if u isa J.BartelsGolubUpdate
                for s in u.steps;write(io,s.row,s.last,UInt8(s.swapped),s.multiplier);end
            else
                write(io,u.pivot);u isa J.SuhlSuhlUpdate&&write(io,u.last)
                write(io,length(u.indices));write(io,u.indices);write(io,u.multipliers);write(io,u.swapped_rows)
            end
        end
    end
    bytes2hex(sha256(take!(io)))
end
function metrics(f,step,event,pos,last,nb)
    stored=sum(c->length(c.values),f.upper);actual=sum(c->count(!iszero,c.values),f.upper)
    coeff=0;stored_coeff=0;records=0;swaps=0
    for u in f.updates
        if u isa J.BartelsGolubUpdate
            records+=length(u.steps);stored_coeff+=length(u.steps)
            for s in u.steps;coeff+=!iszero(s.multiplier);swaps+=s.swapped ? s.last-s.row+1 : 0;end
        else
            records+=1;stored_coeff+=length(u.multipliers);coeff+=count(!iszero,u.multipliers);swaps+=length(u.swapped_rows)
        end
    end
    d=Dict{String,Any}("step"=>step,"event"=>event,"u_stored"=>stored,"u_nonzero"=>actual,"l_nonzero"=>nnz(f.base.lower),"history_updates"=>length(f.updates),"history_records"=>records,"history_nonzero_coefficients"=>coeff,"history_stored_coefficients"=>stored_coeff,"factor_storage_count"=>J._factor_storage_count(f),"swap_span_proxy"=>swaps,"row_cache_ops"=>length(f.row_cache.operations),"leaving_position"=>pos,"spike_last"=>last,"basis_nonzeros"=>nb,"u_max"=>maximum(c->maximum(abs,c.values;init=0.),f.upper;init=0.))
    (step%16==0||event!="update")&&(d["reachable_bytes"]=Base.summarysize(f))
    d
end
function spike_last(f,dir)
    cache=f.row_cache.prepared
    cache===nothing&&return -1
    for e in cache.entries
        e.destination===dir && isequal(e.direction,dir) && return something(findlast(!iszero,e.spike),0)
    end
    -1
end
function replay(F::Type,backend,c,cold::Bool)
    n=c.n;dir=zeros(n);xf=zeros(n);xb=zeros(n);middle_outputs=zeros(2n)
    state=collect(1:n);trace=Dict{String,Any}[];clocks=zeros(UInt64,5)
    f=nothing;init="";completed=0
    try
    t=time_ns();f=J._direct_lu_factor(F,c.initial,backend,policy(backend);normalize=true);clocks[1]+=time_ns()-t
    J._direct_mode(f)==:normalized||error("Unexpected direct fallback/normalization")
    f.base.pivot_policy==policy(backend)||error("Policy changed")
    init=cold ? digest_factor(f;initial=true) : ""
    cold&&push!(trace,metrics(f,0,"initial",0,0,c.nnzs[1]))
    reference_storage=cold ? J._factor_storage_count(f) : 0
    cold&&(trace[end]["storage_ratio_since_refactor"]=1.)
    reference_growth=cold ? maximum(col->maximum(abs,col.values;init=0.),f.upper;init=0.) : 0.
    for (k,(j,idx)) in enumerate(c.steps)
        a=c.pool[idx];pos=cold ? f.positions[j] : 0
        t=time_ns();J.forward_solve!(dir,f,a);clocks[2]+=time_ns()-t
        all(isfinite,dir)||error("Nonfinite entering direction")
        last=cold ? spike_last(f,dir) : -1
        if cold
            oracle(c,state,dir,a,c.norms[k])||return (ok=false,reason="entering residual at $k",step=k,factor=f,trace=trace,clocks=clocks,initial=init,dir=dir,xf=xf,xb=xb,middle=middle_outputs)
        end
        t=time_ns();J.replace_column!(f,dir,j);clocks[4]+=time_ns()-t
        state[j]=idx
        t=time_ns();J.forward_solve!(xf,f,c.rhs);clocks[2]+=time_ns()-t
        t=time_ns();J.transpose_solve!(xb,f,c.rhs2);clocks[3]+=time_ns()-t
        all(isfinite,xf)&&all(isfinite,xb)||error("Nonfinite solves")
        if cold
            good=oracle(c,state,xf,c.rhs,c.norms[k+1])&&oracle(c,state,xb,c.rhs2,c.norms[k+1],true)
            row=metrics(f,k,"update",pos,last,c.nnzs[k+1]);row["storage_ratio_since_refactor"]=row["factor_storage_count"]/max(1,reference_storage);push!(trace,row)
            good||return (ok=false,reason="post-update residual at $k",step=k,factor=f,trace=trace,clocks=clocks,initial=init,dir=dir,xf=xf,xb=xb,middle=middle_outputs)
            (isfinite(row["u_max"])&&row["u_max"]<=1e8*reference_growth)||return (ok=false,reason="growth guard at $k",step=k,factor=f,trace=trace,clocks=clocks,initial=init,dir=dir,xf=xf,xb=xb,middle=middle_outputs)
        end
        completed=k
        if k==128
            copyto!(middle_outputs,1,xf,1,n);copyto!(middle_outputs,n+1,xb,1,n)
            t=time_ns();J.refactorize!(f,c.middle);clocks[5]+=time_ns()-t
            J._direct_mode(f)==:normalized&&f.base.pivot_policy==policy(backend)||error("Refactor mode/policy changed")
            if cold
                push!(trace,metrics(f,k,"refactor",0,0,c.nnzs[k+1]))
                reference_storage=J._factor_storage_count(f)
                trace[end]["storage_ratio_since_refactor"]=1.
                reference_growth=maximum(col->maximum(abs,col.values;init=0.),f.upper;init=0.)
            end
        end
    end
    all(j->state[j]==j,1:n)||error("Sequence failed to restore original basis")
    return (ok=true,reason="",step=completed,factor=f,trace=trace,clocks=clocks,initial=init,dir=dir,xf=xf,xb=xb,middle=middle_outputs)
    catch err
        err isa InterruptException && rethrow()
        cold || rethrow()
        return (ok=false,reason="exception after $completed: "*sprint(showerror,err),step=completed,factor=f,trace=trace,clocks=clocks,initial=init,dir=dir,xf=xf,xb=xb,middle=middle_outputs)
    end
end
function runall()
    data=Dict{String,Any}("cold"=>Any[],"windows"=>Any[],"fixture_preparation"=>Any[],"scope"=>"Float64 factor component experiment, not public solver or production admission")
    for kind in ("band","blocks","sparse","dense")
        prep=@timed makecase(kind);c=prep.value;input_before=inputhash(c)
        push!(data["fixture_preparation"],Dict("fixture"=>kind,"seconds"=>prep.time,"bytes"=>prep.bytes,"events"=>Base.gc_alloc_count(prep.gcstats),"compile_seconds"=>prep.compile_time))
        for backend in (Val(:native),Val(:markowitz))
            bname=string(typeof(backend).parameters[1]);refs=Any[];eligible=true
            for (i,F) in enumerate(MANAGERS)
                t=@timed replay(F,backend,c,true);r=t.value
                push!(refs,(initial=r.initial,signature=r.factor===nothing ? "" : digest_factor(r.factor),dir=copy(r.dir),xf=copy(r.xf),xb=copy(r.xb),middle=copy(r.middle)));@test r.ok;@test inputhash(c)==input_before
                eligible&=r.ok
                push!(data["cold"],Dict("fixture"=>kind,"backend"=>bname,"manager"=>LABELS[i],"ok"=>r.ok,"reason"=>r.reason,"completed_updates"=>r.step,"seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"initial_factor_hash"=>r.initial,"final_factor_hash"=>refs[end].signature,"trace"=>r.trace))
                r=nothing;t=nothing
            end
            @test refs[1].initial==refs[2].initial==refs[3].initial
            if eligible
                signatures=map(r->r.signature,refs)
                GC.gc() # Release cold factor owners/oracle garbage before whole-cycle timing.
                for repetition in 0:5
                    order=mod1.(collect(1:3).+repetition,3)
                    for i in order
                        t=@timed replay(MANAGERS[i],backend,c,false);r=t.value
                        @test r.ok && digest_factor(r.factor)==signatures[i]
                        @test isequal((r.dir,r.xf,r.xb,r.middle),(refs[i].dir,refs[i].xf,refs[i].xb,refs[i].middle))
                        @test oracle(c,collect(1:c.n),r.xf,c.rhs,c.norms[end])&&oracle(c,collect(1:c.n),r.xb,c.rhs2,c.norms[end],true)
                        @test inputhash(c)==input_before
                        if repetition>0;@test t.compile_time==t.recompile_time==0;end
                        push!(data["windows"],Dict("fixture"=>kind,"backend"=>bname,"manager"=>LABELS[i],"repetition"=>repetition,"warm"=>repetition==0,"seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,"construct_seconds"=>r.clocks[1]/1e9,"ftran_seconds"=>r.clocks[2]/1e9,"btran_seconds"=>r.clocks[3]/1e9,"update_seconds"=>r.clocks[4]/1e9,"refactor_seconds"=>r.clocks[5]/1e9,"updates"=>r.step,"refactors"=>1,"retained_bytes"=>Base.summarysize(r.factor)))
                        r=nothing;t=nothing
                    end
                end
            end
            open(joinpath(D,"results-1.toml"),"w")do io;TOML.print(io,data);end
            println("COMPLETED ",kind,"/",bname," eligible=",eligible);flush(stdout)
        end
    end
end
@testset "Direct FT SS BG long-chain comparison" begin
    runall()
end
