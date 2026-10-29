# Exact production consumer with qualified names; subset adds only row selection and unit producer/solver hook.
function original_weights!(trial::JSimplex.SimplexWorkspace{T},stop) where T
    # Primal weights remain invalid and are computed on demand. Dual steepest
    # edge weights belong to basic rows and must match the rebuilt inverse.
    JSimplex._weight_pricing(trial,:dual) == :steepest_edge || return true
    m = length(trial.basis.basic_indices)
    rhs,direction = zeros(T,m),zeros(T,m)
    policy = trial.progress.numerical_policy
    for row in 1:m
        stop() && return false
        fill!(rhs,zero(T))
        rhs[row] = one(T)
        JSimplex.transpose_solve!(direction,trial.factorization,rhs)
        JSimplex.refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable || return false
        weight = dot(direction,direction)
        isfinite(weight) && weight > zero(T) || return false
        trial.pricing_weights[trial.basis.basic_indices[row]] = max(JSimplex._typed_ratio(T,1,10^4),weight)
    end
    return true
end


function weights!(trial::JSimplex.SimplexWorkspace{T},rows,stop,mode::Val) where T
    # Primal weights remain invalid and are computed on demand. Dual steepest
    # edge weights belong to basic rows and must match the rebuilt inverse.
    JSimplex._weight_pricing(trial,:dual) == :steepest_edge || return true
    m = length(trial.basis.basic_indices)
    rhs,direction = zeros(T,m),zeros(T,m)
    policy = trial.progress.numerical_policy
    for row in rows
        stop() && return false
        unit_btran!(direction,trial.factorization.ctx,rhs,row,mode)
        JSimplex.refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable || return false
        weight = dot(direction,direction)
        isfinite(weight) && weight > zero(T) || return false
        trial.pricing_weights[trial.basis.basic_indices[row]] = max(JSimplex._typed_ratio(T,1,10^4),weight)
    end
    return true
end

