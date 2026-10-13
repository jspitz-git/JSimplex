using LinearAlgebra, SparseArrays
isdefined(@__MODULE__, :bg_replay_forward) || include("helpers/triangular_replay.jl")

@testset "Upper invalidation retains only a proven unchanged prefix" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization), T in (Float32,Float64)
        B=Matrix{T}(I,8,8); f=Factor(B)
        JSimplex.forward_solve(f,ones(T,8))
        available=hasproperty(f.row_cache,:upper_dirty_from)
        @test available
        available || continue
        a=copy(B[:,7]); a[8]=T(1//4)
        JSimplex.replace_column!(f,B\a,7); B[:,7]=a
        @test f.row_cache.upper_dirty_from==7
        a=copy(B[:,2]); a[4]=T(1//8)
        JSimplex.replace_column!(f,B\a,2); B[:,2]=a
        @test f.row_cache.upper_dirty_from==2
        rhs=T[1,2,3,4,5,6,7,8]
        @test isequal(JSimplex.forward_solve(f,rhs),bg_replay_forward(f,rhs))
        @test B*JSimplex.forward_solve(f,rhs)≈rhs
        @test B'*JSimplex.transpose_solve(f,rhs)≈rhs
        saved=JSimplex.copy_basis_factorization(f)
        @test saved.row_cache.upper_dirty_from==1
        @test isequal(JSimplex.forward_solve(saved,rhs),bg_replay_forward(saved,rhs))
        @test_throws SingularException JSimplex.refactorize!(f,zeros(T,8,8))
        @test B*JSimplex.forward_solve(f,rhs)≈rhs
        # External/unclassified mutations must still invalidate from column 1.
        JSimplex._invalidate_sparse_upper!(f)
        @test f.row_cache.upper_dirty_from==1
        JSimplex.refactorize!(f,Matrix{T}(I,3,3))
        @test isempty(JSimplex._dense_upper_columns(f))
        @test JSimplex.forward_solve(f,ones(T,3))==ones(T,3)
    end
end

@testset "Incidence clears previous touched rows across disjoint query ranges" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization)
        f=Factor(Matrix{Float64}(I,8,8))
        for (row,col) in ((2,3),(4,5),(7,8))
            JSimplex._set_upper_value!(f.upper[col],row,0.5)
        end
        rows=JSimplex._triangular_row_columns!(f,2,4)
        @test rows[2]==[3] && rows[4]==[5]
        @test all(isempty(rows[i]) for i in (1,3,5,6,7,8))
        available=hasproperty(f.row_cache,:incidence_touched)
        @test available
        available || continue
        @test sort(f.row_cache.incidence_touched)==[2,4]
        rows=JSimplex._triangular_row_columns!(f,7,7)
        @test rows[7]==[8]
        @test all(isempty(rows[i]) for i in 1:6)
        @test f.row_cache.incidence_touched==[7]
        g=JSimplex.copy_basis_factorization(f)
        @test isempty(g.row_cache.incidence_touched)
        @test JSimplex._triangular_row_columns!(g,2,4)[2]==[3]
        @test rows[7]==[8]
        JSimplex.refactorize!(f,Matrix{Float64}(I,3,3))
        @test isempty(f.row_cache.incidence_touched)
        @test all(isempty,f.row_columns)
    end
end

@testset "Partial invalidation survives mutation without an appended update" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        f=Factor(Matrix{Float64}(I,8,8))
        f.upper[2].values[1]=2.0
        JSimplex._invalidate_sparse_upper!(f)
        @test JSimplex._dense_upper_columns(f)==[2]
        # A replacement may fail after invalidating and changing a suffix,
        # before publishing its history entry. Keep the old active prefix.
        JSimplex._invalidate_sparse_upper!(f,7)
        f.upper[7].values[1]=3.0
        @test isempty(f.updates)
        @test JSimplex._dense_upper_columns(f)==[2,7]
        expected=[1.0,0.5,1.0,1.0,1.0,1.0,1/3,1.0]
        @test JSimplex.forward_solve(f,ones(8))≈expected
        @test JSimplex.transpose_solve(f,ones(8))≈expected
    end
end
