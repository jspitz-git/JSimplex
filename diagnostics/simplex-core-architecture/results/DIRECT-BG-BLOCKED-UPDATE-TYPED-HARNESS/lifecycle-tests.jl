# UNEXECUTED Task2 source. Fault modules are isolated exact-inverse clones.
module BGBlockedLifecycleTests
using ..HarnessRecords: @check, @checkthrows
import ..HarnessRecords
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
    f=HarnessRecords.api("factory_micro",module_._bgb_factor,sparse(Matrix{Float64}(I,n,n)),Val(:native),J._NATIVE_PIVOT_ONE)
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
        B=upper_fixture(96);before=copy(B);f=HarnessRecords.api("factory_candidate",A._bgb_factor,B,Val(backend),policy)
        @check "L001" f.workspace===nothing && !f.busy && B==before
        # Two prepared RHS, then identical last-column replacement (no elimination).
        j=f.inner.column_order[end];@check "L002" f.inner.positions[j]==96
        a=Vector(B[:,j]);x=zeros(96);v=similar(x)
        HarnessRecords.api("FTRAN",J.forward_solve!,x,f,a);HarnessRecords.api("FTRAN",J.forward_solve!,v,f,ones(96))
        @check "L003" any(e.destination===x for e in f.inner.row_cache.prepared.entries)
        old=length(f.inner.updates);HarnessRecords.api("replace",J.replace_column!,f,x,j)
        @check "L004" length(f.inner.updates)==old+1 && isempty(f.inner.updates[end].steps) && f.workspace===nothing
        saved=HarnessRecords.api("copy",J.copy_basis_factorization,f)
        @check "L005" saved.workspace===nothing && saved.inner.upper!==f.inner.upper
        @check "L006" all(a.values!==b.values && a.indices.ids!==b.indices.ids for (a,b) in zip(saved.inner.upper,f.inner.upper))
        oldsaved=N.unpack(saved.inner)
        newer=Vector(B[:,1]);newer[2]+=1/32
        HarnessRecords.api("FTRAN",J.forward_solve!,x,f,newer);HarnessRecords.api("replace",J.replace_column!,f,x,1)
        changed=copy(B);changed[:,1]=newer
        HarnessRecords.api("FTRAN",J.forward_solve!,x,f,ones(96));HarnessRecords.api("FTRAN",J.forward_solve!,v,saved,ones(96))
        @check "L007" N.residual(changed,x,ones(96)) && N.residual(B,v,ones(96))
        # A copy of a used, possibly scratch-owning factor is also cache-empty.
        usedcopy=HarnessRecords.api("copy",J.copy_basis_factorization,f)
        @check "L008" usedcopy.workspace===nothing && usedcopy.inner.updates!==f.inner.updates
        # First-use/reuse workspace ownership is tested without assuming a given LU ordering.
        f.workspace=K.BGPanelWorkspace(96);owner=f.workspace
        HarnessRecords.api("refactor",J.refactorize!,f,copy(B));@check "L009" f.workspace===owner
        HarnessRecords.api("refactor",J.refactorize!,f,upper_fixture(64));@check "L010" f.workspace===nothing
        f.workspace=K.BGPanelWorkspace(64)
        HarnessRecords.api("refactor",J.refactorize!,f,upper_fixture(32));@check "L011" f.workspace===nothing
        @check "L012" N.bits(N.unpack(saved.inner))==N.bits(oldsaved)
        f.busy=true
        try
            @checkthrows "L013" ArgumentError HarnessRecords.api("replace",J.replace_column!,f,ones(32),1)
            @checkthrows "L014" ArgumentError HarnessRecords.api("refactor",J.refactorize!,f,upper_fixture(32))
            @checkthrows "L015" ArgumentError HarnessRecords.api("copy",J.copy_basis_factorization,f)
            @checkthrows "L016" ArgumentError HarnessRecords.api("FTRAN",J.forward_solve!,zeros(32),f,ones(32))
            @checkthrows "L017" ArgumentError HarnessRecords.api("BTRAN",J.transpose_solve!,zeros(32),f,ones(32))
        finally
            f.busy=false
        end
        @checkthrows "L018" ArgumentError HarnessRecords.api("replace",J.replace_column!,f,ones(32),1;zero_tolerance=-1.0)
        @check "L019" failed_cache(f)
    end
    # Exact separated pivots, multiple panels, shadow/history oracle; no LU solves.
    for n in (96,256)
        f=micro(band(n));t=N.Trace();HarnessRecords.api("eliminate",A._bgb_test_eliminate!,f,1;probe=t)
        @check "L020" t.panels>=2 && t.rejections<=1
        @check "L021" N.relation(N.unpack(f.inner),t.T,t.H)
        @check "L022" K._bgb_charge(n)<=2^20
    end
    # An explicit stored zero in the second band rejects after a committed panel.
    M=band(96);M[10,20]=0.0;f=micro(M)
    col=f.inner.upper[20];slot=searchsortedfirst(col.indices,10)
    insert!(col.indices,slot,10);insert!(col.values,slot,0.0)
    f.inner.row_columns_ready=false
    J._ensure_bartels_golub_incidence!(f.inner)
    t=N.Trace();HarnessRecords.api("eliminate",A._bgb_test_eliminate!,f,1;probe=t)
    @check "L023" t.panels==1 && t.rejections==1
    @check "L024" count(==(:eligibility),t.events)==2
    # Private failure after arithmetic: overflow of first elimination, original
    # suffix retained; prefix safety must stay false even if later values cancel.
    M=band(96);M[1,1]=1.0;M[2,1]=1.0;M[1,2]=-floatmax(Float64);M[2,2]=floatmax(Float64)
    f=micro(M);events=Symbol[]
    try HarnessRecords.api("eliminate",A._bgb_test_eliminate!,f,1;probe=(e,args...)->push!(events,e)) catch e
        HarnessRecords.tick("catch_overflow");@check "L025" e isa LinearAlgebra.ZeroPivotException
    end
    @check "L026" count(==(:panel_reject),events)==1 && count(==(:eligibility),events)==1
    @check "L027" !f.inner.row_cache.upper_prefix_safe && !f.inner.row_cache.upper_prefix_candidate
    # Explicit zero diagonal with no swap: original scalar failure, no safe cache.
    M=band(96);M[1,1]=0;M[2,1]=0;f=micro(M)
    @checkthrows "L028" LinearAlgebra.ZeroPivotException HarnessRecords.api("eliminate",A._bgb_test_eliminate!,f,1)
    @check "L029" failed_cache(f)
    # Nonfinite admission declines, even when no panel scratch was allocated.
    for value in (Inf,NaN)
        M=band(96);M[1,20]=value;f=micro(M);events=Symbol[]
        try HarnessRecords.api("eliminate",A._bgb_test_eliminate!,f,1;probe=(e,args...)->push!(events,e)) catch e
            HarnessRecords.tick("catch_nonfinite");@check "L030" e isa LinearAlgebra.ZeroPivotException
        end
        @check "L031" count(==(:eligibility),events)==1 && count(==(:panel_reject),events)==1
        @check "L032" !f.inner.row_cache.upper_prefix_safe
    end
    # Exceptions inside gather, reserve and writeback are injected in a separate
    # exact-inverse kernel clone. They propagate; partial mutation is allowed.
    for point in (:gather,:reserve,:writeback)
        f=micro(band(96);fault=true);FK.arm!(point,OutOfMemoryError())
        caught=nothing
        try HarnessRecords.api("eliminate_fault",F._bgb_test_eliminate!,f,1) catch e;caught=e;end
        @check "L033" caught===FK.sentinel[] && FK.hits[]==1
        @check "L034" failed_cache(f)
        @check "L035" isempty(f.inner.updates)
        FK.disarm!()
    end
    # Fail in the second writeback, after one complete panel changed live U.
    # This checks cleanup after partial progress, not rollback.
    f=micro(band(96);fault=true);FK.disarm!()
    events=Symbol[];begins=Ref(0);sentinel=OutOfMemoryError()
    late=(e,args...)->begin
        push!(events,e)
        if e===:panel_begin
            begins[]+=1
            begins[]==2 && FK.arm!(:writeback,sentinel)
        end
    end
    caught=nothing
    try HarnessRecords.api("eliminate_fault",F._bgb_test_eliminate!,f,1;probe=late) catch e;caught=e;end
    @check "L036" caught===sentinel && FK.hits[]==1 && begins[]==2
    @check "L037" count(==(:panel_commit),events)==1 && !(:finish in events)
    @check "L038" isempty(f.inner.updates) && failed_cache(f)
    FK.disarm!()
    # Callback reentrancy fails before an inner solve; outer failure drops scratch.
    f=micro(band(96));entered=Ref(0)
    p=(e,args...)->begin
        if e===:panel_begin
            entered[]+=1;HarnessRecords.api("FTRAN",J.forward_solve!,zeros(96),f,ones(96))
        end
    end
    @checkthrows "L039" ArgumentError HarnessRecords.api("eliminate",A._bgb_test_eliminate!,f,1;probe=p)
    @check "L040" entered[]==1 && failed_cache(f)
 end
 nothing
end
end
