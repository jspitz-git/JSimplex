mutable struct RecordingSimplexLogger <: JSimplex.Logging.AbstractLogger
    records::Vector{Any}
end

function repeated_feasibility_queries(workspace, repetitions)
    for _ in 1:repetitions
        JSimplex.primal_infeasibility(workspace)
        JSimplex.dual_infeasibility(workspace)
    end
    return nothing
end

JSimplex.Logging.min_enabled_level(::RecordingSimplexLogger) = JSimplex.Logging.Debug
JSimplex.Logging.shouldlog(::RecordingSimplexLogger, args...) = true
JSimplex.Logging.catch_exceptions(::RecordingSimplexLogger) = false
function JSimplex.Logging.handle_message(
    logger::RecordingSimplexLogger,
    level,
    message,
    args...;
    kwargs...,
)
    push!(logger.records, (; level, message, kwargs...))
    return nothing
end

function test_workspace_type(::Type{T}) where {T}
    problem = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[2], 1, 1)), T[5];
        row_lower=T[1], column_lower=T[1], column_upper=T[4])
    workspace = @inferred JSimplex.initialize_workspace(problem, SolverOptions(T))
    @test workspace isa JSimplex.SimplexWorkspace{T}
    @test all(isconcretetype, fieldtypes(typeof(workspace)))
    @test eltype(workspace.primal) === T
    @test workspace.primal == T[1, 2]
    @test (@inferred JSimplex.primal_infeasibility(workspace)) isa T
    @test (@inferred JSimplex.dual_infeasibility(workspace)) isa T
    @test JSimplex.primal_infeasibility(workspace) == zero(T)
    @test JSimplex.dual_infeasibility(workspace) == zero(T)
    @test (@inferred JSimplex.recompute!(workspace)) === workspace
    workspace.basis = JSimplex.Basis([1], [JSimplex.BASIC, JSimplex.AT_LOWER])
    @test (@inferred JSimplex.recompute!(workspace; refactorize=true)) === workspace
    @test workspace.primal == T[1//2, 1]
    @test workspace.reduced_costs == T[0, 5//2]
    @test JSimplex.primal_infeasibility(workspace) == T(1//2)
    @test (@inferred JSimplex.initialize_workspace(problem, SolverOptions())).options isa SolverOptions{T}
    empty_problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 1), T[1]; column_lower=[nothing])
    empty_workspace = @inferred JSimplex.initialize_workspace(empty_problem, SolverOptions(T))
    @test empty_workspace.primal == T[0]
    @test (@inferred JSimplex.dual_infeasibility(empty_workspace)) == one(T)
end

@testset "Typed simplex workspace" begin
    foreach(test_workspace_type, (Float32, Float64, BigFloat, Rational{BigInt}))
end

@testset "Simplex workspace" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse([1.0 2.0; -1.0 1.0]), [3.0, 1.0];
        row_lower=[1.0, -Inf], row_upper=[1.0, 4.0],
        column_lower=[0.0, 0.0], column_upper=[Inf, Inf],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    nrows, ncols = size(problem.A)
    @test workspace.basis.basic_indices == collect(ncols + 1:ncols + nrows)
    @test all(workspace.basis.states[ncols + 1:end] .== JSimplex.BASIC)
    @test JSimplex.basis_matrix(workspace) == [-1.0 0.0; 0.0 -1.0]
    @test JSimplex.primal_infeasibility(workspace) >= 0.0
    @test JSimplex.dual_infeasibility(workspace) >= 0.0
end

@testset "Feasibility queries do not allocate" begin
    dimension = 512
    problem = LinearProblem(
        JSimplex.SparseArrays.spdiagm(0 => ones(dimension)),
        ones(dimension);
        row_lower=ones(dimension),
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))

    JSimplex.primal_infeasibility(workspace)
    JSimplex.dual_infeasibility(workspace)

    repeated_feasibility_queries(workspace, 100)
    allocated = @allocated repeated_feasibility_queries(workspace, 100)
    @test allocated == 0
end

@testset "Simplex workspace nonbasic bounds" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(zeros(1, 3)), zeros(3);
        column_lower=[2.0, -Inf, -Inf],
        column_upper=[2.0, 3.0, Inf],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())

    @test workspace.basis.states[1:3] == [
        JSimplex.AT_LOWER,
        JSimplex.AT_UPPER,
        JSimplex.FREE_NONBASIC,
    ]
    @test workspace.primal[1:3] == [2.0, 3.0, 0.0]
    @test !isfinite(workspace.lower[4])
    @test !isfinite(workspace.upper[4])
end

@testset "Simplex workspace recomputation and validation" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([2.0], 1, 1)), [5.0];
        row_lower=[1.0], row_upper=[Inf],
        column_lower=[1.0], column_upper=[4.0],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())

    @test workspace.primal == [1.0, 2.0]
    @test workspace.reduced_costs == [5.0, 0.0]
    @test JSimplex.dual_infeasibility(workspace) == 0.0
    @test workspace.refactorizations == 0

    workspace.basis = JSimplex.Basis(
        [2],
        JSimplex.VariableState[JSimplex.AT_UPPER, JSimplex.BASIC],
    )
    JSimplex.recompute!(workspace)
    @test workspace.primal == [4.0, 8.0]
    @test JSimplex.dual_infeasibility(workspace) == 5.0

    workspace.basis = JSimplex.Basis(
        [1],
        JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER],
    )
    JSimplex.recompute!(workspace; refactorize=true)
    @test JSimplex.basis_matrix(workspace) == [2.0;;]
    @test workspace.primal == [0.5, 1.0]
    @test workspace.reduced_costs == [0.0, 2.5]
    @test workspace.refactorizations == 1
    @test JSimplex.dual_infeasibility(workspace) == 0.0

    workspace.basis = JSimplex.Basis(
        [1, 1],
        JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER],
    )
    @test_throws ArgumentError JSimplex.basis_matrix(workspace)
end

@testset "Zero-row simplex workspace" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(0, 1), [-1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())

    @test isempty(workspace.basis.basic_indices)
    @test workspace.primal == [0.0]
    @test workspace.reduced_costs == [-1.0]
    JSimplex.recompute!(workspace; refactorize=true)
    @test workspace.refactorizations == 1
end

@testset "Refactorization progress reports current simplex metrics" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([2.0], 1, 1)), [-5.0];
        objective_constant=7.0,
        row_lower=[1.0],
        column_lower=[1.0],
        column_upper=[4.0],
    )
    records = Any[]
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    workspace.iterations = 12
    workspace.basis = JSimplex.Basis(
        [1],
        JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER],
    )
    JSimplex.Logging.with_logger(RecordingSimplexLogger(records)) do
        JSimplex.recompute!(workspace; refactorize=true)
    end

    progress_records = filter(
        record -> record.message isa AbstractString && startswith(record.message, "iter="),
        records,
    )
    @test length(progress_records) == 1
    if length(progress_records) == 1
        progress = only(progress_records)
        @test progress.level == JSimplex.Logging.Info
        @test keys(progress) == (:level, :message)
        matched = match(
            r"^iter=12 obj=4\.5 pinf=0\.5 \(1\) dinf=2\.5 \(1\) time=([0-9.e+-]+)s$",
            progress.message,
        )
        @test !isnothing(matched)
        @test parse(Float64, only(something(matched).captures)) >= 0.0
    end

    output = IOBuffer()
    JSimplex.Logging.with_logger(
        JSimplex.Logging.ConsoleLogger(output, JSimplex.Logging.Info),
    ) do
        JSimplex.recompute!(workspace; refactorize=true)
    end
    rendered = String(take!(output))
    @test count(==('\n'), rendered) == 1
    @test occursin("iter=12 obj=4.5 pinf=0.5 (1) dinf=2.5 (1) time=", rendered)

    empty!(records)
    quiet = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    JSimplex.Logging.with_logger(RecordingSimplexLogger(records)) do
        JSimplex.recompute!(quiet; refactorize=true)
    end
    @test all(
        record -> !(record.message isa AbstractString) || !startswith(record.message, "iter="),
        records,
    )
end

@testset "Progress objective preserves stored BigFloat cancellation" begin
    problem = setprecision(BigFloat, 256) do
        large = BigFloat(2)^200
        LinearProblem(
            JSimplex.SparseArrays.sparse(reshape(BigFloat[1], 1, 1)),
            BigFloat[large + 1];
            objective_constant=-large,
            row_lower=BigFloat[1],
            row_upper=BigFloat[1],
        )
    end
    records = Any[]
    setprecision(BigFloat, 64) do
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(BigFloat))
        workspace.basis = JSimplex.Basis(
            [1],
            JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER],
        )
        JSimplex.Logging.with_logger(RecordingSimplexLogger(records)) do
            JSimplex.recompute!(workspace; refactorize=true)
        end
    end

    progress_records = filter(
        record -> record.message isa AbstractString && startswith(record.message, "iter="),
        records,
    )
    @test length(progress_records) == 1
    if length(progress_records) == 1
        @test occursin(" obj=1.0 ", only(progress_records).message)
    end
end
