# UNEXECUTED Task1 tests. Definitions only; load after the three adapted test modules.
module BGSpecializedBoundaryTests
using Test, LinearAlgebra, SparseArrays, JSimplex
using ..BGSpecializedExportWorkspaceTests: caught, OrientationSolve, orientation_parts
using ..BGSpecializedExportImportTests: snapshot, packed_snapshot, export_snapshot
using ..BGSpecializedExportLifecycleTests: graph, samegraph
const X=JSimplex
mutable struct OriginalOwner
    workspace::Union{Nothing,X.BGExportWorkspace}
end
OriginalOwner()=OriginalOwner(nothing)
mutable struct SpecializedOwner
    workspace::Union{Nothing,X.BGSpecializedExportWorkspace}
end
SpecializedOwner()=SpecializedOwner(nothing)
const SIDES=(
    (;owner=OriginalOwner,checked=X._bgx_checked_basis_lu,scale=X._bgx_scale_mode,
      export_parts=X._bgx_export,import_upper=X._bgx_import_upper,build=X._bgx_build,
      factor=X._bgx_factor,refactor=X._bgx_refactor_with!,allocate=X._bgx_allocate),
    (;owner=SpecializedOwner,checked=X._bgxs_checked_basis_lu,scale=X._bgxs_scale_mode,
      export_parts=X._bgxs_export,import_upper=X._bgxs_import_upper,build=X._bgxs_build,
      factor=X._bgxs_factor,refactor=X._bgxs_refactor_with!,allocate=X._bgxs_allocate))
const ARMS=((:native,X._NATIVE_PIVOT_ONE),(:markowitz,X._NATIVE_PIVOT_DEFAULT))
# Fixed diagnostic storage, no resizing; request entries are initialized before inspection.
mutable struct Requests
    count::Int
    fail_at::Int
    sentinel::Exception
    entries::Vector{Tuple{Any,Int}}
end
Requests(k=0)=Requests(0,k,ErrorException("boundary allocation"),Vector{Tuple{Any,Int}}(undef,256))
function (a::Requests)(::Type{T},n::Int) where T
    a.count+=1
    a.count<=length(a.entries) || error("request budget exceeded")
    a.entries[a.count]=(T,n)
    a.count==a.fail_at && throw(a.sentinel)
    T===Bool ? falses(n) : Vector{T}(undef,n)
end
requests(a)=a.entries[1:a.count]
cache_owners(o)=isnothing(o.workspace) ? () :
    (o.workspace,o.workspace.seen,o.workspace.orientation)
function same_cache(o,owners)
    now=cache_owners(o)
    length(now)==length(owners) && all(a===b for (a,b) in zip(now,owners))
end
function checked_orientation(side,k)
    L,U,p,q,s=orientation_parts(64);before=(snapshot(L),snapshot(U),copy(p),copy(q),copy(s))
    owner=side.owner();a=Requests(k);f=OrientationSolve(:ok,Ref(0),ErrorException("unused"))
    answer=Ref{Any}(nothing)
    err=caught(()->begin
        e=side.checked(L,U,p,q,s,false,owner;allocate=a)
        answer[]=side.scale(f,L,U,p,q,s,owner,64,nnz(L),nnz(U);allocate=a)
        @test e.lower===L && e.upper===U && e.rows===p && e.columns===q && e.scaling===s
    end)
    if k==0
        @test isnothing(err) && answer[]===false && a.count==5 && f.calls[]==1
        @test requests(a)==[(Bool,64),(Float64,64),(Float64,64),(Float64,64),(Float64,64)]
        owners=cache_owners(owner);group=owner.workspace.orientation
        @test !isnothing(owner.workspace.seen) && length(group)==4
        side.checked(L,U,p,q,s,false,owner;allocate=a)
        @test side.scale(f,L,U,p,q,s,owner,64,nnz(L),nnz(U);allocate=a)===false
        @test a.count==5 && f.calls[]==2 && same_cache(owner,owners)
        @test all(group[i]===owner.workspace.orientation[i] for i in 1:4)
    else
        @test err===a.sentinel && a.count==k && isnothing(owner.workspace)
        @test f.calls[]==(k<=3 ? 0 : 1)
    end
    @test (snapshot(L),snapshot(U),p,q,s)==before
    (requests(a),answer[],f.calls[])
end
function import_inputs()
    (spzeros(0,0),sparse(reshape([2.0],1,1)),
     SparseMatrixCSC(3,3,[1,2,4,7],[1,1,2,1,2,3],[2.0,-0.0,4.0,0.0,-0.0,8.0]),
     sparse([floatmin(Float64) floatmax(Float64);0.0 1.0]),
     sparse([floatmax(Float64) nextfloat(0.0);0.0 1.0]))
end
# Catches skipped/duplicated/reordered requests, different failure prefixes,
# loss of private reuse, or arithmetic/input changes across the new core boundary.
function boundary_request_equivalence()
    @testset "boundary_request_equivalence" begin
        for k in 0:5
            a=checked_orientation(SIDES[1],k);b=checked_orientation(SIDES[2],k)
            @test isequal(a,b)
        end
        for U in import_inputs(), normalize in (false,true)
            before=snapshot(U);owners=(U.colptr,U.rowval,U.nzval)
            a=Requests();b=Requests()
            x,dx=SIDES[1].import_upper(U,normalize;allocate=a)
            y,dy=SIDES[2].import_upper(U,normalize;allocate=b)
            @test requests(a)==requests(b)
            @test isequal(packed_snapshot(x),packed_snapshot(y))
            @test isnothing(dx) ? isnothing(dy) : !isnothing(dy) && reinterpret(UInt64,dx)==reinterpret(UInt64,dy)
            @test all(c.values!==U.nzval && c.indices.ids!==U.rowval for c in (x...,y...))
            for k in 1:a.count
                aa=Requests(k);bb=Requests(k)
                @test caught(()->SIDES[1].import_upper(U,normalize;allocate=aa))===aa.sentinel
                @test caught(()->SIDES[2].import_upper(U,normalize;allocate=bb))===bb.sentinel
                @test aa.count==bb.count==k && requests(aa)==requests(bb)==requests(a)[1:k]
                @test snapshot(U)==before
            end
            @test snapshot(U)==before && all(a===b for (a,b) in zip(owners,(U.colptr,U.rowval,U.nzval)))
        end
    end
end
mutable struct HookLog
    count::Int
    fail_at::Int
    sentinel::Exception
    entries::Vector{Symbol}
end
HookLog(k)=HookLog(0,k,ErrorException("hook boundary"),Vector{Symbol}(undef,5))
struct Hook{F}
    log::HookLog
    name::Symbol
    action::F
end
function (h::Hook)(args...;kwargs...)
    l=h.log;l.count+=1
    l.count<=length(l.entries) || error("duplicate hook")
    l.entries[l.count]=h.name
    l.count==l.fail_at && throw(l.sentinel)
    h.action(args...;kwargs...)
end
function hook_case(side,R,p,k)
    B=sparse([4.0 1.0;0.5 3.0]);before=snapshot(B)
    f=side.factor(B,Val(R),p);old=f.inner;state=graph(old);log=HookLog(k)
    checker=(active,candidate)->begin
        @test active===old && f.inner===old && f.busy && candidate!==old
        nothing
    end
    err=caught(()->side.refactor(f,B;
        factorize=Hook(log,:factorize,X._factorize_basis),
        export_parts=Hook(log,:export,side.export_parts),
        import_upper=Hook(log,:import,side.import_upper),
        make_inner=Hook(log,:make_inner,X._init_direct_manager),
        check_inner=Hook(log,:check_inner,checker)))
    expected=(:factorize,:export,:import,:make_inner,:check_inner)
    @test log.count==(k==0 ? 5 : k)
    @test log.entries[1:log.count]==collect(expected[1:log.count])
    @test !f.busy && snapshot(B)==before
    if k==0
        @test isnothing(err) && f.inner!==old
    else
        @test err===log.sentinel && f.inner===old && samegraph(old,state) && isnothing(f.workspace)
    end
    (log.entries[1:log.count],graph(f.inner)[2],X._direct_mode(f))
end
# Catches bypassed hooks, duplicate callbacks, publication before the mandatory
# check, wrong exception propagation or failure to release the busy flag.
function boundary_hook_order()
    @testset "boundary_hook_order" begin
        for (R,p) in ARMS, k in 0:5
            a=hook_case(SIDES[1],R,p,k);b=hook_case(SIDES[2],R,p,k)
            @test isequal(a,b)
        end
    end
end
function build_pair(side,B,R,p,normalize)
    before=snapshot(B);oa=side.owner();ob=side.owner();a=Requests();b=Requests()
    # Only the allocator is replaced in the first call. The second explicitly
    # supplies every default hook, exercising the same ordinary algorithm.
    x=side.build(B,Val(R),p,normalize,oa;allocate=a)
    y=side.build(B,Val(R),p,normalize,ob;factorize=X._factorize_basis,
        export_parts=side.export_parts,import_upper=side.import_upper,allocate=b,
        make_inner=X._init_direct_manager)
    @test requests(a)==requests(b) && isequal(graph(x)[2],graph(y)[2])
    @test X._direct_mode(x)==X._direct_mode(y)
    @test isnothing(oa.workspace)==isnothing(ob.workspace)
    if !isnothing(oa.workspace)
        @test oa.workspace!==ob.workspace
        @test oa.workspace.charged_bytes==ob.workspace.charged_bytes
        @test oa.workspace.seen!==ob.workspace.seen
    end
    n=size(B,1);rhs=ones(n);rb=copy(reinterpret(UInt64,rhs));solutions=Vector{Vector{UInt64}}()
    for op in (X.forward_solve!,X.transpose_solve!)
        out=zeros(n);control=zeros(n);op(out,x,rhs);op(control,y,rhs)
        @test reinterpret(UInt64,out)==reinterpret(UInt64,control)
        @test reinterpret(UInt64,rhs)==rb
        push!(solutions,copy(reinterpret(UInt64,out)))
    end
    @test snapshot(B)==before
    (requests(a),solutions,X._direct_mode(x))
end
# Catches a different hot/default path or keyword forwarding semantics; importer
# controls also cover normalization rejection without constructing invalid LPs.
function boundary_hot_and_hook_agree()
    @testset "boundary_hot_and_hook_agree" begin
        inputs=(spzeros(0,0),sparse(reshape([2.0],1,1)),sparse([4.0 1.0;0.5 3.0]))
        for B in inputs, (R,p) in ARMS, normalize in (false,true)
            a=build_pair(SIDES[1],B,R,p,normalize);b=build_pair(SIDES[2],B,R,p,normalize)
            @test isequal(a,b)
        end
        for U in import_inputs()[4:5], side in SIDES
            before=snapshot(U);a=Requests()
            hot,dh=side.import_upper(U,true)
            hook,dk=side.import_upper(U,true;allocate=a)
            @test isnothing(dh) && isnothing(dk)
            @test isequal(packed_snapshot(hot),packed_snapshot(hook))
            @test [v for col in hot for v in col.values]==U.nzval
            @test snapshot(U)==before && a.count==8
        end
    end
end
function run_boundary_tests()
    boundary_request_equivalence()
    boundary_hook_order()
    boundary_hot_and_hook_agree()
end
end
