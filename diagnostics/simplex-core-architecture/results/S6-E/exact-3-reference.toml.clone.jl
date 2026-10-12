function _s6_exact_remove_artificials!(phase::SimplexWorkspace{T}, map, original, policy, stop) where T
    #= none:144 =#
    #= none:145 =#
    normalized = false
    #= none:146 =#
    m = length(phase.basis.basic_indices)
    #= none:147 =#
    (rhs, column, unit, rho) = (zeros(T, m), zeros(T, m), zeros(T, m), zeros(T, m))
    #= none:148 =#
    prices = zeros(T, length(phase.basis.states))
    #= none:149 =#
    for row = 1:m
        #= none:150 =#
        leaving = phase.basis.basic_indices[row]
        #= none:151 =#
        map.phase_to_original[leaving] != 0 && continue
        #= none:152 =#
        stop() && return false
        #= none:153 =#
        phase.iterations < phase.options.iteration_limit || return false
        #= none:154 =#
        if !(abs(phase.primal[leaving]) <= phase.options.primal_tolerance)
            #= none:155 =#
            normalized && return false
            #= none:156 =#
            _normalize_phase_artificial_bounds!(phase, map, original, policy, stop) || return false
            #= none:157 =#
            normalized = true
        end
        #= none:159 =#
        abs(phase.primal[leaving]) <= phase.options.primal_tolerance || return false
        #= none:160 =#
        fill!(unit, zero(T))
        #= none:160 =#
        unit[row] = one(T)
        #= none:161 =#
        begin
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:43 =#
            _checked_basis_solve!(rho, phase, unit, stop; transposed = true)
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:44 =#
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:44 =# @assert row == 1 && length(rho) == 6
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:45 =#
            rho .= [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:46 =#
            Bprobe = basis_matrix(phase)
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:47 =#
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:47 =# @assert transpose(Bprobe) * rho == unit
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:48 =#
            qprobe = solve_quality!(SolveQualityScratch(eltype(rho), length(rho)), Bprobe, rho, unit, policy; transposed = true)
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:50 =#
            #= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/reproduce/artificial_row_exact_counterfactual.jl:50 =# @assert qprobe.reliable && iszero(qprobe.absolute_error)
        end
        #= none:165 =#
        if _native_phase_transfer_enabled(phase) && policy.max_refinements > 0
            #= none:166 =#
            B = _basis_matrix!(phase)
            #= none:167 =#
            quality = solve_quality!((_pivot_quality_buffers(phase)).row, B, rho, unit, policy; transposed = true)
            #= none:168 =#
            if !(quality.reliable)
                #= none:169 =#
                _native_cleanup_solve!(rho, phase, B, unit, stop; transposed = true) || return false
            end
        end
        #= none:174 =#
        _csc_price!(prices, phase.problem.A, rho)
        #= none:176 =#
        entering = 0
        #= none:177 =#
        strength = zero(T)
        #= none:178 =#
        for j = map.original_to_phase
            #= none:179 =#
            stop() && return false
            #= none:180 =#
            phase.basis.states[j] == BASIC && continue
            #= none:181 =#
            candidate = abs(prices[j])
            #= none:182 =#
            if candidate > strength
                #= none:183 =#
                _pivot_column!(rhs, phase, j)
                #= none:184 =#
                _checked_basis_solve!(column, phase, rhs, stop)
                #= none:185 =#
                abs(column[row]) > policy.pivot_error_tolerance * maximum(abs, column; init = zero(T)) || continue
                #= none:186 =#
                proposal = PivotCandidate(j, row, prices[j], column, rho)
                #= none:187 =#
                validate_pivot!(phase, proposal, policy) == :accept || continue
                #= none:188 =#
                (entering, strength) = (j, candidate)
            end
            #= none:190 =#
        end
        #= none:191 =#
        entering == 0 && return false
        #= none:192 =#
        _pivot_column!(rhs, phase, entering)
        #= none:193 =#
        _checked_basis_solve!(column, phase, rhs, stop; prepare_update = true)
        #= none:194 =#
        validate_pivot!(phase, PivotCandidate(entering, row, dot(rho, rhs), column, rho), policy) == :accept || return false
        #= none:195 =#
        movement = phase.primal[leaving] / column[row]
        #= none:196 =#
        stop() && return false
        #= none:197 =#
        replace_column!(phase.factorization, column, row; zero_tolerance = zero(T))
        #= none:198 =#
        _finite_updated_factor(phase.factorization) || return false
        #= none:199 =#
        _prepare_primal_candidate!(phase, entering, one(T), movement, column, row, AT_LOWER) || return false
        #= none:200 =#
        phase.basis.basic_indices[row] = entering
        #= none:201 =#
        phase.basis.states[entering] = BASIC
        #= none:201 =#
        phase.basis.states[leaving] = AT_LOWER
        #= none:202 =#
        phase.iterations += 1
        #= none:203 =#
        _phase_inherit_work!(original, phase)
        #= none:204 =#
        _invalidate_basis_checkpoints!(phase)
        #= none:207 =#
        _phase_refactor!(phase, original, stop)
        #= none:208 =#
        _finite_workspace(phase) || return false
        #= none:209 =#
        if !(_recomputed_basis_reliable(phase))
            #= none:212 =#
            _native_phase_transfer_enabled(phase) && (_complete_native_phase_transfer!(phase, stop) && _recomputed_basis_reliable(phase)) || return false
        end
        #= none:216 =#
        _start_primal_feasible(phase) || return false
        #= none:217 =#
        _simplex_event!(phase, :artificial_removed)
        #= none:218 =#
    end
    #= none:219 =#
    stop() && return false
    #= none:220 =#
    states = phase.basis.states[map.original_to_phase]
    #= none:221 =#
    indices = map.phase_to_original[phase.basis.basic_indices]
    #= none:222 =#
    all((>)(0), indices) || return false
    #= none:223 =#
    fresh = initialize_workspace(original.problem, original.options; progress = original.progress)
    #= none:224 =#
    _phase_inherit_work!(fresh, phase)
    #= none:225 =#
    fresh.basis = Basis(indices, states, Val(:owned))
    #= none:226 =#
    native_point = _native_phase_transfer_enabled(fresh)
    #= none:227 =#
    native_point && copyto!(fresh.primal, phase.primal[map.original_to_phase])
    #= none:228 =#
    _phase_refactor!(fresh, original, stop)
    #= none:229 =#
    native_point && (!(_complete_native_phase_transfer!(fresh, stop)) && return false)
    #= none:230 =#
    stop() && return false
    #= none:231 =#
    _finite_workspace(fresh) && (_recomputed_basis_reliable(fresh) && _start_primal_feasible(fresh)) || return false
    #= none:232 =#
    _original_primal_feasible(fresh, fresh.primal[1:size(fresh.problem.A, 2)]) || return false
    #= none:233 =#
    reset_devex!(fresh)
    #= none:236 =#
    _inherit_primal_phase_pricing!(fresh, phase)
    #= none:237 =#
    _adopt_phase_basis!(original, fresh)
    #= none:238 =#
    _reset_auto_pricing!(original)
    #= none:239 =#
    return true
end
function s6_exact_remove_artificials!(phase, map, original, policy, stop)::Bool
    #= none:247 =#
    #= none:248 =#
    guard = _guard_stop_callback(stop)
    #= none:249 =#
    try
        #= none:250 =#
        return _with_recovery_precision(phase, phase) do
                #= none:251 =#
                _s6_exact_remove_artificials!(phase, map, original, policy, guard)
            end
    catch exception
        #= none:254 =#
        exception === guard.exception && rethrow()
        #= none:255 =#
        _crash_numerical_exception(exception) || rethrow()
        #= none:256 =#
        return false
    finally
        #= none:258 =#
        _phase_inherit_work!(original, phase)
    end
end