using Test, JSimplex, LinearAlgebra, SparseArrays
function test_factorization_type(::Type{T}) where {T}
    B = JSimplex.SparseArrays.sparse(T[2 1; 1 3])
    rhs = T[5, 7]
    factor = @inferred Main.NP.PFIFactorization(B)
    x = @inferred Main.NP.forward_solve(factor, rhs)
    xt = @inferred Main.NP.transpose_solve(factor, rhs)
    @test eltype(x) === T
    @test eltype(xt) === T
    if T <: Rational
        @test B * x == rhs
        @test transpose(B) * xt == rhs
    else
        @test B * x ≈ rhs
        @test transpose(B) * xt ≈ rhs
    end
    @test fieldtype(typeof(factor), :base) !== Any
    if T === Float64
        @test factor.base isa JSimplex.UMFPACKBackend
    elseif T === Float32
        @test factor.base isa JSimplex.Float32LUBackend
    else
        @test factor.base isa JSimplex.DenseLUBackend
    end
end

@testset "Parametric factorization backends" begin
    foreach(test_factorization_type, (Float32, Float64, BigFloat, Rational{BigInt}))

    empty_factor = @inferred Main.NP.PFIFactorization(
        JSimplex.SparseArrays.spzeros(Float64, 0, 0),
    )
    @test isempty(@inferred Main.NP.forward_solve(empty_factor, Float64[]))
end

@testset "Float64 factorization backend stability" begin
    dense_basis = Float64[2 1; 1 3]
    factor = @inferred Main.NP.PFIFactorization(dense_basis)
    backend_type = typeof(factor.base)

    @test factor.base isa JSimplex.UMFPACKBackend
    Main.NP.refactorize!(factor, JSimplex.SparseArrays.sparse(Float64[4 1; -1 3]))
    @test typeof(factor.base) === backend_type
    @test factor.base isa JSimplex.UMFPACKBackend

    empty_factor = @inferred Main.NP.PFIFactorization(zeros(Float64, 0, 0))
    @test empty_factor.base isa JSimplex.UMFPACKBackend
end

@testset "Dimension-changing refactorization resizes solve scratch" begin
    for T in (Float32, Float64)
        factor = Main.NP.PFIFactorization(reshape(T[2], 1, 1))
        basis = JSimplex.SparseArrays.sparse(T[2 0; 0 4])
        rhs = T[4, 8]

        Main.NP.refactorize!(factor, basis)

        @test Main.NP.forward_solve(factor, rhs) ≈ T[2, 2]
        @test Main.NP.transpose_solve(factor, rhs) ≈ T[2, 2]
    end
end

@testset "Owned snapshots survive backend reuse and solve aliases" begin
    for kind in (:native,:markowitz)
        B = spdiagm(-1=>fill(-1.0,11),0=>fill(4.0,12),1=>fill(1.0,11))
        backend = Main.NP._factorize_basis(B,Val(kind))
        old = Main.NP.sparse_solve_view(backend)
        for offset in (1.0,2.0,3.0)
            backend = Main.NP._refactorize_backend(backend,B+offset*I)
        end
        rhs = JSimplex.IndexedVector{Float64}(12)
        JSimplex.set_entry!(rhs,1,1.0)
        values = copy(rhs.values)
        Main.NP.hypersparse_forward_solve!(rhs,old,rhs)
        @test B*rhs.values ≈ values
        JSimplex.load_indexed!(rhs,values)
        Main.NP.hypersparse_transpose_solve!(rhs,old,rhs)
        @test transpose(B)*rhs.values ≈ values
        @test_throws ArgumentError Main.NP.hypersparse_forward_solve!(old.work,old,rhs)
        @test_throws ArgumentError Main.NP.hypersparse_forward_solve!(rhs,old,old.work)
        @test_throws DimensionMismatch Main.NP.hypersparse_forward_solve!(JSimplex.IndexedVector{Float64}(1),old,rhs)
        newer = Main.NP.sparse_solve_view(backend)
        @test old.work.values !== newer.work.values
        @test old.lower.reach.order !== newer.lower.reach.order
    end
    for T in (Float32,BigFloat,Rational{Int},Rational{BigInt})
        @test isnothing(Main.NP.sparse_solve_view(Main.NP._factorize_basis(Matrix{T}(I,2,2))))
    end
    singular = Main.NP.raw_lu(sparse([1.0 1;1 1]);check=false)
    @test_throws SingularException Main.NP.sparse_solve_view(Main.NP.UMFPACKBackend(singular,2))
end

@testset "Triangular identity reset uses current BigFloat precision without changing copies" begin
    for Factor in (Main.NP.ForrestTomlinFactorization, Main.NP.SuhlSuhlFactorization,
                   Main.NP.BartelsGolubFactorization)
        factor, saved = setprecision(BigFloat, 512) do
            f = Factor(Matrix{BigFloat}(I, 2, 2))
            Main.NP.replace_column!(f, BigFloat[2, 1], 1)
            f, Main.NP.copy_basis_factorization(f)
        end
        before = deepcopy([c.values for c in saved.upper])
        setprecision(BigFloat, 64) do
            Main.NP.refactorize!(factor, Matrix{BigFloat}(I, 2, 2))
            @test all(precision(only(c.values)) == 64 for c in factor.upper)
            @test all(isone(only(c.values)) for c in factor.upper)
        end
        @test [c.values for c in saved.upper] == before
        @test all(precision(x) == 512 for c in saved.upper for x in c.values)
    end
end
