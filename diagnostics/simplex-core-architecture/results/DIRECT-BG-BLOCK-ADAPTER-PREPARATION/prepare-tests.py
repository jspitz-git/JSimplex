"""New exclusive offline Task2 test-text preparation; never imports Julia."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce';O=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
s=(O/'dynamic-bg-tests-reviewed.jl').read_text()
s=s.replace('DynamicBGTests','BlockBGTests').replace('DynamicBGFactor','BlockBGFactor').replace('_dynamic_bg','_block_bg').replace('_dbg_','_bbg_').replace('run_dynamic_bg_tests','run_block_bg_tests')
s=s.replace('include("slot-oracles.jl")','''module StorageOracles
using Test, SparseArrays
import JSimplex: BGBlockUpper, _bgu_handle, _bgu_tuple, _bgu_cid, _bgu_build,
    _bgu_build_with, _bgu_set!, _bgu_copy, _bgu_copy_with
include("block-oracles.jl")
end
const _check_block_upper=StorageOracles._bgu_check
function block_tokens(U)
    ptr=Int[1];rows=Int[];values=UInt64[]
    for cid in U.column_order
        b=Int(U.column_head[cid])
        while b!=0
            for k in 1:Int(U.count[b])
                v,r,p=J._bgu_tuple(U,J._bgu_handle(b,k))
                push!(rows,Int(U.row_position[r]));push!(values,reinterpret(UInt64,v))
            end
            b=Int(U.next[b])
        end
        push!(ptr,length(rows)+1)
    end
    return (n=U.n,colptr=ptr,rowval=rows,bits=values)
end''')
s=s.replace('_check_bg_slots','_check_block_upper').replace('_bg_selected_state','block_tokens').replace('J._bg_slots','J._bgu_build')
s=s.replace('copy(sd.upper.column_order)','Int.(sd.upper.column_order)')
s=s.replace('for i in 1:15','for i in 1:23')
s=s.replace('@test all(getfield(sd.upper,k)!==getfield(d.upper,k) for k in 1:15)','@test StorageOracles._bgu_test_disjoint(sd.upper,d.upper)')
s=s.replace('oldcapacity=d.upper.capacity;@test oldcapacity==17','oldcapacity=StorageOracles._bgu_test_capacity(d.upper);@test oldcapacity[1]==17')
s=s.replace('@test d.upper.capacity==33 && d.upper.live_count==21','@test d.upper.live==21 && StorageOracles._bgu_test_capacity(d.upper)[2]>oldcapacity[2]')
s=s.replace('Seventeen imported slots, then four new row2 entries: a real fill growth.','Seventeen imported entries, then four new row2 entries: row-gap/block growth.')
s=s.replace('const ARMS=', 'const ARMS=')
# Explicit source-independent boundary/failure oracles, enumerated before adapter text.
extra=r'''
# Task2-only coverage. Failure seams cover explicit storage requests, not arbitrary OOM.
function block_boundaries()
    @testset "Block boundaries, diagonals and contiguous solve order" begin
        for n in (0,1,31,32,33,64), (backend,policy) in ARMS
            M=sparse([i<=j ? (i==j ? 4.0 : (-1.0)^(i+j)/128) : 0.0 for i in 1:n,j in 1:n])
            q=reverse(collect(1:n));B=M[:,invperm(q)]
            exporter=x->J.BasisLUExport(spdiagm(0=>ones(n)),copy(M),collect(1:n),copy(q),ones(n),false)
            r=J._direct_lu_factor_with_exporter(J.BartelsGolubFactorization,B,Val(backend),policy,exporter;normalize=false)
            d=J._block_bg_with_exporter(B,Val(backend),policy,exporter;normalize=false)
            @test d.upper.column_order==q
            solve_pair(r,d,B,ones(n));solve_pair(r,d,B,ones(n);transposed=true)
            if n>0
                dense=Matrix(B);j,a=DirectLUFixtures.replacement(dense,0)
                replace_pair!(r,d,dense,j,a)
                J.refactorize!(r,sparse(dense));J.refactorize!(d,sparse(dense));pair_state(r,d)
            end
        end
        # Explicit signed zeros survive arithmetic; missing/Hessenberg diagonals
        # exercise original fallback rather than a new triangular-only assumption.
        for M in (SparseMatrixCSC(3,3,[1,2,4,7],[1,1,2,1,2,3],[1.,-0.,2.,0.,-0.,3.]),
                  sparse([1. 2. 0.;3. 0. 1.;0. 4. 2.]),spzeros(3,3))
            r,d=controlled_pair(M,[3,1,2]);a=[1.,-0.,2.]
            for op in (J.forward_solve!,J.transpose_solve!)
                x=zeros(3);y=zeros(3);er=try op(x,r,a);nothing catch e;e end
                ed=try op(y,d,a);nothing catch e;e end
                @test typeof(er)===typeof(ed)
                @test bits(x)==bits(y)
                @test _check_block_upper(d.upper)
            end
        end
        # Pure rotation across block boundary: exact history run and logical U.
        for n in (33,64)
            q=reverse(collect(1:n));r,d=controlled_pair(spdiagm(0=>ones(n)),q)
            J.replace_column!(r,ones(n),q[1];zero_tolerance=0.0)
            J.replace_column!(d,ones(n),q[1];zero_tolerance=0.0)
            @test history(r)==history(d)==[[(1,n-1,true,reinterpret(UInt64,0.0))]]
            pair_state(r,d)
        end
        # Elimination fills into full columns (split), cancels target entries,
        # and reloads source handles repaired by each insertion/deletion.
        n=64
        for q in (collect(1:n),reverse(collect(1:n)))
            M=sparse([i==1 || (j%2==0 && i==2) || (3<=i<=33) ? 1.0 : 0.0 for i in 1:n,j in 1:n])
            r,d=controlled_pair(M,q);J._ensure_bartels_golub_incidence!(r)
            trace=Int[]
            for cid in r.row_columns[1]
                col=r.positions[cid];col<=1 && continue;push!(trace,cid)
                U=r.upper[col];s,old=J._upper_entry(U,2)
                J._set_upper_value_at!(r.upper,r.row_columns,col,2,old-J._upper_value(U,1),s,cid)
            end
            observed=Int[];J._bbg_eliminate_row!(d,1,1.0,cid->push!(observed,cid))
            @test trace==observed
            @test isequal(packed_tokens(r),block_tokens(d.upper)) && _check_block_upper(d.upper)
        end
    end
end
struct StorageFailure <: Exception end
function refusal_seam(stop,calls)
    return (T,n)->begin
        calls[]+=1;calls[]==stop && throw(StorageFailure());Vector{T}(undef,n)
    end
end
function storage_failure_boundaries()
    @testset "Setup copy refactor reserves and failed update boundary" begin
        B=spdiagm(0=>[2.,3.,4.]);original=copy(B)
        for (backend,policy) in ARMS
            d=J._block_bg_factor(B,Val(backend),policy)
            saved=J.copy_basis_factorization(d);savedstate=snapshot(saved)
            # Allocate failures only at Task1 storage seam; lower factor/export
            # setup is real and must be counted in a future exact admission.
            for operation in (:setup,:copy,:refactor)
                held=owners(d);before=snapshot(d);calls=Ref(0)
                function attempt(allocate)
                    build=(A,q)->J._bgu_build_with(A,q,allocate,typemax(Int32))
                    if operation===:setup
                        return J._block_bg_with_exporter(B,Val(backend),policy,J._export_basis_lu;build)
                    elseif operation===:copy
                        return J._block_bg_copy_with(d,U->J._bgu_copy_with(U,allocate))
                    else
                        return J._block_bg_refactor_with_exporter!(d,B,J._export_basis_lu;build)
                    end
                end
                attempt(refusal_seam(typemax(Int),calls));total=calls[];@test total>0
                # Successful copy/refactor is preparation, snapshot again.
                held=owners(d);before=snapshot(d)
                for stop in 1:total
                    count=Ref(0);@test_throws StorageFailure attempt(refusal_seam(stop,count))
                    @test count[]==stop
                    assert_owners(d,held);@test isequal(snapshot(d),before)
                    @test _check_block_upper(d.upper)
                    @test isequal(snapshot(saved),savedstate)
                end
            end
            @test isequal(B,original)
            @test StorageOracles._bgu_test_disjoint(d.upper,saved.upper)
        end
        # Overflow rejected before backend; no huge allocation is attempted.
        calls=Ref(0);factorize=(args...)->(calls[]+=1;error("backend must not run"))
        @test_throws OverflowError J._block_bg_with_exporter(B,Val(:native),J._NATIVE_PIVOT_ONE,J._export_basis_lu;limit=3,factorize)
        @test calls[]==0
        # Force a storage failure after mutation began. No success history or
        # solve after failure; refactor is the only recovery exercised here.
        for stop in (1,2)
            r,d=controlled_pair(spdiagm(0=>ones(33)),collect(1:33))
            saved=J.copy_basis_factorization(d);before=snapshot(saved);calls=Ref(0)
            @test_throws StorageFailure J._block_bg_replace!(d,ones(33),1,0.0;allocate=refusal_seam(stop,calls))
            @test isempty(d.updates) && !d.row_cache.upper_prefix_safe
            @test all(isnothing(e.destination) for e in (isnothing(d.row_cache.prepared) ? () : d.row_cache.prepared.entries))
            @test _check_block_upper(d.upper)
            @test isequal(snapshot(saved),before)
            J.refactorize!(d,spdiagm(0=>ones(33)))
            @test isempty(d.updates) && isnothing(d.row_cache.prepared)
        end
    end
end
function new_scratch_aliases()
    @testset "New block scratch aliases reject before dimension backend" begin
        u=J._bgu_build(spdiagm(0=>ones(3)),collect(1:3))
        f=J.BlockBGFactor(RejectBackend(),u,J.BartelsGolubUpdate{Float64}[],zeros(3),zeros(3),
            J.BartelsGolubUpdate{Float64}[],0,J.TriangularRowCache(Float64,3))
        for op in (J.forward_solve!,J.transpose_solve!)
            @test_throws ArgumentError op(f.upper.scratch_value,f,ones(3))
            @test_throws ArgumentError op(f.work,f,ones(3))
        end
    end
end
'''
s=s.replace('function run_block_bg_tests()\n    lifecycles();rejection_and_aliases();export_modes();focused_updates()\nend',extra+'\nfunction run_block_bg_tests()\n    lifecycles();rejection_and_aliases();export_modes();focused_updates()\n    block_boundaries();storage_failure_boundaries();new_scratch_aliases()\nend')
assert 'function block_boundaries' in s and '_bg_slots' not in s
s=s.replace('# UNEXECUTED Task2 tests. Future driver must explicitly call run_block_bg_tests().','# UNEXECUTED Task2 tests. A future separately admitted driver must call run_block_bg_tests().')
for name,data in [('block-bg-tests.jl',s.encode()),('fixtures.jl',(O/'fixtures.jl').read_bytes())]:
 with (C/name).open('xb') as f:f.write(data)
record=dict(scope='Test text written before adapter; no Julia and no runtime assertions executed',source=str(O/'dynamic-bg-tests-reviewed.jl'),source_sha256=hashlib.sha256((O/'dynamic-bg-tests-reviewed.jl').read_bytes()).hexdigest(),sha256={str(C/n):hashlib.sha256((C/n).read_bytes()).hexdigest() for n in ['block-bg-tests.jl','fixtures.jl']},self_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (E/'tests-first.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('UNEXECUTED tests/fixtures written before adapter')
