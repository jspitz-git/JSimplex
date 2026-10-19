# UNEXECUTED Task1 tests. Load in a parent containing JSimplex and BGBlockedPanel.
module BGBlockedPanelTests
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
function run_task1_tests()
    @testset "budget and cheap eligibility" begin
        for n in (32,64,96,4096,4097)
            d=K._bgb_dimensions(n,1)
            @test d.accepted == (64<=n<=4096)
        end
        @test !K._bgb_dimensions(96,34).accepted # width63
        @test K._bgb_dimensions(96,33).accepted # width64
        @test !K._bgb_dimensions(64,61).accepted # only3steps
        @test !K._bgb_dimensions(64,60).accepted # 4steps, width gate
        @test K._bgb_store_budget(1152,9,64)
        @test !K._bgb_store_budget(1153,9,64)
        @test_throws OverflowError K._bgb_charge(typemax(Int))
        @test_throws ArgumentError K.BGPanelWorkspace(4097)
        @test K._bgb_charge(4096) <= 2^20
        # Two identical calls after warm compilation: future harness admits execution.
        f=carrier(zeros(32,32)); K._bgb_eligibility(f,1)
        @test (@allocated K._bgb_eligibility(f,1)) == 0
        @test K._bgb_eligibility(f,1).counters == ntuple(_->0,20)
        for count in (287,288)
            A=zeros(64,64)
            for x in 1:count
                i=mod(x-1,9)+1; j=div(x-1,9)+1; A[i,j]=1.0
            end
            @test K._bgb_eligibility(carrier(A),1).accepted == (count==288)
        end
        f=carrier(denseband(64)); @test K._bgb_eligibility(f,1).accepted
        for value in (0.0,-0.0,Inf,NaN)
            g=carrier(denseband(64));g.upper[end].values[1]=value
            @test K._bgb_eligibility(g,1).reason == :invalid_input
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
            @test d.accepted == (status==:ok)
            @test snapshot(f)==saved
            @test observed==pre
            if d.accepted
                for i in 1:9,j in 1:64
                    @test isequal(ws.values[j,i],get(D,(i,j),0.0))
                    @test ws.present[j,i] == haskey(D,(i,j))
                end
                @test [(ws.steps[t].row,ws.steps[t].swapped,ws.steps[t].multiplier) for t in 1:8] == steps
                @test ws.steps[1].swapped == (abs(lower)>4.0)
                @test all(ws.steps[k].last==ws.steps[k].row==k for k in 1:8)
                @test ws.touched[1:64,1:9]==touched
                # Independent exact elementary matrices from oracle decisions;
                # compare original history forward AND transpose implementations.
                RT=Rational{BigInt}; T=Matrix{RT}(I,9,9)
                for (k,sw,m) in steps
                    if sw;T[k,:],T[k+1,:]=copy(T[k+1,:]),copy(T[k,:]);end
                    T[k+1,:] .-= RT(m).*T[k,:]
                end
                exactsteps=[J.BartelsGolubStep{RT}(s.row,s.last,s.swapped,RT(s.multiplier)) for s in ws.steps]
                update=J.BartelsGolubUpdate{RT}(exactsteps);v=RT.(1:9)
                @test J._apply_row_update!(copy(v),update)==T*v
                @test J._apply_transposed_row_update!(copy(v),update)==transpose(T)*v
            end
        end
        for k in (1,4,8)
            A=Matrix{Float64}(I,64,64); A[k,k]=0.0
            # Zero subdiagonals prevent earlier steps changing selected diagonal.
            ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
            @test !d.accepted && d.reason==:zero_diagonal && d.finite
        end
        # Pure lookahead may cross panel end. Panel must reject without touching U.
        A=denseband(64);A[1,:].=0.0;f=carrier(A);saved=snapshot(f)
        d=K._bgb_apply!(prepared(f),1,8,64)
        @test !d.accepted && d.reason==:zero_diagonal && snapshot(f)==saved
        A=Matrix{Float64}(I,64,64);A[2,1]=1.0;A[1,10]=1.0;A[2,10]=1.0
        A[1,11]=nextfloat(0.0);A[2,11]=0.0
        ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
        @test d.accepted
        @test !ws.present[10,2] && isequal(ws.values[10,2],0.0)
        @test ws.values[11,2] == -nextfloat(0.0)
        A=Matrix{Float64}(I,64,64);A[2,1]=1.0;A[1,10]=-floatmax(Float64);A[2,10]=floatmax(Float64)
        ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
        @test !d.accepted && !d.finite && d.reason==:nonfinite
        @test_throws ArgumentError K._bgb_apply!(ws,1,8,64) # single-use private panel
    end
    @testset "packed commit, incidence, support and source counters" begin
        for reverse_rows in (false,true), reverse_columns in (false,true)
            A=denseband(96);r=3;b=8;A[r,r-1]=0.0;f=carrier(A;reverse_rows,reverse_columns)
            saved=snapshot(f);order=copy(f.upper[1].indices.order.order)
            ws=prepared(f,r,b);d=K._bgb_apply!(ws,r,b,94)
            @test d.accepted
            status,D,_,_,_=oracle(A,r,b);@test status==:ok
            out=K._bgb_commit!(f,ws,d)
            @test out.accepted # rejection must not bypass writeback assertions
            expected=copy(A)
            for i in r:r+b,j in r:96;expected[i,j]=get(D,(i,j),0.0);end
            @test bits(unpack(f))==bits(expected)
            @test f.upper[1].indices.order.order==order
            @test all(f.row_columns[i]==[id for id in 1:96 if !iszero(expected[i,f.positions[id]])] for i in 1:96)
            @test ws.counts.values[15]==96
            @test ws.counts.values[12] <= 2*9*94
            @test ws.counts.values[11]==ws.counts.values[12]
            @test ws.counts.values[18]==94
            @test ws.counts.values[19]==9
            @test_throws ArgumentError K._bgb_commit!(f,ws,d)
        end
        # No arithmetic, same support: all interval owners remain unchanged.
        f=carrier(denseband(64));owners=[c.values for c in f.upper];ids=[c.indices.ids for c in f.upper];ws=prepared(f)
        ws.phase=0x02;d=K._bgb_decision(ws,true,:ok,true)
        @test K._bgb_commit!(f,ws,d).accepted
        @test all(f.upper[j].values===owners[j] && f.upper[j].indices.ids===ids[j] for j in 1:64)
        @test ws.counts.values[13]==0 # fresh column arrays
        # Long prefix: changed support in every trailing column exceeds fixed cap.
        A=denseband(96);A[33,32]=0.0;f=carrier(A);ws=prepared(f,33,8);saved=snapshot(f)
        for j in 1:64
            ws.present[j,1]=!ws.present[j,1];ws.values[j,1]=ws.present[j,1] ? 2.0 : 0.0
        end
        ws.phase=0x02;d=K._bgb_decision(ws,true,:ok,true)
        @test K._bgb_commit!(f,ws,d).reason==:store_budget
        @test snapshot(f)==saved && ws.counts.values[13]==0
        # One support change: copied outside-band values and physical IDs stay exact.
        A=denseband(96);A[3,2]=0.0;f=carrier(A;reverse_rows=true);ws=prepared(f,3,8);before=unpack(f);oldvalues=f.upper[96].values;oldids=f.upper[96].indices.ids
        ws.present[94,1]=false;ws.values[94,1]=0.0;ws.phase=0x02
        d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
        @test d.accepted && ws.counts.values[13]==2
        @test f.upper[96].values!==oldvalues && f.upper[96].indices.ids!==oldids
        @test length(f.upper[96].values)==length(f.upper[96].indices.ids)==95
        @test ws.counts.values[17]==2*(96-9) # copied prefix AND suffix elements
        expected=copy(before);expected[3,96]=0.0
        @test bits(unpack(f))==bits(expected)
        @test ws.counts.values[14]==16*(length(f.upper[96].values)+1+length(f.upper[96].values))
        @test ws.counts.values[1]==0 # separate eligibility, not hidden in gather
        @test ws.counts.values[2]==2*94*3 # gather, budget, commit two searches each
        @test ws.counts.values[20]==9*94 # row-capacity prepass
        @test ws.owner===nothing && ws.phase==0x00
        @test all(iszero(before[i,j]) for i in 3:11 for j in 1:2)
        # Repeated adversarial support proposals always refuse before allocating.
        for r in (17,25,33)
            A=denseband(96);A[r,r-1]=0.0;f=carrier(A);saved=snapshot(f)
            ws=prepared(f,r,8)
            for j in 1:ws.width
                ws.present[j,1]=false;ws.values[j,1]=0.0
            end
            ws.phase=0x02
            d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
            @test d.reason==:store_budget
            @test ws.counts.values[12]==0 && ws.counts.values[13]==0
            @test snapshot(f)==saved && ws.owner===nothing
        end
        # Four-step internal panel boundary; width admission remains independent.
        ws=prepared(carrier(denseband(64)),1,4)
        @test K._bgb_apply!(ws,1,4,64).accepted
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
            @test ws.counts.values[11]==1152+Int(extra)
            if extra
                @test !d.accepted && d.reason==:store_budget
                @test snapshot(f)==saved && f.row_columns_ready
                @test all(ws.counts.values[k]==0 for k in (12,13,14,15,16,18,19,20))
            else
                @test d.accepted && ws.counts.values[12]==1152
                @test ws.counts.values[13]==22
                @test ws.counts.values[18]==64
                @test ws.counts.values[17]==2*(10*(53-9)+(57-9))
                A[1,54:64].=0.0;@test bits(unpack(f))==bits(A)
                @test all(f.row_columns[i]==[id for id in 1:64 if !iszero(A[i,f.positions[id]])] for i in 1:64)
            end
        end
        A=denseband(64);f=carrier(A);c=K.BGPanelCounts()
        d=K._bgb_eligibility(f,1,c);@test d.accepted
        @test c.values[1]==sum(!iszero(A[i,j]) for i in 1:9,j in 1:64)
        @test c.values[2]==128 && c.values[3]>0
        ws=prepared(f);@test ws.counts.values[1]==0 && ws.counts.values[2]==128
        @test ws.counts.values[4]==c.values[1]
        # Positive fill: new packed entry, new owner, new stable-ID incidence.
        A=Matrix{Float64}(I,64,64);f=carrier(A;reverse_rows=true,reverse_columns=true)
        old=f.upper[64];ws=prepared(f);ws.present[64,1]=true;ws.values[64,1]=2.0
        ws.phase=0x02;d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
        @test d.accepted && f.upper[64].values!==old.values && f.upper[64].indices.ids!==old.indices.ids
        @test length(f.upper[64].values)==2 && length(f.upper[64].indices.ids)==2
        A[1,64]=2.0;@test bits(unpack(f))==bits(A)
        @test f.row_columns[1]==sort([f.column_order[1],f.column_order[64]])
        # Reuse the same tile for multiple successful adjacent panels; independent
        # expected matrix evolves from each dictionary oracle, never from factors.
        A=denseband(96);f=carrier(A);ws=K.BGPanelWorkspace(96;counted=true)
        for r in (1,9,17)
            @test K._bgb_eligibility(f,r).accepted
            K._bgb_gather!(ws,f,r,8);d=K._bgb_apply!(ws,r,8,97-r)
            @test d.accepted
            status,D,_,_,_=oracle(A,r,8);@test status==:ok
            out=K._bgb_commit!(f,ws,d);@test out.accepted
            for i in r:r+8,j in r:96;A[i,j]=get(D,(i,j),0.0);end
            @test bits(unpack(f))==bits(A)
            @test ws.owner===nothing && ws.phase==0x00
            @test all(f.row_columns[i]==[id for id in 1:96 if !iszero(A[i,f.positions[id]])] for i in 1:96)
        end
        # Source absence preserves target exactly; tiny multiplication rounds to
        # zero and must delete presence and canonicalize the -0 result to +0.
        A=Matrix{Float64}(I,64,64);A[1,1]=2.0;A[2,1]=1.0
        A[2,12]=3.0;A[1,13]=nextfloat(0.0)
        ws=prepared(carrier(A));d=K._bgb_apply!(ws,1,8,64)
        @test d.accepted && ws.values[12,2]==3.0 && ws.present[12,2]
        @test !ws.touched[12,2]
        @test !ws.present[13,2] && isequal(ws.values[13,2],0.0) && ws.touched[13,2]
    end
end
end
