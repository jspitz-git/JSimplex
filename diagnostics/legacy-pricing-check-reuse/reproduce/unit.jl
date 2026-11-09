include("common.jl")
const green = arm == "unit"
green && include("candidate.jl")
deadline() = JS._guard_stop_callback(JS._SolveDeadline(time_ns(),Inf))
function workspace(; selected=pricing, observer=nothing, interval=160)
    lp=LinearProblem(sparse([1.0 0.0;0.0 1.0]),[1.0,10.0];row_lower=[1.0,-Inf])
    diag=isnothing(observer) ? nothing : JS.SimplexDiagnostics(;observer)
    return JS.initialize_workspace(lp,opts(100;selected,interval);progress=JS.SimplexProgressContext(lp;diagnostics=diag))
end

@testset "Pricing-specific eligibility and unchanged safeguards" begin
    for selected in (:dantzig,:steepest_edge)
        w=workspace(;selected)
        @test JS._can_reuse_dual_checks(w,deadline())
        green || continue
        @test !JS._can_reuse_dual_checks(w,JS._guard_stop_callback(()->false))
        @test !JS._can_reuse_corrected_row(w,deadline(),w.scratch.rho,w.scratch.rho)
        @test !JS._can_reuse_dual_checks(workspace(;selected=:auto),deadline())
        w.dual_pricing_fallback=true
        @test JS._can_reuse_dual_checks(w,deadline()) == (selected==:dantzig)
        w.dual_pricing_fallback=false
        w.dual_devex_fallback=true
        @test JS._can_reuse_dual_checks(w,deadline())
        observed=workspace(;selected,observer=(ev,w)->ev==:pivot_completed && (w.costs[1]=NaN))
        @test !JS._can_reuse_dual_checks(observed,deadline())
        @test JS.dual_iteration!(observed,deadline()).status==NUMERICAL_ERROR
        w=workspace(;selected,interval=1)
        @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
        @test w.refactorizations>0 && JS._finite_workspace(w)
    end
end

if green
    const corrected_reuses=Ref(0)
    install_method("_dual_iteration_unchecked!",(
        "                    row_failed = false"=>"""                    @assert _dual_row_residual_ratio(workspace,rho,leaving_row)<=1.0
                    Main.corrected_reuses[]+=1
                    row_failed = false""",))
    @testset "Accepted BTRAN correction and mutating stop callbacks" begin
        for selected in (:dantzig,:steepest_edge)
            w=workspace(;selected)
            stale=sparse([-1.0 1e-5;0.0 -1.0])
            w.factorization=JS._basis_factorization(stale,opts(100;selected))
            corrected_reuses[]=0
            @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
            @test corrected_reuses[]>0
            @test w.iterations==1 && w.refactorizations==0
            @test w.basis.basic_indices==[1,4] && w.primal[1]≈1.0 && JS._finite_workspace(w)
            row,rho,values=w.scratch.tableau_row,w.scratch.rho,w.problem.A.nzval
            for (dst,src) in ((rho,rho),(values,rho),(row,values))
                @test !JS._can_reuse_corrected_row(w,deadline(),dst,src)
            end
            fields=selected==:dantzig ? (:primal,:costs,:reduced_costs) :
                (:primal,:costs,:reduced_costs,:pricing_weights)
            for field in fields
                altered=workspace(;selected)
                callback=JS._guard_stop_callback(()->begin
                    altered.iterations>0 && (getproperty(altered,field)[1]=NaN)
                    false
                end)
                @test !JS._can_reuse_dual_checks(altered,callback)
                @test JS._dual_optimize!(altered,callback).status==NUMERICAL_ERROR
            end
        end
    end
    # Retire the unit-only row probe before the small reference/candidate solves.
    Core.eval(JS,Meta.parse(definition("dual_simplex","_dual_iteration_unchecked!")))
    @testset "DSE weight disagreement and recovery" begin
        w=workspace(;selected=:steepest_edge)
        w.pricing_weights .= 1e6
        terminal=JS.dual_iteration!(w,deadline())
        @test isnothing(terminal)
        @test w.dual_devex_fallback && JS._weight_pricing(w,:dual)==:devex
        @test JS._finite_workspace(w) && JS._can_reuse_dual_checks(w,deadline())
        @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
        for failure in (:none,:primal,:updated_devex)
            lp=LinearProblem(sparse(reshape([1.0,0.0],2,1)),[1.0])
            w=JS.initialize_workspace(lp,opts(100;selected=:steepest_edge))
            failure==:primal && (w.primal[end]=NaN)
            row=failure==:updated_devex ? [0.0,1e200,0.0] : [0.0,1.0,0.0]
            valid=JS.update_dual_pricing_weights!(w,[1e150,0.0],row,[1e10,1.0],1,1.0,1e300,deadline())
            @test w.dual_devex_fallback && JS._weight_pricing(w,:dual)==:devex
            @test valid == (failure==:none)
            @test JS._finite_workspace(w) == valid
        end
    end
    @testset "Original safeguards remain active" begin
        include(joinpath(@__DIR__,"dual-weight-tests.jl"))
    end
    @testset "Complete small solves reference and candidate" begin
        for selected in (:dantzig,:steepest_edge), name in ("afiro","sc50a")
            lp=read_mps(joinpath(@__DIR__,name*".mps"))
            Core.eval(JS,Meta.parse(definition("dual_simplex","_can_reuse_dual_checks")))
            r=Base.invokelatest(solve,lp;options=opts(typemax(Int);selected),relax_integrality=true)
            install_candidate!()
            c=Base.invokelatest(solve,lp;options=opts(typemax(Int);selected),relax_integrality=true)
            @test r.status==c.status==OPTIMAL
            @test JS._original_primal_feasible(lp,r.primal,1e-7) && JS._original_primal_feasible(lp,c.primal,1e-7)
            @test reinterpret(UInt64,r.objective_value)==reinterpret(UInt64,c.objective_value)
            @test isequal(r.primal,c.primal)
            @test r.statistics.iterations==c.statistics.iterations && r.statistics.refactorizations==c.statistics.refactorizations
        end
    end
    open(io->TOML.print(io,Dict("passed"=>true,"profile"=>profile)),output,"w")
end
