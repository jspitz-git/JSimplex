using Test,JSimplex,SparseArrays,LinearAlgebra

if isdefined(JSimplex,:transfer_precision)
    @testset "Precision transfer owns active perturbation journals" begin
        p=LinearProblem(sparse([1.0 1.0]),[1.0,2.0];row_lower=[1.0])
        policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,sparse_pricing=true)
        ws=JSimplex.initialize_from_basis(p,
            JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]),
            SolverOptions(;verbose=false);policy)
        journal=JSimplex.PerturbationJournal(ws)
        journal.bounds=JSimplex.BoundPerturbationState(ws)
        journal.active_costs[1]=1.125;journal.active_costs[2]=2.25
        journal.bounds.active_lower[2]=Bound(-0.125)
        journal.bounds.active_lower[3]=Bound(0.75)
        journal.active=true;journal.bounds.active=true
        journal.level=2;journal.bounds.level=1
        journal.cooldown_until=11;journal.bounds.cooldown_until=13
        monitor=JSimplex._new_workspace_stagnation(ws,UInt(0))
        journal.last_monitor=monitor.monitor;journal.bounds.last_monitor=monitor.monitor
        journal.last_observation=9;journal.bounds.last_observation=8
        ws.scratch.stagnation=monitor
        ws.costs=journal.active_costs;ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
        ws.scratch.perturbations=journal;ws.perturbed=true
        JSimplex.recompute!(ws)
        JSimplex._sparse_pricing_workspace!(ws)
        push!(ws.scratch.checkpoints,JSimplex.checkpoint_basis(ws))
        old_checkpoints=copy(ws.scratch.checkpoints)
        saved=(copy(ws.costs),copy(ws.lower),copy(ws.upper),copy(ws.primal))
        fresh=JSimplex.transfer_precision(ws,BigFloat,128,JSimplex.SimplexRunBudget(ws),policy)
        j=fresh.scratch.perturbations
        @test j isa JSimplex.PerturbationJournal{BigFloat}
        @test j.workspace_id==objectid(fresh) && j.workspace_id!=journal.workspace_id
        @test j.active && j.bounds.active && fresh.perturbed
        @test j.level==2 && j.bounds.level==1
        @test j.cooldown_until==11 && j.bounds.cooldown_until==13
        @test isnothing(j.last_monitor) && isnothing(j.bounds.last_monitor)
        @test isnothing(fresh.scratch.stagnation)
        @test fresh.costs===j.active_costs && fresh.lower===j.bounds.active_lower
        @test fresh.upper===j.bounds.active_upper
        @test j.original_costs==journal.original_costs && j.original_costs!==journal.original_costs
        @test j.bounds.original_lower==journal.bounds.original_lower
        @test fresh.costs==saved[1] && fresh.lower==saved[2] && fresh.upper==saved[3]
        @test all(c->JSimplex._checkpoint_matches(fresh,c) &&
            c.working_model!=JSimplex._checkpoint_model(ws),fresh.scratch.checkpoints)
        @test ws.scratch.checkpoints==old_checkpoints
        cache=JSimplex._sparse_pricing_workspace!(fresh)
        @test cache.rows.matrix===fresh.problem.A && cache.rows.matrix!==p.A
        JSimplex.restore_perturbations!(fresh,j)
        @test fresh.costs==journal.original_costs
        @test fresh.lower==journal.bounds.original_lower && fresh.upper==journal.bounds.original_upper
        @test !j.active && !j.bounds.active && !fresh.perturbed
        @test ws.costs==saved[1] && ws.lower==saved[2] && ws.upper==saved[3] && ws.primal==saved[4]
        @test journal.active && journal.bounds.active
        @test p.objective==[1.0,2.0] && bound_value(p.row_lower[1])==1.0
    end

    @testset "Transfer precision includes hidden stored input precision" begin
        for location in (:constant,:progress,:tolerance,:journal)
            ws=setprecision(BigFloat,512) do
                p=LinearProblem(sparse(BigFloat[1 1]),BigFloat[1,2];row_lower=BigFloat[1])
                JSimplex.initialize_from_basis(p,
                    JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]),
                    SolverOptions(BigFloat;verbose=false))
            end
            high=setprecision(BigFloat,1024) do
                BigFloat(1)+BigFloat(2)^(-700)
            end
            if location==:constant
                p=ws.problem
                ws.problem=LinearProblem{BigFloat}(p.A,p.objective,high,p.objective_sense,
                    p.row_lower,p.row_upper,p.column_lower,p.column_upper,p.variable_domains,
                    p.name,p.row_names,p.column_names)
            elseif location==:progress
                p=ws.progress
                ws.progress=typeof(p)(p.start_ns,[high],p.objective_constant,p.scaling,
                    p.iteration_offset,p.refactorization_offset,p.diagnostics,p.numerical_policy)
            elseif location==:tolerance
                o=ws.options
                ws.options=typeof(o)((k==:primal_tolerance ? high : getfield(o,k) for k in fieldnames(typeof(o)))...)
            else
                j=JSimplex.PerturbationJournal(ws)
                j.original_costs[1]=high
                ws.scratch.perturbations=j
            end
            fresh=setprecision(BigFloat,64) do
                result=JSimplex.transfer_precision(ws,BigFloat,128,JSimplex.SimplexRunBudget(ws),ws.progress.numerical_policy)
                @test precision(BigFloat)==64
                result
            end
            @test minimum(precision,fresh.problem.A.nzval)>=1024
            @test minimum(precision,fresh.primal)>=1024
            @test fresh.problem.objective_constant==ws.problem.objective_constant
            @test fresh.progress.objective==ws.progress.objective
            @test fresh.options.primal_tolerance==ws.options.primal_tolerance
            if location==:journal
                @test fresh.scratch.perturbations.original_costs[1]==high
                @test precision(fresh.scratch.perturbations.original_costs[1])>=1024
            end
        end
    end

    @testset "Transfer checks invalid bases and shared deadlines" begin
        p=LinearProblem(sparse([1.0 1.0;1.0 1.0]),[1.0,2.0];row_lower=[1.0,1.0])
        function start_precision_guard(;diagnostics=nothing)
            JSimplex.initialize_workspace(p,SolverOptions(;verbose=false);
                progress=JSimplex.SimplexProgressContext(p;diagnostics))
        end
        ws=start_precision_guard();budget=JSimplex.SimplexRunBudget(ws)
        budget.time_limit_seconds=0.0
        @test isnothing(JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy))
        @test ws.refactorizations==budget.refactorizations==0
        budget.time_limit_seconds=Inf
        @test isnothing(JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy;stop=()->true))
        @test ws.refactorizations==budget.refactorizations==0
        failure=ErrorException("precision callback")
        caught=try
            JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy;stop=()->throw(failure))
        catch e;e end
        @test caught===failure
        ws.basis.basic_indices[2]=ws.basis.basic_indices[1]
        @test_throws ArgumentError JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy)
        @test budget.refactorizations==0
        ws=start_precision_guard();budget=JSimplex.SimplexRunBudget(ws)
        ws.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        @test_throws LinearAlgebra.SingularException JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy)
        @test ws.refactorizations==budget.refactorizations==1
        stopped=Ref(false)
        d=JSimplex.SimplexDiagnostics(;observer=(reason,trial)->begin
            reason==:refactor_other && (stopped[]=true)
        end)
        ws=start_precision_guard(;diagnostics=d);budget=JSimplex.SimplexRunBudget(ws)
        @test isnothing(JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy;stop=()->stopped[]))
        @test stopped[] && ws.refactorizations==budget.refactorizations==1
        @test JSimplex.event_count(d,:refactor_other)==1
        @test ws.basis.basic_indices==[3,4]
        ws=start_precision_guard();budget=JSimplex.SimplexRunBudget(ws)
        @test isnothing(JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy;
            stop=()->budget.refactorizations>0))
        @test budget.refactorizations==1
        callback_failure=SingularException(7)
        d=JSimplex.SimplexDiagnostics(;observer=(reason,trial)->begin
            reason==:refactor_other && throw(callback_failure)
        end)
        ws=start_precision_guard(;diagnostics=d);budget=JSimplex.SimplexRunBudget(ws)
        caught=try
            JSimplex.transfer_precision(ws,BigFloat,128,budget,ws.progress.numerical_policy)
        catch e;e end
        @test caught isa JSimplex.DiagnosticObserverFailure
        @test caught.cause===callback_failure
        @test budget.refactorizations==1 && ws.basis.basic_indices==[3,4]
        q=LinearProblem(sparse(Rational{BigInt}[1;;]),[1//big(1)];row_lower=[1//big(1)])
        exact=JSimplex.initialize_workspace(q,SolverOptions(Rational{BigInt};verbose=false))
        @test_throws ArgumentError JSimplex.transfer_precision(exact,BigFloat,128,JSimplex.SimplexRunBudget(exact),exact.progress.numerical_policy)
    end

    @testset "Rebuilt steepest-edge weights and exact transfers" begin
        for T in (Float64,Rational{Int64},Rational{BigInt})
            p=LinearProblem(sparse(T[2 1;1 3]),T[1,2];row_lower=T[2,0],row_upper=T[2,0])
            policy=JSimplex.NumericalPolicy(T)
            ws=JSimplex.initialize_from_basis(p,
                JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]),
                SolverOptions(T;verbose=false,pricing=:steepest_edge);policy)
            fill!(ws.pricing_weights,T(999))
            S,bits=T===Float64 ? (BigFloat,128) : (T,0)
            fresh=JSimplex.transfer_precision(ws,S,bits,JSimplex.SimplexRunBudget(ws),policy)
            @test eltype(fresh.costs)===S
            @test all(==(T(999)),ws.pricing_weights)
            @test fresh.pricing_weights[1:2]≈S[2//5,1//5]
            @test JSimplex._recomputed_basis_reliable(fresh)
            @test fresh.primal[1:2]≈S[6//5,-2//5]
            @test fresh.options.basis_update==ws.options.basis_update
            if T <: Rational
                @test fresh.primal[1:2]==T[6//5,-2//5]
                @test iszero(fresh.progress.numerical_policy.solve_tolerance)
            end
        end
    end
end

include("simplex_precision_working_bits_tests.jl")
