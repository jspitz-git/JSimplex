function proposal_case(A::AbstractMatrix,c,target;lower=zeros(size(A,2)),upper=fill(Inf,size(A,2)),states=nothing,weights=nothing,time_limit=Inf)
    A=sparse(Float64.(A));c=Float64.(c);target=Float64.(target)
    p=J.LinearProblem(A,c;row_lower=target,row_upper=target,column_lower=Float64.(lower),column_upper=Float64.(upper))
    ws=J.initialize_workspace(p,J.SolverOptions(Float64;pricing=:devex,verbose=false,time_limit=time_limit))
    if !isnothing(states)
        for i in eachindex(states)
            ws.basis.states[i]=states[i]
            ws.primal[i]=states[i]==J.AT_UPPER ? upper[i] : states[i]==J.FREE_NONBASIC ? 0. : lower[i]
        end
    end
    J.recompute!(ws)
    !isnothing(weights) && (ws.pricing_weights.=weights)
    clock=J._SolveDeadline(ws.progress.start_ns,time_limit)
    e=E.import_phase(ws,clock,E.EnginePolicy(ws))
    (e=e,source=ws,A=A)
end
function proposal_snapshot(e)
    w=e.ws
    (primal=copy(w.primal),price=copy(w.reduced_costs),cost=copy(w.costs),weight=copy(w.pricing_weights),reference=copy(w.devex_reference),basis=copy(w.basis.basic_indices),states=copy(w.basis.states),lower=copy(w.lower),upper=copy(w.upper),generation=e.generation,primal_bad=members(e.invariants.primal_bad),dual_bad=members(e.invariants.dual_bad),factor_id=objectid(w.factorization),base_id=objectid(w.factorization.base),native_id=objectid(w.factorization.base.factorization),updates=copy(w.factorization.updates),iterations=w.iterations,refactors=w.refactorizations)
end
function simulated_proposal(e)
    p=e.proposal;w=e.ws
    x=copy(w.primal);prices=copy(w.reduced_costs);cost=copy(w.costs);weights=copy(w.pricing_weights);states=copy(w.basis.states);basis=copy(w.basis.basic_indices)
    for k in 1:p.used
        i=p.ids[k];mask=p.masks[i]
        mask&0x01!=0 && (x[i]=p.values[1][i])
        mask&0x02!=0 && (prices[i]=p.values[2][i])
        mask&0x04!=0 && (cost[i]=p.values[3][i])
        mask&0x08!=0 && (weights[i]=p.values[4][i])
        mask&0x10!=0 && (states[i]=p.states[i])
    end
    basis[p.leaving_row]=p.entering
    (x=x,prices=prices,cost=cost,weights=weights,states=states,basis=basis)
end
function full_simulated_oracle(e)
    s=simulated_proposal(e);w=e.ws;A=w.problem.A;m,n=size(A)
    residual=A*s.x[1:n]-s.x[n+1:end]
    all(isfinite,s.x)&&all(isfinite,s.prices)&&all(isfinite,s.cost)&&all(x->isfinite(x)&&x>0,s.weights) || return false
    maximum(abs,residual)<=1e-10 || return false
    for i in eachindex(s.x)
        state=s.states[i]
        if state!=J.BASIC
            J._is_fixed(w.lower[i],w.upper[i]) || J._dual_price_feasible(state,s.prices[i],w.options.dual_tolerance) || return false
            state==J.AT_LOWER && s.x[i]!=w.lower[i].value && return false
            state==J.AT_UPPER && s.x[i]!=w.upper[i].value && return false
        else
            abs(s.prices[i])<=w.options.dual_tolerance || return false
        end
    end
    # Full-N independent dual-cost relation. The old multiplier is independently
    # reconstructed (closed-form slack basis, or exact solve for at most4rows).
    old_basic=w.basis.basic_indices
    if old_basic==collect(n+1:n+m)
        old_y=-Rational{BigInt}.(w.costs[old_basic])
    else
        m<=4 || error("exact nontrivial-basis oracle is deliberately tiny")
        B=hcat(Matrix(A),-Matrix{Float64}(I,m,m))[:,old_basic]
        old_y=transpose(Rational{BigInt}.(B))\Rational{BigInt}.(w.costs[old_basic])
    end
    y=old_y+Rational{BigInt}(e.proposal.dual_step).*Rational{BigInt}.(e.supports[1].values)
    exact_prices=vcat(Rational{BigInt}.(s.cost[1:n])-transpose(Rational{BigInt}.(A))*y,Rational{BigInt}.(s.cost[n+1:end])+y)
    all(i->abs(exact_prices[i]-Rational{BigInt}(s.prices[i]))<=Rational{BigInt}(w.options.dual_tolerance),eachindex(s.prices)) || return false
    # Independent exact small-case primal equations, not the planner's support.
    exact=Rational{BigInt}.(Matrix(A))*Rational{BigInt}.(s.x[1:n])-Rational{BigInt}.(s.x[n+1:end])
    maximum(abs,exact)<=1//10^10
end

function general_proposal_case(B,C,c,target;upper=fill(Inf,size(C,2)))
    m=size(B,1);A=sparse(hcat(B,C));n=size(A,2)
    p=J.LinearProblem(A,Float64.(c);row_lower=Float64.(target),row_upper=Float64.(target),column_lower=zeros(n),column_upper=vcat(fill(Inf,m),Float64.(upper)))
    ws=J.initialize_workspace(p,J.SolverOptions(Float64;pricing=:devex,verbose=false))
    ws.basis.basic_indices.=1:m;fill!(ws.basis.states,J.AT_LOWER);ws.basis.states[1:m].=J.BASIC
    ws.primal[n+1:end].=target
    J.recompute!(ws;refactorize=true)
    clock=J._SolveDeadline(ws.progress.start_ns,Inf)
    (e=E.import_phase(ws,clock,E.EnginePolicy(ws)),source=ws,A=A)
end
# Two explicit cold native probes validate the live factor against the owned
# committed original B, instead of keeping an alias as a value snapshot.
function factor_matches_committed_basis(e)
    w=e.ws;B=J._assemble_basis_matrix(w,nothing);m=size(B,1)
    expected=[(-1.)^i/8 for i in 1:m];out=zeros(m)
    rhs=B*expected;J.forward_solve!(out,w.factorization,rhs)
    norm(B*out-rhs,Inf)<=1e-12 && norm(out-expected,Inf)<=1e-12 || return false
    rhs=transpose(B)*expected;J.transpose_solve!(out,w.factorization,rhs)
    norm(transpose(B)*out-rhs,Inf)<=1e-12 && norm(out-expected,Inf)<=1e-12
end
