# UNEXECUTED Task1 tests. Load in a parent containing JSimplex and BGBlockedPanel.
module BGBlockedPanelTests
using ..HarnessRecords: @check, @checkthrows
import ..HarnessRecords
using Test
using LinearAlgebra: I
import ..JSimplex
import ..BGBlockedPanel
const J = JSimplex
const K = BGBlockedPanel

# No factorization/solve: actual production packed types with a structural carrier.
mutable struct Carrier
    upper::Vector{J.PackedUpperColumn{Float64,J.UpperRowIndices}}
    column_order::Vector{Int}
    positions::Vector{Int}
    row_columns::Vector{Vector{Int}}
    row_cache::J.TriangularRowCache{Float64}
    sparse::Nothing
    row_columns_ready::Bool
end
function carrier(A; reverse_rows=false, reverse_columns=false)
    n = size(A, 1)
    order = J.UpperRowOrder(n)
    if reverse_rows
        order.order .= n:-1:1
        order.positions .= n:-1:1
    end
    upper = [J.PackedUpperColumn{Float64}(J.UpperRowIndices(
        [order.order[i] for i in 1:n if !iszero(A[i,j])], order),
        [A[i,j] for i in 1:n if !iszero(A[i,j])]) for j in 1:n]
    columns = reverse_columns ? collect(n:-1:1) : collect(1:n)
    positions = invperm(columns)
    rows = [[id for id in 1:n if !iszero(A[i,positions[id]])] for i in 1:n]
    return Carrier(upper,columns,positions,rows,J.TriangularRowCache(Float64,n),nothing,true)
end
function denseband(n)
    A = zeros(n,n)
    for j in 1:n, i in 1:min(n,j+1)
        A[i,j] = i == j ? 4.0 : (i == j+1 ? 0.25 : 0.125)
    end
    A
end
unpack(f) = [J._upper_value(f.upper[j],i) for i in 1:length(f.upper), j in 1:length(f.upper)]
snapshot(f) = ([copy(c.indices.ids) for c in f.upper], [copy(c.values) for c in f.upper], deepcopy(f.row_columns))
bits(A) = reinterpret(UInt64, vec(copy(A)))

# Independent scalar oracle: dictionary structural presence, logical row-major loops.
function oracle(A, r, b)
    n=size(A,1); D=Dict((i,j)=>A[i,j] for j in r:n for i in r:r+b if !iszero(A[i,j]))
    decisions=Tuple{Int,Bool,Float64}[]
    pre=Tuple{Int,UInt64,UInt64,Bool}[]; touched=falses(n-r+1,b+1)
    for k in r:r+b-1
        a=get(D,(k,k),0.0); z=get(D,(k+1,k),0.0)
        iszero(a) && return (:zero_diagonal,D,decisions,pre,touched)
        swap=abs(z)>abs(a)
        push!(pre,(k,reinterpret(UInt64,a),reinterpret(UInt64,z),swap))
        if swap
            for j in r:n
                touched[j-r+1,k-r+1]=true;touched[j-r+1,k-r+2]=true
                x=pop!(D,(k,j),nothing); y=pop!(D,(k+1,j),nothing)
                isnothing(y) || (D[(k,j)]=y)
                isnothing(x) || (D[(k+1,j)]=x)
            end
        end
        m=get(D,(k+1,k),0.0)/D[(k,k)]
        isfinite(m) || return (:nonfinite,D,decisions,pre,touched)
        delete!(D,(k+1,k));touched[k-r+1,k-r+2]=true
        if !iszero(m)
            for j in k+1:n
                haskey(D,(k,j)) || continue
                v=fma(-m,D[(k,j)],get(D,(k+1,j),0.0));touched[j-r+1,k-r+2]=true
                isfinite(v) || return (:nonfinite,D,decisions,pre,touched)
                if iszero(v); delete!(D,(k+1,j)); else; D[(k+1,j)]=v; end
            end
        end
        push!(decisions,(k,swap,m))
    end
    (:ok,D,decisions,pre,touched)
end
function prepared(f,r=1,b=8)
    ws=K.BGPanelWorkspace(length(f.upper); counted=true)
    K._bgb_gather!(ws,f,r,b)
    ws
end
# P011 repair helpers: cold test code; no calls at include time.
# Explicit argument avoids the macro closure over the reassigned testset local f.
p011_eligibility(f::Carrier)::K.BGPanelDecision = K._bgb_eligibility(f,1)
function p011_consume!(sink::Base.RefValue{K.BGPanelDecision}, f::Carrier)
    sink[] = p011_eligibility(f)
    nothing
end
function p011_expected(d::K.BGPanelDecision)
    d.start == 1 && d.count == 0 && !d.accepted && d.reason === :dimensions &&
        d.finite && d.counters == (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
end
# Every Carrier field's value, packed contents, row order, and cache fields.
# Selected mutable owners are retained only for this cold n32 assertion group.
function p011_state(f::Carrier)
    cache = f.row_cache
    cache.prepared === nothing && f.sparse === nothing || error("Unexpected P011 cache")
    order = f.upper[1].indices.order
    values = (snapshot(f), copy(order.order), copy(order.positions),
        copy(f.column_order), copy(f.positions), f.row_columns_ready,
        Tuple(deepcopy(getfield(cache,k)) for k in fieldnames(typeof(cache))))
    owners = Any[f, f.upper, f.column_order, f.positions, f.row_columns, cache,
        order, order.order, order.positions]
    append!(owners,f.row_columns)
    for col in f.upper
        append!(owners,(col.values,col.indices.ids,col.indices.order))
    end
    for k in fieldnames(typeof(cache))
        x = getfield(cache,k)
        x isa AbstractArray && push!(owners,x)
    end
    (values=values,owners=owners)
end
function p011_probe(f::Carrier)
    before = p011_state(f)
    sentinel = K.BGPanelDecision(0,0,false,:uninitialized,false,
        (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
    sink = Ref(sentinel)
    # Five warm calls, including both allocation meters and observable-result arms.
    warm = p011_eligibility(f)
    Base.allocated(p011_eligibility,f)
    Base.allocations(p011_eligibility,f)
    Base.allocated(p011_consume!,sink,f)
    Base.allocations(p011_consume!,sink,f)
    # Four measured calls. Snapshot/Ref/record/Test costs are outside these meters.
    bytes = Base.allocated(p011_eligibility,f)
    events = Base.allocations(p011_eligibility,f)
    sink[] = sentinel
    consumed_bytes = Base.allocated(p011_consume!,sink,f)
    bytes_decision = sink[]
    sink[] = sentinel
    consumed_events = Base.allocations(p011_consume!,sink,f)
    events_decision = sink[]
    after = p011_state(f)
    (bytes=bytes,events=events,consumed_bytes=consumed_bytes,consumed_events=consumed_events,
        warm=warm,bytes_decision=bytes_decision,events_decision=events_decision,
        values_unchanged=isequal(before.values,after.values),
        owners_unchanged=length(before.owners)==length(after.owners) &&
            all(a === b for (a,b) in zip(before.owners,after.owners)))
end

function run_task1_tests()
    @testset "budget and cheap eligibility" begin
        for n in (32,64,96,4096,4097)
            d=K._bgb_dimensions(n,1)
            @check "P001" d.accepted == (64<=n<=4096)
        end
        @check "P002" !K._bgb_dimensions(96,34).accepted # width63
        @check "P003" K._bgb_dimensions(96,33).accepted # width64
        @check "P004" !K._bgb_dimensions(64,61).accepted # only3steps
        @check "P005" !K._bgb_dimensions(64,60).accepted # 4steps, width gate
        @check "P006" K._bgb_store_budget(1152,9,64)
        @check "P007" !K._bgb_store_budget(1153,9,64)
        @checkthrows "P008" OverflowError K._bgb_charge(typemax(Int))
        @checkthrows "P009" ArgumentError K.BGPanelWorkspace(4097)
        @check "P010" K._bgb_charge(4096) <= 2^20
        # Cold typed probe; no macro capture of the reassigned testset local f.
        f=carrier(zeros(32,32)); p011=p011_probe(f)
        @check "P011" p011.bytes == 0
        @check "P095" p011.events == 0
        @check "P096" p011.consumed_bytes == 0
        @check "P097" p011.consumed_events == 0
        @check "P098" p011_expected(p011.warm)
        @check "P099" p011_expected(p011.bytes_decision)
        @check "P100" p011_expected(p011.events_decision)
        @check "P101" p011.values_unchanged
        @check "P102" p011.owners_unchanged
        @check "P012" K._bgb_eligibility(f,1).counters == ntuple(_->0,20)
        for count in (287,288)
            A=zeros(64,64)
            for x in 1:count
                i=mod(x-1,9)+1; j=div(x-1,9)+1; A[i,j]=1.0
            end
            @check "P013" K._bgb_eligibility(carrier(A),1).accepted == (count==288)
        end
        f=carrier(denseband(64)); @check "P014" K._bgb_eligibility(f,1).accepted
        for value in (0.0,-0.0,Inf,NaN)
            g=carrier(denseband(64));g.upper[end].values[1]=value
            @check "P015" K._bgb_eligibility(g,1).reason == :invalid_input
        end
    end
    @testset "independent arithmetic, policy and canonical zeros" begin
        for lower in (0.0,0.25,4.0,8.0,-8.0), reversed in (false,true)
            A=denseband(64);A[2,1]=lower
            f=carrier(A;reverse_rows=reversed); saved=snapshot(f);ws=prepared(f)
            status,D,steps,pre,touched=oracle(A,1,8)
            observed=Tuple{Int,UInt64,UInt64,Bool}[]
            probe=(k,a,z,swapped)->push!(observed,(k,reinterpret(UInt64,a),reinterpret(UInt64,z),swapped))
            d=K._bgb_apply!(ws,1,8,64,probe)
            @check "P016" d.accepted == (status==:ok)
            @check "P017" snapshot(f)==saved
            @check "P018" observed==pre
            if d.accepted
                for i in 1:9,j in 1:64
                    @check "P019" isequal(ws.values[j,i],get(D,(i,j),0.0))
                    @check "P020" ws.present[j,i] == haskey(D,(i,j))
                end
                @check "P021" [(ws.steps[t].row,ws.steps[t].swapped,ws.steps[t].multiplier) for t in 1:8] == steps
                @check "P022" ws.steps[1].swapped == (abs(lower)>4.0)
                @check "P023" all(ws.steps[k].last==ws.steps[k].row==k for k in 1:8)
                @check "P024" ws.touched[1:64,1:9]==touched
                # Independent exact elementary matrices from oracle decisions;
                # compare original history forward AND transpose implementations.
                RT=Rational{BigInt}; T=Matrix{RT}(I,9,9)
                for (k,sw,m) in steps
                    if sw;T[k,:],T[k+1,:]=copy(T[k+1,:]),copy(T[k,:]);end
                    T[k+1,:] .-= RT(m).*T[k,:]
                end
                exactsteps=[J.BartelsGolubStep{RT}(s.row,s.last,s.swapped,RT(s.multiplier)) for s in ws.steps]
                update=J.BartelsGolubUpdate{RT}(exactsteps);v=RT.(1:9)
                @check "P025" J._apply_row_update!(copy(v),update)==T*v
                @check "P026" J._apply_transposed_row_update!(copy(v),update)==transpose(T)*v
            end
        end
        for k in (1,4,8)
            A=Matrix{Float64}(I,64,64); A[k,k]=0.0
            # Zero subdiagonals prevent earlier steps changing selected diagonal.
            ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
            @check "P027" !d.accepted && d.reason==:zero_diagonal && d.finite
        end
        # Pure lookahead may cross panel end. Panel must reject without touching U.
        A=denseband(64);A[1,:].=0.0;f=carrier(A);saved=snapshot(f)
        d=K._bgb_apply!(prepared(f),1,8,64)
        @check "P028" !d.accepted && d.reason==:zero_diagonal && snapshot(f)==saved
        A=Matrix{Float64}(I,64,64);A[2,1]=1.0;A[1,10]=1.0;A[2,10]=1.0
        A[1,11]=nextfloat(0.0);A[2,11]=0.0
        ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
        @check "P029" d.accepted
        @check "P030" !ws.present[10,2] && isequal(ws.values[10,2],0.0)
        @check "P031" ws.values[11,2] == -nextfloat(0.0)
        A=Matrix{Float64}(I,64,64);A[2,1]=1.0;A[1,10]=-floatmax(Float64);A[2,10]=floatmax(Float64)
        ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
        @check "P032" !d.accepted && !d.finite && d.reason==:nonfinite
        @checkthrows "P033" ArgumentError K._bgb_apply!(ws,1,8,64) # single-use private panel
    end
    @testset "packed commit, incidence, support and source counters" begin
        for reverse_rows in (false,true), reverse_columns in (false,true)
            A=denseband(96);r=3;b=8;A[r,r-1]=0.0;f=carrier(A;reverse_rows,reverse_columns)
            saved=snapshot(f);order=copy(f.upper[1].indices.order.order)
            ws=prepared(f,r,b);d=K._bgb_apply!(ws,r,b,94)
            @check "P034" d.accepted
            status,D,_,_,_=oracle(A,r,b);@check "P035" status==:ok
            out=K._bgb_commit!(f,ws,d)
            @check "P036" out.accepted # rejection must not bypass writeback assertions
            expected=copy(A)
            for i in r:r+b,j in r:96;expected[i,j]=get(D,(i,j),0.0);end
            @check "P037" bits(unpack(f))==bits(expected)
            @check "P038" f.upper[1].indices.order.order==order
            @check "P039" all(f.row_columns[i]==[id for id in 1:96 if !iszero(expected[i,f.positions[id]])] for i in 1:96)
            @check "P040" ws.counts.values[15]==96
            @check "P041" ws.counts.values[12] <= 2*9*94
            @check "P042" ws.counts.values[11]==ws.counts.values[12]
            @check "P043" ws.counts.values[18]==94
            @check "P044" ws.counts.values[19]==9
            @checkthrows "P045" ArgumentError K._bgb_commit!(f,ws,d)
        end
        # No arithmetic, same support: all interval owners remain unchanged.
        f=carrier(denseband(64));owners=[c.values for c in f.upper];ids=[c.indices.ids for c in f.upper];ws=prepared(f)
        ws.phase=0x02;d=K._bgb_decision(ws,true,:ok,true)
        @check "P046" K._bgb_commit!(f,ws,d).accepted
        @check "P047" all(f.upper[j].values===owners[j] && f.upper[j].indices.ids===ids[j] for j in 1:64)
        @check "P048" ws.counts.values[13]==0 # fresh column arrays
        # Long prefix: changed support in every trailing column exceeds fixed cap.
        A=denseband(96);A[33,32]=0.0;f=carrier(A);ws=prepared(f,33,8);saved=snapshot(f)
        for j in 1:64
            ws.present[j,1]=!ws.present[j,1];ws.values[j,1]=ws.present[j,1] ? 2.0 : 0.0
        end
        ws.phase=0x02;d=K._bgb_decision(ws,true,:ok,true)
        @check "P049" K._bgb_commit!(f,ws,d).reason==:store_budget
        @check "P050" snapshot(f)==saved && ws.counts.values[13]==0
        # One support change: copied outside-band values and physical IDs stay exact.
        A=denseband(96);A[3,2]=0.0;f=carrier(A;reverse_rows=true);ws=prepared(f,3,8);before=unpack(f);oldvalues=f.upper[96].values;oldids=f.upper[96].indices.ids
        ws.present[94,1]=false;ws.values[94,1]=0.0;ws.phase=0x02
        d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
        @check "P051" d.accepted && ws.counts.values[13]==2
        @check "P052" f.upper[96].values!==oldvalues && f.upper[96].indices.ids!==oldids
        @check "P053" length(f.upper[96].values)==length(f.upper[96].indices.ids)==95
        @check "P054" ws.counts.values[17]==2*(96-9) # copied prefix AND suffix elements
        expected=copy(before);expected[3,96]=0.0
        @check "P055" bits(unpack(f))==bits(expected)
        @check "P056" ws.counts.values[14]==16*(length(f.upper[96].values)+1+length(f.upper[96].values))
        @check "P057" ws.counts.values[1]==0 # separate eligibility, not hidden in gather
        @check "P058" ws.counts.values[2]==2*94*3 # gather, budget, commit two searches each
        @check "P059" ws.counts.values[20]==9*94 # row-capacity prepass
        @check "P060" ws.owner===nothing && ws.phase==0x00
        @check "P061" all(iszero(before[i,j]) for i in 3:11 for j in 1:2)
        # Repeated adversarial support proposals always refuse before allocating.
        for r in (17,25,33)
            A=denseband(96);A[r,r-1]=0.0;f=carrier(A);saved=snapshot(f)
            ws=prepared(f,r,8)
            for j in 1:ws.width
                ws.present[j,1]=false;ws.values[j,1]=0.0
            end
            ws.phase=0x02
            d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
            @check "P062" d.reason==:store_budget
            @check "P063" ws.counts.values[12]==0 && ws.counts.values[13]==0
            @check "P064" snapshot(f)==saved && ws.owner===nothing
        end
        # Four-step internal panel boundary; width admission remains independent.
        ws=prepared(carrier(denseband(64)),1,4)
        @check "P065" K._bgb_apply!(ws,1,4,64).accepted
    end
    @testset "computed commit cap and independent work witnesses" begin
        for extra in (false,true)
            A=zeros(64,64)
            for j in 54:64;A[1:(j==64 ? 57 : 53),j].=1.0;end
            extra && (A[1,1]=1.0)
            f=carrier(A;reverse_rows=true,reverse_columns=true);saved=snapshot(f)
            ws=prepared(f)
            for j in 54:64;ws.present[j,1]=false;ws.values[j,1]=0.0;end
            ws.phase=0x02
            d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
            @check "P066" ws.counts.values[11]==1152+Int(extra)
            if extra
                @check "P067" !d.accepted && d.reason==:store_budget
                @check "P068" snapshot(f)==saved && f.row_columns_ready
                @check "P069" all(ws.counts.values[k]==0 for k in (12,13,14,15,16,18,19,20))
            else
                @check "P070" d.accepted && ws.counts.values[12]==1152
                @check "P071" ws.counts.values[13]==22
                @check "P072" ws.counts.values[18]==64
                @check "P073" ws.counts.values[17]==2*(10*(53-9)+(57-9))
                A[1,54:64].=0.0;@check "P074" bits(unpack(f))==bits(A)
                @check "P075" all(f.row_columns[i]==[id for id in 1:64 if !iszero(A[i,f.positions[id]])] for i in 1:64)
            end
        end
        A=denseband(64);f=carrier(A);c=K.BGPanelCounts()
        d=K._bgb_eligibility(f,1,c);@check "P076" d.accepted
        @check "P077" c.values[1]==sum(!iszero(A[i,j]) for i in 1:9,j in 1:64)
        @check "P078" c.values[2]==128 && c.values[3]>0
        ws=prepared(f);@check "P079" ws.counts.values[1]==0 && ws.counts.values[2]==128
        @check "P080" ws.counts.values[4]==c.values[1]
        # Positive fill: new packed entry, new owner, new stable-ID incidence.
        A=Matrix{Float64}(I,64,64);f=carrier(A;reverse_rows=true,reverse_columns=true)
        old=f.upper[64];ws=prepared(f);ws.present[64,1]=true;ws.values[64,1]=2.0
        ws.phase=0x02;d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
        @check "P081" d.accepted && f.upper[64].values!==old.values && f.upper[64].indices.ids!==old.indices.ids
        @check "P082" length(f.upper[64].values)==2 && length(f.upper[64].indices.ids)==2
        A[1,64]=2.0;@check "P083" bits(unpack(f))==bits(A)
        @check "P084" f.row_columns[1]==sort([f.column_order[1],f.column_order[64]])
        # Reuse the same tile for multiple successful adjacent panels; independent
        # expected matrix evolves from each dictionary oracle, never from factors.
        A=denseband(96);f=carrier(A);ws=K.BGPanelWorkspace(96;counted=true)
        for r in (1,9,17)
            @check "P085" K._bgb_eligibility(f,r).accepted
            K._bgb_gather!(ws,f,r,8);d=K._bgb_apply!(ws,r,8,97-r)
            @check "P086" d.accepted
            status,D,_,_,_=oracle(A,r,8);@check "P087" status==:ok
            out=K._bgb_commit!(f,ws,d);@check "P088" out.accepted
            for i in r:r+8,j in r:96;A[i,j]=get(D,(i,j),0.0);end
            @check "P089" bits(unpack(f))==bits(A)
            @check "P090" ws.owner===nothing && ws.phase==0x00
            @check "P091" all(f.row_columns[i]==[id for id in 1:96 if !iszero(A[i,f.positions[id]])] for i in 1:96)
        end
        # Source absence preserves target exactly; tiny multiplication rounds to
        # zero and must delete presence and canonicalize the -0 result to +0.
        A=Matrix{Float64}(I,64,64);A[1,1]=2.0;A[2,1]=1.0
        A[2,12]=3.0;A[1,13]=nextfloat(0.0)
        ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
        @check "P092" d.accepted && ws.values[12,2]==3.0 && ws.present[12,2]
        @check "P093" !ws.touched[12,2]
        @check "P094" !ws.present[13,2] && isequal(ws.values[13,2],0.0) && ws.touched[13,2]
    end
end
end
