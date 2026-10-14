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

