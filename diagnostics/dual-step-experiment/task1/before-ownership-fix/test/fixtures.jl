function fixture(::Type{T}=Float64; update=:pfi, pricing=:devex) where T
    p=J.LinearProblem(sparse(Matrix{T}(I,3,3)),T[1,2,3];row_lower=ones(T,3),column_lower=zeros(T,3),column_upper=fill(T(4),3))
    opts=J.SolverOptions(T;algorithm=:dual,pricing=pricing,basis_update=update,verbose=false)
    progress=J.SimplexProgressContext(p;start_ns=UInt64(123456789),iteration_offset=7,refactorization_offset=11)
    ws=J.initialize_workspace(p,opts;progress)
    ws,J._SolveDeadline(progress.start_ns,Inf)
end
members(s)=sort(collect(@view s.ids[1:s.used]))
function snapshot(ws)
    (costs=copy(ws.costs),lower=copy(ws.lower),upper=copy(ws.upper),primal=copy(ws.primal),prices=copy(ws.reduced_costs),weights=copy(ws.pricing_weights),reference=copy(ws.devex_reference),basic=copy(ws.basis.basic_indices),states=copy(ws.basis.states),work=copy(ws.factorization.work),updates=length(ws.factorization.updates),shared=ws.factorization.shared_update_count,backend_shared=ws.factorization.base.shared)
end
function independent_members(ws)
    primal=Int[];dual=Int[]
    for (r,i) in enumerate(ws.basis.basic_indices)
        lo=ws.lower[i];hi=ws.upper[i];x=ws.primal[i];tol=ws.options.primal_tolerance
        ((isfinite(lo)&&lo.value-x>tol)||(isfinite(hi)&&x-hi.value>tol))&&push!(primal,r)
    end
    for i in eachindex(ws.costs)
        st=ws.basis.states[i];st==J.BASIC&&continue
        lo=ws.lower[i];hi=ws.upper[i]
        isfinite(lo)&&isfinite(hi)&&lo.value==hi.value&&continue
        p=ws.reduced_costs[i];t=ws.options.dual_tolerance
        bad=st==J.AT_LOWER ? p < -t : st==J.AT_UPPER ? p > t : abs(p)>t
        bad&&push!(dual,i)
    end
    primal,dual
end
