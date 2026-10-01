using Test,JSimplex,SparseArrays,LinearAlgebra

@testset "Coupled phase reconstruction retains nonzero tiny right-hand sides" begin
    for T in (Float32,Float64)
        tiny=T===Float32 ? T(1e-20) : T(1e-66)
        noise=T===Float32 ? T(1e-10) : T(1e-30)
        cutoff=T(100)*noise
        B=sparse(T[1 2 0;3 4 0;0 0 1]);rhs=T[tiny,0,7]
        initial=T[noise,-noise,7];policy=JSimplex.NumericalPolicy(T)
        x=copy(initial)
        accepted=JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
        @test accepted
        if accepted
            @test isapprox(x[1],-2tiny;rtol=T(16)*eps(T),atol=zero(T))
            @test isapprox(x[2],T(1.5)*tiny;rtol=T(16)*eps(T),atol=zero(T))
            @test x[3]==7
            exact=Rational{BigInt}.(B)*Rational{BigInt}.(x)-Rational{BigInt}.(rhs)
            @test maximum(abs,exact)<=Rational{BigInt}(T(16)*eps(T)*tiny)
        end
        for limit in (zero(T),noise/T(100))
            x=copy(initial)
            @test !JSimplex._native_phase_local_rows!(x,B,rhs,policy,limit,()->false)
            @test isequal(x,initial)
        end
        # A large boundary coefficient makes the small-coordinate repair unsafe.
        boundary=copy(B);boundary[3,1]=inv(noise);unsafe_rhs=T[tiny,0,8]
        x=copy(initial)
        @test !JSimplex._native_phase_local_rows!(x,boundary,unsafe_rhs,policy,cutoff,()->false)
        @test isequal(x,initial)
        for throwing in (false,true)
            x=copy(initial);error=ErrorException("cancel coupled reconstruction")
            stop=()->(throwing ? throw(error) : true)
            result=try JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,stop) catch e;e end
            @test result === (throwing ? error : false)
            @test isequal(x,initial)
        end
    end
end

@testset "Coupled reconstruction is bounded and transactional" begin
    policy=JSimplex.NumericalPolicy(Float64)
    block=sparse([1.0 2;3 4]);initial=[1e-30,-1e-30];rhs=[1e-66,0.0];cutoff=1e-28
    # An oversized search must not allocate an unbounded dense solve.
    B=blockdiag(fill(block,33)...);x=repeat(initial,33);before=copy(x)
    @test !JSimplex._native_phase_local_rows!(x,B,repeat(rhs,33),policy,cutoff,()->false)
    @test isequal(x,before)
    # Inconsistent small equations cannot be accepted by a least-squares fit.
    B=sparse([1.0 2;2 4]);x=copy(initial)
    @test !JSimplex._native_phase_local_rows!(x,B,[1e-30,0.0],policy,cutoff,()->false)
    @test isequal(x,initial)
    calls=Ref(0);x=copy(initial)
    accepted=JSimplex._native_phase_local_rows!(x,block,rhs,policy,cutoff,
        ()->begin calls[]+=1;false end)
    @test accepted
    if accepted
        cancel_at=calls[]-2
        for throwing in (false,true)
            x=copy(initial);calls[]=0;error=ErrorException("cancel after block reconstruction")
            stop=()->begin
                calls[]+=1
                if calls[]==cancel_at
                    throwing && throw(error)
                    return true
                end
                false
            end
            result=try JSimplex._native_phase_local_rows!(x,block,rhs,policy,cutoff,stop) catch e;e end
            @test result === (throwing ? error : false)
            @test calls[]==cancel_at
            @test isequal(x,initial)
        end
    end
end

@testset "Coupled reconstruction survives row and column reordering and scaling" begin
    for T in (Float32,Float64), order in ([1,2],[2,1])
        tiny=T===Float32 ? T(1e-20) : T(1e-66)
        noise=T===Float32 ? T(1e-10) : T(1e-30)
        # Row scales 1/8 and 16, column scales 2 and 1/2 applied to
        # [1 2; 3 4] x = [tiny,0] give the exact solution [-tiny,3tiny].
        B=sparse(T[0.25 0.125;96 32][order,reverse(order)])
        rhs=T[tiny/8,0][order]
        x=T[noise,-noise]
        accepted=JSimplex._native_phase_local_rows!(x,B,rhs,JSimplex.NumericalPolicy(T),T(100)*noise,()->false)
        @test accepted
        if accepted
            @test all(isapprox.(x,T[-tiny,3tiny][reverse(order)];rtol=T(32)*eps(T),atol=zero(T)))
            residual=Rational{BigInt}.(B)*Rational{BigInt}.(x)-Rational{BigInt}.(rhs)
            @test maximum(abs,residual)<=Rational{BigInt}(T(128)*eps(T)*tiny)*maximum(sum(abs,Rational{BigInt}.(B);dims=2))
        end
    end
end
