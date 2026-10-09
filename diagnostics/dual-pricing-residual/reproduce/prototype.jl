# Diagnostic only. Ordered basic indices and states must describe the same basis.
@inline function row_ratio(residual,scale,roundoff,tolerance)
    isfinite(residual) && isfinite(scale) || return oftype(residual,Inf)
    threshold=max(tolerance,roundoff*(scale+one(scale)))
    isfinite(threshold) || return oftype(residual,Inf)
    abs(residual)/threshold
end
function combined!(out::Vector{T},ws,rho::Vector{T},leaving::Int) where T
    A=ws.problem.A;m,n=size(A);basics=ws.basis.basic_indices;states=ws.basis.states
    length(rho)==length(basics)==m || throw(DimensionMismatch("residual dimensions"))
    length(out)>=m+n && length(states)==m+n || throw(DimensionMismatch("pricing dimensions"))
    for j in basics;1<=j<=n+m || throw(BoundsError(ws.primal,j));end
    leaving_index=basics[leaving]
    worst=zero(T);roundoff=T(256)*eps(one(T));tolerance=ws.options.zero_tolerance
    @inbounds for j in 1:n
        value=zero(T)
        if states[j]==JSimplex.BASIC
            expected=j==leaving_index ? one(T) : zero(T)
            residual=-expected;scale=expected
            for p in A.colptr[j]:(A.colptr[j+1]-1)
                multiplier=rho[A.rowval[p]];coefficient=A.nzval[p]
                value += multiplier*coefficient
                term=coefficient*multiplier
                residual+=term;scale+=abs(term)
            end
            worst=max(worst,row_ratio(residual,scale,roundoff,tolerance))
        else
            for p in A.colptr[j]:(A.colptr[j+1]-1)
                value+=rho[A.rowval[p]]*A.nzval[p]
            end
        end
        out[j]=value
    end
    @inbounds for i in 1:m
        out[n+i]=-rho[i]
        if states[n+i]==JSimplex.BASIC
            expected=n+i==leaving_index ? one(T) : zero(T)
            residual=-expected;scale=expected
            term=-rho[i]
            residual+=term;scale+=abs(term)
            worst=max(worst,row_ratio(residual,scale,roundoff,tolerance))
        end
    end
    worst
end
