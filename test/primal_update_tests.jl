using SparseArrays, LinearAlgebra

@testset "Primal bound flips preserve the basis and prices" begin
    @test isdefined(JSimplex, :apply_primal_flip!)
    if isdefined(JSimplex, :apply_primal_flip!)
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            p = LinearProblem(sparse(reshape(T[1], 1, 1)), T[-1];
                row_upper=T[2], column_upper=T[1])
            w = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
            basis, factor = copy(w.basis.basic_indices), w.factorization
            costs, prices = copy(w.costs), copy(w.reduced_costs)
            weights = copy(w.pricing_weights)
            @test isnothing(JSimplex.apply_primal_flip!(w, 1, one(T), T[-1]))
            @test w.primal == T[1, 1]
            @test w.basis.states[1] == JSimplex.AT_UPPER
            @test w.basis.basic_indices == basis
            @test w.factorization === factor
            @test (w.costs, w.reduced_costs, w.pricing_weights) == (costs, prices, weights)
            @test w.iterations == 0
            @test isnothing(JSimplex.apply_primal_flip!(w, 1, -one(T), T[-1]))
            @test w.primal == T[0, 0]
            @test w.basis.states[1] == JSimplex.AT_LOWER
            @test w.basis.basic_indices == basis
            @test w.factorization === factor
            @test (w.costs, w.reduced_costs, w.pricing_weights) == (costs, prices, weights)
        end
    end
end

@testset "Flip updates retain stored precision and reject aliased directions" begin
    setprecision(BigFloat, 512) do
        coefficient = one(BigFloat) + BigFloat(2)^-400
        p = LinearProblem(sparse(reshape([coefficient], 1, 1)), BigFloat[-1];
            row_upper=BigFloat[2], column_upper=BigFloat[1])
        w = JSimplex.initialize_workspace(p, SolverOptions(BigFloat; verbose=false))
        column = [-coefficient]
        setprecision(BigFloat, 64) do
            JSimplex.apply_primal_flip!(w, 1, one(BigFloat), column)
            @test w.primal[2] == coefficient
            @test precision(w.primal[2]) >= 512
            @test precision(BigFloat) == 64
        end
    end
    p = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[2.0], column_upper=[1.0])
    w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
    w.primal[2] = -1.0
    before = copy(w.primal)
    @test_throws ArgumentError JSimplex.apply_primal_flip!(w, 1, 1.0, view(w.primal, 2:2))
    @test w.primal == before
end

function flip_workspace(::Type{T}=Float64; count=1, update=:pfi, backend=:native,
                        observer=nothing, adaptive=false, incremental=true) where T
    p = LinearProblem(sparse(ones(T, 1, count)), -ones(T, count);
        row_upper=T[count+1], column_upper=ones(T, count))
    options = SolverOptions(T; verbose=false, algorithm=:primal, pricing=:dantzig,
        presolve=false, basis_update=update, basis_refactorization=backend)
    policy = JSimplex.NumericalPolicy(T; simplex_strategy=adaptive ? :adaptive : :legacy,
        incremental_primal=incremental)
    d = JSimplex.SimplexDiagnostics(; observer, kernel_timing=true)
    w = JSimplex.initialize_workspace(p, options;
        progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy, diagnostics=d))
    for key in keys(d.kernel_calls)
        d.kernel_calls[key] = 0
    end
    return w, d
end

@testset "A completed flip has one FTRAN and no hidden recomputation" begin
    legacy, legacy_diagnostics = flip_workspace(; incremental=false)
    @test isnothing(JSimplex._primal_iteration!(legacy, ()->false, legacy.options.dual_tolerance))
    @test legacy.primal == [1.0, 1.0]
    @test legacy_diagnostics.kernel_calls[:ftran] == 2
    @test legacy_diagnostics.kernel_calls[:btran] == 1
    for adaptive in (false, true), update in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl),
        backend in (:native, :markowitz)
        w, d = flip_workspace(; adaptive, update, backend)
        factor = w.factorization
        @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
        @test w.primal == [1.0, 1.0]
        @test w.iterations == 1
        @test w.factorization === factor
        @test isempty(factor.updates)
        @test d.kernel_calls[:ftran] == 1
        @test d.kernel_calls[:btran] == 0
        @test JSimplex.event_count(d, :flip_completed) == 1
    end
end

@testset "A deadline before flip commit preserves the live state" begin
    for adaptive in (false, true)
        proposed = Ref(false)
        observer = (event, w) -> (event == :pivot_proposed && (proposed[] = true); nothing)
        w, d = flip_workspace(; observer, adaptive)
        before = (copy(w.primal), copy(w.basis.states), copy(w.reduced_costs))
        result = JSimplex._primal_iteration!(w, ()->proposed[], w.options.dual_tolerance)
        @test result.status == TIME_LIMIT
        @test (w.primal, w.basis.states, w.reduced_costs) == before
        @test w.iterations == 0
        @test JSimplex.event_count(d, :flip_completed) == 0
    end
end

@testset "Flip chains use periodic independent audits" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        w, d = flip_workspace(T; count=45)
        for i in 1:45
            @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
            @test w.primal[end] == T(i)
            @test sum(w.primal[1:45]) == w.primal[end]
        end
        @test w.iterations == 45
        @test d.kernel_calls[:btran] == 2
        @test w.primal == vcat(ones(T,45), T[45])
        @test w.reduced_costs == vcat(-ones(T,45), T[0])
    end
    @test isdefined(JSimplex, :audit_primal_values!)
    if isdefined(JSimplex, :audit_primal_values!)
        w, _ = flip_workspace()
        w.primal[end] = 0.25
        @test !JSimplex.audit_primal_values!(w)
        @test w.primal == [0.0, 0.0]
        @test JSimplex.audit_primal_values!(w)
    end
end

@testset "A zero flip changes no bound state or counter" begin
    if isdefined(JSimplex, :apply_primal_flip!)
        for upper in (0.0, 1.0)
            p = LinearProblem(sparse([1.0;;]), [-1.0];
                row_upper=[2.0], column_upper=[upper])
            w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
            before = (copy(w.primal), copy(w.basis.states), w.iterations)
            @test isnothing(JSimplex.apply_primal_flip!(w, 1, 0.0, [-1.0]))
            @test (w.primal, w.basis.states, w.iterations) == before
        end
    end
end

@testset "Unsafe flip predictions leave live values untouched" begin
    if isdefined(JSimplex, :apply_primal_flip!)
        p = LinearProblem(sparse([1.0;;]), [-1.0];
            row_upper=[nothing], column_upper=[2.0])
        w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
        before = (copy(w.primal), copy(w.basis.states), w.iterations)
        @test_throws JSimplex._UnreliableBasisSolve JSimplex.apply_primal_flip!(
            w, 1, 2.0, [-floatmax(Float64)])
        @test (w.primal, w.basis.states, w.iterations) == before
        @test_throws ArgumentError JSimplex.apply_primal_flip!(w, 1, -2.0, [-1.0])
        @test (w.primal, w.basis.states, w.iterations) == before
        @test_throws DimensionMismatch JSimplex.apply_primal_flip!(w, 1, 2.0, Float64[])
        @test (w.primal, w.basis.states, w.iterations) == before
    end
end

@testset "Reverse flips and audits preserve completed work" begin
    w, d = flip_workspace(; count=25)
    for _ in 1:19
        JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance)
    end
    w.primal[end] += 0.25
    @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
    @test w.iterations == 20
    @test w.primal[end] == 20.0
    @test JSimplex.event_count(d, :flip_completed) == 20
    @test JSimplex.event_count(d, :pivot_rejected) > 0
    @test JSimplex.primal_infeasibility(w) == 0.0

    w, d = flip_workspace()
    JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance)
    w.costs[1] = 1.0
    JSimplex.recompute!(w)
    for key in keys(d.kernel_calls)
        d.kernel_calls[key] = 0
    end
    @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
    @test w.primal == [0.0, 0.0]
    @test w.iterations == 2
    @test w.basis.states[1] == JSimplex.AT_LOWER
    @test d.kernel_calls[:ftran] == 1
    @test d.kernel_calls[:btran] == 0
end

@testset "Boxed public solves retain Phase I and original-model certification" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}),
        pricing in (:dantzig, :devex, :steepest_edge), phase_one in (false, true)
        p = LinearProblem(sparse(ones(T, 1, 5)), -ones(T, 5);
            row_lower=T[phase_one ? 3 : 0], row_upper=T[6], column_upper=ones(T, 5))
        o = SolverOptions(T; algorithm=:primal, pricing, presolve=false,
            verbose=false, simplex_strategy=:adaptive)
        result = solve(p; options=o)
        @test result.status == OPTIMAL
        @test result.primal == ones(T, 5)
        @test result.objective_value == T(-5)
    end
    for limit in (0, 1, 5), presolve in (false, true)
        p = LinearProblem(sparse(ones(1, 5)), -ones(5);
            row_upper=[6.0], column_upper=ones(5))
        o = SolverOptions(; algorithm=:primal, pricing=:dantzig, presolve,
            verbose=false, iteration_limit=limit)
        policy = JSimplex.NumericalPolicy(Float64; incremental_primal=true)
        result = JSimplex._solve_diagnosed(p, nothing; options=o, numerical_policy=policy)
        @test result.status == (presolve || limit == 5 ? OPTIMAL : ITERATION_LIMIT)
        @test result.statistics.iterations <= limit
        if result.status == OPTIMAL
            @test result.primal == ones(5)
            @test result.objective_value == -5.0
        end
    end
end

@testset "Flip observers see a complete step and retain exception provenance" begin
    seen = Ref(false)
    failure = JSimplex.SingularException(17)
    observer = (event, ws) -> begin
        if event == :flip_completed
            @test ws.primal == [1.0, 1.0]
            @test ws.basis.states[1] == JSimplex.AT_UPPER
            @test ws.iterations == 1
            seen[] = true
            throw(failure)
        end
        nothing
    end
    w, d = flip_workspace(; observer)
    exception = try
        JSimplex._solve_diagnosed(w.problem, d; options=w.options,
            numerical_policy=w.progress.numerical_policy)
    catch e
        e
    end
    @test seen[]
    @test exception isa JSimplex.DiagnosticObserverFailure
    @test exception.cause === failure
end

@testset "The integrated flip retains a stored high-precision bound" begin
    setprecision(BigFloat, 512) do
        upper = one(BigFloat) + BigFloat(2)^-400
        p = LinearProblem(sparse(BigFloat[1;;]), BigFloat[-1];
            row_upper=BigFloat[2], column_upper=[upper])
        policy = JSimplex.NumericalPolicy(BigFloat; incremental_primal=true)
        w = JSimplex.initialize_workspace(p, SolverOptions(BigFloat; verbose=false, pricing=:dantzig);
            progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
        setprecision(BigFloat, 64) do
            @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
            @test w.primal == [upper, upper]
            @test w.iterations == 1
            @test precision(BigFloat) == 64
        end
    end
end

@testset "Incremental reduced costs use the old unit leaving column" begin
    @test isdefined(JSimplex, :update_reduced_costs!)
    if isdefined(JSimplex, :update_reduced_costs!)
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            r = T[-2,3,0]
            @test isnothing(JSimplex.update_reduced_costs!(r,T[-1,2,1],1,3,-one(T)))
            @test r == T[0,-1,-2]
        end
        r = [-2.0,3.0,0.0]
        @test_throws ArgumentError JSimplex.update_reduced_costs!(r,r,1,3,-1.0)
        @test r == [-2.0,3.0,0.0]
        @test_throws JSimplex._UnreliableBasisSolve JSimplex.update_reduced_costs!(r,[-1.0,Inf,1.0],1,3,-1.0)
        @test r == [-2.0,3.0,0.0]
    end
end

@testset "Incremental pivots agree with an independent basis solve" begin
    @test isdefined(JSimplex, :apply_primal_pivot!)
    if isdefined(JSimplex, :apply_primal_pivot!)
        for T in (Float32, Float64, BigFloat, Rational{BigInt}),
            upper in (zero(T),T(3))
            p = LinearProblem(sparse(T[1 2; 2 1]), T[-2,-1]; row_upper=T[upper,10])
            w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
            factor = w.factorization
            @test isnothing(JSimplex.apply_primal_pivot!(w,1,1,upper,T[-1,-2],T[-1,-2,1,0];leaving_state=JSimplex.AT_UPPER))
            @test w.basis.basic_indices == [1,4]
            @test w.basis.states == [JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_UPPER,JSimplex.BASIC]
            @test w.scratch.basic_mask == [true,false,false,true]
            @test w.primal == T[upper,0,upper,2upper]
            @test w.reduced_costs == T[0,3,-2,0]
            @test w.factorization === factor
            @test w.iterations == 0
            @test JSimplex.basis_matrix(w) * JSimplex.forward_solve!(zeros(T,2),factor,T[1,2]) ≈ T[1,2]
            predicted = (copy(w.primal),copy(w.reduced_costs))
            JSimplex.recompute!(w)
            @test (w.primal,w.reduced_costs) == predicted
        end
    end
end

function pivot_workspace(::Type{T}=Float64; count=2, pricing=:dantzig, update=:pfi,
        backend=:native, adaptive=false, incremental=true, observer=nothing,
        mixed=false, interval=100) where T
    p = LinearProblem(sparse(Matrix{T}(I,count,count)), -ones(T,count);
        row_upper=ones(T,count), column_upper=mixed ? T[iseven(i) ? 2 : 1//2 for i in 1:count] : fill(T(2),count))
    o = SolverOptions(T;verbose=false,algorithm=:primal,pricing,basis_update=update,
        basis_refactorization=backend,refactorization_interval=interval,presolve=false)
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=adaptive ? :adaptive : :legacy,
        incremental_primal=true,incremental_primal_pivots=incremental)
    d = JSimplex.SimplexDiagnostics(;observer,kernel_timing=true)
    w = JSimplex.initialize_workspace(p,o;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
    for k in keys(d.kernel_calls); d.kernel_calls[k]=0; end
    return w,d
end

@testset "Incremental pivots share validated rows with pricing" begin
    for adaptive in (false,true), pricing in (:dantzig,:devex,:steepest_edge),
        update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl), backend in (:native,:markowitz)
        w,d = pivot_workspace(;adaptive,pricing,update,backend)
        @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
        @test w.primal == [1,0,1,0]
        @test w.reduced_costs == [0,-1,-1,0]
        @test w.scratch.basic_mask == [true,false,false,true]
        @test w.iterations == 1
        @test d.kernel_calls[:ftran] == 1
        @test d.kernel_calls[:btran] == (pricing == :steepest_edge ? 2 : 1)
    end
end

@testset "Pivot and mixed chains retain values and prices through audits" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), mixed in (false,true)
        w,d = pivot_workspace(T;count=45,mixed)
        for i in 1:45
            @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
            x = w.primal[1:45]
            @test w.problem.A*x == w.primal[46:end]
            @test all(iszero,w.reduced_costs[w.basis.basic_indices])
            B = Matrix(JSimplex.basis_matrix(w))
            dual = transpose(B) \ w.costs[w.basis.basic_indices]
            @test w.reduced_costs[1:45] ≈ w.costs[1:45]-transpose(w.problem.A)*dual
            @test w.reduced_costs[46:end] ≈ w.costs[46:end]+dual
            @test w.scratch.basic_mask == (w.basis.states .== JSimplex.BASIC)
        end
        @test d.kernel_calls[:btran] == (mixed ? 22 : 45)+2
        @test JSimplex.audit_primal_values!(w)
        w.reduced_costs[end] += one(T)
        @test !JSimplex.audit_primal_values!(w)
    end
end

@testset "Pivot audits correct drift and publish only a verified step" begin
    for update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl)
        seen = Ref(0)
        observer = (event,w) -> begin
            if event == :pivot_completed
                seen[] += 1
                @test w.iterations == 20
                @test w.primal == [1,0,1,0]
                @test w.reduced_costs == [0,-1,-1,0]
            end
            nothing
        end
        w,d = pivot_workspace(;update,observer)
        w.iterations = 19
        w.reduced_costs[2] = -0.5
        @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
        @test seen[] == 1
        @test w.refactorizations == 0
        @test JSimplex.event_count(d,:pivot_rejected) == 0
        @test JSimplex.basis_matrix(w)*JSimplex.forward_solve!(zeros(2),w.factorization,[2.0,3.0]) ≈ [2.0,3.0]
    end
end

@testset "Pivot deadlines and overflow cannot publish partial values" begin
    proposed = Ref(false)
    observer = (event,w)->(event == :pivot_proposed && (proposed[]=true); nothing)
    w,d = pivot_workspace(;observer)
    before = (copy(w.primal),copy(w.reduced_costs),copy(w.basis.basic_indices))
    result = JSimplex._primal_iteration!(w,()->proposed[],w.options.dual_tolerance)
    @test result.status == TIME_LIMIT
    @test (w.primal,w.reduced_costs,w.basis.basic_indices) == before
    @test isempty(w.factorization.updates)
    @test w.iterations == 0
    w,_ = pivot_workspace()
    before = (copy(w.primal),copy(w.reduced_costs),copy(w.basis.basic_indices))
    @test_throws JSimplex._UnreliableBasisSolve JSimplex.apply_primal_pivot!(w,1,1,1.0,[-1.0,Inf],[-1.0,0,1,0];leaving_state=JSimplex.AT_UPPER)
    @test (w.primal,w.reduced_costs,w.basis.basic_indices) == before
    @test isempty(w.factorization.updates)
end

@testset "Integrated pivots and corrected audits preserve stored precision" begin
    for drift in (false,true), update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl)
        setprecision(BigFloat,512) do
            upper = one(BigFloat)+BigFloat(2)^-400
            p = LinearProblem(sparse(BigFloat[1 0;0 1]),BigFloat[-2,-1];row_upper=BigFloat[upper,2])
            policy = JSimplex.NumericalPolicy(BigFloat;incremental_primal_pivots=true)
            w = JSimplex.initialize_workspace(p,SolverOptions(BigFloat;verbose=false,pricing=:dantzig,basis_update=update);
                progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
            if drift
                w.iterations = 19
                w.reduced_costs[2] = -BigFloat(1)/2
            end
            setprecision(BigFloat,64) do
                @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
                @test w.primal == BigFloat[upper,0,upper,0]
                @test w.reduced_costs == BigFloat[0,-1,-2,0]
                @test precision(w.primal[1]) >= 512
                @test precision(BigFloat) == 64
                @test w.iterations == (drift ? 20 : 1)
            end
        end
    end
end

@testset "Independent incremental pivots reprice before certification" begin
    w,_ = pivot_workspace()
    w.reduced_costs[1:2] .= 0
    result = JSimplex._primal_optimize!(w,()->false)
    @test result.status == OPTIMAL
    @test w.primal == ones(4)
    @test w.iterations == 2
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), pricing in (:dantzig,:devex,:steepest_edge),
        adaptive in (false,true), phase_one in (false,true)
        p = LinearProblem(sparse(T[1 2;2 1]),T[-2,-1];row_lower=phase_one ? T[1,1] : T[0,0],row_upper=T[3,4])
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=adaptive ? :adaptive : :legacy,incremental_primal_pivots=true)
        result = JSimplex._solve_diagnosed(p,nothing;
            options=SolverOptions(T;algorithm=:primal,pricing,verbose=false,presolve=false),numerical_policy=policy)
        @test result.status == OPTIMAL
        @test result.objective_value ≈ T(-4)
        @test all(p.A*result.primal .<= T[3,4] .+ T(1//1000))
    end
end

@testset "A recomputed infeasible point cannot certify unboundedness" begin
    p = LinearProblem(spzeros(1,1),[-1.0];row_lower=[1.0])
    policy = JSimplex.NumericalPolicy(Float64;incremental_primal_pivots=true)
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,pricing=:dantzig);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    w.primal[2] = 1.0
    @test JSimplex.primal_infeasibility(w) == 0
    result = JSimplex._primal_optimize!(w,()->false)
    @test result.status == NUMERICAL_ERROR
end

@testset "Coupled pivots agree with independent dense reference solves" begin
    for T in (Float32,Float64,Rational{BigInt}), pricing in (:dantzig,:devex,:steepest_edge),
        update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl), backend in (:native,:markowitz)
        A = T[(mod(3i+7j+i*j,13)+1)//10 for i in 1:6,j in 1:12]
        p = LinearProblem(sparse(A),T[-(mod(7j,11)+1)//3 for j in 1:12];
            row_upper=T[2+i//3 for i in 1:6],column_upper=T[iseven(j) ? 5//2 : 1//4 for j in 1:12])
        policy = JSimplex.NumericalPolicy(T;incremental_primal=true,incremental_primal_pivots=true)
        options = SolverOptions(T;verbose=false,pricing,basis_update=update,basis_refactorization=backend,refactorization_interval=7)
        w = JSimplex.initialize_workspace(p,options;progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        tolerance = T <: Rational ? zero(T) : T(100)*eps(T)
        terminal = nothing
        for step in 1:100
            terminal = JSimplex._primal_iteration!(w,()->false,options.dual_tolerance)
            W = T <: Rational ? T : Float64
            B = Matrix{W}(JSimplex.basis_matrix(w))
            dual = transpose(B) \ W.(w.costs[w.basis.basic_indices])
            reference = vcat(W.(w.costs[1:12])-transpose(W.(A))*dual,W.(w.costs[13:end])+dual)
            @test maximum(abs,w.reduced_costs-reference) <= tolerance*max(one(T),maximum(abs,reference))
            @test maximum(abs,A*w.primal[1:12]-w.primal[13:end]) <= tolerance*max(one(T),maximum(abs,w.primal))
            @test all(iszero,w.reduced_costs[w.basis.basic_indices])
            for j in eachindex(w.basis.states)
                if w.basis.states[j] != JSimplex.BASIC
                    @test w.primal[j] == JSimplex._nonbasic_value(w,j)
                end
            end
            isnothing(terminal) || break
        end
        @test !isnothing(terminal)
        @test terminal.status == OPTIMAL
    end
end
@testset "Reverse and free entering pivots retain the signed step" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), free in (false,true)
        p = LinearProblem(sparse(T[1;;]),T[1];row_lower=T[-1],row_upper=T[1],
            column_lower=free ? [nothing] : T[-2],column_upper=free ? [nothing] : T[2])
        policy = JSimplex.NumericalPolicy(T;incremental_primal_pivots=true)
        w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false,pricing=:dantzig);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        if !free
            w.basis.states[1] = JSimplex.AT_UPPER
            JSimplex.recompute!(w)
            # Use a feasible upper start with the row at its upper bound.
            w.upper[1] = JSimplex.Bound(one(T))
            JSimplex.recompute!(w)
        end
        @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
        @test w.primal == T[-1,-1]
        @test w.basis.states == [JSimplex.BASIC,JSimplex.AT_LOWER]
        @test w.reduced_costs == T[0,1]
    end
end

function price_audit_workspace(::Type{T}, magnitude) where T
    p = LinearProblem(sparse(T[1 1]),T[magnitude,magnitude+one(T)];row_lower=T[0],row_upper=T[1])
    w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
    w.basis = JSimplex.Basis([1],JSimplex.VariableState[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    JSimplex.recompute!(w;refactorize=true)
    return w
end

@testset "Price audits measure backward error without cancellation bias" begin
    for (T,power) in ((Float32,20),(Float64,40),(BigFloat,400))
        setprecision(BigFloat,512) do
            magnitude = T(2)^power
            w = price_audit_workspace(T,magnitude)
            correct = copy(w.reduced_costs)
            w.reduced_costs[2] += eps(magnitude)
            @test abs(w.reduced_costs[2]-correct[2]) > w.progress.numerical_policy.solve_tolerance
            @test JSimplex.audit_primal_values!(w)
            @test w.reduced_costs == correct
            w.reduced_costs[2] += magnitude/T(10)
            @test !JSimplex.audit_primal_values!(w)
        end
    end
    # A finite dot-product scale can overflow the working scalar type.
    w = price_audit_workspace(Float64,1e308)
    w.reduced_costs[2] += 1e292
    @test JSimplex.audit_primal_values!(w)
    @test iszero(w.reduced_costs[2])
    # The test must also retain sensitivity when the absolute residual is tiny.
    w = price_audit_workspace(Float64,0.0)
    w.reduced_costs[2] = 1e-300
    w.costs[2] = 0.0
    @test !JSimplex.audit_primal_values!(w)
    w = price_audit_workspace(Rational{BigInt},big(10)^12//1)
    w.reduced_costs[2] += 1//big(10)^8
    @test !JSimplex.audit_primal_values!(w)
end

@testset "Implicit pricing residuals match an explicit system in both directions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        A = sparse(T[1 2 0;0 -3 4])
        B = JSimplex._PriceAuditMatrix(A)
        explicit = hcat(vcat(Matrix(transpose(A)),-Matrix{T}(I,2,2)),Matrix{T}(I,5,5))
        @test Matrix(B) == explicit
        policy = JSimplex.NumericalPolicy(T)
        for transposed in (false,true)
            rows,cols = transposed ? reverse(size(B)) : size(B)
            x = T.(1:cols)
            rhs = (transposed ? transpose(explicit) : explicit)*x
            scratch = JSimplex.SolveQualityScratch(T,rows)
            q = JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed)
            @test q.reliable
            @test iszero(q.absolute_error)
            rhs[1] += one(T)
            @test !JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed).reliable
        end
    end
    setprecision(BigFloat,512) do
        w = price_audit_workspace(BigFloat,BigFloat(2)^400)
        correct = copy(w.reduced_costs)
        w.reduced_costs[2] += eps(w.costs[1])
        setprecision(BigFloat,64) do
            @test JSimplex.audit_primal_values!(w)
            @test w.reduced_costs == correct
            @test precision(BigFloat) == 64
        end
    end
end

@testset "Verified audit corrections do not discard a valid new basis" begin
    for update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl)
        p=LinearProblem(sparse([1.0 0;0 1]),[-1.0,-1.0];row_upper=[1.0,1.0])
        policy=JSimplex.NumericalPolicy(Float64;incremental_primal_pivots=true)
        d=JSimplex.SimplexDiagnostics()
        w=JSimplex.initialize_workspace(p,SolverOptions(verbose=false,pricing=:dantzig,basis_update=update);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        w.iterations=19
        w.reduced_costs[2]=-0.5
        @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
        @test w.primal == [1,0,1,0]
        @test w.reduced_costs == [0,-1,-1,0]
        @test w.iterations == 20
        @test w.refactorizations == 0
        @test JSimplex.event_count(d,:pivot_rejected) == 0
        @test JSimplex.event_count(d,:pivot_completed) == 1
    end
end

@testset "Unreliable or infeasible audited pivots still roll back atomically" begin
    for update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl), fault in (:nonfinite,:infeasible)
        p=LinearProblem(sparse([1.0 0;0 1]),[-1.0,-1.0];row_upper=[1.0,1.0])
        policy=JSimplex.NumericalPolicy(Float64;incremental_primal_pivots=true)
        d=JSimplex.SimplexDiagnostics()
        w=JSimplex.initialize_workspace(p,SolverOptions(verbose=false,pricing=:dantzig,basis_update=update);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        w.iterations=19
        saved=(copy(w.primal),copy(w.reduced_costs),copy(w.basis.states),copy(w.lower),copy(w.costs))
        @test_throws JSimplex._PivotRejection JSimplex._transactional_simplex_step!(w,()->false) do c,stop
            r=JSimplex._primal_iteration_unchecked!(c,stop,c.options.dual_tolerance)
            @test isnothing(r)
            if fault==:nonfinite
                c.costs[2]=NaN
            else
                c.lower[1]=JSimplex.Bound(2.0)
            end
            r
        end
        @test (w.primal,w.reduced_costs,w.basis.states,w.lower,w.costs)==saved
        @test w.iterations==19
        @test JSimplex.event_count(d,:pivot_completed)==0
        @test isempty(w.factorization.updates)
        @test JSimplex.basis_matrix(w)*JSimplex.forward_solve!(zeros(2),w.factorization,[2.0,3.0]) ≈ [2.0,3.0]
    end
end
