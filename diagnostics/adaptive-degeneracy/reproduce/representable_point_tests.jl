using JSimplex, Test, SparseArrays

@testset "Representable joint recovery with an active coordinate bound" begin
    for T in (Float32,Float64), mirror in (1,-1), explicit_zero in (false,true)
        tol=T(1e-7)
        x=T[1.6431022010982876e-5,-2.731252684658847e-7,1.7953218601001334e-5]
        A=sparse(T[-1.111111111 -1.111111111 1;1e-6 0 0;0 1e-6 0])
        if explicit_zero
            i,j,v=findnz(A)
            A=sparse([i;1;4],[j;4;4],[v;zero(T);T(1e-6)],4,4)
            push!(x,one(T))
        end
        x .*= T(mirror)
        n=length(x)
        rhs=A*x;rhs[1]=zero(T)
        lower=fill(mirror==1 ? zero(T) : T(-Inf),n)
        upper=fill(mirror==1 ? T(Inf) : zero(T),n)
        p=LinearProblem(A,zeros(T,n);column_lower=lower,column_upper=upper,row_lower=rhs,row_upper=rhs)
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,
            primal_tolerance=tol,basis_refactorization=:native,verbose=false))
        ws.basis=JSimplex.Basis(collect(1:n),[fill(JSimplex.BASIC,n);fill(JSimplex.AT_LOWER,n)])
        ws.primal .= [x;rhs]
        original=copy(ws.primal)
        @test !JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test JSimplex._legacy_primal_point_certified(ws)
        q=Rational{BigInt}
        @test all(mirror*q(v)>=-q(tol) for v in ws.primal[1:n])
        @test all(abs(sum(q(A[i,j])*q(ws.primal[j]) for j in 1:n)-q(rhs[i]))<=q(tol) for i in 1:n)
        @test ws.primal[n+1:end]==original[n+1:end]
        @test maximum(abs.(ws.primal-original))<=8tol
        @test ws.scratch.row_solution==ws.primal[1:n]
        if explicit_zero
            @test ws.primal[4]===original[4]
        end
    end
end

function remote_joint_workspace(T)
    tol=T===Float32 ? T(1e-4) : T(1e-7)
    activity=-tol/T(2)
    p=LinearProblem(sparse(reshape(T[0.01,1],2,1)),T[0];column_lower=T[0],
        row_lower=T[activity,-Inf],row_upper=T[activity,Inf])
    ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,
        primal_tolerance=tol,basis_refactorization=:native,verbose=false))
    ws.basis=JSimplex.Basis([1,3],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.BASIC])
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Joint recovery retains a nearby prediction when reconstruction is remote" begin
    for T in (Float32,Float64)
        ws=remote_joint_workspace(T)
        tol=ws.options.primal_tolerance
        activity=-tol/T(2)
        original=copy(ws.primal)
        candidate=JSimplex._pivot_quality_buffers(ws).trial
        candidate .= T[0,1.25tol]
        prediction=copy(candidate)
        @test original[1] < -9tol
        @test !JSimplex._legacy_primal_point_certified(ws)
        terminal=JSimplex._finish_legacy_primal_point!(ws,candidate,()->false)
        @test isnothing(terminal)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.primal[2]===original[2]
        @test maximum(abs.(ws.primal[ws.basis.basic_indices]-prediction))<=8tol
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
        q=Rational{BigInt}
        @test q(ws.primal[1])>=-q(tol)
        @test abs(q(T(0.01))*q(ws.primal[1])-q(activity))<=q(tol)
        @test abs(q(ws.primal[1])-q(ws.primal[3]))<=q(tol)
    end
end

@testset "Prediction-anchored recovery rolls back failed and cancelled trials" begin
    for T in (Float32,Float64), mode in (:stop,:throw,:unreachable,:nonfinite,:length)
        ws=remote_joint_workspace(T);tol=ws.options.primal_tolerance
        original=copy(ws.primal);cache=copy(ws.scratch.row_solution)
        prediction=T[0,1.25tol]
        mode==:unreachable && (prediction .= 1000tol)
        mode==:nonfinite && (prediction[1]=T(NaN))
        mode==:length && pop!(prediction)
        interrupted=Ref(false)
        stop=()->begin
            if mode in (:stop,:throw) && !isequal(ws.primal,original)
                interrupted[]=true
                mode==:throw && error("cancel prediction anchor")
                return true
            end
            false
        end
        if mode==:throw
            @test_throws ErrorException("cancel prediction anchor") JSimplex._try_joint_primal_point_recovery!(ws,stop,prediction)
        else
            @test !JSimplex._try_joint_primal_point_recovery!(ws,stop,prediction)
        end
        @test isequal(ws.primal,original)
        @test isequal(ws.scratch.row_solution,cache)
        @test ws.basis.basic_indices==[1,3]
        @test interrupted[] == (mode in (:stop,:throw))
    end
end

@testset "A locally repairable reconstruction remains the recovery anchor" begin
    for T in (Float32,Float64)
        ws=remote_joint_workspace(T);tol=ws.options.primal_tolerance
        ws.primal[1]=-T(1.25)*tol;ws.primal[3]=T(1.25)*tol
        original=copy(ws.primal)
        @test JSimplex._try_joint_primal_point_recovery!(ws,()->false,T[1000tol,1000tol])
        @test JSimplex._legacy_primal_point_certified(ws)
        @test maximum(abs.(ws.primal-original))<=8tol
        @test ws.primal[2]===original[2]
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
    end
end
