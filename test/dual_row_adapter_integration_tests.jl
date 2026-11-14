module DualRowAdapterIntegrationTests
using Test, JSimplex, SparseArrays, LinearAlgebra
const JS=JSimplex
const MANAGERS=(:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub,:pfi)
deadline()=JS._guard_stop_callback(JS._SolveDeadline(time_ns(),Inf))
function fixture(T, manager=:pfi; m=200, enabled=true, policy=nothing, diagnostics=nothing, kwargs...)
    n=97
    p=LinearProblem(sparse(1:n,1:n,ones(T,n),m,n),zeros(T,n);column_upper=fill(T(3),n))
    options=SolverOptions(T;verbose=false,presolve=false,dual_row_adapter=enabled,
        basis_update=manager,kwargs...)
    progress=JS.SimplexProgressContext(p;diagnostics,
        numerical_policy=isnothing(policy) ? JS.NumericalPolicy(T,options) : policy)
    return JS.initialize_workspace(p,options;progress)
end
function consumed(w,stop,rho,leaving,n;ratio=false)
    out=w.scratch.tableau_row; total=zero(eltype(rho))
    for _ in 1:n
        c=JS._dual_row_context(w,stop)
        JS._timed_dual_row_price!(c,w,out,rho,leaving)
        total+=out[end]
        r=JS._dual_row_residual!(c,w,rho,leaving)
        total+=isfinite(r) ? r : zero(r)
        ratio && JS._dual_row_ratio!(c,w,out,one(eltype(rho)),one(eltype(rho)))
    end
    return total
end
allocation(w,stop,rho,leaving,n;kwargs...)=@allocated consumed(w,stop,rho,leaving,n;kwargs...)
@testset "Opt-out and unsupported gates allocate no adapter storage" begin
    stop=deadline()
    for T in (Float32,Float64)
        w=fixture(T;enabled=false)
        @test JS._dual_row_context(w,stop)===nothing && w.scratch.dual_row===nothing
        for kwargs in ((simplex_strategy=:adaptive,), (partial_pricing=true,),
                       (basis_refactorization=:markowitz,))
            w=fixture(T;kwargs...)
            @test JS._dual_row_context(w,stop)===nothing && w.scratch.dual_row===nothing
        end
        for flag in (:stable_ratio,:sparse_pricing,:hypersparse)
            policy=JS.NumericalPolicy(T;NamedTuple{(flag,)}((true,))...)
            w=fixture(T;policy)
            @test JS._dual_row_context(w,stop)===nothing
        end
        w=fixture(T;diagnostics=JS.SimplexDiagnostics())
        @test JS._dual_row_context(w,stop)===nothing
        w=fixture(T)
        @test JS._dual_row_context(w,()->false)===nothing
        original=w.scratch.tableau_row
        w.scratch.tableau_row=w.scratch.rho
        @test JS._dual_row_context(w,stop)===nothing
        w.scratch.tableau_row=original
        w.scratch.rho=w.problem.A.nzval
        @test JS._dual_row_context(w,stop)===nothing
        w=fixture(T);w.scratch.tableau_row=w.problem.A.nzval
        @test JS._dual_row_context(w,stop)===nothing
    end
    for T in (BigFloat,Rational{BigInt},Float16)
        # A tiny basis avoids unrelated Float16 dimension/error-bound limits.
        p=LinearProblem(sparse(T[1 0;0 1]),zeros(T,2))
        w=JS.initialize_workspace(p,SolverOptions(T;dual_row_adapter=true,verbose=false,presolve=false))
        @test JS._dual_row_context(w,stop)===nothing && w.scratch.dual_row===nothing
    end
end
@testset "Owned scratch, reset, refactorization and staging" begin
    for T in (Float32,Float64), manager in MANAGERS
        w=fixture(T,manager);stop=deadline();c=JS._dual_row_context(w,stop)
        @test c===w.scratch.dual_row
        c.ready=true;c.support_valid=true;c.mode=:fused
        push!(c.support,1);c.generation=7
        @test JS._dual_row_context(w,stop)===c
        @test !c.ready && !c.support_valid && c.mode===:none
        @test c.support==[1] && c.generation==7
        staged=JS._candidate_workspace(w)
        @test staged.scratch!==w.scratch && staged.scratch.dual_row===nothing
        @test JS._dual_row_context(staged,stop)===nothing
        @test JS._dual_row_context(fixture(T,manager),stop)!==c
        JS.recompute!(w;refactorize=true)
        @test JS._dual_row_native_factor(w.factorization,T)
        @test JS._dual_row_context(w,stop)===c
    end
end
@testset "Consumed timed pricing and ratio have no warmed per-call allocations" begin
    for T in (Float32,Float64), manager in MANAGERS
        w=fixture(T,manager;m=600);stop=deadline()
        for sparse_route in (false,true), row in (1,600)
            rho=sparse_route ? zeros(T,600) : ones(T,600)
            sparse_route && (rho[row]=one(T))
            consumed(w,stop,rho,row,100;ratio=true)
            allocation(w,stop,rho,row,100;ratio=true)
            @test allocation(w,stop,rho,row,1000;ratio=true)==0
            expected=similar(w.scratch.tableau_row);JS._csc_price!(expected,w.problem.A,rho)
            @test isequal(expected,w.scratch.tableau_row)
        end
    end
end
@testset "Entire dual iterations preserve endpoints and native mode" begin
    for T in (Float32,Float64), manager in MANAGERS, pricing in (:devex,:steepest_edge,:dantzig,:auto)
        p=LinearProblem(sparse(T[1 0;0 1]),T[1,10];row_lower=T[1,2])
        states=[]
        for enabled in (false,true)
            options=SolverOptions(T;dual_row_adapter=enabled,presolve=false,scaling=:off,
                algorithm=:dual,pricing,basis_update=manager,refactorization_interval=1,verbose=false)
            w=JS.initialize_workspace(p,options)
            @test JS._dual_optimize!(w,deadline()).status==OPTIMAL
            @test JS._dual_row_native_factor(w.factorization,T)
            @test JS._original_primal_feasible(p,w.primal[1:2],options.primal_tolerance)
            @test enabled ? !isnothing(w.scratch.dual_row) : isnothing(w.scratch.dual_row)
            push!(states,(copy(w.primal),copy(w.reduced_costs),copy(w.pricing_weights),
                copy(w.basis.basic_indices),copy(w.basis.states),w.iterations,w.refactorizations))
        end
        @test isequal(states[1],states[2])
    end
end
@testset "Timing callback retains exception accounting" begin
    for T in (Float32,Float64)
        diagnostics=JS.SimplexDiagnostics(kernel_timing=true)
        w=fixture(T;diagnostics);rho=ones(T,200)
        @test_throws DimensionMismatch JS._timed_dual_row_price!(nothing,w,T[],rho,1)
        @test diagnostics.kernel_calls[:pricing]==1
        @test diagnostics.kernel_nanoseconds[:pricing]>0
    end
end
function unowned()
    w=fixture(Float64);c=JS._dual_row_context(w,deadline())
    return WeakRef(w),WeakRef(c)
end
@testset "Scratch context does not outlive its workspace" begin
    a,b=unowned();GC.gc()
    @test a.value===nothing && b.value===nothing
end
end
