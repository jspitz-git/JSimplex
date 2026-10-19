from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def put(n,s):
 with (C/n).open('x') as f:f.write(s)
put('numerical-tests.jl',r'''# UNEXECUTED Task2 source; define first, call only under later admission.
module BGBlockedNumericalTests
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
    @test bits([a,z])==bits([t.shadow[k,k],t.shadow[k+1,k]])
    @test swapped==(abs(z)>abs(a))
    if swapped;t.shadow[k,:],t.shadow[k+1,:]=copy(t.shadow[k+1,:]),copy(t.shadow[k,:]);end
    pivot=t.shadow[k,k];@test !iszero(pivot)
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
            @test iszero(t.shadow[k,k]) && abs(t.shadow[k+1,k])>0
            push!(t.pivots,(k,true))
            t.shadow[k,:],t.shadow[k+1,:]=copy(t.shadow[k+1,:]),copy(t.shadow[k,:])
            action!(t.T,k,k,true,0.0)
        end
    elseif event===:panel_reject
        t.rejections+=1
        if t.checkpoint!==nothing
            t.shadow,t.T,l=t.checkpoint;resize!(t.pivots,l);t.checkpoint=nothing
        end
    elseif event===:panel_commit
        t.panels+=1;t.checkpoint=nothing
    elseif event===:finish
        f,steps=args
        @test relation(unpack(f),t.T,t.H)
        @test history_matrix(steps,length(f.upper))==t.T
        @test bits(unpack(f))==bits(t.shadow)
        @test f.base===t.base[1]
        @test isequal(f.base.lower,t.base[2]) && f.base.row_order==t.base[3] && f.base.scaling==t.base[4] && isequal(f.base.diagonal,t.base[5])
        @test all(issorted(c.indices) && length(c.indices)==length(c.values) for c in f.upper)
        @test all(f.row_columns[i]==[id for id in eachindex(f.positions) if !iszero(J._upper_value(f.upper[f.positions[id]],i))] for i in eachindex(f.upper))
        t.accepted_pivots=copy(t.pivots)
        @test t.rejections<=1
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
    r=J._direct_lu_factor(J.BartelsGolubFactorization,left,Val(backend),policy)
    c=A._bgb_factor(right,Val(backend),policy)
    @test left==original && right==original && left.nzval!==right.nzval
    @test J._direct_mode(r)!==:fallback && J._direct_mode(c)!==:fallback
    observed=NamedTuple[]
    for s in steps
        snapshots=(copy(s.a),copy(s.dse),copy(s.unit))
        x=zeros(f["n"]);y=similar(x);u=similar(x);v=similar(x)
        J.forward_solve!(x,r,s.a);J.forward_solve!(y,c,s.a)
        @test residual(B,x,s.a) && residual(B,y,s.a)
        J.forward_solve!(u,r,s.dse);J.forward_solve!(v,c,s.dse)
        @test residual(B,u,s.dse) && residual(B,v,s.dse)
        @test any(e.destination===y for e in c.inner.row_cache.prepared.entries)
        @test any(e.destination===v for e in c.inner.row_cache.prepared.entries)
        direction=copy(y);rcount=length(r.updates);ccount=length(c.inner.updates)
        tr=Trace();tc=Trace()
        # Test-only ordinary wrapper runs exactly the copied scalar suffix.
        A._bgb_reference_replace!(r,x,s.j;probe=tr)
        A._bgb_replace!(c,y,s.j;probe=tc,blocked=!reference_route)
        @test bits(y)==bits(direction)
        @test length(r.updates)==rcount+1 && length(c.inner.updates)==ccount+1
        B[:,s.j]=s.a # independent original-basis column replacement
        for (op,trans) in ((J.forward_solve!,false),(J.transpose_solve!,true))
            op(x,r,s.unit);op(y,c,s.unit)
            @test residual(B,x,s.unit;transposed=trans) && residual(B,y,s.unit;transposed=trans)
        end
        @test all(bits(a)==bits(b) for (a,b) in zip((s.a,s.dse,s.unit),snapshots))
        @test !c.busy && (c.workspace===nothing || c.workspace.owner===nothing && c.workspace.phase==0)
        f["pivot_agreement"] && (@test tc.accepted_pivots==tr.accepted_pivots)
        U=unpack(c.inner)
        @test all(isfinite,U) && minimum(abs(U[i,i]) for i in axes(U,1))>0
        push!(observed,(panels=tc.panels,rejections=tc.rejections,growth=maximum(abs,U),minpivot=minimum(abs(U[i,i]) for i in axes(U,1))))
    end
    # Positive coverage is a real gate, never a conditional assertion skip.
    @test sum(o.panels for o in observed)>=f["minimum_panels"]
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
''')
put('lifecycle-tests.jl',r'''# UNEXECUTED Task2 source. Fault modules are isolated exact-inverse clones.
module BGBlockedLifecycleTests
using Test, LinearAlgebra, SparseArrays
import ..JSimplex, ..BGBlockedAdapter, ..BGBlockedPanel, ..BGBlockedAdapterFault, ..BGBlockedPanelFault
import ..BGBlockedNumericalTests
const J=JSimplex
const A=BGBlockedAdapter
const K=BGBlockedPanel
const N=BGBlockedNumericalTests
const F=BGBlockedAdapterFault
const FK=BGBlockedPanelFault
function upper_fixture(n)
    sparse([i==j ? 4.0 : i<j ? 0.125 : 0.0 for i in 1:n,j in 1:n])
end
function failed_cache(f)
    c=f.inner.row_cache
    !f.busy && f.workspace===nothing && c.upper_dirty && !c.upper_prefix_safe && !c.upper_prefix_candidate && !f.inner.row_columns_ready &&
        (c.prepared===nothing || all(e.destination===nothing for e in c.prepared.entries))
end
# Construct an actual BG manager with a known lower/base; replace U only in a
# cold microcase to supply exact post-rotation H. Not an original-B solve case.
function micro(M;fault=false)
    n=size(M,1);module_=fault ? F : A
    f=module_._bgb_factor(sparse(Matrix{Float64}(I,n,n)),Val(:native),J._NATIVE_PIVOT_ONE)
    f.inner.upper=J._direct_packed_upper(sparse(M),J.BartelsGolubFactorization)
    J._ensure_bartels_golub_incidence!(f.inner)
    f
end
function band(n)
    [i==j ? 4.0 : i==j+1 ? 0.25 : i<j ? 0.125 : 0.0 for i in 1:n,j in 1:n]
end
function run_lifecycle()
 @testset "blocked BG lifecycle and failure ownership" begin
    for (backend,policy) in N.ARMS
        B=upper_fixture(96);before=copy(B);f=A._bgb_factor(B,Val(backend),policy)
        @test f.workspace===nothing && !f.busy && B==before
        # Two prepared RHS, then identical last-column replacement (no elimination).
        a=Vector(B[:,end]);x=zeros(96);v=similar(x)
        J.forward_solve!(x,f,a);J.forward_solve!(v,f,ones(96))
        @test any(e.destination===x for e in f.inner.row_cache.prepared.entries)
        old=length(f.inner.updates);J.replace_column!(f,x,96)
        @test length(f.inner.updates)==old+1 && isempty(f.inner.updates[end].steps) && f.workspace===nothing
        saved=J.copy_basis_factorization(f)
        @test saved.workspace===nothing && saved.inner.upper!==f.inner.upper
        @test all(a.values!==b.values && a.indices.ids!==b.indices.ids for (a,b) in zip(saved.inner.upper,f.inner.upper))
        oldsaved=N.unpack(saved.inner)
        # First-use/reuse workspace ownership is tested without assuming a given LU ordering.
        f.workspace=K.BGPanelWorkspace(96);owner=f.workspace
        J.refactorize!(f,copy(B));@test f.workspace===owner
        J.refactorize!(f,upper_fixture(64));@test f.workspace===nothing
        f.workspace=K.BGPanelWorkspace(64)
        J.refactorize!(f,upper_fixture(32));@test f.workspace===nothing
        @test N.bits(N.unpack(saved.inner))==N.bits(oldsaved)
        f.busy=true
        try
            @test_throws ArgumentError J.replace_column!(f,ones(32),1)
            @test_throws ArgumentError J.refactorize!(f,upper_fixture(32))
            @test_throws ArgumentError J.copy_basis_factorization(f)
            @test_throws ArgumentError J.forward_solve!(zeros(32),f,ones(32))
            @test_throws ArgumentError J.transpose_solve!(zeros(32),f,ones(32))
        finally
            f.busy=false
        end
        @test_throws ArgumentError J.replace_column!(f,ones(32),1;zero_tolerance=-1.0)
        @test failed_cache(f)
    end
    # Exact separated pivots, multiple panels, shadow/history oracle; no LU solves.
    for n in (96,256)
        f=micro(band(n));t=N.Trace();A._bgb_test_eliminate!(f,1;probe=t)
        @test t.panels>=2 && t.rejections<=1
        @test N.relation(N.unpack(f.inner),t.T,t.H)
        @test K._bgb_charge(n)<=2^20
    end
    # An explicit stored zero in the second band rejects after a committed panel.
    M=band(96);M[10,20]=0.0;f=micro(M)
    col=f.inner.upper[20];slot=searchsortedfirst(col.indices,10)
    insert!(col.indices,slot,10);insert!(col.values,slot,0.0)
    J._ensure_bartels_golub_incidence!(f.inner)
    t=N.Trace();A._bgb_test_eliminate!(f,1;probe=t)
    @test t.panels==1 && t.rejections==1
    @test count(==(:eligibility),t.events)==2
    # Private failure after arithmetic: overflow of first elimination, original
    # suffix retained; prefix safety must stay false even if later values cancel.
    M=band(96);M[1,1]=1.0;M[2,1]=1.0;M[1,2]=-floatmax(Float64);M[2,2]=floatmax(Float64)
    f=micro(M);events=Symbol[]
    try A._bgb_test_eliminate!(f,1;probe=(e,args...)->push!(events,e)) catch e
        @test e isa LinearAlgebra.ZeroPivotException
    end
    @test count(==(:panel_reject),events)==1 && count(==(:eligibility),events)==1
    @test !f.inner.row_cache.upper_prefix_safe && !f.inner.row_cache.upper_prefix_candidate
    # Explicit zero diagonal with no swap: original scalar failure, no safe cache.
    M=band(96);M[1,1]=0;M[2,1]=0;f=micro(M)
    @test_throws LinearAlgebra.ZeroPivotException A._bgb_test_eliminate!(f,1)
    @test failed_cache(f)
    # Nonfinite admission declines, even when no panel scratch was allocated.
    for value in (Inf,NaN)
        M=band(96);M[1,20]=value;f=micro(M);events=Symbol[]
        try A._bgb_test_eliminate!(f,1;probe=(e,args...)->push!(events,e)) catch e
            @test e isa LinearAlgebra.ZeroPivotException
        end
        @test count(==(:eligibility),events)==1 && count(==(:panel_reject),events)==1
        @test !f.inner.row_cache.upper_prefix_safe
    end
    # Exceptions inside gather, reserve and writeback are injected in a separate
    # exact-inverse kernel clone. They propagate; partial mutation is allowed.
    for point in (:gather,:reserve,:writeback)
        f=micro(band(96);fault=true);FK.arm!(point,OutOfMemoryError())
        caught=nothing
        try F._bgb_test_eliminate!(f,1) catch e;caught=e;end
        @test caught===FK.sentinel[] && FK.hits[]==1
        @test failed_cache(f)
        @test isempty(f.inner.updates)
        FK.disarm!()
    end
    # Callback reentrancy fails before an inner solve; outer failure drops scratch.
    f=micro(band(96));entered=Ref(0)
    p=(e,args...)->begin
        if e===:panel_begin
            entered[]+=1;J.forward_solve!(zeros(96),f,ones(96))
        end
    end
    @test_throws ArgumentError A._bgb_test_eliminate!(f,1;probe=p)
    @test entered[]==1 && failed_cache(f)
 end
 nothing
end
end
''')
with (Q/'tests-first.json').open('x') as f:json.dump(dict(scope='Test text before factor.jl; no Julia RED or parser execution',sha256={str(C/n):hashlib.sha256((C/n).read_bytes()).hexdigest() for n in ['numerical-tests.jl','lifecycle-tests.jl']},candidate_absent=not (C/'factor.jl').exists()),f,indent=2)
print('Task2 test text saved before adapter; UNEXECUTED')
