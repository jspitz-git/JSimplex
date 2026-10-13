module HypersparseBoundaryInvalidationTests
using Test, JSimplex, SparseArrays, LinearAlgebra
const JS = JSimplex

function boundary_workspace(T, manager, backend; enabled=true)
    n = 8
    problem = JS.LinearProblem(spdiagm(0=>ones(T,n)), zeros(T,n); row_lower=zeros(T,n))
    options = JS.SolverOptions(T; simplex_strategy=:adaptive, pricing=:dantzig,
        basis_update=manager, basis_refactorization=backend, verbose=false)
    policy = JS.NumericalPolicy(T; simplex_strategy=:adaptive, hypersparse=enabled,
        refactor_timing=false)
    return JS.initialize_workspace(problem, options; progress=JS.SimplexProgressContext(
        problem; numerical_policy=policy))
end

function check_refinement_destination(T, manager, backend, kind)
    ws = boundary_workspace(T, manager, backend)
    rhs = JS._pipeline_unit_rhs!(ws, 3)
    parent = ws.scratch.rho
    fill!(parent, zero(T))
    JS._pipeline_changed!(ws, parent)
    @test isempty(JS._pipeline_vector!(ws, parent).indices)
    destination = kind == :vector ? parent : kind == :view ? view(parent, :) :
        kind == :reordered ? view(parent, 8:-1:1) :
        kind == :external ? zeros(T,8) : view(zeros(T,8), :)
    external = kind in (:external, :unrelated_view)
    quality = JS.refine_basis_solve!(destination, ws, rhs,
        ws.progress.numerical_policy, ()->false; transposed=true)
    @test quality.reliable
    @test destination == -rhs
    expected = external ? zeros(T,8) : T[-(i == (kind == :reordered ? 6 : 3)) for i in 1:8]
    @test parent == expected
    indices = JS._pipeline_vector!(ws, parent).indices
    @test indices == findall(!iszero, expected)
    JS._pipeline_price!(ws.scratch.tableau_row, ws, parent; kernel_mode=:sparse)
    @test ws.scratch.tableau_row == vcat(expected, -expected)
end

function check_projected_probe(observer_metadata; observer_failure=false)
    p = JS.LinearProblem(sparse(reshape([1.0],1,1)), [1.0];
        column_lower=[1.0], row_lower=[1.0], row_upper=[2.0])
    options = JS.SolverOptions(; verbose=false, presolve=false, scaling=:off)
    policy = JS.NumericalPolicy(Float64; lp_refinement=true, hypersparse=true,
        refactor_timing=false)
    armed, seen = Ref(false), Ref(0)
    failure = ErrorException("projected witness observer failed")
    observer = function (event, probe)
        if armed[] && event == :refactor_other
            seen[] += 1
            # Read existing values; only optional support metadata is constructed.
            @assert all(iszero, probe.scratch.rho)
            if observer_metadata
                @assert isempty(JS._pipeline_vector!(probe, probe.scratch.rho).indices)
            end
            observer_failure && throw(failure)
        end
        return nothing
    end
    diagnostics = JS.SimplexDiagnostics(; observer)
    progress = JS.SimplexProgressContext(p; numerical_policy=policy, diagnostics)
    basis = JS.Basis([1], [JS.BASIC, JS.AT_LOWER])
    ws = JS.initialize_from_basis(p, basis, options; policy, progress)
    residual = JS._lp_residuals(ws, [1.25,1.5], [1.0])
    correction, map = JS.build_correction_problem(ws, residual, 4, 8)
    auxiliary_basis = JS.Basis([3], [JS.AT_LOWER,JS.AT_LOWER,JS.BASIC])
    auxiliary = JS.initialize_from_basis(correction, auxiliary_basis, options)
    saved_primal, saved_basis = copy(ws.primal), copy(ws.basis.basic_indices)
    source_support = JS._pipeline_vector!(ws, ws.scratch.rho)
    saved_rho, saved_support = copy(ws.scratch.rho), copy(source_support.indices)
    armed[] = true
    caught = nothing
    probe = try
        JS._lp_project_certificate(ws, auxiliary, map, [1.0,1.0], [1.0],
            JS.SimplexRunBudget(ws), JS._guard_stop_callback(()->false))
    catch exception
        caught = exception
        nothing
    end
    armed[] = false
    @test seen[] == 1
    @test ws.scratch.rho == saved_rho
    @test JS._pipeline_vector!(ws,ws.scratch.rho) === source_support
    @test source_support.indices == saved_support
    if observer_failure
        @test caught isa JS.DiagnosticObserverFailure
        @test caught.cause === failure
        @test isnothing(probe)
        return
    end
    @test isnothing(caught)
    @test !isnothing(probe)
    if !isnothing(probe)
        @test probe.primal == [1.0,1.0]
        @test probe.scratch.rho == [1.0]
        @test probe.scratch.lp_dual_witness == [1.0]
        @test JS._original_optimality_certified(probe, [1.0])
        @test JS._pipeline_vector!(probe, probe.scratch.rho).indices == [1]
        JS._pipeline_price!(probe.scratch.tableau_row, probe, probe.scratch.rho; kernel_mode=:sparse)
        @test probe.scratch.tableau_row == [1.0,-1.0]
    end
    @test ws.primal == saved_primal && ws.basis.basic_indices == saved_basis
end


@testset "Accepted refinement invalidates all supported destination forms" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        backend in (:native,:markowitz), kind in (:vector,:view,:reordered,:external,:unrelated_view)
        @testset "$T/$manager/$backend/$kind" begin
            check_refinement_destination(T,manager,backend,kind)
        end
    end
end

@testset "Invalidation preserves ownership and rejected corrections" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        ws = boundary_workspace(T,:pfi,:native; enabled=false)
        rhs = JS._pipeline_unit_rhs!(ws,3)
        fill!(ws.scratch.rho,zero(T))
        @test isnothing(ws.scratch.hypersparse)
        q = JS.refine_basis_solve!(view(ws.scratch.rho,:),ws,rhs,
            ws.progress.numerical_policy,()->false; transposed=true)
        @test q.reliable && ws.scratch.rho == -rhs
        @test isnothing(ws.scratch.hypersparse)

        ws = boundary_workspace(T,:pfi,:native)
        rhs = JS._pipeline_unit_rhs!(ws,3)
        fill!(ws.scratch.rho,zero(T))
        JS._pipeline_changed!(ws,ws.scratch.rho)
        support = JS._pipeline_vector!(ws,ws.scratch.rho)
        cache = ws.scratch.hypersparse
        index = JS._pipeline_buffer_index(cache,ws.scratch.rho)
        rebuilds = cache.support_rebuilds
        policy = JS.NumericalPolicy(T; max_refinements=0)
        q = JS.refine_basis_solve!(view(ws.scratch.rho,:),ws,rhs,policy,()->false)
        @test !q.reliable && all(iszero,ws.scratch.rho)
        @test cache.valid[index]
        @test isempty(JS._pipeline_vector!(ws,ws.scratch.rho).indices)
        @test cache.support_rebuilds == rebuilds
        # Each owned buffer must be invalidated when written through an alias.
        for field in JS.HYPERSPARSE_BUFFER_FIELDS
            values = getfield(ws.scratch,field)
            fill!(values,zero(T)); JS._pipeline_changed!(ws,values)
            @test isempty(JS._pipeline_vector!(ws,values).indices)
            alias = view(values,:)
            alias[2] = one(T)
            JS._pipeline_changed!(ws,alias)
            @test JS._pipeline_vector!(ws,values).indices == [2]
        end
        # Model storage remains forbidden even through a view.
        saved = copy(ws.problem.A.nzval)
        @test_throws ArgumentError JS.refine_basis_solve!(view(ws.problem.A.nzval,:),
            ws,ones(T,8),policy,()->false)
        @test ws.problem.A.nzval == saved
    end
end

@testset "Projected witness publication and observer provenance" begin
    for metadata in (false,true), failure in (false,true)
        @testset "metadata=$metadata/failure=$failure" begin
            check_projected_probe(metadata;observer_failure=failure)
        end
    end
end

end
