function test_factorization_type(::Type{T}) where {T}
    B = JSimplex.SparseArrays.sparse(T[2 1; 1 3])
    rhs = T[5, 7]
    factor = @inferred JSimplex.PFIFactorization(B)
    x = @inferred JSimplex.forward_solve(factor, rhs)
    xt = @inferred JSimplex.transpose_solve(factor, rhs)
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
    else
        @test factor.base isa JSimplex.DenseLUBackend
    end
end

@testset "Parametric factorization backends" begin
    foreach(test_factorization_type, (Float32, Float64, BigFloat, Rational{BigInt}))

    empty_factor = @inferred JSimplex.PFIFactorization(
        JSimplex.SparseArrays.spzeros(Float64, 0, 0),
    )
    @test isempty(@inferred JSimplex.forward_solve(empty_factor, Float64[]))
end

@testset "Float64 factorization backend stability" begin
    dense_basis = Float64[2 1; 1 3]
    factor = @inferred JSimplex.PFIFactorization(dense_basis)
    backend_type = typeof(factor.base)

    @test factor.base isa JSimplex.UMFPACKBackend
    JSimplex.refactorize!(factor, JSimplex.SparseArrays.sparse(Float64[4 1; -1 3]))
    @test typeof(factor.base) === backend_type
    @test factor.base isa JSimplex.UMFPACKBackend

    empty_factor = @inferred JSimplex.PFIFactorization(zeros(Float64, 0, 0))
    @test empty_factor.base isa JSimplex.UMFPACKBackend
end

@testset "Product-form basis factorization" begin
    B = JSimplex.SparseArrays.sparse([2.0 1.0; 1.0 3.0])
    factor = JSimplex.PFIFactorization(B)
    rhs = [5.0, 7.0]
    @test JSimplex.forward_solve(factor, rhs) ≈ Matrix(B) \ rhs
    @test JSimplex.transpose_solve(factor, rhs) ≈ Matrix(B)' \ rhs

    replacement = [4.0, -1.0]
    tableau_column = JSimplex.forward_solve(factor, replacement)
    JSimplex.replace_column!(factor, tableau_column, 1)
    B2 = JSimplex.SparseArrays.sparse([4.0 1.0; -1.0 3.0])
    @test JSimplex.forward_solve(factor, rhs) ≈ Matrix(B2) \ rhs
    @test JSimplex.transpose_solve(factor, rhs) ≈ Matrix(B2)' \ rhs

    JSimplex.refactorize!(factor, B2)
    @test isempty(factor.updates)
    @test JSimplex.forward_solve(factor, rhs) ≈ Matrix(B2) \ rhs
end

@testset "Product-form factorization validation" begin
    B = JSimplex.SparseArrays.sparse([2.0 1.0; 1.0 3.0])
    factor = JSimplex.PFIFactorization(B)
    rhs = [5.0, 7.0]
    original_rhs = copy(rhs)

    JSimplex.forward_solve(factor, rhs)
    JSimplex.transpose_solve(factor, rhs)
    @test rhs == original_rhs

    tableau_column = [1.0, 2.0]
    @test_throws JSimplex.LinearAlgebra.ZeroPivotException JSimplex.replace_column!(factor, [0.0, 2.0], 1)
    @test_throws BoundsError JSimplex.replace_column!(factor, tableau_column, 0)
    @test_throws ArgumentError JSimplex.replace_column!(factor, tableau_column, 1; zero_tolerance=-1.0)
    @test_throws DimensionMismatch JSimplex.replace_column!(factor, [1.0], 1)
end

@testset "Product-form transpose solve RHS precision" begin
    B = JSimplex.SparseArrays.sparse([2.0 1.0; 1.0 3.0])
    factor = JSimplex.PFIFactorization(B)
    replacement = [4.0, -1.0]
    JSimplex.replace_column!(factor, JSimplex.forward_solve(factor, replacement), 1)
    B2 = JSimplex.SparseArrays.sparse([4.0 1.0; -1.0 3.0])

    integer_rhs = [5, 7]
    float32_rhs = Float32[5, 7]
    expected_integer = Matrix(B2)' \ Float64.(integer_rhs)
    expected_float32 = Matrix(B2)' \ Float64.(float32_rhs)

    @test JSimplex.transpose_solve(factor, integer_rhs) ≈ expected_integer rtol=1.0e-12
    @test JSimplex.transpose_solve(factor, float32_rhs) ≈ expected_float32 rtol=1.0e-12
    @test integer_rhs == [5, 7]
    @test float32_rhs == Float32[5, 7]
end
