using JSimplex, LinearAlgebra, SparseArrays, Test
Base.include(JSimplex,joinpath(@__DIR__,"direct.jl"))
@testset "Diagonal transfer restores inactive unit upper columns" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        B=spdiagm(0=>[-2.,3.,-4.,5.]);f=JSimplex._trial_direct_factor(Factor,B;normalize=true)
        @test isempty(JSimplex._dense_upper_columns(f))
        @test JSimplex.forward_solve(f,ones(4))≈B\ones(4)
        @test JSimplex.transpose_solve(f,ones(4))≈B'\ones(4)
        g=JSimplex.copy_basis_factorization(f)
        @test g.base.normalize_requested
        JSimplex.refactorize!(f,spdiagm(0=>[nextfloat(1.0),1.0]))
        @test !isnothing(f.base.fallback) && f.base.normalize_requested
        JSimplex.refactorize!(f,B)
        @test isempty(JSimplex._dense_upper_columns(f))
        @test JSimplex.forward_solve(g,ones(4))≈B\ones(4)
    end
end
@testset "Unsafe upper normalization is transactional" begin
    for U in (sparse([1e-300 1e300;0.0 1.0]),sparse([1e300 1e-300;0.0 1.0]))
        before=copy(U)
        @test isnothing(JSimplex._trial_normalize_upper!(U))
        @test isequal(U,before)
    end
end
@testset "Normalized identity lower with permutation and public aliasing" begin
    B=sparse([0.0 0.0 -2.0;3.0 0.0 0.0;0.0 -4.0 0.0])
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        f=JSimplex._trial_direct_factor(Factor,B;normalize=true)
        @test nnz(f.base.lower)==3
        # UMFPACK may move the permutation to q; row and column maps together
        # must reproduce the nontrivial original coordinates in either case.
        @test f.base.row_order!=collect(1:3) || f.column_order!=collect(1:3)
        # Pin a known valid decomposition too; native ordering may put the
        # permutation entirely into q on another platform.
        f.base=JSimplex.TrialLowerBackend(spdiagm(0=>ones(3)),[2,3,1],ones(3),
            false,[3.,-4.,-2.],true,nothing,zeros(3))
        f.column_order.=1:3;f.positions.=1:3
        JSimplex._reset_identity_upper!(f.upper,3)
        JSimplex._invalidate_dense_upper!(f)
        for operation in (JSimplex.forward_solve!,JSimplex.transpose_solve!)
            rhs=[1.,-2.,3.];reference=operation===JSimplex.forward_solve! ? Matrix(B)\rhs : Matrix(B')\rhs
            operation(rhs,f,rhs)
            @test rhs≈reference
            copyto!(f.work,[1.,-2.,3.]);operation(f.spike,f,f.work)
            @test f.spike≈reference
        end
    end
end
