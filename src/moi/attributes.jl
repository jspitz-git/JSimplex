const _RAW_OPTIMIZER_ATTRIBUTES = (
    "relax_integrality",
    "iteration_limit",
    "primal_tolerance",
    "dual_tolerance",
    "zero_tolerance",
    "refactorization_interval",
    "verbose",
    "algorithm",
    "pricing",
    "basis_update",
    "basis_refactorization",
    "scaling",
    "presolve",
)

function _solver_options(optimizer::Optimizer{T})::SolverOptions{T} where {T}
    return SolverOptions(
        T;
        primal_tolerance=optimizer.primal_tolerance,
        dual_tolerance=optimizer.dual_tolerance,
        zero_tolerance=optimizer.zero_tolerance,
        iteration_limit=optimizer.iteration_limit,
        time_limit=optimizer.time_limit,
        refactorization_interval=optimizer.refactorization_interval,
        verbose=optimizer.verbose && !optimizer.silent,
        log_level=optimizer.silent ? Logging.BelowMinLevel : Logging.Debug,
        algorithm=optimizer.algorithm,
        pricing=optimizer.pricing,
        basis_update=optimizer.basis_update,
        basis_refactorization=optimizer.basis_refactorization,
        scaling=optimizer.scaling,
        presolve=optimizer.presolve,
    )
end

function _set_solver_options!(
    optimizer::Optimizer{T};
    primal_tolerance=optimizer.primal_tolerance,
    dual_tolerance=optimizer.dual_tolerance,
    zero_tolerance=optimizer.zero_tolerance,
    iteration_limit=optimizer.iteration_limit,
    time_limit=optimizer.time_limit,
    refactorization_interval=optimizer.refactorization_interval,
    verbose=optimizer.verbose,
    algorithm=optimizer.algorithm,
    pricing=optimizer.pricing,
    basis_update=optimizer.basis_update,
    basis_refactorization=optimizer.basis_refactorization,
    scaling=optimizer.scaling,
    presolve=optimizer.presolve,
) where {T}
    options = SolverOptions(
        T;
        primal_tolerance,
        dual_tolerance,
        zero_tolerance,
        iteration_limit,
        time_limit,
        refactorization_interval,
        verbose,
        log_level=optimizer.silent ? Logging.BelowMinLevel : Logging.Debug,
        algorithm,
        pricing,
        basis_update,
        basis_refactorization,
        scaling,
        presolve,
    )
    optimizer.primal_tolerance = options.primal_tolerance
    optimizer.dual_tolerance = options.dual_tolerance
    optimizer.zero_tolerance = options.zero_tolerance
    optimizer.iteration_limit = options.iteration_limit
    optimizer.time_limit = options.time_limit
    optimizer.refactorization_interval = options.refactorization_interval
    optimizer.verbose = options.verbose
    optimizer.algorithm = options.algorithm
    optimizer.pricing = options.pricing
    optimizer.basis_update = options.basis_update
    optimizer.basis_refactorization = options.basis_refactorization
    optimizer.scaling = options.scaling
    optimizer.presolve = options.presolve
    _clear_result!(optimizer)
    return
end

MOI.get(::Optimizer, ::MOI.SolverName) = "JSimplex"
MOI.get(::Optimizer, ::MOI.SolverVersion) = string(pkgversion(JSimplex))
MOI.supports(::Optimizer, ::MOI.Silent) = true
MOI.supports(::Optimizer, ::MOI.TimeLimitSec) = true
MOI.supports(::Optimizer, ::MOI.ObjectiveSense) = true

function MOI.set(optimizer::Optimizer, ::MOI.Silent, value::Bool)
    optimizer.silent = value
    _clear_result!(optimizer)
    return
end

MOI.get(optimizer::Optimizer, ::MOI.Silent) = optimizer.silent
MOI.get(optimizer::Optimizer, ::MOI.TimeLimitSec) =
    isinf(optimizer.time_limit) ? nothing : optimizer.time_limit

function MOI.set(
    optimizer::Optimizer,
    ::MOI.TimeLimitSec,
    value::Union{Nothing,Real},
)
    return _set_solver_options!(optimizer; time_limit=something(value, Inf))
end

MOI.supports(::Optimizer, attr::MOI.RawOptimizerAttribute) =
    attr.name in _RAW_OPTIMIZER_ATTRIBUTES

function _unsupported_optimizer_attribute(attr::MOI.RawOptimizerAttribute)
    throw(MOI.UnsupportedAttribute(
        attr,
        "Supported JSimplex optimizer attributes are: " *
        join(_RAW_OPTIMIZER_ATTRIBUTES, ", "),
    ))
end

function MOI.get(optimizer::Optimizer, attr::MOI.RawOptimizerAttribute)
    if attr.name == "relax_integrality"
        return optimizer.relax_integrality
    elseif attr.name == "iteration_limit"
        return optimizer.iteration_limit
    elseif attr.name == "primal_tolerance"
        return optimizer.primal_tolerance
    elseif attr.name == "dual_tolerance"
        return optimizer.dual_tolerance
    elseif attr.name == "zero_tolerance"
        return optimizer.zero_tolerance
    elseif attr.name == "refactorization_interval"
        return optimizer.refactorization_interval
    elseif attr.name == "verbose"
        return optimizer.verbose
    elseif attr.name == "algorithm"
        return optimizer.algorithm
    elseif attr.name == "pricing"
        return optimizer.pricing
    elseif attr.name == "basis_update"
        return optimizer.basis_update
    elseif attr.name == "basis_refactorization"
        return optimizer.basis_refactorization
    elseif attr.name == "scaling"
        return optimizer.scaling
    elseif attr.name == "presolve"
        return optimizer.presolve
    end
    return _unsupported_optimizer_attribute(attr)
end

function MOI.set(
    optimizer::Optimizer,
    attr::MOI.RawOptimizerAttribute,
    value,
)
    if attr.name == "relax_integrality"
        value isa Bool || throw(ArgumentError("relax_integrality must be a Bool"))
        optimizer.relax_integrality = value
        _clear_result!(optimizer)
        return
    elseif attr.name == "iteration_limit"
        return _set_solver_options!(optimizer; iteration_limit=value)
    elseif attr.name == "primal_tolerance"
        return _set_solver_options!(optimizer; primal_tolerance=value)
    elseif attr.name == "dual_tolerance"
        return _set_solver_options!(optimizer; dual_tolerance=value)
    elseif attr.name == "zero_tolerance"
        return _set_solver_options!(optimizer; zero_tolerance=value)
    elseif attr.name == "refactorization_interval"
        return _set_solver_options!(optimizer; refactorization_interval=value)
    elseif attr.name == "verbose"
        value isa Bool || throw(ArgumentError("verbose must be a Bool"))
        return _set_solver_options!(optimizer; verbose=value)
    elseif attr.name == "algorithm"
        value isa Symbol || throw(ArgumentError("algorithm must be a Symbol"))
        return _set_solver_options!(optimizer; algorithm=value)
    elseif attr.name == "pricing"
        value isa Symbol || throw(ArgumentError("pricing must be a Symbol"))
        return _set_solver_options!(optimizer; pricing=value)
    elseif attr.name == "basis_update"
        value isa Symbol || throw(ArgumentError("basis_update must be a Symbol"))
        return _set_solver_options!(optimizer; basis_update=value)
    elseif attr.name == "basis_refactorization"
        value isa Symbol || throw(ArgumentError("basis_refactorization must be a Symbol"))
        return _set_solver_options!(optimizer; basis_refactorization=value)
    elseif attr.name == "scaling"
        value isa Symbol || throw(ArgumentError("scaling must be a Symbol"))
        return _set_solver_options!(optimizer; scaling=value)
    elseif attr.name == "presolve"
        value isa Bool || throw(ArgumentError("presolve must be a Bool"))
        return _set_solver_options!(optimizer; presolve=value)
    end
    return _unsupported_optimizer_attribute(attr)
end
