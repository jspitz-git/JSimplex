from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json']:
 with (Q/(name+'.before-review')).open('xb') as f:f.write((C/name).read_bytes())
p=C/'panel-tests.jl';t=p.read_text()
t=t.replace('decisions=Tuple{Int,Bool,Float64}[]','decisions=Tuple{Int,Bool,Float64}[]\n    pre=Tuple{Int,UInt64,UInt64,Bool}[]; touched=falses(n-r+1,b+1)')
t=t.replace('(:zero_diagonal,D,decisions)', '(:zero_diagonal,D,decisions,pre,touched)').replace('(:nonfinite,D,decisions)', '(:nonfinite,D,decisions,pre,touched)').replace('(:ok,D,decisions)', '(:ok,D,decisions,pre,touched)')
t=t.replace('swap=abs(z)>abs(a)\n', 'swap=abs(z)>abs(a)\n        push!(pre,(k,reinterpret(UInt64,a),reinterpret(UInt64,z),swap))\n')
t=t.replace('for j in r:n\n                x=pop!', 'for j in r:n\n                touched[j-r+1,k-r+1]=true;touched[j-r+1,k-r+2]=true\n                x=pop!')
t=t.replace('delete!(D,(k+1,k))','delete!(D,(k+1,k));touched[k-r+1,k-r+2]=true')
t=t.replace('v=fma(-m,D[(k,j)],get(D,(k+1,j),0.0))','v=fma(-m,D[(k,j)],get(D,(k+1,j),0.0));touched[j-r+1,k-r+2]=true')
t=t.replace('status,D,steps=oracle(A,1,8);d=K._bgb_apply!(ws,1,8,64)', 'status,D,steps,pre,touched=oracle(A,1,8)\n            observed=Tuple{Int,UInt64,UInt64,Bool}[]\n            probe=(k,a,z,swapped)->push!(observed,(k,reinterpret(UInt64,a),reinterpret(UInt64,z),swapped))\n            d=K._bgb_apply!(ws,1,8,64,probe)')
t=t.replace('@test snapshot(f)==saved\n            if d.accepted', '@test snapshot(f)==saved\n            @test observed==pre\n            if d.accepted')
t=t.replace('@test ws.steps[1].swapped == (abs(lower)>4.0)', '''@test ws.steps[1].swapped == (abs(lower)>4.0)
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
                @test J._apply_transposed_row_update!(copy(v),update)==transpose(T)*v''')
t=t.replace('status,D,_=oracle(A,r,b);@test status==:ok', 'status,D,_,_,_=oracle(A,r,b);@test status==:ok')
a=t.index('            if out.accepted\n');b=t.index('\n        end\n        # No arithmetic',a)
t=t[:a]+'''            @test out.accepted # rejection must not bypass writeback assertions
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
            @test_throws ArgumentError K._bgb_commit!(f,ws,d)''' +t[b:]
t=t.replace('owners=[c.values for c in f.upper];ws=prepared(f)', 'owners=[c.values for c in f.upper];ids=[c.indices.ids for c in f.upper];ws=prepared(f)')
t=t.replace('@test all(f.upper[j].values===owners[j] for j in 1:64)', '@test all(f.upper[j].values===owners[j] && f.upper[j].indices.ids===ids[j] for j in 1:64)')
t=t.replace('ws=prepared(f,3,8);before=unpack(f)', 'ws=prepared(f,3,8);before=unpack(f);oldvalues=f.upper[96].values;oldids=f.upper[96].indices.ids')
t=t.replace('@test d.accepted && ws.counts.values[13]==2','''@test d.accepted && ws.counts.values[13]==2
        @test f.upper[96].values!==oldvalues && f.upper[96].indices.ids!==oldids
        @test length(f.upper[96].values)==length(f.upper[96].indices.ids)==95
        @test ws.counts.values[17]==2*(96-9) # copied prefix AND suffix elements''')
# Append distinct testsets before function end.
pos=t.rindex('\nend\nend')
t=t[:pos]+'''
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
    end''' +t[pos:]
p.write_text(t)
# Exact test hash saved BEFORE adding probe to candidate; no test execution.
with (Q/'review-tests-first.json').open('x') as f:json.dump({'tests_sha256':sha(p),'candidate_before_probe_sha256':sha(C/'panel.jl'),'execution':'UNEXECUTED offline review coverage corrections'},f,indent=2)
p=C/'panel.jl';t=p.read_text().replace('function _bgb_apply!(ws,r::Int,b::Int,w::Int)', 'function _bgb_apply!(ws,r::Int,b::Int,w::Int,probe=nothing)')
t=t.replace('swapped=J._pivot_magnitude(z)>J._pivot_magnitude(a)\n', 'swapped=J._pivot_magnitude(z)>J._pivot_magnitude(a)\n        # Optional cold observer; no trace stored by the unobserved kernel.\n        probe===nothing || probe(r+t-1,a,z,swapped)\n')
p.write_text(t)
p=C/'work-memory-ledger.md';t=p.read_text();t += '''
## Independent review corrections R1–R3

All main arithmetic-to-commit fixtures now REQUIRE acceptance; no success assertion is conditional on a candidate choice. Tests additionally require positive fill-in, exact new array lengths/owners, same-support owner reuse, and three consecutive successful panels using one workspace with an independently evolved reference matrix.

A separate optional cold probe argument to apply records predecision a/z bits and strict swap decision before mutation. Default nothing stores no trace. Tests compare to an independent dictionary oracle, full touched/presence masks, .row/.last chronology and original forward/transpose history helpers with exact converted rational steps against independent elementary matrices. These are cold tests, not a new supported production scalar type, and no Julia has run. Probe callbacks that throw propagate; Task2 must discard a failed workspace rather than retry it.

Real commit fixtures compute1152 and1153 planned stores for h9/w64 by deleting row1 from eleven long columns. At the cap commit must succeed; cap+1 must refuse before row reservation, stores or allocations, preserving all input arrays/incidence/readiness. Independent expected counters cover separate eligibility/gather, every merge, prefix/suffix copied elements, actual stores and stable-ID incidence. Underflow-to-signed-zero is explicitly canonicalized; absent-source target preservation is checked.

Carrier tests intentionally hit generic no-op dense-cache invalidation; they DO NOT verify actual factor cache, prepared provenance, policy validation, adapter rejection latch or exception rollback. Those remain explicit Task2 duties. No numerical/performance acceptance is claimed by this source review.
''';p.write_text(t)
(Q/'REVIEW-FIX.md').write_text('''# R1–R3 offline coverage fix

Preserved all four pre-review deliverables. Tests strengthened before optional probe implementation. R1 removes conditional acceptance bypass and adds fill/ownership/reuse. R2 adds independent predecision-bit/mask/history/transpose/absent-source/underflow checks. R3 tests computed commit budget at cap and cap+1 with independent operation counters. Generic structural carrier is not cache/provenance evidence. No Julia/old checker/numerics or plan/gate changes. Previous source-check.json candidate/test/ledger/map bindings map ONLY to matching *.before-review files; other bindings unchanged.
''')
with (Q/'review-fix.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print('R1-R3 coverage text fixed; tests-first hash recorded before probe implementation')
