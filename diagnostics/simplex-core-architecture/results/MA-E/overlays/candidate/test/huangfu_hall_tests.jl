using Test, JSimplex, SparseArrays, LinearAlgebra, Random
function equation_error(B,x,rhs)
    norm(B*x-rhs,Inf)/max(opnorm(B,Inf)*norm(x,Inf)+norm(rhs,Inf),floatmin(Float64))
end
@testset "Huangfu-Hall middle product form" begin
    @test isdefined(JSimplex, :HuangfuHallFactorization)
    if isdefined(JSimplex, :HuangfuHallFactorization)
        rng = MersenneTwister(7129)
        for n in (0, 1, 7, 25), scaled in (false, true)
            B = Matrix{Float64}(I,n,n) + 0.1randn(rng,n,n)
            if scaled && n>0
                B = Diagonal(10.0 .^ (n==1 ? [0.0] : range(-3,3;length=n))) * B[:,randperm(rng,n)]
            end
            f = JSimplex.HuangfuHallFactorization(sparse(B))
            x=zeros(n);y=zeros(n);rhs=randn(rng,n)
            for step in 0:(n==0 ? 0 : 30)
                if step>0
                    p=mod1(step,n)
                    new=copy(B[:,p])+0.01B*randn(rng,n)
                    JSimplex.forward_solve!(x,f,new)
                    if step%3==0
                        # A changed solve invalidates the cached direction; updates
                        # must also work with an independently supplied direction.
                        JSimplex.forward_solve!(y,f,rhs)
                    end
                    JSimplex.replace_column!(f,x,p)
                    B[:,p]=new
                end
                JSimplex.forward_solve!(x,f,rhs)
                @test equation_error(B,x,rhs) <= 1e-12
                @test x ≈ B\rhs rtol=1e-9 atol=1e-10
                JSimplex.transpose_solve!(x,f,rhs)
                @test equation_error(transpose(B),x,rhs) <= 1e-12
                @test x ≈ transpose(B)\rhs rtol=1e-9 atol=1e-10
                for transposed in (false,true)
                    copyto!(y,rhs)
                    op=transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                    op(y,f,y)
                    @test equation_error(transposed ? transpose(B) : B,y,rhs) <= 1e-12
                end
                if step>0 && step%10==0
                    saved=JSimplex.copy_basis_factorization(f)
                    JSimplex.refactorize!(f,sparse(2B))
                    @test JSimplex.forward_solve(f,rhs) ≈ (2B)\rhs
                    @test JSimplex.forward_solve(saved,rhs) ≈ B\rhs
                    JSimplex.refactorize!(f,sparse(B))
                    @test isempty(f.updates)
                end
            end
            if n>0
                # Modifying a prepared direction must use the supplied values.
                JSimplex.forward_solve!(x,f,B[:,1]);x[1]*=1.01
                new=B*x;JSimplex.replace_column!(f,x,1);B[:,1]=new
                @test JSimplex.forward_solve(f,rhs) ≈ B\rhs
                for op in (JSimplex.forward_solve!,JSimplex.transpose_solve!)
                    copyto!(f.work,rhs);op(y,f,f.work)
                    @test y ≈ (op===JSimplex.forward_solve! ? B\rhs : transpose(B)\rhs)
                    @test_throws ArgumentError op(f.work,f,rhs)
                    @test_throws DimensionMismatch op(zeros(n+1),f,rhs)
                end
                before=JSimplex.forward_solve(f,rhs);age=length(f.updates)
                @test_throws LinearAlgebra.ZeroPivotException JSimplex.replace_column!(f,zeros(n),1)
                @test_throws ArgumentError JSimplex.replace_column!(f,fill(NaN,n),1)
                @test_throws ArgumentError JSimplex.replace_column!(f,ones(n),1;zero_tolerance=-1)
                @test_throws DimensionMismatch JSimplex.replace_column!(f,zeros(n+1),1)
                @test_throws BoundsError JSimplex.replace_column!(f,ones(n),n+1)
                @test_throws Exception JSimplex.refactorize!(f,spzeros(n,n))
                @test JSimplex.forward_solve(f,rhs) == before
                @test length(f.updates)==age
            end
        end
    end
end


function sparse_update_bytes(n)
    f=JSimplex.HuangfuHallFactorization(spdiagm(0=>ones(n)))
    direction=zeros(n);direction[1]=2.0;direction[end]=1e-200
    # Reconstruct from the supplied direction, including a very small nonzero.
    bytes=@allocated JSimplex.replace_column!(f,direction,1)
    t=only(f.updates)
    @test t.u_indices==[1,n] && t.u_values==[1.0,1e-200]
    @test t.v_indices==[1] && t.v_values==[1.0]
    bytes
end
@testset "Sparse MPF packing allocation" begin
    sparse_update_bytes(8)
    @test sparse_update_bytes(100_000)<4096
end

@testset "Refactorization scratch, copies and failure isolation" begin
    B=sparse([3.0 1 0; 2 4 1; 0 1 5]);rhs=[1.0,2,3]
    f=JSimplex.HuangfuHallFactorization(B)
    saved=JSimplex.copy_basis_factorization(f)
    work=f.work;aux=f.auxiliary
    JSimplex.refactorize!(f,2B)
    @test f.work===work && f.auxiliary===aux
    @test JSimplex.forward_solve(f,rhs) ≈ (2B)\rhs
    @test JSimplex.forward_solve(saved,rhs) ≈ B\rhs
    @test_throws Exception JSimplex.refactorize!(f,spzeros(3,3))
    @test JSimplex.forward_solve(f,rhs) ≈ (2B)\rhs
    JSimplex.refactorize!(saved,3B)
    JSimplex.refactorize!(f,4B)
    @test JSimplex.forward_solve(saved,rhs) ≈ (3B)\rhs
    @test JSimplex.forward_solve(f,rhs) ≈ (4B)\rhs
    JSimplex.refactorize!(f,spdiagm(0=>ones(5)))
    @test JSimplex.forward_solve(f,ones(5))==ones(5)
    JSimplex.refactorize!(f,spzeros(0,0))
    @test isempty(JSimplex.forward_solve(f,Float64[]))
    JSimplex.refactorize!(f,B)
    @test JSimplex.forward_solve(f,rhs) ≈ B\rhs
end

@testset "Reachable unit transpose solve" begin
    @test isdefined(JSimplex,:_hh_unit_transpose!)
    if isdefined(JSimplex,:_hh_unit_transpose!)
        rng=MersenneTwister(178)
        for n in (1,9,40), density in (0.0,0.1,1.0)
            B=triu(sprand(rng,n,n,density))+spdiagm(0=>fill(2.0,n))
            f=JSimplex.HuangfuHallFactorization(B)
            for p in reverse(1:n)
                expected=zeros(n);expected[p]=1.0
                JSimplex._hh_upper!(expected,f.base,true)
                actual=JSimplex._hh_unit_transpose!(f,p)
                @test all(i->iszero(expected[i]) ? iszero(actual.values[i]) :
                    isequal(expected[i],actual.values[i]),1:n)
                @test issorted(actual.indices) && allunique(actual.indices)
                @test all(i->iszero(expected[i]) || i in actual.indices,1:n)
            end
        end
    end
end
@testset "Signed zero and cancellation in reachable solve" begin
    U=sparse([-2.0 1 1 0 0;0 1 1 0 0;0 0 -3 0 0;0 0 0 -1 2;0 0 0 0 4])
    f=JSimplex.HuangfuHallFactorization(spdiagm(0=>ones(5)))
    ids=collect(1:5)
    f.base=JSimplex.HHBase(spdiagm(0=>ones(5)),U,ids,ids,ids,ones(5),false,[1,3,4,4,5,5],[2,3,3,5])
    for p in (1,4,1)
        dense=zeros(5);dense[p]=1.0;JSimplex._hh_upper!(dense,f.base,true)
        w=JSimplex._hh_unit_transpose!(f,p)
        record=JSimplex._hh_pack_update(zeros(5),w,1.0)
        indices=findall(!iszero,dense)
        @test record.v_indices==indices
        @test isequal(record.v_values,dense[indices])
        @test (record.v_indices,record.v_values)==(p==1 ? ([1,2],[-0.5,0.5]) : ([4,5],[-1.0,0.5]))
    end
end
@testset "Allocation-light scaling verification" begin
    @test isdefined(JSimplex,:_hh_scale_mode)
    if isdefined(JSimplex,:_hh_scale_mode)
        rng=MersenneTwister(457)
        for n in (1,7,30)
            A=sprandn(rng,n,n,0.3);x=randn(rng,n);out=zeros(n)
            JSimplex._hh_abs_mul!(out,A,x)
            @test isequal(out,abs.(A)*abs.(x))
        end
        for exponents in ([-280.0,-30,0,30,280],[-3.0,-1,0,1,3],zeros(5))
            B=spdiagm(0=>(10.0.^exponents).*[2.0,-3,4,-5,6]);F=lu(B)
            L,U,p,q,s=F.L,F.U,F.p,F.q,F.Rs
            expected=JSimplex._umfpack_scale_mode(F,L,U,p,q,s)
            @test JSimplex._hh_scale_mode(F,L,U,p,q,s,zeros(5),zeros(5))===expected
        end
    end
end
@testset "Bounded retired update recycling" begin
    @test hasfield(JSimplex.HuangfuHallFactorization,:u_pool)
    if hasfield(JSimplex.HuangfuHallFactorization,:u_pool)
        n=128;B=spdiagm(0=>ones(n));d=ones(n);d[1]=2.0
        f=JSimplex.HuangfuHallFactorization(B)
        JSimplex.replace_column!(f,d,1)
        saved=JSimplex.copy_basis_factorization(f)
        rhs=collect(1.0:n);expected=JSimplex.forward_solve(saved,rhs)
        immutable_record=deepcopy(only(saved.updates))
        JSimplex.refactorize!(f,B)
        @test isempty(f.u_pool.pairs) && isempty(f.v_pool.pairs)
        JSimplex.replace_column!(f,d,1)
        retired=only(f.updates)
        JSimplex.refactorize!(f,B)
        @test only(f.u_pool.pairs)[1]===retired.u_indices
        @test only(f.v_pool.pairs)[1]===retired.v_indices
        @test_throws ArgumentError JSimplex.replace_column!(f,fill(NaN,n),1)
        @test length(f.u_pool.pairs)==length(f.v_pool.pairs)==1
        d[1]=3.0;d[end]=1e-200
        JSimplex.replace_column!(f,d,1)
        reused=only(f.updates)
        @test reused.u_indices===retired.u_indices && reused.u_values===retired.u_values
        @test reused.v_indices===retired.v_indices && reused.v_values===retired.v_values
        @test reused.u_values[end]==1e-200
        @test isequal(JSimplex.forward_solve(saved,rhs),expected)
        @test all(k->isequal(getfield(only(saved.updates),k),getfield(immutable_record,k)),fieldnames(JSimplex.HHUpdate))
        # A second generation of snapshots must protect both original branches.
        saved2=JSimplex.copy_basis_factorization(f);expected2=JSimplex.forward_solve(saved2,rhs)
        for active in (saved,f)
            JSimplex.refactorize!(active,B)
            JSimplex.replace_column!(active,d,1)
            JSimplex.refactorize!(active,B)
            JSimplex.replace_column!(active,2d,1)
        end
        @test isequal(JSimplex.forward_solve(saved2,rhs),expected2)
        # Retire the private suffix, while preserving a shared prefix in a copy.
        mixed=JSimplex.HuangfuHallFactorization(B)
        JSimplex.replace_column!(mixed,d,1)
        prefix=JSimplex.copy_basis_factorization(mixed)
        prefix_expected=JSimplex.forward_solve(prefix,rhs)
        JSimplex.replace_column!(mixed,2d,2)
        private=last(mixed.updates)
        JSimplex.refactorize!(mixed,B)
        @test only(mixed.u_pool.pairs)[1]===private.u_indices
        @test only(mixed.v_pool.pairs)[1]===private.v_indices
        @test isequal(JSimplex.forward_solve(prefix,rhs),prefix_expected)
        pooled=mixed.u_pool.entries
        @test_throws Exception JSimplex.refactorize!(mixed,spzeros(n,n))
        @test mixed.u_pool.entries==pooled && length(mixed.u_pool.pairs)==1
        @test JSimplex.forward_solve(mixed,rhs)==rhs
        JSimplex.refactorize!(mixed,spdiagm(0=>ones(2)))
        @test isempty(mixed.u_pool.pairs) && isempty(mixed.v_pool.pairs)
        for length_each in (1,4096)
            pool=JSimplex.HHPool()
            for _ in 1:400
                JSimplex._hh_retire_pair!(pool,zeros(Int,length_each),zeros(length_each))
            end
            @test length(pool.pairs)<=256
            @test pool.entries==sum(length(t[1]) for t in pool.pairs)<=262144
            @test Base.summarysize(pool)<4*1024^2+128*1024
        end
        pool=JSimplex.HHPool()
        JSimplex._hh_retire_pair!(pool,zeros(Int,262145),zeros(262145))
        @test isempty(pool.pairs) && pool.entries==0
        # Exact-size reuse cannot retain a large capacity behind a short vector.
        JSimplex._hh_retire_pair!(pool,zeros(Int,4096),zeros(4096))
        indices,values=JSimplex._hh_take_pair!(pool,1)
        @test length(indices)==length(values)==1 && length(pool.pairs)==1
        large_indices,large_values=JSimplex._hh_take_pair!(pool,4096)
        @test isempty(pool.pairs) && pool.entries==0
        # Warm the update path, then measure only replacement (not LU).
        JSimplex.refactorize!(f,B)
        JSimplex.replace_column!(f,d,1)
        JSimplex.refactorize!(f,B)
        recycled=@allocated JSimplex.replace_column!(f,d,1)
        fresh=JSimplex.HuangfuHallFactorization(B)
        JSimplex.replace_column!(fresh,d,1)
        fresh=JSimplex.HuangfuHallFactorization(B)
        allocated=@allocated JSimplex.replace_column!(fresh,d,1)
        @test recycled<allocated/2
    end
end

@testset "Bounded native extraction scratch" begin
    @test isdefined(JSimplex,:HHExtractWorkspace)
    if isdefined(JSimplex,:HHExtractWorkspace)
        w=JSimplex.HHExtractWorkspace();rng=MersenneTwister(502)
        for (n,density) in ((40,0.5),(40,0.4),(40,0.0),(7,0.5),(0,0.0))
            n==0 && continue
            B=sprandn(rng,n,n,density)+spdiagm(0=>fill(10.0,n));F=lu(B)
            actual=JSimplex._hh_extract_parts(F,w);expected=(F.L,F.U,F.p,F.q,F.Rs)
            for (a,b) in zip(actual,expected)
                @test a isa SparseMatrixCSC ? (isequal(a.colptr,b.colptr) && isequal(a.rowval,b.rowval) && isequal(a.nzval,b.nzval)) : isequal(a,b)
            end
            @test 8*(length(w.rowptr)+length(w.columns)+length(w.values))<=8*1024^2
        end
        F32=lu(SparseMatrixCSC{Float64,Int32}(spdiagm(0=>ones(3))))
        @test_throws MethodError JSimplex._hh_extract_parts(F32,w)
        broken=JSimplex.HHExtractWorkspace(zeros(Int,4),zeros(Int,6),zeros(1))
        p,c,v=JSimplex._hh_extract_buffers!(broken,3,3)
        @test length(c)==length(v)>=3
        p,c,v=JSimplex._hh_extract_buffers!(broken,400_000,400_000)
        @test length(p)==400_001 && length(c)==length(v)==400_000
        @test isempty(broken.rowptr) && isempty(broken.columns) && isempty(broken.values)
        B=sparse([3.0 1 0;2 4 1;0 1 5]);f=JSimplex.HuangfuHallFactorization(B)
        saved=JSimplex.copy_basis_factorization(f);L=copy(saved.base.lower)
        for C in (2B,3B,spdiagm(0=>ones(3)),4B)
            JSimplex.refactorize!(f,C)
            @test isequal(saved.base.lower.nzval,L.nzval)
            @test JSimplex.forward_solve(saved,ones(3))≈B\ones(3)
        end
        @test f.extract_workspace!==saved.extract_workspace
        JSimplex.refactorize!(f,spzeros(0,0))
        @test isempty(f.extract_workspace.rowptr)
    end
end
