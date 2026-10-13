using LinearAlgebra, SparseArrays

@testset "Triangular updates recover a well-conditioned basis" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization),
        T in (Float32,Float64,BigFloat), backend in (:native,:markowitz)
        B=Matrix{T}(I,2,2)
        f=Factor(copy(B),Val(backend))
        tiny=eps(T)/T(2)
        for (row,a) in ((1,T[tiny,1]),(2,T[1,1]))
            direction=JSimplex.forward_solve(f,a)
            JSimplex.replace_column!(f,direction,row;zero_tolerance=zero(T))
            B[:,row]=a
        end
        @test cond(Float64.(B)) < 3
        for b in (T[1,0],T[0,1],T[1,1]), transposed in (false,true)
            x=transposed ? JSimplex.transpose_solve(f,b) : JSimplex.forward_solve(f,b)
            M=transposed ? transpose(B) : B
            residual=norm(M*x-b,Inf)/(opnorm(M,Inf)*norm(x,Inf)+norm(b,Inf))
            @test residual <= T(8)*eps(T)
        end
    end
end

@testset "Row swaps preserve dense, indexed and transposed solves" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}),
        (Factor,last) in ((JSimplex.ForrestTomlinFactorization,24),
                         (JSimplex.SuhlSuhlFactorization,20))
        n=24
        B=Matrix{T}(I,n,n)
        for row in 1:last-1
            B[row,row+1]=T(4)
        end
        B[last,1]=T(1//8); B[last,3]=T(2); B[last,last]=T(3)
        last<n && (B[last,n]=T(5); B[3,n]=T(2))
        f=Factor(Matrix{T}(I,n,n))
        for column in 1:n
            JSimplex._packed_column!(f.upper[column],B[:,column])
        end
        f.spike .= B[last,:]
        for column in 1:last-1
            JSimplex._set_upper_value!(f.upper[column],last,zero(T))
        end
        indices,multipliers,swaps=JSimplex._eliminate_triangular_row_spike!(
            f,1,last,sum(c->length(c.values),f.upper))
        @test length(swaps)>=2
        @test maximum(abs,multipliers)<=one(T)
        update=Factor===JSimplex.ForrestTomlinFactorization ?
            JSimplex.ForrestTomlinUpdate{T}(last,indices,multipliers,swaps) :
            JSimplex.SuhlSuhlUpdate{T}(last,last,indices,multipliers,swaps)
        push!(f.updates,update)
        saved=JSimplex.copy_basis_factorization(f)
        rhs,dest,scratch=(JSimplex.IndexedVector{T}(n) for _ in 1:3)
        tolerance=T<:Rational ? zero(T) : T(128)*eps(T)
        for b in (ones(T,n),T.(1:n)), transposed in (false,true)
            M=transposed ? transpose(B) : B
            x=transposed ? JSimplex.transpose_solve(f,b) : JSimplex.forward_solve(f,b)
            @test norm(M*x-b,Inf)<=tolerance*(opnorm(M,Inf)*norm(x,Inf)+norm(b,Inf))
            for mode in (:sparse,:dense,:auto)
                JSimplex.load_indexed!(rhs,b)
                operation=transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                operation(dest,f,rhs;kernel_mode=mode)
                @test dest.values ≈ x
                @test Set(dest.indices)==Set(findall(!iszero,dest.values))
            end
            raw=copy(b); compiled=copy(b)
            if transposed
                JSimplex._apply_transposed_row_update!(raw,update)
                JSimplex._apply_dense_transposed_row_updates!(compiled,f)
                JSimplex.load_indexed!(rhs,b)
                JSimplex._apply_transposed_row_update!(rhs,update,scratch)
            else
                JSimplex._apply_row_update!(raw,update)
                JSimplex._apply_dense_row_updates!(compiled,f)
                JSimplex.load_indexed!(rhs,b)
                JSimplex._apply_row_update!(rhs,update,scratch)
            end
            @test raw==compiled==rhs.values
        end
        JSimplex.refactorize!(f,Matrix{T}(I,n,n))
        # A shared update must remain valid after the original factor resets.
        b=ones(T,n); x=JSimplex.forward_solve(saved,b)
        @test norm(B*x-b,Inf)<=tolerance*(opnorm(B,Inf)*norm(x,Inf)+one(T))
    end
end

@testset "A zero diagonal swap is retained without an elimination" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization)
        f=Factor(Matrix{Float64}(I,2,2))
        JSimplex._packed_column!(f.upper[1],[0.0,0.0])
        JSimplex._packed_column!(f.upper[2],[1.0,0.0])
        f.spike .= [1.0,0.0]
        indices,multipliers,swaps=JSimplex._eliminate_triangular_row_spike!(f,1,2,1)
        update=Factor===JSimplex.ForrestTomlinFactorization ?
            JSimplex.ForrestTomlinUpdate{Float64}(2,indices,multipliers,swaps) :
            JSimplex.SuhlSuhlUpdate{Float64}(2,2,indices,multipliers,swaps)
        push!(f.updates,update)
        @test JSimplex.forward_solve(f,[2.0,3.0])==[3.0,2.0]
        @test JSimplex.transpose_solve(f,[2.0,3.0])==[3.0,2.0]
        # Retired swap storage is cleared before an unrelated no-swap update.
        JSimplex.refactorize!(f,Matrix{Float64}(I,2,2))
        JSimplex.replace_column!(f,[0.0,2.0],2)
        @test JSimplex.forward_solve(f,[2.0,6.0])==[2.0,3.0]
        @test JSimplex.transpose_solve(f,[2.0,6.0])==[2.0,3.0]
        JSimplex.refactorize!(f,Matrix{Float64}(I,2,2))
        # Prepare a nonempty row spike without consuming the retired history.
        # The represented basis is now [1 0.25; 0 2]. Replacing its first
        # column by the sum of both columns forces both FT and SS to rotate
        # and eliminate without a row swap.
        JSimplex._packed_column!(f.upper[2],[0.25,2.0])
        JSimplex.replace_column!(f,[1.0,1.0],1)
        @test !isempty(f.updates[end].indices)
        @test isempty(f.updates[end].swapped_rows)
        @test JSimplex.forward_solve(f,[3.25,10.0])==[2.0,3.0]
        @test JSimplex.transpose_solve(f,[8.5,6.5])==[2.0,3.0]
    end
end
