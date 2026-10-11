# Pending S3 safety regressions, prepared during the sole S0 long reference.
# No production patch. Run through the serial guard: optional smoke|matrix.
using Test, JSimplex, SparseArrays, LinearAlgebra
const JS = JSimplex
const ROOT = realpath(joinpath(@__DIR__, "../../.."))
@assert realpath(dirname(dirname(pathof(JS)))) == ROOT
@assert Threads.nthreads() == BLAS.get_num_threads() == 1
const MODE = isempty(ARGS) ? "smoke" : only(ARGS)
MODE in ("smoke", "matrix") || error("Expected smoke or matrix")

function boundary_workspace(T, manager, backend)
    n = 8
    problem = JS.LinearProblem(spdiagm(0=>ones(T,n)), zeros(T,n); row_lower=zeros(T,n))
    options = JS.SolverOptions(T; simplex_strategy=:adaptive, pricing=:dantzig,
        basis_update=manager, basis_refactorization=backend, verbose=false)
    policy = JS.NumericalPolicy(T; simplex_strategy=:adaptive, hypersparse=true,
        refactor_timing=false)
    return JS.initialize_workspace(problem, options; progress=JS.SimplexProgressContext(
        problem; numerical_policy=policy))
end

function check_refinement_destination(T, manager, backend, as_view)
    ws = boundary_workspace(T, manager, backend)
    rhs = JS._pipeline_unit_rhs!(ws, 3)
    parent = ws.scratch.rho
    fill!(parent, zero(T))
    JS._pipeline_changed!(ws, parent)
    @test isempty(JS._pipeline_vector!(ws, parent).indices)
    destination = as_view ? view(parent, :) : parent
    quality = JS.refine_basis_solve!(destination, ws, rhs,
        ws.progress.numerical_policy, ()->false; transposed=true)
    @test quality.reliable
    @test parent[3] == -one(T)
    @test count(!iszero, parent) == 1
    @test JS._pipeline_vector!(ws, parent).indices == [3]
    JS._pipeline_price!(ws.scratch.tableau_row, ws, parent; kernel_mode=:sparse)
    @test ws.scratch.tableau_row[3] == -one(T)
    @test ws.scratch.tableau_row[11] == one(T)
end

function check_projected_probe(observer_metadata)
    p = JS.LinearProblem(sparse(reshape([1.0],1,1)), [1.0];
        column_lower=[1.0], row_lower=[1.0], row_upper=[2.0])
    options = JS.SolverOptions(; verbose=false, presolve=false, scaling=:off)
    policy = JS.NumericalPolicy(Float64; lp_refinement=true, hypersparse=true,
        refactor_timing=false)
    armed, seen = Ref(false), Ref(0)
    observer = function (event, probe)
        if armed[] && event == :refactor_other
            seen[] += 1
            # Read existing values; only optional support metadata is constructed.
            @assert all(iszero, probe.scratch.rho)
            if observer_metadata
                @assert isempty(JS._pipeline_vector!(probe, probe.scratch.rho).indices)
            end
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
    armed[] = true
    probe = JS._lp_project_certificate(ws, auxiliary, map, [1.0,1.0], [1.0],
        JS.SimplexRunBudget(ws), JS._guard_stop_callback(()->false))
    armed[] = false
    @test seen[] == 1
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

@testset "Pipeline boundary regression candidates" begin
@testset "Accepted refinement updates parent support through a view" begin
    types = MODE == "smoke" ? (Float64,) : (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
    managers = MODE == "smoke" ? (:pfi,) : (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)
    backends = MODE == "smoke" ? (:native,) : (:native,:markowitz)
    for T in types, manager in managers, backend in backends, as_view in (false,true)
        @testset "$T/$manager/$backend/view=$as_view" begin
            check_refinement_destination(T,manager,backend,as_view)
        end
    end
end
@testset "Projected LP witness invalidates observer-created scratch support" begin
    for metadata in (false,true)
        @testset "observer_metadata=$metadata" begin
            check_projected_probe(metadata)
        end
    end
end
end
