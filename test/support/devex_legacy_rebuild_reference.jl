module LegacyRecoveryWeights
using LinearAlgebra, JSimplex
const J=JSimplex
function _rebuild_recovery_weights!(trial::J.SimplexWorkspace{T},stop) where T
    # Primal weights remain invalid and are computed on demand. Dual steepest
    # edge weights belong to basic rows and must match the rebuilt inverse.
    J._weight_pricing(trial,:dual) == :steepest_edge || return true
    m = length(trial.basis.basic_indices)
    rhs,direction = zeros(T,m),zeros(T,m)
    policy = trial.progress.numerical_policy
    for row in 1:m
        stop() && return false
        fill!(rhs,zero(T))
        rhs[row] = one(T)
        J.transpose_solve!(direction,trial.factorization,rhs)
        J.refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable || return false
        weight = dot(direction,direction)
        isfinite(weight) && weight > zero(T) || return false
        trial.pricing_weights[trial.basis.basic_indices[row]] = max(J._typed_ratio(T,1,10^4),weight)
    end
    return true
end

end
