# Diagnostic only: validated basis states agree with the ordered basic indices.
function combined!(out::Vector{T},ws,rho::Vector{T},leaving::Int) where T
    A=ws.problem.A;m,n=size(A);basics=ws.basis.basic_indices;states=ws.basis.states
    length(rho)==length(basics)==m || throw(DimensionMismatch("residual dimensions"))
    length(out)>=m+n && length(states)==m+n || throw(DimensionMismatch("pricing dimensions"))
    @inbounds for j in 1:n
        states[j]==JSimplex.BASIC && continue
        value=zero(T)
        for p in A.colptr[j]:(A.colptr[j+1]-1)
            value += rho[A.rowval[p]]*A.nzval[p]
        end
        out[j]=value
    end
    @inbounds for i in 1:m;out[n+i]=-rho[i];end
    worst=zero(T);roundoff=T(256)*eps(one(T))
    for (i,j) in enumerate(basics)
        1<=j<=n+m || throw(BoundsError(ws.primal,j))
        expected=i==leaving ? one(T) : zero(T)
        residual=-expected;scale=expected
        if j<=n
            value=zero(T)
            @inbounds for p in A.colptr[j]:(A.colptr[j+1]-1)
                multiplier=rho[A.rowval[p]];coefficient=A.nzval[p]
                value += multiplier*coefficient
                term=coefficient*multiplier
                residual += term
                scale += abs(term)
            end
            out[j]=value
        else
            term=@inbounds -rho[j-n]
            residual+=term;scale+=abs(term)
        end
        tolerance=max(ws.options.zero_tolerance,roundoff*(scale+one(T)))
        if isfinite(residual) && isfinite(scale) && isfinite(tolerance)
            worst=max(worst,abs(residual)/tolerance)
        else
            worst=T(Inf)
        end
    end
    worst
end
