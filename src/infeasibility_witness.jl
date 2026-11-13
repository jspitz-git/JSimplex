# Invocation-local authority only: no cached rounding or flush-to-zero state.
_tight_certificate_bounds(::Type) = false
_tight_certificate_bounds(::Type{T}) where {T<:Union{Float32,Float64}} =
    _primal_nearest_rounding(T) && !get_zero_subnormals()
_tight_certificate_bounds(::Type{BigFloat}) = _primal_nearest_rounding(BigFloat)

@inline function _certificate_add_product_bounds(lower,upper,a,b,tight::Bool)
    if tight && isfinite(lower) && isfinite(upper) && isfinite(a) && isfinite(b)
        product_lower,product_upper=_primal_product_bounds(a,b)
        lower,_=_primal_sum_bounds(lower,product_lower)
        _,upper=_primal_sum_bounds(upper,product_upper)
        return lower,upper
    end
    return _add_product_bounds(lower,upper,a,b)
end

_witness_negate(value::T) where {T<:AbstractFloat} = -value
function _witness_negate(value::BigFloat)
    # Sign change is exact at stored precision, including a higher-precision
    # witness reused at lower ambient precision. No arithmetic precision boost.
    result=BigFloat(precision=precision(value))
    ccall((:mpfr_neg,Base.MPFR.libmpfr),Cint,
        (Ref{BigFloat},Ref{BigFloat},Base.MPFR.MPFRRoundingMode),
        result,value,Base.MPFR.MPFRRoundNearest)
    return result
end

function _witness_coefficient_bounds(workspace,rho,below,column,tight)
    T=eltype(rho);lower=upper=zero(T)
    A=workspace.problem.A
    for position in nzrange(A,column)
        value=rho[A.rowval[position]]
        oriented=below ? value : _witness_negate(value)
        lower,upper=_certificate_add_product_bounds(lower,upper,oriented,A.nzval[position],tight)
    end
    return lower,upper
end

_certified_infeasibility_witness(workspace,rho,below) =
    (_floating_infeasibility_certified(workspace,rho,below),rho,0)

"""Try bounded private witness proposals; only the full original predicate accepts.

An invalid sign on an unbounded variable is never rounded to zero. Instead a
private multiplier moves toward zero and is tested against every original
coefficient, bound and feasibility allowance. No basis solve or live-state write.
"""
function _certified_infeasibility_witness(workspace::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:Union{Float32,Float64,BigFloat}}
    _floating_infeasibility_certified(workspace,rho,below) && return (true,rho,0)
    # Preserve the established successful fast path and its allocation costs.
    # Only an inconclusive certificate pays for tighter interval evaluation.
    _tight_certificate_bounds(T) || return (false,rho,0)
    _floating_infeasibility_certified(workspace,rho,below,Val(true)) && return (true,rho,0)
    policy=workspace.progress.numerical_policy
    (_tight_certificate_bounds(T) && workspace.options.simplex_strategy===:legacy &&
     isinf(workspace.options.time_limit) && policy.max_refinements>0) || return (false,rho,0)
    candidate=copy(rho)
    A=workspace.problem.A;n=size(A,2);attempts=0
    while attempts<policy.max_refinements
        bad=0;boundary=zero(T);need_up=false
        for column in 1:n
            lower,upper=_witness_coefficient_bounds(workspace,candidate,below,column,true)
            if !isfinite(workspace.upper[column]) && lower<zero(T)
                bad=column;boundary=lower;need_up=true;break
            elseif !isfinite(workspace.lower[column]) && upper>zero(T)
                bad=column;boundary=upper;break
            end
        end
        bad==0 && break
        changed=false
        for position in nzrange(A,bad)
            row=A.rowval[position]
            coefficient=below ? A.nzval[position] : _witness_negate(A.nzval[position])
            old=candidate[row]
            iszero(old) && continue
            (need_up ? coefficient*old<zero(T) : coefficient*old>zero(T)) || continue
            value=old-boundary/coefficient
            isfinite(value) && (sign(value)==sign(old) || iszero(value)) && abs(value)<=abs(old) || continue
            value==old && (value=old>zero(T) ? prevfloat(old) : nextfloat(old))
            candidate[row]=value;attempts+=1;changed=true;break
        end
        changed || break
        _floating_infeasibility_certified(workspace,candidate,below,Val(true)) && return (true,candidate,attempts)
    end
    return false,rho,attempts
end
