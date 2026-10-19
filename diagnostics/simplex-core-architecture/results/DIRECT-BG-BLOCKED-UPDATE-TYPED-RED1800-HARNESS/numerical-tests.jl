# UNEXECUTED Task2 source; define first, call only under later admission.
module BGBlockedNumericalTests
using ..HarnessRecords: @check, @checkthrows
import ..HarnessRecords
using Test, LinearAlgebra, SparseArrays, TOML
import ..JSimplex, ..BGBlockedAdapter
const J=JSimplex
const A=BGBlockedAdapter
const ARMS=((:native,J._NATIVE_PIVOT_ONE),(:markowitz,J._NATIVE_PIVOT_DEFAULT))
const Q=Rational{BigInt}
bits(x)=reinterpret(UInt64,vec(copy(x)))
q(x::Float64)=rationalize(BigInt,x;tol=0)
unpack(f)=[J._upper_value(f.upper[j],i) for i in eachindex(f.upper),j in eachindex(f.upper)]
norminf(x::AbstractVector)=maximum(abs,x;init=zero(Q))
norminf(x::AbstractMatrix)=maximum((sum(abs,x[i,:]) for i in axes(x,1));init=zero(Q))
function residual(B,x,rhs;transposed=false)
    all(isfinite,x) || return false
    M=q.(Matrix(B));transposed && (M=permutedims(M))
    z=q.(x);b=q.(rhs);n=length(z)
    norminf(M*z-b)<=128*n*Q(1,2^52)*max(one(Q),norminf(M)*norminf(z),norminf(b))
end
function relation(U,T,H)
    all(isfinite,U) && all(isfinite,H) || return false
    V=q.(U);G=q.(H);n=size(U,1)
    norminf(V-T*G)<=128*n*Q(1,2^52)*max(one(Q),norminf(T)*norminf(G),norminf(V))
end
# Independent chronological elementary action, not production history helpers.
function action!(M,k,last,swap,m)
    if swap
        top=copy(M[k,:])
        for i in k:last;M[i,:]=M[i+1,:];end
        M[last+1,:]=top
    end
    if !iszero(m);M[k+1,:]-=q(m).*M[k,:];end
    M
end
function history_matrix(steps,n)
    T=Matrix{Q}(I,n,n)
    for s in steps;action!(T,s.row,s.last,s.swapped,s.multiplier);end
    T
end
mutable struct Trace
    H::Matrix{Float64}
    shadow::Matrix{Float64}
    T::Matrix{Q}
    checkpoint::Any
    events::Vector{Symbol}
    pivots::Vector{Tuple{Int,Bool}}
    accepted_pivots::Vector{Tuple{Int,Bool}}
    panels::Int
    rejections::Int
    current_fma::Bool
    base::Any
end
Trace()=Trace(zeros(0,0),zeros(0,0),zeros(Q,0,0),nothing,Symbol[],Tuple{Int,Bool}[],Tuple{Int,Bool}[],0,0,false,nothing)
function pivot!(t,k,a,z,swapped,fused)
    HarnessRecords.tick("pivot")
    @check "N001" bits([a,z])==bits([t.shadow[k,k],t.shadow[k+1,k]])
    @check "N002" swapped==(abs(z)>abs(a))
    if swapped;t.shadow[k,:],t.shadow[k+1,:]=copy(t.shadow[k+1,:]),copy(t.shadow[k,:]);end
    pivot=t.shadow[k,k];@check "N003" !iszero(pivot)
    m=t.shadow[k+1,k]/pivot
    action!(t.T,k,k,swapped,m)
    t.shadow[k+1,k]=0.0
    for j in k+1:size(t.shadow,2)
        v=t.shadow[k,j]
        # Packed source rows skip absent exact zeros.
        if !iszero(m) && !iszero(v)
            value=fused ? fma(-m,v,t.shadow[k+1,j]) : t.shadow[k+1,j]-m*v
            t.shadow[k+1,j]=iszero(value) ? 0.0 : value
        end
    end
    push!(t.pivots,(k,swapped))
end
function (t::Trace)(event,args...)
    HarnessRecords.tick("event_"*string(event))
    push!(t.events,event)
    if event===:begin
        f=args[1];t.H=unpack(f);t.shadow=copy(t.H);t.T=Matrix{Q}(I,size(t.H)...)
        t.base=(f.base,copy(f.base.lower),copy(f.base.row_order),copy(f.base.scaling),isnothing(f.base.diagonal) ? nothing : copy(f.base.diagonal))
    elseif event===:panel_begin
        t.checkpoint=(copy(t.shadow),copy(t.T),length(t.pivots));t.current_fma=true
    elseif event===:panel_pivot
        pivot!(t,args...,true)
    elseif event===:scalar_pivot
        pivot!(t,args...,false)
    elseif event===:pure
        first,last=args
        for k in first:last
            HarnessRecords.tick("pure_row")
            @check "N004" iszero(t.shadow[k,k]) && abs(t.shadow[k+1,k])>0
            push!(t.pivots,(k,true))
            t.shadow[k,:],t.shadow[k+1,:]=copy(t.shadow[k+1,:]),copy(t.shadow[k,:])
            action!(t.T,k,k,true,0.0)
        end
    elseif event===:panel_reject
        t.checkpoint===nothing && HarnessRecords.tick("declined_before_gather")
        t.rejections+=1
        if t.checkpoint!==nothing
            t.shadow,t.T,l=t.checkpoint;resize!(t.pivots,l);t.checkpoint=nothing
        end
    elseif event===:panel_commit
        t.panels+=1;t.checkpoint=nothing
    elseif event===:finish
        HarnessRecords.tick("finish")
        f,steps=args
        @check "N005" relation(unpack(f),t.T,t.H)
        @check "N006" history_matrix(steps,length(f.upper))==t.T
        @check "N007" bits(unpack(f))==bits(t.shadow)
        @check "N008" f.base===t.base[1]
        @check "N009" isequal(f.base.lower,t.base[2]) && f.base.row_order==t.base[3] && f.base.scaling==t.base[4] && isequal(f.base.diagonal,t.base[5])
        @check "N010" all(issorted(c.indices) && length(c.indices)==length(c.values) for c in f.upper)
        @check "N011" all(f.row_columns[i]==[id for id in eachindex(f.positions) if i in f.upper[f.positions[id]].indices] for i in eachindex(f.upper))
        t.accepted_pivots=copy(t.pivots)
        @check "N012" t.rejections<=1
    end
    nothing
end
function decode_fixture(f)
    val(s)=reinterpret(Float64,parse(UInt64,s;base=16))
    n=f["n"];m=f["initial"]
    B=SparseMatrixCSC(n,n,Int.(m["colptr"]),Int.(m["rowval"]),val.(m["bits"]))
    steps=[(j=Int(s["j"]),a=val.(s["a"]),dse=val.(s["dse"]),unit=val.(s["unit"])) for s in f["steps"]]
    B,steps
end
function run_stream(f,backend,policy;reference_route=false)
    B,steps=decode_fixture(f);original=copy(B)
    left=copy(B);right=copy(B)
    r=HarnessRecords.api("factory_reference",J._direct_lu_factor,J.BartelsGolubFactorization,left,Val(backend),policy)
    c=HarnessRecords.api("factory_candidate",A._bgb_factor,right,Val(backend),policy)
    @check "N013" left==original && right==original && left.nzval!==right.nzval
    @check "N014" J._direct_mode(r)!==:fallback && J._direct_mode(c)!==:fallback
    observed=NamedTuple[]
    for s in steps
        snapshots=(copy(s.a),copy(s.dse),copy(s.unit))
        x=zeros(f["n"]);y=similar(x);u=similar(x);v=similar(x)
        HarnessRecords.api("FTRAN",J.forward_solve!,x,r,s.a);HarnessRecords.api("FTRAN",J.forward_solve!,y,c,s.a)
        @check "N015" residual(B,x,s.a) && residual(B,y,s.a)
        HarnessRecords.api("FTRAN",J.forward_solve!,u,r,s.dse);HarnessRecords.api("FTRAN",J.forward_solve!,v,c,s.dse)
        @check "N016" residual(B,u,s.dse) && residual(B,v,s.dse)
        @check "N017" any(e.destination===y for e in c.inner.row_cache.prepared.entries)
        @check "N018" any(e.destination===v for e in c.inner.row_cache.prepared.entries)
        direction=copy(y);rcount=length(r.updates);ccount=length(c.inner.updates)
        tr=Trace();tc=Trace()
        # Test-only ordinary wrapper runs exactly the copied scalar suffix.
        HarnessRecords.api("replace_reference",A._bgb_reference_replace!,r,x,s.j;probe=tr)
        HarnessRecords.api("replace_candidate",A._bgb_replace!,c,y,s.j;probe=tc,blocked=!reference_route)
        @check "N019" bits(y)==bits(direction)
        @check "N020" length(r.updates)==rcount+1 && length(c.inner.updates)==ccount+1
        B[:,s.j]=s.a # independent original-basis column replacement
        for (op,trans) in ((J.forward_solve!,false),(J.transpose_solve!,true))
            HarnessRecords.api(trans ? "BTRAN" : "FTRAN",op,x,r,s.unit);HarnessRecords.api(trans ? "BTRAN" : "FTRAN",op,y,c,s.unit)
            @check "N021" residual(B,x,s.unit;transposed=trans) && residual(B,y,s.unit;transposed=trans)
        end
        @check "N022" all(bits(a)==bits(b) for (a,b) in zip((s.a,s.dse,s.unit),snapshots))
        @check "N023" !c.busy && (c.workspace===nothing || c.workspace.owner===nothing && c.workspace.phase==0)
        f["pivot_agreement"] && (@check "N024" tc.accepted_pivots==tr.accepted_pivots)
        U=unpack(c.inner)
        @check "N025" all(isfinite,U) && minimum(abs(U[i,i]) for i in axes(U,1))>0
        push!(observed,(panels=tc.panels,rejections=tc.rejections,growth=maximum(abs,U),minpivot=minimum(abs(U[i,i]) for i in axes(U,1))))
    end
    # Positive coverage is a real gate, never a conditional assertion skip.
    @check "N026" sum(o.panels for o in observed)>=f["minimum_panels"]
    observed
end
function run_numerical(path;reference_route=false)
    fixtures=TOML.parsefile(path)["fixtures"]
    results=[]
    @testset "blocked BG original-basis and chronological relation" begin
        for f in fixtures,(backend,policy) in ARMS
            @testset "$(f["name"])/$backend" begin
                push!(results,run_stream(f,backend,policy;reference_route))
            end
        end
    end
    results
end
end
