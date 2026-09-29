using JSimplex, LinearAlgebra, SparseArrays, Serialization, Logging, TOML
const J = JSimplex

function restore_capture(path)
    saved=deserialize(path)
    progress=J.SimplexProgressContext(saved.problem; numerical_policy=saved.numerical_policy,
        iteration_offset=saved.iteration_offset,scaling=saved.scaling)
    ws=J._initialize_workspace_state(saved.problem,saved.options;progress)
    ws.basis=deepcopy(saved.basis)
    ws.factorization=saved.factorization
    ws.scratch=saved.scratch
    ws.costs.=saved.costs; ws.lower.=saved.lower; ws.upper.=saved.upper
    ws.primal.=saved.primal; ws.reduced_costs.=saved.prices
    ws.pricing_weights.=saved.pricing_weights; ws.devex_reference.=saved.devex_reference
    ws.iterations=saved.iteration; ws.refactorizations=saved.refactorizations
    ws.perturbed=saved.perturbed
    ws.zero_dual_step_streak=saved.zero_dual_step_streak
    ws.dual_pricing_fallback=saved.dual_pricing_fallback
    ws.dual_devex_fallback=saved.dual_devex_fallback
    ws.dual_refactorization_interval=saved.dual_refactorization_interval
    J._validate_basis(ws)
    return ws,saved
end

function inspect_capture(path)
    ws,saved=restore_capture(path)
    stop=J._guard_stop_callback(()->false)
    p=ws.progress.numerical_policy
    function report(label)
        println(label," iter=",ws.iterations," pinf=",J.primal_infeasibility_summary(ws),
            " dinf=",J.dual_infeasibility_summary(ws)," original_costs=",J._original_costs_active(ws),
            " original_bounds=",J._original_bounds_active(ws))
        flush(stdout)
    end
    report("STORED")
    for fresh in (false,true)
        J.recompute!(ws;refactorize=fresh,caller_guard=stop)
        verified=J._finite_workspace(ws) && J._recomputed_basis_reliable(ws)
        report("RECOMPUTED fresh=$fresh verified=$verified")
        B=J.basis_matrix(ws)
        rhs=zeros(size(B,1))
        n=size(ws.problem.A,2)
        for j in eachindex(ws.basis.states)
            ws.basis.states[j] == J.BASIC && continue
            value=J._nonbasic_value(ws,j)
            if j <= n
                for k in nzrange(ws.problem.A,j)
                    rhs[ws.problem.A.rowval[k]] -= ws.problem.A.nzval[k]*value
                end
            else
                rhs[j-n] += value
            end
        end
        for transposed in (false,true)
            x=copy(transposed ? ws.scratch.rho : ws.primal[ws.basis.basic_indices])
            b=transposed ? ws.costs[ws.basis.basic_indices] : rhs
            scratch=J.SolveQualityScratch(Float64,length(b))
            for correction in 0:3
                q=J.solve_quality!(scratch,B,x,b,p;transposed)
                native=J._compensated_solve_quality!(scratch,B,x,b,p,transposed)
                println("QUALITY fresh=",fresh," transposed=",transposed," correction=",correction,
                    " ordinary=",q," compensated=",native)
                flush(stdout)
                isnothing(native) && break
                if correction == 1
                    for scaling in (:solution,:correction)
                        cleaned=copy(x)
                        cutoff=p.solve_tolerance*norm(scaling == :solution ? x : step,Inf)
                        changed=J._clean_homogeneous_terms!(cleaned,B,b,transposed,
                            zeros(Int,length(b)),p;cutoff)
                        cq=J._compensated_solve_quality!(scratch,B,cleaned,b,p,transposed)
                        println("CLEANED scaling=",scaling," changed=",changed," quality=",cq,
                            " delta=",norm(cleaned-x,Inf)," count=",count(!iszero,cleaned-x))
                        flush(stdout)
                    end
                    # Restore the residual used by the next ordinary correction.
                    J._compensated_solve_quality!(scratch,B,x,b,p,transposed)
                end
                correction == 3 && break
                step=transposed ? J.transpose_solve(ws.factorization,scratch.residual) :
                                  J.forward_solve(ws.factorization,scratch.residual)
                x .+= step
            end
        end
        primal=ws.primal[1:n]
        println("ORIGINAL primal_feasible=",J._original_primal_feasible(ws,primal),
            " optimality=",J._original_optimality_certified(ws,primal))
        flush(stdout)
    end
end
if abspath(PROGRAM_FILE) == (@__FILE__)
    with_logger(NullLogger()) do
        inspect_capture(only(ARGS))
    end
end
