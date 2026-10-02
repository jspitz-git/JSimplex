function _remove_artificials!(phase::SimplexWorkspace{T},map,original,policy,stop) where T
    m = length(phase.basis.basic_indices)
    rhs,column,unit,rho = zeros(T,m),zeros(T,m),zeros(T,m),zeros(T,m)
    prices = zeros(T,length(phase.basis.states))
    for row in 1:m
        leaving = phase.basis.basic_indices[row]
        map.phase_to_original[leaving] != 0 && continue
        stop() && return false
        phase.iterations < phase.options.iteration_limit || return false
        abs(phase.primal[leaving]) <= phase.options.primal_tolerance || return false
        fill!(unit,zero(T));unit[row]=one(T)
        _checked_basis_solve!(rho,phase,unit,stop;transposed=true)
        # One independent sparse column scan avoids an m-vector dot product
        # for every possible original entering column.
        _csc_price!(prices,phase.problem.A,rho)
        # Original fixed and free columns are eligible for a zero-step exchange.
        entering = 0
        strength = zero(T)
        for j in map.original_to_phase
            stop() && return false
            phase.basis.states[j] == BASIC && continue
            candidate = abs(prices[j])
            if candidate > strength
                _pivot_column!(rhs,phase,j)
                _checked_basis_solve!(column,phase,rhs,stop)
                abs(column[row]) > policy.pivot_error_tolerance*maximum(abs,column;init=zero(T)) || continue
                proposal = PivotCandidate(j,row,prices[j],column,rho)
                validate_pivot!(phase,proposal,policy) == :accept || continue
                entering,strength = j,candidate
            end
        end
        entering == 0 && return false
        _pivot_column!(rhs,phase,entering)
        _checked_basis_solve!(column,phase,rhs,stop;prepare_update=true)
        validate_pivot!(phase,PivotCandidate(entering,row,dot(rho,rhs),column,rho),policy) == :accept || return false
        movement = phase.primal[leaving]/column[row]
        stop() && return false
        replace_column!(phase.factorization,column,row;zero_tolerance=zero(T))
        _finite_updated_factor(phase.factorization) || return false
        _prepare_primal_candidate!(phase,entering,one(T),movement,column,row,AT_LOWER) || return false
        phase.basis.basic_indices[row]=entering
        phase.basis.states[entering]=BASIC;phase.basis.states[leaving]=AT_LOWER
        phase.iterations += 1
        _phase_inherit_work!(original,phase)
        _invalidate_basis_checkpoints!(phase)
        # A tiny artificial is not exactly zero. Recompute the actual exchange
        # and require feasible original bounds before declaring it removable.
        _phase_refactor!(phase,original,stop)
        _finite_workspace(phase) || return false
        if !_recomputed_basis_reliable(phase)
            # Repair the same native reconstruction failure as at final export.
            # Already reliable exchanges retain their existing acceptance path.
            _native_phase_transfer_enabled(phase) &&
                _complete_native_phase_transfer!(phase,stop) &&
                _recomputed_basis_reliable(phase) || return false
        end
        _start_primal_feasible(phase) || return false
        _simplex_event!(phase,:artificial_removed)
    end
    stop() && return false
    states = phase.basis.states[map.original_to_phase]
    indices = map.phase_to_original[phase.basis.basic_indices]
    all(>(0),indices) || return false
    fresh = initialize_workspace(original.problem,original.options;progress=original.progress)
    _phase_inherit_work!(fresh,phase)
    fresh.basis=Basis(indices,states,Val(:owned))
    native_point = _native_phase_transfer_enabled(fresh)
    native_point && copyto!(fresh.primal,phase.primal[map.original_to_phase])
    _phase_refactor!(fresh,original,stop)
    native_point && !_complete_native_phase_transfer!(fresh,stop) && return false
    stop() && return false
    _finite_workspace(fresh) && _recomputed_basis_reliable(fresh) && _start_primal_feasible(fresh) || return false
    _original_primal_feasible(fresh,fresh.primal[1:size(fresh.problem.A,2)]) || return false
    reset_devex!(fresh)
    # Artificial removal changes column indexing. Keep only the safe rule;
    # weights and progress history belong to the newly initialized workspace.
    _inherit_primal_phase_pricing!(fresh,phase)
    _adopt_phase_basis!(original,fresh)
    _reset_auto_pricing!(original)
    return true
end
