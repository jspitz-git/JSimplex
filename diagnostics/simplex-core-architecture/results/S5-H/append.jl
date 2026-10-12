
# BEGIN ACTIVE JOURNAL INTERRUPTION COVERAGE
if isdefined(JSimplex,:transfer_precision)
    @testset "Interrupted precision transfer retains owned active journals" begin
        function journal_state_arrays(ws; checkpoint=false)
            j=ws.scratch.perturbations;b=j.bounds;p=ws.problem;g=ws.progress
            a=(costs=ws.costs,
            lower=ws.lower,
            upper=ws.upper,
            original_costs=j.original_costs,
            active_costs=j.active_costs,
            original_lower=b.original_lower,
            original_upper=b.original_upper,
            active_lower=b.active_lower,
            active_upper=b.active_upper,
            primal=ws.primal,
            reduced_costs=ws.reduced_costs,
            weights=ws.pricing_weights,
            basis=ws.basis.basic_indices,
            states=ws.basis.states,
            devex=ws.devex_reference,
            colptr=p.A.colptr,
            rowval=p.A.rowval,
            nzval=p.A.nzval,
            objective=p.objective,
            row_lower=p.row_lower,
            row_upper=p.row_upper,
            column_lower=p.column_lower,
            column_upper=p.column_upper,
            progress_objective=g.objective,
            row_scaling=g.scaling.row_factors,
            column_scaling=g.scaling.column_factors)
            checkpoint || return a
            c=only(ws.scratch.checkpoints)
            return merge(a,(checkpoint_basis=c.basis.basic_indices,checkpoint_states=c.basis.states,
                checkpoint_costs=c.costs,checkpoint_lower=c.lower,checkpoint_upper=c.upper))
        end
        function journal_state_metadata(ws; checkpoint=false)
            j=ws.scratch.perturbations;b=j.bounds;p=ws.problem;g=ws.progress
            cache=ws.scratch.sparse_pricing
            ck=if checkpoint
                c=only(ws.scratch.checkpoints)
                (identity=c,model=c.working_model,phase=c.phase,perturbed=c.perturbed)
            else
                nothing
            end
            return (workspace=ws,scalar_type=eltype(ws.costs),journal=j,bounds=b,
                owner=j.workspace_id,active=j.active,bound_active=b.active,
                original_perturbed=j.original_perturbed,perturbed=ws.perturbed,
                level=j.level,bound_level=b.level,cooldown=j.cooldown_until,bound_cooldown=b.cooldown_until,
                monitor=j.last_monitor,bound_monitor=b.last_monitor,
                observation=j.last_observation,bound_observation=b.last_observation,
                stagnation=ws.scratch.stagnation,factor=ws.factorization,
                updates=length(ws.factorization.updates),model=p.A,
                cache=cache,cache_model=isnothing(cache) ? nothing : cache.rows.matrix,
                checkpoint_count=length(ws.scratch.checkpoints),checkpoint=ck,
                diagnostics=g.diagnostics,start=g.start_ns,
                iteration_offset=g.iteration_offset,refactorization_offset=g.refactorization_offset,
                objective_constant=p.objective_constant,progress_constant=g.objective_constant,
                objective_sense=p.objective_sense,options=ws.options,policy=g.numerical_policy)
        end
        same_fields(a,b)=fieldnames(typeof(a))==fieldnames(typeof(b)) &&
            all(k->isequal(getfield(a,k),getfield(b,k)),fieldnames(typeof(a)))
        stored128(x::BigFloat)=precision(x)==128
        stored128(x::Bound)=!isfinite(x) || stored128(bound_value(x))

        for mode in (:stop,:throw)
            armed=Ref(false);stopped=Ref(false);hits=Ref(0);true_stops=Ref(0)
            retained=Ref{Any}(nothing);failure=SingularException(7)
            d=JSimplex.SimplexDiagnostics(;kernel_timing=true,observer=(reason,trial)->begin
                if armed[] && reason==:refactor_other
                    hits[]+=1
                    retained[]=trial
                    mode==:stop ? (stopped[]=true) : throw(failure)
                end
                nothing
            end)
            stop=()->begin
                stopped[] && (true_stops[]+=1)
                stopped[]
            end
            p=LinearProblem(sparse([1.0 1.0]),[1.0,2.0];row_lower=[1.0])
            policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,sparse_pricing=true)
            ws=JSimplex.initialize_from_basis(p,
                JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]),
                SolverOptions(;verbose=false);policy,
                progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
            journal=JSimplex.PerturbationJournal(ws)
            journal.bounds=JSimplex.BoundPerturbationState(ws)
            journal.active_costs[1]=1.125;journal.active_costs[2]=2.25
            journal.bounds.active_lower[2]=Bound(-0.125)
            journal.bounds.active_lower[3]=Bound(0.75)
            journal.active=true;journal.bounds.active=true
            journal.level=2;journal.bounds.level=1
            journal.cooldown_until=11;journal.bounds.cooldown_until=13
            monitor=JSimplex._new_workspace_stagnation(ws,UInt(0),:dual)
            journal.last_monitor=monitor.monitor;journal.bounds.last_monitor=monitor.monitor
            journal.last_observation=9;journal.bounds.last_observation=8
            ws.scratch.stagnation=monitor
            ws.costs=journal.active_costs;ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
            ws.scratch.perturbations=journal;ws.perturbed=true
            JSimplex.recompute!(ws)
            JSimplex._sparse_pricing_workspace!(ws)
            push!(ws.scratch.checkpoints,JSimplex.checkpoint_basis(ws))

            # Equality of values does not imply shared ownership.
            ws.costs=copy(ws.costs);ws.lower=copy(ws.lower);ws.upper=copy(ws.upper)
            @test ws.costs==journal.active_costs && ws.costs!==journal.active_costs
            @test ws.lower==journal.bounds.active_lower && ws.lower!==journal.bounds.active_lower
            @test ws.upper==journal.bounds.active_upper && ws.upper!==journal.bounds.active_upper
            @test !policy.solve_refinement && !policy.recovery && policy.max_refinements==3
            @test ws.options.pricing==:steepest_edge && ws.options.basis_update==:pfi
            @test journal.workspace_id==objectid(ws)
            @test ws.scratch.sparse_pricing.rows.matrix===ws.problem.A
            source=journal_state_arrays(ws;checkpoint=true)
            saved=map(copy,source) # 31 small arrays/76 entries; Float64/isbits values.
            metadata=journal_state_metadata(ws;checkpoint=true)
            budget=JSimplex.SimplexRunBudget(ws)
            work=(iterations=ws.iterations,refactors=ws.refactorizations,start=budget.start_ns,
                limit=budget.time_limit_seconds,
                kernels=Tuple(get(d.kernel_calls,k,0) for k in JSimplex.SIMPLEX_KERNEL_KEYS),
                events=Tuple(get(d.counts,k,0) for k in JSimplex.SIMPLEX_EVENT_REASONS))
            ambient=(precision(BigFloat),rounding(BigFloat))
            result=nothing;caught=nothing
            armed[]=true
            try
                result=JSimplex.transfer_precision(ws,BigFloat,128,budget,policy;stop)
            catch e
                caught=e
            finally
                armed[]=false
            end
            @test (precision(BigFloat),rounding(BigFloat))==ambient
            @test isnothing(result) && hits[]==1
            if mode==:stop
                @test isnothing(caught) && stopped[] && true_stops[]>0
            else
                @test !stopped[] && true_stops[]==0
                @test caught isa JSimplex.DiagnosticObserverFailure
                if caught isa JSimplex.DiagnosticObserverFailure
                    @test caught.cause===failure
                end
            end
            after=journal_state_arrays(ws;checkpoint=true)
            @test all(k->after[k]===source[k] && isequal(after[k],saved[k]),keys(source))
            @test isequal(journal_state_metadata(ws;checkpoint=true),metadata)
            @test ws.iterations==work.iterations && ws.refactorizations==work.refactors+1
            @test budget.iterations==ws.progress.iteration_offset+ws.iterations
            @test budget.refactorizations==ws.progress.refactorization_offset+ws.refactorizations
            @test budget.start_ns==work.start && budget.time_limit_seconds==work.limit
            # Existing finally counters omit the direct unit BTRAN used by weight rebuilding.
            for (i,k) in enumerate(JSimplex.SIMPLEX_KERNEL_KEYS)
                delta=get(d.kernel_calls,k,0)-work.kernels[i]
                @test k==:btran ? 1<=delta<=4 : delta==(k in (:ftran,:refactorization) ? 1 : 0)
            end
            corrections=get(d.counts,:correction_attempt,0)-work.events[findfirst(==(:correction_attempt),JSimplex.SIMPLEX_EVENT_REASONS)]
            @test corrections==get(d.kernel_calls,:btran,0)-work.kernels[findfirst(==(:btran),JSimplex.SIMPLEX_KERNEL_KEYS)]-1
            for (i,k) in enumerate(JSimplex.SIMPLEX_EVENT_REASONS)
                delta=get(d.counts,k,0)-work.events[i]
                @test k==:correction_attempt ? 0<=delta<=3 : k==:correction ? 0<=delta<=corrections : delta==(k==:refactor_other ? 1 : 0)
            end
            fresh=retained[]
            @test !isnothing(fresh) && fresh!==ws && eltype(fresh.costs)===BigFloat
            if !isnothing(fresh) && fresh!==ws && eltype(fresh.costs)===BigFloat
                j=fresh.scratch.perturbations;b=j.bounds
                a=journal_state_arrays(fresh)
                m=journal_state_metadata(fresh)
                @test j.workspace_id==objectid(fresh) && j.workspace_id!=journal.workspace_id
                @test j!==journal && b!==journal.bounds
                @test fresh.costs===j.active_costs && fresh.lower===b.active_lower && fresh.upper===b.active_upper
                journal_keys=(:original_costs,:active_costs,:original_lower,:original_upper,:active_lower,:active_upper)
                @test all(k->a[k]!==source[k] && isequal(a[k],saved[k]),journal_keys)
                @test j.original_costs!==j.active_costs
                @test all(a[journal_keys[i]]!==a[journal_keys[l]] for i in 3:6 for l in i+1:6)
                @test isnothing(j.last_monitor) && isnothing(b.last_monitor) && isnothing(fresh.scratch.stagnation)
                @test j.last_observation==b.last_observation==0
                @test all(k->getproperty(m,k)==getproperty(metadata,k),
                    (:active,:bound_active,:original_perturbed,:perturbed,:level,:bound_level,:cooldown,:bound_cooldown))
                owned=(:basis,:states,:colptr,:rowval,:nzval,:objective,:row_lower,:row_upper,:column_lower,:column_upper,
                    :progress_objective,:row_scaling,:column_scaling)
                @test all(k->a[k]!==source[k] && isequal(a[k],saved[k]),owned)
                @test fresh.problem.A!==ws.problem.A && fresh.factorization!==ws.factorization
                @test isempty(fresh.factorization.updates)
                @test isequal(m.objective_constant,metadata.objective_constant) && isequal(m.progress_constant,metadata.progress_constant)
                @test m.objective_sense==metadata.objective_sense
                @test same_fields(fresh.options,ws.options) && same_fields(fresh.progress.numerical_policy,policy)
                @test fresh.options.time_limit isa Float64 && isequal(fresh.options.time_limit,ws.options.time_limit)
                @test isempty(fresh.scratch.checkpoints) && isnothing(fresh.scratch.sparse_pricing)
                @test m.diagnostics===metadata.diagnostics && m.start==budget.start_ns
                @test m.iteration_offset==metadata.iteration_offset && m.refactorization_offset==metadata.refactorization_offset
                for k in (:costs,:lower,:upper,:original_costs,:active_costs,:original_lower,:original_upper,
                          :active_lower,:active_upper,:nzval,:objective,:row_lower,:row_upper,:column_lower,:column_upper,
                          :progress_objective,:row_scaling,:column_scaling)
                    @test all(stored128,a[k])
                end
                @test all(stored128,(m.objective_constant,m.progress_constant,fresh.options.primal_tolerance,
                    fresh.options.dual_tolerance,fresh.options.zero_tolerance,
                    fresh.progress.numerical_policy.solve_tolerance,fresh.progress.numerical_policy.pivot_error_tolerance))
            end
            retained[]=nothing
        end
    end
end
