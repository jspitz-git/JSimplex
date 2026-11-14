# Only audited native production factors may reuse a fused row residual.
_dual_row_native_factor(f, ::Type) = false
function _dual_row_native_factor(f::Union{PFIFactorization,ForrestTomlinFactorization,
        SuhlSuhlFactorization,BartelsGolubFactorization}, ::Type{T}) where {T}
    T in (Float32,Float64) && eltype(f.work) === T || return false
    return T === Float64 ? f.base isa UMFPACKBackend :
        f.base isa Float32LUBackend && eltype(f.base.factorization.factors) === Float32
end
function _dual_row_native_factor(f::HuangfuHallFactorization{T,F,R}, ::Type{T}) where {T,F,R}
    R === :native && T in (Float32,Float64) && eltype(f.work) === T || return false
    return T === Float64 ? F === Float64UMFPACK : F <: LinearAlgebra.LU{Float32}
end

function _dual_row_context(ws::SimplexWorkspace{T}, stop) where {T}
    ws.options.dual_row_adapter || return nothing
    policy = ws.progress.numerical_policy
    T in (Float32,Float64) && _readonly_dual_stop(stop) &&
        _dual_row_native_factor(ws.factorization,T) &&
        ws.options.simplex_strategy === :legacy && !ws.options.partial_pricing &&
        isnothing(ws.progress.diagnostics) && !policy.hypersparse &&
        !policy.sparse_pricing && !policy.stable_ratio &&
        !Base.mightalias(ws.scratch.tableau_row,ws.scratch.rho) &&
        !Base.mightalias(ws.scratch.rho,ws.problem.A.nzval) &&
        !Base.mightalias(ws.scratch.tableau_row,ws.problem.A.nzval) || return nothing
    context = ws.scratch.dual_row
    if isnothing(context)
        m,n = size(ws.problem.A)
        context = _DualRowContext(T,m,n)
        ws.scratch.dual_row = context
    end
    context.ready = false
    context.support_valid = false
    context.mode = :none
    return context
end

# Exact zeros only. Support and CSC sums keep ascending original column order.
_dual_row_route(rho) = count(!iszero,rho) <= length(rho) ÷ 100 ? :support : :fused

function _dual_row_basis_map!(c,ws,rho,out,leaving)
    A=ws.problem.A;m,n=size(A);b=ws.basis.basic_indices
    length(rho)==length(b)==m || throw(DimensionMismatch("tableau residual vectors must match the row count"))
    length(out)>=m+n || throw(DimensionMismatch("pricing output dimensions"))
    # Bounds behavior belongs to the original row guard, after pricing/finite.
    if !(1<=leaving<=m && length(c.epochs)==m+n)
        return false
    end
    if c.generation==typemax(UInt64);fill!(c.epochs,0);c.generation=0;end
    c.generation+=1
    @inbounds for row in eachindex(b)
        j=b[row]
        if !(1<=j<=m+n) || c.epochs[j]==c.generation
            return false
        end
        c.epochs[j]=c.generation;c.slots[j]=row
    end
    true
end
@inline function _dual_row_scaled_residual(r,s,roundoff,tol)
    isfinite(r)&&isfinite(s) || return oftype(r,Inf)
    threshold=max(tol,roundoff*(s+one(s)))
    isfinite(threshold) || return oftype(r,Inf)
    abs(r)/threshold
end
function _dual_row_fused!(c,ws,out::Vector{T},rho::Vector{T},leaving) where T
    A=ws.problem.A;m,n=size(A);worst=zero(T)
    roundoff=T(256)*eps(one(T));tol=ws.options.zero_tolerance
    @inbounds for j in 1:n
        v=zero(T)
        if c.epochs[j]==c.generation
            expected=c.slots[j]==leaving ? one(T) : zero(T);r=-expected;s=expected
            for p in A.colptr[j]:(A.colptr[j+1]-1)
                x=rho[A.rowval[p]];a=A.nzval[p]
                v+=x*a;term=a*x;r+=term;s+=abs(term)
            end
            worst=max(worst,_dual_row_scaled_residual(r,s,roundoff,tol))
        else
            for p in A.colptr[j]:(A.colptr[j+1]-1);v+=rho[A.rowval[p]]*A.nzval[p];end
        end
        out[j]=v
    end
    @inbounds for i in 1:m
        out[n+i]=-rho[i]
        if c.epochs[n+i]==c.generation
            expected=c.slots[n+i]==leaving ? one(T) : zero(T);r=-expected;s=expected
            term=-rho[i];r+=term;s+=abs(term)
            worst=max(worst,_dual_row_scaled_residual(r,s,roundoff,tol))
        end
    end
    c.ratio=worst;c.ready=true;nothing
end
function _dual_row_support!(c,A,out,rho)
    m,n=size(A);T=eltype(out);empty!(c.support)
    length(rho)>=m && length(out)>=m+n || throw(DimensionMismatch("pricing dimensions"))
    @inbounds for j in 1:n
        v=zero(T)
        for p in A.colptr[j]:(A.colptr[j+1]-1);v+=rho[A.rowval[p]]*A.nzval[p];end
        out[j]=v;iszero(v) || push!(c.support,j)
    end
    @inbounds for i in 1:m
        v=-rho[i];out[n+i]=v;iszero(v) || push!(c.support,n+i)
    end
    c.support_valid=length(c.support)<=((m+n)÷16)
    nothing
end
function _dual_row_price!(c::_DualRowContext,ws,out,rho,leaving)
    c.ready=false;c.support_valid=false
    _pipeline_changed!(ws,out)
    c.mode=_dual_row_route(rho)
    if c.mode==:support
        _dual_row_support!(c,ws.problem.A,out,rho)
    elseif _dual_row_basis_map!(c,ws,rho,out,leaving)
        _dual_row_fused!(c,ws,out,rho,leaving)
    else
        c.mode=:fallback;_csc_price!(out,ws.problem.A,rho)
    end
    nothing
end
_dual_row_price!(::Nothing,ws,out,rho,leaving) = price!(out,ws,rho)

# The cached result belongs to this rho/basis and is consumed exactly once.
function _dual_row_residual!(context::_DualRowContext,ws,rho,leaving)
    if context.ready
        context.ready = false
        return context.ratio
    end
    return _dual_row_residual_ratio(ws,rho,leaving)
end
_dual_row_residual!(::Nothing,ws,rho,leaving) = _dual_row_residual_ratio(ws,rho,leaving)

function _dual_row_ratio!(context::_DualRowContext,ws,row,orientation,violation)
    if !context.support_valid || ws.progress.numerical_policy.stable_ratio
        return _configured_dual_ratio_test(ws,row,orientation,violation)
    end
    result = _bound_flipping_ratio_test_indices(ws,row,orientation,violation,context.support)
    if result[1] == -1 && !isempty(ws.scratch.rejected_entering)
        throw(_PivotRejection(ws.scratch.selected_row,0,:next_row))
    end
    return result
end
_dual_row_ratio!(::Nothing,ws,row,o,v) = _configured_dual_ratio_test(ws,row,o,v)

# Specialize before capturing the optional context and (potentially large) row
# in the timer callback. Otherwise each iteration boxes the row and callback.
function _timed_dual_row_price!(context::C,ws,out,rho,leaving) where {C}
    _timed_simplex(ws,:pricing) do
        _dual_row_price!(context,ws,out,rho,leaving)
    end
end
