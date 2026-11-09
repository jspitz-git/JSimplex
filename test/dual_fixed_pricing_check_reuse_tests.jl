module DualFixedPricingCheckReuseTests
using JSimplex, SparseArrays, Test
const JS=JSimplex
deadline()=JS._guard_stop_callback(JS._SolveDeadline(time_ns(),Inf))
function workspace(manager, pricing; observer=nothing, kwargs...)
    lp=LinearProblem(sparse([1.0 0.0;0.0 1.0]),[1.0,10.0];row_lower=[1.0,-Inf])
    options=SolverOptions(;algorithm=:dual,pricing=pricing,basis_update=manager,
        simplex_strategy=:legacy,presolve=false,scaling=:off,verbose=false,kwargs...)
    diagnostics=isnothing(observer) ? nothing : JS.SimplexDiagnostics(;observer)
    JS.initialize_workspace(lp,options;progress=JS.SimplexProgressContext(lp;diagnostics))
end
function run_checks(managers)
    @testset "Fixed pricing reuse eligibility" begin
        for manager in managers, pricing in (:dantzig,:steepest_edge)
            w=workspace(manager,pricing)
            @test JS._can_reuse_dual_checks(w,deadline())
            w.dual_devex_fallback=true
            @test JS._can_reuse_dual_checks(w,deadline())
            w.dual_pricing_fallback=true
            @test JS._can_reuse_dual_checks(w,deadline()) == (pricing==:dantzig)
            @test !JS._can_reuse_dual_checks(w,JS._guard_stop_callback(()->false))
            @test !JS._can_reuse_dual_checks(workspace(manager,:auto),deadline())
            @test !JS._can_reuse_dual_checks(workspace(manager,pricing;partial_pricing=true),deadline())
        end
    end
    @testset "Corrected row, finite publication and refactor with fixed pricing" begin
        for manager in managers, pricing in (:dantzig,:steepest_edge)
            w=workspace(manager,pricing)
            w.factorization=JS._basis_factorization(sparse([-1.0 1e-5;0.0 -1.0]),w.options)
            @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
            @test w.iterations==1 && w.refactorizations==0
            @test w.basis.basic_indices==[1,4] && w.primal[1]≈1.0 && JS._finite_workspace(w)
            row,rho,values=w.scratch.tableau_row,w.scratch.rho,w.problem.A.nzval
            for (dst,src) in ((rho,rho),(values,rho),(row,values))
                @test !JS._can_reuse_corrected_row(w,deadline(),dst,src)
            end
            w=workspace(manager,pricing;refactorization_interval=1)
            @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
            @test w.refactorizations>0 && JS._finite_workspace(w)
            observed=workspace(manager,pricing;observer=(ev,w)->ev==:pivot_completed && (w.costs[1]=NaN))
            @test !JS._can_reuse_dual_checks(observed,deadline())
            @test JS.dual_iteration!(observed,deadline()).status==NUMERICAL_ERROR
            fields=pricing==:dantzig ? (:primal,:costs,:reduced_costs) : (:primal,:costs,:reduced_costs,:pricing_weights)
            for field in fields
                altered=workspace(manager,pricing)
                stop=JS._guard_stop_callback(()->begin
                    altered.iterations>0 && (getproperty(altered,field)[1]=NaN)
                    false
                end)
                @test !JS._can_reuse_dual_checks(altered,stop)
                @test JS._dual_optimize!(altered,stop).status==NUMERICAL_ERROR
            end
        end
    end
    @testset "DSE fallback preserves the original guards" begin
        for manager in managers
            w=workspace(manager,:steepest_edge); w.pricing_weights .= 1e6
            @test isnothing(JS.dual_iteration!(w,deadline()))
            @test w.dual_devex_fallback && JS._weight_pricing(w,:dual)==:devex
            @test JS._finite_workspace(w) && JS._can_reuse_dual_checks(w,deadline())
            @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
            for failure in (:none,:primal,:updated_devex)
                lp=LinearProblem(sparse(reshape([1.0,0.0],2,1)),[1.0])
                state=JS.initialize_workspace(lp,w.options)
                failure==:primal && (state.primal[end]=NaN)
                row=failure==:updated_devex ? [0.0,1e200,0.0] : [0.0,1.0,0.0]
                valid=JS.update_dual_pricing_weights!(state,[1e150,0.0],row,[1e10,1.0],1,1.0,1e300,deadline())
                @test state.dual_devex_fallback && JS._weight_pricing(state,:dual)==:devex
                @test valid == (failure==:none)
                @test JS._finite_workspace(state) == valid
            end
        end
    end
end
run_checks((:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall))
end
