function _can_reuse_dual_checks(ws, stop)
    return _dual_check_factor_supported(ws.factorization) && _readonly_dual_stop(stop) &&
        isnothing(ws.progress.diagnostics) && ws.options.simplex_strategy == :legacy &&
        ws.options.algorithm == :dual && ws.options.pricing == :devex &&
        ws.options.basis_refactorization == :native && !ws.options.partial_pricing &&
        !ws.options.presolve && ws.options.native_pivot_policy == :default &&
        ws.progress.numerical_policy === _LEGACY_DUAL_CHECK_POLICY &&
        isnothing(ws.scratch.hypersparse) && isnothing(ws.scratch.pricing) &&
        !ws.scratch.refactorization.timing_enabled && _weight_pricing(ws,:dual) == :devex
end
