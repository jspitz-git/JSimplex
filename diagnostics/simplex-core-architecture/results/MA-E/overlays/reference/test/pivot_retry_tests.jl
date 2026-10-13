using SparseArrays, LinearAlgebra

@testset "Pivot agreement requires a separated, signed estimate" begin
    @test !JSimplex._pivot_agrees(1.0,1.0001,1e-10)
    @test JSimplex._pivot_agrees(1e-9,1e-9+1e-16,1e-15)
    @test !JSimplex._pivot_agrees(NaN,1.0,1e-10)
    @test !JSimplex._pivot_agrees(Inf,Inf,1.0)
    @test !JSimplex._pivot_agrees(1e-9,-1e-9,3e-9)
    @test !JSimplex._pivot_agrees(1e-9,1e-9,1e-9)
    @test !JSimplex._pivot_agrees(1.0,1.0,-1.0)
    @test JSimplex._pivot_agrees(-1e-14,-1e-14,1e-28)
    @test JSimplex._pivot_agrees(1//10^9,1//10^9,0//1)
    @test !JSimplex._pivot_agrees(0//1,0//1,0//1)
end

@testset "Staged simplex application owns candidate state" begin
    for algorithm in (:dual,:primal), update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl),
        backend in (:native,:markowitz)
        dual = algorithm == :dual
        p = LinearProblem(sparse([1.0;;]),[dual ? 1.0 : -1.0];
            row_lower=dual ? [1.0] : [nothing],row_upper=dual ? [nothing] : [1.0])
        options = SolverOptions(verbose=false,pricing=:dantzig,
                                basis_update=update,basis_refactorization=backend)
        w = JSimplex.initialize_workspace(p,options)
        perform = (staged,stop) -> dual ? JSimplex._dual_iteration!(staged,stop) :
            JSimplex._primal_iteration!(staged,stop,options.dual_tolerance)
        saved = (copy(w.costs),copy(w.primal),copy(w.reduced_costs),
                 copy(w.basis.states),copy(w.basis.basic_indices),w.iterations)
        @test_throws ErrorException JSimplex._transactional_simplex_step!(w,()->false) do staged,guard
            @test staged.costs !== w.costs
            @test staged.basis.states !== w.basis.states
            @test isnothing(perform(staged,guard))
            error("failure after candidate factor update")
        end
        @test saved == (w.costs,w.primal,w.reduced_costs,w.basis.states,
                       w.basis.basic_indices,w.iterations)
        @test JSimplex.basis_matrix(w)*JSimplex.forward_solve!(zeros(1),w.factorization,[1.0]) ≈ [1.0]
        calls = Ref(0)
        stop = () -> (calls[] += 1; calls[] > 1)
        result = JSimplex._transactional_simplex_step!(w,stop) do staged,guard
            perform(staged,guard)
        end
        @test result.status == TIME_LIMIT
        @test saved == (w.costs,w.primal,w.reduced_costs,w.basis.states,
                       w.basis.basic_indices,w.iterations)
        @test isnothing(JSimplex._transactional_simplex_step!(w,()->false) do staged,guard
            perform(staged,guard)
        end)
        @test w.iterations == 1
        @test w.primal[1] == 1.0
        @test JSimplex.basis_matrix(w)*JSimplex.forward_solve!(zeros(1),w.factorization,[1.0]) ≈ [1.0]
    end
end

function pivot_workspace(B::Matrix{T}, rhs::Vector{T}; update=:pfi, backend=:native) where {T}
    p = LinearProblem(sparse(hcat(B,rhs)),zeros(T,size(B,2)+1))
    ws = JSimplex.initialize_workspace(p,SolverOptions(T; verbose=false,
        basis_update=update,basis_refactorization=backend))
    ws.basis.basic_indices .= axes(B,2)
    fill!(ws.basis.states,JSimplex.AT_LOWER)
    ws.basis.states[1:size(B,2)] .= JSimplex.BASIC
    ws.basis.states[(size(B,2)+2):end] .= JSimplex.FREE_NONBASIC
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Pivot validation checks independent basis solves" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        B = T[1 0;0 1]
        rhs = T[1//10^9,1]
        w = pivot_workspace(B,rhs)
        policy = JSimplex.NumericalPolicy(T)
        rho = T[1,0]
        candidate = JSimplex.PivotCandidate(3,1,rhs[1],copy(rhs),rho)
        saved = (copy(w.primal),copy(w.costs),copy(w.reduced_costs),
                 copy(w.basis.states),copy(w.basis.basic_indices),w.iterations)
        @test JSimplex.validate_pivot!(w,candidate,policy) == :accept
        wrong = JSimplex.PivotCandidate(3,1,-rhs[1],copy(rhs),rho)
        @test JSimplex.validate_pivot!(w,wrong,policy) == :reject_candidate
        stale = JSimplex.PivotCandidate(3,1,rhs[1],2rhs,rho)
        @test JSimplex.validate_pivot!(w,stale,policy) == :refresh
        @test saved == (w.primal,w.costs,w.reduced_costs,w.basis.states,
                        w.basis.basic_indices,w.iterations)
    end
    # Both componentwise backward errors can be small while the pivot estimates
    # disagree substantially for an ill-conditioned basis.
    B = [1.0 1.0;1.0 1.0+2.0^-40]
    rhs = [1.0,1.0]
    w = pivot_workspace(B,rhs)
    v = [1.0001,-0.0001]
    rho = [2.0^40+1,-2.0^40]
    policy = JSimplex.NumericalPolicy(Float64)
    scratch = JSimplex.SolveQualityScratch(Float64,2)
    @test JSimplex.solve_quality!(scratch,B,v,rhs,policy).reliable
    candidate = JSimplex.PivotCandidate(3,1,1.0,v,rho)
    @test JSimplex.validate_pivot!(w,candidate,policy) != :accept
end
