using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Phase export retains certified nonbasic values" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        options=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false)
        delta=options.primal_tolerance/T(2)
        p=LinearProblem(sparse(reshape(T[1,1],1,2)),zeros(T,2);row_lower=T[1],row_upper=T[1])
        aux=LinearProblem(sparse(reshape(T[1,1,1],1,3)),T[0,0,1];row_lower=T[1],row_upper=T[1])
        original=JSimplex.initialize_workspace(p,options)
        phase=JSimplex.initialize_workspace(aux,options)
        phase.basis=JSimplex.Basis([2],[JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        phase.iterations=1
        phase.primal.=T[-delta,1+delta,0,1]
        JSimplex.recompute!(phase;refactorize=true)
        mapping=JSimplex.PhaseOneMap([1,2,4],[1,2,0,3],[3])
        @test JSimplex._legacy_primal_point_certified(phase)
        @test JSimplex.remove_artificials!(phase,mapping,original,phase.progress.numerical_policy,()->false)
        @test original.primal[1]==-delta
        @test JSimplex._original_primal_feasible(original,original.primal[1:2])
    end
end

@testset "Local phase rows preserve tiny right-hand sides and reject cycles" begin
    for T in (Float32,Float64)
        tiny=T === Float32 ? T(1e-20) : T(1e-66)
        noise=T === Float32 ? T(1e-10) : T(1e-30)
        cutoff=T === Float32 ? T(1e-8) : T(1e-21)
        B=sparse(T[1 1;0 1]);rhs=T[0,tiny]
        policy=JSimplex.NumericalPolicy(T)
        x=T[noise,tiny]
        @test JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
        @test x==T[-tiny,tiny]
        for (initial,limit) in ((T[0,tiny],cutoff),(T[noise,tiny],zero(T)))
            x=copy(initial)
            @test !JSimplex._native_phase_local_rows!(x,B,rhs,policy,limit,()->false)
            @test isequal(x,initial)
        end
        for throwing in (false,true)
            x=T[noise,tiny];before=copy(x);calls=Ref(0);error=ErrorException("cancel local rows")
            stop=()->begin
                calls[]+=1
                if calls[]==8
                    throwing && throw(error)
                    return true
                end
                false
            end
            result=try JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,stop) catch e; e end
            @test result === (throwing ? error : false)
            @test isequal(x,before)
        end
        x=T[noise,tiny];before=copy(x)
        old=get_zero_subnormals()
        try
            set_zero_subnormals(true)
            @test !JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
            @test isequal(x,before)
        finally
            set_zero_subnormals(old)
        end
    end
end
