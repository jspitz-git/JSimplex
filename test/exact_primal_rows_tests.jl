using Test, JSimplex, SparseArrays, Random

@testset "Exact row feasibility preserves binary products and absolute bounds" begin
    for T in (Float32, Float64)
        tiny = nextfloat(zero(T))
        large = floatmax(T)
        cases = [
            (T[large,-large,1], T[2,2,1], T(1), T(1), zero(T), true),
            (T[large,1], T[1,1], nothing, nothing, zero(T), false),
            (T[tiny], T[tiny], nothing, zero(T), zero(T), false),
            (T[-tiny], T[tiny], zero(T), nothing, zero(T), false),
            (T[1,-1,tiny], T[1,1,1], zero(T), zero(T), tiny, true),
            (T[1,-1,tiny], T[1,1,1], zero(T), zero(T), zero(T), false),
            (T[1], T[T(0.1)], zero(T), zero(T), T(0.1), true),
            (T[1], T[nextfloat(T(0.1))], zero(T), zero(T), T(0.1), false),
            (T[1,-1], T[0,-0.0], zero(T), zero(T), zero(T), true),
        ]
        for (a,x,lo,hi,tol,want) in cases
            p=LinearProblem(sparse(reshape(a,1,:)),zeros(T,length(a));row_lower=[lo],row_upper=[hi])
            before=copy(x)
            @test JSimplex._refined_primal_rows_feasible(p,x,tol,[1]) == want
            @test x == before
        end
        p=LinearProblem(sparse(reshape(T[1],1,1)),zeros(T,1))
        for bad in (T(Inf),T(-Inf),T(NaN))
            p.A.nzval[1]=bad
            @test !JSimplex._refined_primal_rows_feasible(p,T[0],zero(T),[1])
        end
    end
end

@testset "Exact row feasibility agrees with independent rational dot products" begin
    rng=MersenneTwister(82417)
    for T in (Float32,Float64)
        exponents=T===Float32 ? (-149,-126,-25,-1,0,25,126) : (-1074,-1022,-53,-1,0,53,1022)
        values=T[0, -0.0, 1, -1, nextfloat(zero(T)),floatmax(T)]
        append!(values,T[ldexp(T(sign),e) for e in exponents for sign in (-1,1)])
        for trial in 1:25
            A=rand(rng,values,6,9);x=rand(rng,values,9)
            exact=Rational{BigInt}.(A)*Rational{BigInt}.(x)
            lo=Union{Nothing,T}[isfinite(T(v)) ? prevfloat(T(v)) : nothing for v in exact]
            hi=Union{Nothing,T}[isfinite(T(v)) ? nextfloat(T(v)) : nothing for v in exact]
            # Include strict zero bounds and unbounded rows as well as close enclosures.
            lo[1]=nothing;hi[1]=nothing;lo[2]=zero(T);hi[2]=nothing;lo[3]=nothing;hi[3]=zero(T)
            p=LinearProblem(sparse(A),zeros(T,9);row_lower=lo,row_upper=hi)
            tol=trial%2==0 ? zero(T) : eps(T)
            for row in 1:6
                v=exact[row]
                want=abs(v)<=Rational{BigInt}(floatmax(T)) &&
                    (isnothing(lo[row]) || !isfinite(lo[row]) || v>=Rational{BigInt}(lo[row])-Rational{BigInt}(tol)) &&
                    (isnothing(hi[row]) || !isfinite(hi[row]) || v<=Rational{BigInt}(hi[row])+Rational{BigInt}(tol))
                @test JSimplex._refined_primal_rows_feasible(p,x,tol,[row]) == want
            end
        end
    end
end

@testset "Moderate cancellation is decided in native precision" begin
    rng=MersenneTwister(441)
    for T in (Float32,Float64), trial in 1:40
        a=rand(rng,T,4,8).-T(0.5)
        x=rand(rng,T,8).-T(0.5)
        # Non-dyadic-looking mantissas exercise FMA residuals; paired products
        # cancel mathematically, leaving the independently known activity 1.
        A=hcat(a,-a,ones(T,4));primal=vcat(x,x,one(T))
        permutation=randperm(rng,length(primal));A=A[:,permutation];primal=primal[permutation]
        tolerance=T(16)*eps(T)
        p=LinearProblem(sparse(A),zeros(T,length(primal));
            row_lower=Union{Nothing,T}[1,1+2*tolerance,nothing,0],
            row_upper=Union{Nothing,T}[1,nothing,0,2])
        for (row,want) in enumerate((true,false,false,true))
            @test JSimplex._native_primal_rows_filter(p,primal,tolerance,[row],p.row_lower,p.row_upper) === want
            @test JSimplex._refined_primal_rows_feasible(p,primal,tolerance,[row]) === want
        end
    end
end

@testset "Exact fallback reads subnormal bits under flush-to-zero mode" begin
    for T in (Float32,Float64)
        tiny=nextfloat(zero(T))
        fixtures=[(LinearProblem(sparse(reshape(T[tiny],1,1)),zeros(T,1);row_upper=T[0]),T[1]),
                  (LinearProblem(sparse(reshape(T[1],1,1)),zeros(T,1);row_upper=T[0]),T[tiny])]
        previous=get_zero_subnormals()
        try
            set_zero_subnormals(true)
            if get_zero_subnormals()
                for (p,x) in fixtures
                    @test !JSimplex._refined_primal_rows_feasible(p,x,zero(T),[1])
                end
            else
                @test_skip "Hardware flush-to-zero mode is unavailable"
            end
        finally
            set_zero_subnormals(previous)
        end
    end
end


@testset "Native row bounds retain noncancelling product residuals" begin
    for T in (Float32,Float64)
        for (a,x,lo,hi) in (
            (nextfloat(one(T)),prevfloat(one(T)),nothing,one(T)),
            (one(T)+eps(T),one(T)-eps(T),one(T),nothing))
            @test a*x == one(T)
            p=LinearProblem(sparse(reshape(T[a],1,1)),zeros(T,1);row_lower=[lo],row_upper=[hi])
            @test JSimplex._native_primal_rows_filter(p,T[x],zero(T),[1],p.row_lower,p.row_upper) === false
            @test !JSimplex._refined_primal_rows_feasible(p,T[x],zero(T),[1])
        end
    end
end
