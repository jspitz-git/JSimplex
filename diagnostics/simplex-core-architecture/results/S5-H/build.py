from pathlib import Path
import re
r=Path.cwd();h=r/'diagnostics/simplex-core-architecture/results/S5-H';f=(h.parent/'S5-F/driver-reviewed.jl').read_text();original=(r/'test/simplex_precision_state_tests.jl').read_text()
fixture=f.split('    # BEGIN EXISTING FIXTURE (only progress injection differs)\n',1)[1].split('    # END EXISTING FIXTURE',1)[0].replace('JS.','JSimplex.')
# Reuse the qualified field list; use references and one source copy, no encodings.
section=f.split('for (key,a) in (',1)[1].split('        arrays[key]',1)[0]
fields=re.findall(r'\(:(\w+),([^\)]+)\)',section)
assert len(fields)==26
arrays=',\n            '.join(k+'='+v for k,v in fields)
meta=f.split('    metadata=(',1)[1].split('    @assert length(arrays)',1)[0].strip()
# Replace tokenization with the actual references/typed scalars; no semantic serialization.
meta=re.sub(r'identity_token\(([^()]*)\)',r'identity(\1)',meta)
meta=meta.replace('string(eltype(ws.costs))','eltype(ws.costs)').replace('string(j.workspace_id)','j.workspace_id').replace('string(g.start_ns)','g.start_ns').replace('scalar(p.objective_constant)','p.objective_constant').replace('scalar(g.objective_constant)','g.objective_constant').replace('string(p.objective_sense)','p.objective_sense').replace('fields(ws.options)','ws.options').replace('fields(g.numerical_policy)','g.numerical_policy').replace('"nothing"','nothing')
# metadata text already ends with closing parenthesis.
suffix='''
# BEGIN ACTIVE JOURNAL INTERRUPTION COVERAGE
if isdefined(JSimplex,:transfer_precision)
    @testset "Interrupted precision transfer retains owned active journals" begin
        function journal_state_arrays(ws; checkpoint=false)
            j=ws.scratch.perturbations;b=j.bounds;p=ws.problem;g=ws.progress
            a=('''+arrays+''')
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
            return ('''+meta+'''
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
'''+''.join('        '+line+'\n' for line in fixture.splitlines())+'''
            # Equality of values does not imply shared ownership.
            ws.costs=copy(ws.costs);ws.lower=copy(ws.lower);ws.upper=copy(ws.upper)
            @test ws.costs==journal.active_costs && ws.costs!==journal.active_costs
            @test ws.lower==journal.bounds.active_lower && ws.lower!==journal.bounds.active_lower
            @test ws.upper==journal.bounds.active_upper && ws.upper!==journal.bounds.active_upper
            @test !policy.solve_refinement && !policy.recovery && policy.max_refinements==3
            @test ws.options.pricing==:steepest_edge && ws.options.basis_update==:pfi
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
                @test isnothing(caught) && stopped[] && true_stops[]==1
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
'''
with (h/'candidate.jl').open('x') as o:o.write(original+suffix)
with (h/'append.jl').open('x') as o:o.write(suffix)
print('prefix bytes',len(original.encode()),'append lines',len(suffix.splitlines()))
