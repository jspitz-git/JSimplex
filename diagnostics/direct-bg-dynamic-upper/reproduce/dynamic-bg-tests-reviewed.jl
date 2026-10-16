# UNEXECUTED Task2 tests. Future driver must explicitly call run_dynamic_bg_tests().
module DynamicBGTests
using Test, LinearAlgebra, SparseArrays, JSimplex
const J=JSimplex
include("fixtures.jl")
include("slot-oracles.jl")
const ARMS=((:native,J._NATIVE_PIVOT_ONE),(:markowitz,J._NATIVE_PIVOT_DEFAULT))
bits(v)=collect(reinterpret(UInt64,v))
history(f)=[[(s.row,s.last,s.swapped,reinterpret(UInt64,s.multiplier)) for s in u.steps] for u in f.updates]
function packed_tokens(f)
    ptr=Int[1];rows=Int[];values=UInt64[]
    for col in f.upper
        append!(rows,collect(col.indices));append!(values,bits(col.values));push!(ptr,length(rows)+1)
    end
    return (n=length(f.upper),colptr=ptr,rowval=rows,bits=values)
end
function pair_state(r,d)
    @test _check_bg_slots(d.upper)
    @test isequal(packed_tokens(r),_bg_selected_state(d.upper))
    @test r.column_order==d.upper.column_order && r.positions==d.upper.column_position
    @test all(d.upper.row_position[d.upper.row_order[i]]==i for i in 1:d.upper.n)
    @test isequal(history(r),history(d))
    @test J._direct_mode(r)==J._dynamic_bg_mode(d)
    @test r.row_cache.upper_prefix_safe==d.row_cache.upper_prefix_safe
    @test r.row_cache.upper_prefix_candidate==d.row_cache.upper_prefix_candidate
    @test J._factor_storage_count(r)==J._dynamic_bg_storage_count(d)
    @test isequal(J._factor_growth_measure(r),J._dynamic_bg_growth(d))
end
function solve_pair(r,d,B,rhs;transposed=false,unit=0)
    op=transposed ? J.transpose_solve! : J.forward_solve!
    a=zeros(length(rhs));b=similar(a);before=bits(rhs)
    rr=unit==0 ? rhs : J._unit_transpose_rhs(r,rhs,unit)
    dd=unit==0 ? rhs : J._unit_transpose_rhs(d,rhs,unit)
    op(a,r,rr);op(b,d,dd)
    @test bits(a)==bits(b)
    @test DirectLUFixtures.solve_residual(B,a,rhs;transposed)
    @test DirectLUFixtures.solve_residual(B,b,rhs;transposed)
    @test bits(rhs)==before
    pair_state(r,d)
    return a,b
end
function replace_pair!(r,d,B,j,a)
    before=bits(a);dr,dd=solve_pair(r,d,B,a)
    solve_pair(r,d,B,collect(1.0:length(a))./max(1,length(a)))
    @test J._copy_prepared_spike!(r,dr) && J._dbg_copy_prepared!(d,dd)
    J.replace_column!(r,dr,j);J.replace_column!(d,dd,j)
    @test !J._copy_prepared_spike!(r,dr) && !J._dbg_copy_prepared!(d,dd)
    @test bits(a)==before
    B[:,j]=a;pair_state(r,d)
    unit=zeros(length(a));unit[j]=1
    solve_pair(r,d,B,unit;transposed=true,unit=j)
    return nothing
end
owners(d)=(Tuple(getfield(d,i) for i in 1:fieldcount(typeof(d))),
    Tuple(getfield(d.upper,i) for i in 1:15))
function snapshot(d)
    c=d.row_cache
    return (_bg_selected_state(d.upper),copy(d.upper.row_order),copy(d.upper.column_order),
      history(d),bits(d.work),bits(d.spike),copy(c.order),copy(c.operations),c.update_count,
      c.permuted,copy(c.active_upper),c.upper_dirty,c.upper_dirty_from,c.upper_prefix_safe,
      c.upper_prefix_candidate,d.shared_update_count)
end
function assert_owners(d,o)
    @test all(getfield(d,i)===o[1][i] for i in eachindex(o[1]))
    @test all(getfield(d.upper,i)===o[2][i] for i in eachindex(o[2]))
end
function lifecycles()
    @testset "Seven fixed fixtures, two policies, direct reference" begin
        for fixture in DirectLUFixtures.export_fixtures(), (backend,policy) in ARMS
            input=fixture.B;inputbits=bits(input.nzval);B=Matrix(input);n=size(B,1)
            r=J._direct_lu_factor(J.BartelsGolubFactorization,input,Val(backend),policy;normalize=true)
            d=J._dynamic_bg_factor(input,Val(backend),policy)
            pair_state(r,d);solve_pair(r,d,B,ones(n));solve_pair(r,d,B,ones(n);transposed=true)
            saved=nothing;savedB=nothing
            if n>=2
                for t in 0:7
                    j,a=DirectLUFixtures.replacement(B,t);replace_pair!(r,d,B,j,a)
                    if t==1
                        sr=J.copy_basis_factorization(r);sd=J.copy_basis_factorization(d)
                        saved=(sr,sd);savedB=copy(B)
                        @test all(getfield(sd.upper,k)!==getfield(d.upper,k) for k in 1:15)
                        @test sd.base.work!==d.base.work && sd.work!==d.work && sd.spike!==d.spike
                        @test isnothing(sd.row_cache.prepared)
                        @test d.shared_update_count==length(d.updates)==sd.shared_update_count
                        @test all(sd.updates[k]===d.updates[k] for k in eachindex(d.updates))
                        a2=savedB[:,1]+[i==2 ? 1/64 : 0.0 for i in 1:n]
                        replace_pair!(sr,sd,savedB,1,a2)
                    end
                    if t in (3,7)
                        J.refactorize!(r,sparse(B));J.refactorize!(d,sparse(B))
                        @test isempty(d.updates) && isnothing(d.row_cache.prepared)
                        @test d.base.pivot_policy===policy && d.base.normalize_requested
                        pair_state(r,d)
                    end
                    isnothing(saved) || solve_pair(saved[1],saved[2],savedB,ones(n))
                end
            end
            before=snapshot(d);held=owners(d)
            @test_throws SingularException J.refactorize!(d,DirectLUFixtures.singular_basis())
            assert_owners(d,held);@test isequal(snapshot(d),before)
            sentinel=ErrorException("export failure")
            caught=try J._dynamic_bg_refactor_with_exporter!(d,sparse(B),x->throw(sentinel));nothing catch e;e end
            @test caught===sentinel;assert_owners(d,held);@test isequal(snapshot(d),before)
            solve_pair(r,d,B,ones(n))
            for newB in (spdiagm(0=>[2.,3.,4.]),spzeros(0,0))
                J.refactorize!(r,newB);J.refactorize!(d,newB)
                solve_pair(r,d,newB,ones(size(newB,1)))
                @test d.base.pivot_policy===policy && d.base.normalize_requested
            end
            @test bits(input.nzval)==inputbits
            isnothing(saved) || solve_pair(saved[1],saved[2],savedB,ones(n))
        end
    end
end

# Test-only owned nominal backend: unsupported routes must not touch even dimension.
struct RejectBackend end
J._backend_dimension(::RejectBackend)=error("unexpected dimension call")
J._backend_forward_solve!(out,::RejectBackend,rhs)=error("unexpected FTRAN")
J._backend_transpose_solve!(out,::RejectBackend,rhs)=error("unexpected BTRAN")
function rejection_and_aliases()
    @testset "Private scratch and supported routes" begin
        B=spdiagm(0=>[2.,3.,4.]);rhs=[1.,-0.,2.]
        for (backend,policy) in ARMS
            r=J._direct_lu_factor(J.BartelsGolubFactorization,B,Val(backend),policy)
            d=J._dynamic_bg_factor(B,Val(backend),policy)
            for op in (J.forward_solve!,J.transpose_solve!)
                a=copy(rhs);b=copy(rhs);op(a,r,a);op(b,d,b);@test bits(a)==bits(b)
                @test_throws ArgumentError op(d.work,d,rhs)
                @test_throws DimensionMismatch op(zeros(4),d,rhs)
                copyto!(r.work,rhs);copyto!(d.work,rhs)
                op(r.spike,r,r.work);op(d.spike,d,d.work);@test bits(r.spike)==bits(d.spike)
            end
            dr,dd=solve_pair(r,d,B,rhs)
            equalcopy=copy(dd);@test !J._dbg_copy_prepared!(d,equalcopy)
            dd[2]=iszero(dd[2]) ? -dd[2] : nextfloat(dd[2])
            @test !J._dbg_copy_prepared!(d,dd)
            # BTRAN destroys provenance even if it happens to write equal values.
            dr,dd=solve_pair(r,d,B,ones(3))
            J.transpose_solve!(dr,r,ones(3));J.transpose_solve!(dd,d,ones(3))
            @test !J._copy_prepared_spike!(r,dr) && !J._dbg_copy_prepared!(d,dd)
            before=snapshot(d)
            for tol in (-1.0,Inf,NaN)
                @test_throws ArgumentError J.replace_column!(d,ones(3),1;zero_tolerance=tol)
            end
            @test_throws DimensionMismatch J.replace_column!(d,ones(4),1)
            @test_throws BoundsError J.replace_column!(d,ones(3),0)
            @test_throws ZeroPivotException J.replace_column!(d,zeros(3),1)
            @test isequal(snapshot(d),before)
        end
        u=J._bg_slots(spdiagm(0=>ones(3)),collect(1:3))
        f=J.DynamicBGFactor(RejectBackend(),u,J.BartelsGolubUpdate{Float64}[],
            zeros(3),zeros(3),J.BartelsGolubUpdate{Float64}[],0,J.TriangularRowCache(Float64,3))
        idx=J.IndexedVector{Float64}(3)
        for op in (J.forward_solve!,J.transpose_solve!)
            for mode in (:sparse,:dense,:auto)
                @test_throws ArgumentError op(idx,f,idx;kernel_mode=mode)
                @test_throws ArgumentError op(zeros(3),f,ones(3);kernel_mode=mode)
            end
            @test_throws ArgumentError op(zeros(Float32,3),f,ones(Float32,3))
            @test_throws ArgumentError op(zeros(3),f,view(ones(3),:))
        end
        @test_throws ArgumentError J.replace_column!(f,idx,1)
        @test_throws ArgumentError J.replace_column!(f,ones(Float32,3),1)
        calls=Ref(0);factorize=(args...)->(calls[]+=1;error("unexpected factorization"))
        for (backend,policy) in ((:native,J._NATIVE_PIVOT_DEFAULT),(:markowitz,J._NATIVE_PIVOT_ONE),(:unknown,J._NATIVE_PIVOT_ONE))
            @test_throws ArgumentError J._dynamic_bg_with_exporter(B,Val(backend),policy,J._export_basis_lu;factorize)
        end
        @test calls[]==0
        @test_throws ArgumentError J._dynamic_bg_factor(Float32.(B),Val(:native),J._NATIVE_PIVOT_ONE)
    end
end

function export_modes()
    @testset "Fallback, normalization fallback, q, transactional refactor" begin
        # A supplied exact export with explicit nonidentity q; real backend setup
        # still occurs. Identity L and scaling make this an independent identity.
        U=sparse([2. 1. 0.;0. 3. 1.;0. 0. 4.]);q=[3,1,2]
        exporter=x->J.BasisLUExport(spdiagm(0=>ones(3)),copy(U),collect(1:3),copy(q),ones(3),false)
        for (backend,policy) in ARMS
            B=U[:,invperm(q)]
            r=J._direct_lu_factor_with_exporter(J.BartelsGolubFactorization,B,Val(backend),policy,exporter)
            d=J._dynamic_bg_with_exporter(B,Val(backend),policy,exporter)
            @test d.upper.column_order==q
            @test DirectLUFixtures.export_identity(B,exporter(nothing))
            for t in 0:2
                j,a=DirectLUFixtures.replacement(Matrix(B),t)
                dense=Matrix(B);replace_pair!(r,d,dense,j,a);B=sparse(dense)
            end
            sr=J.copy_basis_factorization(r);sd=J.copy_basis_factorization(d)
            solve_pair(sr,sd,B,ones(3))
            J._direct_refactorize_with_exporter!(r,B,x->nothing)
            J._dynamic_bg_refactor_with_exporter!(d,B,x->nothing)
            @test J._dynamic_bg_mode(d)==:fallback
            solve_pair(r,d,B,ones(3));solve_pair(sr,sd,B,ones(3))
            J.refactorize!(r,B);J.refactorize!(d,B)
            @test J._dynamic_bg_mode(d)==:normalized
            solve_pair(r,d,B,ones(3))
        end
        # Unsafe normalization must keep a valid exported U, not reject/drop it.
        V=sparse([floatmin(Float64) floatmax(Float64);0. 1.])
        supplied=x->J.BasisLUExport(spdiagm(0=>ones(2)),copy(V),[1,2],[2,1],ones(2),false)
        B0=spdiagm(0=>ones(2))
        r=J._direct_lu_factor_with_exporter(J.BartelsGolubFactorization,B0,Val(:native),J._NATIVE_PIVOT_ONE,supplied)
        d=J._dynamic_bg_with_exporter(B0,Val(:native),J._NATIVE_PIVOT_ONE,supplied)
        @test J._dynamic_bg_mode(d)==:direct;pair_state(r,d) # no solve claim for deliberately substituted export
    end
end

function controlled_pair(M,q)
    n=size(M,1);B=spdiagm(0=>ones(n))
    exporter=x->J.BasisLUExport(spdiagm(0=>ones(n)),copy(M),collect(1:n),copy(q),ones(n),false)
    r=J._direct_lu_factor_with_exporter(J.BartelsGolubFactorization,B,Val(:native),J._NATIVE_PIVOT_ONE,exporter;normalize=false)
    d=J._dynamic_bg_with_exporter(B,Val(:native),J._NATIVE_PIVOT_ONE,exporter;normalize=false)
    return r,d
end
function focused_updates()
    @testset "Exact storage branches, failures, ordering" begin
        for (M,q,a,j,expected) in (
            (sparse(reshape([1.],1,1)),[1],[2.],1,Tuple{Int,Int,Bool,Float64}[]),
            (spdiagm(0=>ones(3)),[3,1,2],[1.,2.,3.],3,[(1,2,true,0.0)]),
            (sparse([1. 1. 0.;0. 1. 1.;0. 0. 1.]),[1,2,3],[1.,1.,1.],1,[(1,1,false,1.0),(2,2,false,1.0)]),
            (spdiagm(0=>ones(4)),[4,2,1,3],[1.,1.,1.,1.],4,[(1,3,true,0.0)]),
            (sparse([1. 0. 2.;0. 1. 0.;0. 0. 1.]),[1,2,3],[1.,0.,1.],1,[(1,1,true,0.0),(2,2,false,0.5)]))
            r,d=controlled_pair(M,q)
            # Prepared spiked values are deliberately supplied without another solve;
            # compare reconstruction, not a claimed public-factor witness.
            er=try J.replace_column!(r,copy(a),j;zero_tolerance=0.0);nothing catch e;e end
            ed=try J.replace_column!(d,copy(a),j;zero_tolerance=0.0);nothing catch e;e end
            @test isnothing(er) && isnothing(ed)
            @test length(r.updates)==length(d.updates)==1
            @test history(r)==history(d)==[[(a,b,c,reinterpret(UInt64,m)) for (a,b,c,m) in expected]]
            pair_state(r,d)
        end
        # Exact zero pivot fails after mutation; prefix eligibility/cache invalidation
        # is compared, no solve of the partially failed state follows.
        for M in (spzeros(3,3),sparse([1. Inf 0.;0. 1. NaN;0. 0. 1.]))
            r,d=controlled_pair(M,[1,2,3]);nr=length(r.updates);nd=length(d.updates)
            er=try J.replace_column!(r,ones(3),1;zero_tolerance=0.0);nothing catch e;e end
            ed=try J.replace_column!(d,ones(3),1;zero_tolerance=0.0);nothing catch e;e end
            if nnz(M)==0
                @test er isa ZeroPivotException && ed isa ZeroPivotException
                @test er.info==ed.info==1
            else
                @test isnothing(er) && isnothing(ed)
                @test length(r.updates)==nr+1 && length(d.updates)==nd+1
                @test !d.row_cache.upper_prefix_safe
            end
            @test isequal(history(r),history(d)) && _check_bg_slots(d.upper)
            @test r.row_cache.upper_prefix_safe==d.row_cache.upper_prefix_safe
            if !isnothing(er)
                @test length(r.updates)==nr && length(d.updates)==nd
                @test !d.row_cache.upper_prefix_safe
            end
        end
        # Finite inputs, overflow in elimination: max - 1*(-max) = +Inf.
        m=floatmax(Float64);M=sparse([1. 1. -m;0. 1. m;0. 0. 1.])
        @test all(isfinite,M.nzval)
        r,d=controlled_pair(M,[1,2,3])
        er=try J.replace_column!(r,[1.,0.,0.],1;zero_tolerance=0.0);nothing catch e;e end
        ed=try J.replace_column!(d,[1.,0.,0.],1;zero_tolerance=0.0);nothing catch e;e end
        @test isnothing(er) && isnothing(ed)
        @test J._upper_value(r.upper[2],2)==J._dbg_value(d.upper,2,2)==Inf
        @test !r.row_cache.upper_prefix_safe && !d.row_cache.upper_prefix_safe
        pair_state(r,d) # no solve of this nonfinite factor

        # Force distinct physical maps in a TEST-OWNED copied arena. Actual copy
        # preserves its IDs; this deliberate exact rebase exercises the independent
        # upper/history map handoff without changing production copy semantics.
        B=Matrix{Float64}(I,4,4);r,d=controlled_pair(sparse(B),collect(1:4))
        replace_pair!(r,d,B,1,ones(4))
        sr=J.copy_basis_factorization(r);sd=J.copy_basis_factorization(d)
        logical=_bg_selected_state(sd.upper)
        A=SparseMatrixCSC(logical.n,logical.n,copy(logical.colptr),copy(logical.rowval),
            collect(reinterpret(Float64,logical.bits)))
        sd.upper=J._bg_slots(A,copy(sd.upper.column_order))
        J._dbg_sync_rows!(sd);J._sync_triangular_rows!(sr)
        @test sd.upper.row_order!=sd.row_cache.order
        @test J._upper_order(sr.upper).order!=sr.row_cache.order
        solve_pair(sr,sd,B,ones(4));solve_pair(sr,sd,B,ones(4);transposed=true)
        j,a=DirectLUFixtures.replacement(B,1);replace_pair!(sr,sd,B,j,a)
        # Seventeen imported slots, then four new row2 entries: a real fill growth.
        # Deliberately nontriangular storage oracle; no solve/pivot claim.
        M=sparse([1. 1. 1. 1. 1.;1. 0. 0. 0. 0.;1. 1. 1. 1. 1.;
                  1. 1. 1. 1. 1.;1. 0. 0. 0. 0.])
        r,d=controlled_pair(M,collect(1:5));J._ensure_bartels_golub_incidence!(r)
        oldcapacity=d.upper.capacity;@test oldcapacity==17
        for cid in r.row_columns[1]
            trailing=r.positions[cid];trailing<=1 && continue
            col=r.upper[trailing];slot,old=J._upper_entry(col,2)
            J._set_upper_value_at!(r.upper,r.row_columns,trailing,2,
                old-J._upper_value(col,1),slot,cid)
        end
        J._dbg_eliminate_row!(d,1,1.0)
        @test d.upper.capacity==33 && d.upper.live_count==21
        @test isequal(packed_tokens(r),_bg_selected_state(d.upper)) && _check_bg_slots(d.upper)
        # Direct row-merge oracle, including insertion/deletion while traversing.
        for q in ([1,2,3,4],[4,2,1,3])
            M=sparse([2. 1. 1. 0.;0. 1. 0. 1.;0. 0. 1. 0.;0. 0. 0. 1.])
            r,d=controlled_pair(M,q);J._ensure_bartels_golub_incidence!(r)
            trace=Int[]
            for cid in r.row_columns[1]
                trailing=r.positions[cid];trailing<=1 && continue
                push!(trace,cid);col=r.upper[trailing]
                s,old=J._upper_entry(col,2);v=J._upper_value(col,1)
                J._set_upper_value_at!(r.upper,r.row_columns,trailing,2,old-v,s,cid)
            end
            observed=Int[];J._dbg_eliminate_row!(d,1,1.0,cid->push!(observed,cid))
            @test observed==trace
            @test isequal(packed_tokens(r),_bg_selected_state(d.upper))
            @test _check_bg_slots(d.upper)
        end
    end
end
function run_dynamic_bg_tests()
    lifecycles();rejection_and_aliases();export_modes();focused_updates()
end
end
