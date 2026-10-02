using JSimplex, Test, SparseArrays

function joint_point_workspace(T, manager=:pfi; impossible=false)
    tolerance=T===Float32 ? T(1e-4) : T(1e-7)
    activity=-(impossible ? T(4) : T(1.25))*tolerance
    problem=LinearProblem(sparse(reshape(T[1,-1],2,1)),T[0];
        column_lower=T[0],row_upper=T[activity,0])
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,primal_tolerance=tolerance,verbose=false)
    diagnostics=JSimplex.SimplexDiagnostics()
    ws=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;diagnostics))
    ws.basis=JSimplex.Basis([1,3],[JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.BASIC])
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal .= T[activity,activity,-activity]
    candidate=JSimplex._pivot_quality_buffers(ws).trial
    candidate .= T[1.5tolerance,-1.5tolerance]
    return ws,candidate,diagnostics
end

@testset "Joint recovery satisfies column, actual row and equation bounds" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws,candidate,diagnostics=joint_point_workspace(T,manager)
        original=copy(ws.primal); prediction=copy(candidate)
        @test !JSimplex._restore_legacy_primal_point!(ws,candidate,()->false)
        @test ws.primal==original
        @test !JSimplex._try_native_primal_point_correction!(ws,()->false)
        @test ws.primal==original
        candidate .= prediction
        terminal=JSimplex._finish_legacy_primal_point!(ws,candidate,()->false)
        @test isnothing(terminal)
        q=Rational{BigInt}; tol=q(ws.options.primal_tolerance)
        @test q(ws.primal[1])>=-tol
        @test q(ws.primal[1])<=q(original[2])+tol
        @test -q(ws.primal[1])<=tol
        @test abs(q(ws.primal[1])-q(ws.primal[2]))<=tol
        @test abs(-q(ws.primal[1])-q(ws.primal[3]))<=tol
        @test ws.primal[2]===original[2]
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
    end
end

@testset "Joint recovery preserves state when feasibility or its budget fails" begin
    for T in (Float32,Float64), mode in (:impossible,:nonbasic,:immutable,:radius,:unowned,:nonfinite,:stop,:throw)
        ws,candidate,diagnostics=joint_point_workspace(T;impossible=mode==:impossible)
        tol=ws.options.primal_tolerance
        if mode==:nonbasic
            ws.primal[2]=JSimplex.bound_value(ws.upper[2])+2tol
        elseif mode==:immutable
            ws.basis=JSimplex.Basis([2,3],[JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC])
            ws.primal[1]=zero(T)
        elseif mode==:radius
            ws.problem.A.nzval .*= T(1e-6)
            ws.problem.column_lower[1]=ws.lower[1]=Bound{T}(nothing)
            ws.primal[1]=zero(T)
        elseif mode==:unowned
            ws.lower[1]=Bound(-10tol);ws.upper[1]=Bound(-4tol)
        elseif mode==:nonfinite
            ws.primal[1]=T(NaN)
        end
        original=copy(ws.primal);cache=copy(ws.scratch.row_solution)
        metadata=(copy(ws.lower),copy(ws.upper),copy(ws.costs),copy(ws.basis.basic_indices),copy(ws.basis.states))
        cancelled=Ref(false)
        stop=()->begin
            cancelled[] && return true
            if mode in (:stop,:throw) && !isequal(ws.primal,original)
                mode==:throw && error("cancel joint recovery")
                cancelled[]=true
                return true
            end
            false
        end
        if mode==:throw
            @test_throws ErrorException("cancel joint recovery") JSimplex._try_joint_primal_point_recovery!(ws,stop)
        else
            @test !JSimplex._try_joint_primal_point_recovery!(ws,stop)
        end
        @test isequal(ws.primal,original)
        @test ws.scratch.row_solution==cache
        @test metadata==(ws.lower,ws.upper,ws.costs,ws.basis.basic_indices,ws.basis.states)
        @test JSimplex.event_count(diagnostics,:primal_point_projected)==0
    end
end

@testset "Joint recovery uses only owned active working bounds" begin
    for T in (Float32,Float64)
        ws,candidate,diagnostics=joint_point_workspace(T)
        tol=ws.options.primal_tolerance
        ws.problem.row_upper[1]=ws.upper[2]=Bound(-10tol)
        journal=JSimplex.PerturbationJournal(ws)
        journal.bounds=JSimplex.BoundPerturbationState(ws)
        journal.bounds.active_upper[2]=Bound(-T(1.25)*tol)
        journal.bounds.active=true;journal.bounds.level=1
        ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
        ws.scratch.perturbations=journal;ws.perturbed=true
        original=copy(ws.primal);owner=journal.workspace_id
        journal.workspace_id=UInt(0)
        @test_throws ArgumentError JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test ws.primal==original
        journal.workspace_id=owner
        @test JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test !JSimplex._original_primal_feasible(ws.problem,ws.primal[1:1],tol)
        @test ws.primal[2]===original[2]
        @test journal.workspace_id==owner && journal.bounds.active && journal.bounds.level==1
        JSimplex.restore_perturbations!(ws,journal)
        @test !JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test !JSimplex._legacy_primal_point_certified(ws)
    end
end

@testset "Joint recovery cancels within a partially projected sweep" begin
    for T in (Float32,Float64), throwing in (false,true)
        tol=T===Float32 ? T(1e-4) : T(1e-7)
        m=300
        p=LinearProblem(sparse(reshape(vcat(one(T),fill(-one(T),m-1)),m,1)),T[0];
            column_lower=T[0],row_upper=vcat(-T(1.25)*tol,zeros(T,m-1)))
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,primal_tolerance=tol,verbose=false))
        ws.basis=JSimplex.Basis(vcat(1,collect(3:m+1)),vcat(JSimplex.BASIC,JSimplex.AT_UPPER,fill(JSimplex.BASIC,m-1)))
        ws.primal .= vcat(-T(1.25)*tol,-T(1.25)*tol,fill(T(1.25)*tol,m-1))
        original=copy(ws.primal);cache=copy(ws.scratch.row_solution);interrupted=Ref(false)
        stop=()->begin
            if !isequal(ws.primal,original)
                interrupted[]=true
                throwing && error("stop partial sweep")
                return true
            end
            false
        end
        if throwing
            @test_throws ErrorException("stop partial sweep") JSimplex._try_joint_primal_point_recovery!(ws,stop)
        else
            @test !JSimplex._try_joint_primal_point_recovery!(ws,stop)
        end
        @test interrupted[]
        @test ws.primal==original
        @test ws.scratch.row_solution==cache
    end
end

@testset "Finite-input overflow rolls back a partially changed point" begin
    for T in (Float32,Float64)
        tol=T===Float32 ? T(1e-4) : T(1e-7)
        A=sparse([1,2,3],[1,2,1],T[1,floatmax(T)/2,-1],3,2)
        p=LinearProblem(A,zeros(T,2);column_lower=T[0,0],
            row_lower=T[-Inf,0,-Inf],row_upper=T[-1.25tol,Inf,0])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,primal_tolerance=tol,verbose=false))
        ws.basis=JSimplex.Basis([1,2,5],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.AT_LOWER,JSimplex.BASIC])
        ws.primal .= T[-1.25tol,4,-1.25tol,0,1.25tol]
        original=copy(ws.primal);cache=copy(ws.scratch.row_solution)
        @test all(isfinite,ws.primal) && all(isfinite,A.nzval)
        # The first basic coordinate is clamped before row two overflows.
        @test !JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        @test ws.primal==original
        @test ws.scratch.row_solution==cache
    end
end

@testset "Joint recovery preserves a thin feasible intersection" begin
    for T in (Float32,Float64)
        tol=T(1e-7)
        A=sparse(T[1 0.01;1 0])
        p=LinearProblem(A,zeros(T,2);column_lower=T[-Inf,0],column_upper=T[Inf,0],
            row_lower=T[-Inf,1.9tol],row_upper=T[0,Inf])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,primal_tolerance=tol,verbose=false))
        ws.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.AT_LOWER])
        ws.primal .= T[0,0,0,1.9tol]
        original=copy(ws.primal)
        @test JSimplex._try_joint_primal_point_recovery!(ws,()->false)
        q=Rational{BigInt}
        @test q(ws.primal[1])+q(T(0.01))*q(ws.primal[2])<=q(tol)
        @test q(ws.primal[1])>=q(original[4])-q(tol)
        @test abs(q(ws.primal[2]))<=q(tol)
        @test ws.primal[3:4]==original[3:4]
        @test ws.scratch.row_solution==ws.primal[1:2]
    end
end

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
