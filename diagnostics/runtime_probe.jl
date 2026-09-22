# Whole-source, interleaved runtime and numerical-equivalence audit.
# julia --startup-file=no --compiled-modules=existing --project=dev \
#   diagnostics/runtime_probe.jl BEFORE_SRC OUTPUT.toml [AFTER_SRC]
using SparseArrays, LinearAlgebra, Logging, Statistics, SHA, TOML, Test
BLAS.set_num_threads(1)

function load_snapshot(name, source)
    root = joinpath(mktempdir(), "src")
    cp(source, root)
    hashes = Dict(relpath(joinpath(dir, file), root) => bytes2hex(sha256(read(joinpath(dir, file))))
        for (dir, _, files) in walkdir(root) for file in files if endswith(file, ".jl"))
    for (file, old, replacement) in (
        ("JSimplex.jl", "import OrderedCollections",
         "const OrderedCollections = Base.require(Base.PkgId(Base.UUID(\"bac558e1-5e72-5ebc-8fee-abe8a469f55d\"), \"OrderedCollections\"))"),
        ("moi.jl", "import MathOptInterface as MOI",
         "const MOI = Base.require(Base.PkgId(Base.UUID(\"b8f27783-ece8-5eb3-8dc8-9495eed66fee\"), \"MathOptInterface\"))"))
        path = joinpath(root, file)
        write(path, replace(read(path, String), old => replacement))
    end
    scope = Module(name)
    Base.include(scope, joinpath(root, "JSimplex.jl"))
    return scope, hashes
end

const before_scope, before_hashes = load_snapshot(:RuntimeBefore, abspath(ARGS[1]))
const Before = getfield(before_scope, :JSimplex)
const after_scope, after_hashes = load_snapshot(:RuntimeAfter,
    abspath(length(ARGS) >= 3 ? ARGS[3] : "src"))
const After = getfield(after_scope, :JSimplex)
const results = Dict{String,Any}[]
const checks = Dict{String,Any}[]

function timed_batch(f, repetitions)
    elapsed = @elapsed for _ in 1:repetitions
        f()
    end
    return elapsed / repetitions
end

function compare_time(label, old, new; repetitions=5, samples=15)
    for _ in 1:3
        timed_batch(old, repetitions)
        timed_batch(new, repetitions)
    end
    old_times, new_times = Float64[], Float64[]
    GC.gc()
    for i in 1:samples
        # Alternate order to reduce bias from frequency and thermal drift.
        if isodd(i)
            push!(old_times, timed_batch(old, repetitions))
            push!(new_times, timed_batch(new, repetitions))
        else
            push!(new_times, timed_batch(new, repetitions))
            push!(old_times, timed_batch(old, repetitions))
        end
    end
    old_alloc = @timed old()
    new_alloc = @timed new()
    row = Dict{String,Any}("case" => label,
        "before_seconds_median" => median(old_times), "after_seconds_median" => median(new_times),
        "paired_speedup_median" => median(old_times ./ new_times),
        "before_samples" => old_times, "after_samples" => new_times,
        "before_bytes" => old_alloc.bytes, "after_bytes" => new_alloc.bytes,
        "compile_seconds" => old_alloc.compile_time + new_alloc.compile_time,
        "repetitions" => repetitions)
    push!(results, row)
    println(label, " speedup=", round(row["paired_speedup_median"], digits=3))
    flush(stdout)
end

function ratio_case(M, ::Type{T}, n) where T
    p = M.LinearProblem(sparse(ones(T, 1, n)), [T(mod(73i, 257) + 1) for i in 1:n];
        column_upper=ones(T, n))
    w = M.initialize_workspace(p, M.SolverOptions(T; verbose=false))
    row = [T(1 + mod(i, 5)) for i in 1:n+1]
    row[end] = zero(T)
    ratio = M._bound_flipping_ratio_test
    return () -> ratio(w, row, one(T), T(1_000_000))
end

function upper_case(M, n)
    column = M.PackedUpperColumn{Float64}(collect(1:n), ones(n))
    upper = [column]
    incidence = [Int[1] for _ in 1:n]
    setter = M._set_upper_value!
    return () -> begin
        for i in 1:n
            setter(upper, incidence, 1, i, 2.0)
        end
        nothing
    end
end

function markowitz_case(M, n)
    D = M.OrderedCollections.OrderedDict{Int,Float64}
    rows = [D(i => 1.0 for i in 1:n)]
    columns = [D(1 => 1.0) for _ in 1:n]
    singleton_rows, singleton_columns, doubletons = Int[], Int[], BitSet()
    setter = M._markowitz_set_entry!
    return () -> begin
        nonzeros = n
        for i in 1:n
            nonzeros = setter(rows, columns, singleton_rows,
                singleton_columns, doubletons, 1, i, 2.0, nonzeros)
        end
        nonzeros
    end
end

function solution_signature(s)
    return (Int(s.status), s.objective_value, s.primal, s.statistics.iterations,
        s.statistics.refactorizations, s.message)
end

function state_signature(M, w)
    T = eltype(w.primal)
    rhs = T.(1:length(w.basis.basic_indices))
    return (copy(w.basis.basic_indices), UInt8.(w.basis.states), copy(w.primal),
        copy(w.reduced_costs), copy(w.costs), copy(w.pricing_weights),
        w.iterations, w.refactorizations,
        M.forward_solve(w.factorization, rhs), M.transpose_solve(w.factorization, rhs))
end

function iteration_trace(M, ::Type{T}, algorithm, method, backend, pricing) where T
    # Initially primal feasible, with boxed columns to exercise ratio sorting.
    p = M.LinearProblem(sparse(T[1 2 0 1; 0 1 2 1; 2 0 1 1]), T[-4, -3, -2, -1];
        row_upper=T[4, 5, 6], column_upper=T[3, 3, 3, 3])
    options = M.SolverOptions(T; algorithm, basis_update=method,
        basis_refactorization=backend, pricing, verbose=false, presolve=false,
        scaling=:off, refactorization_interval=2)
    w = M.initialize_workspace(p, options)
    guard = M._guard_stop_callback(() -> false)
    states = Any[state_signature(M, w)]
    terminal = algorithm == :dual ? M.make_dual_feasible!(w, guard) : nothing
    push!(states, state_signature(M, w))
    for _ in 1:100
        isnothing(terminal) || break
        terminal = algorithm == :dual ? M.dual_iteration!(w, guard) :
            M._primal_iteration!(w, guard, options.dual_tolerance)
        push!(states, state_signature(M, w))
    end
    @test !isnothing(terminal)
    return states, Int(terminal.status)
end

with_logger(NullLogger()) do
    @testset "Identical iteration states and basis solves" begin
        for T in (Float32, Float64, BigFloat, Rational{BigInt}),
            algorithm in (:dual, :primal), method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub),
            backend in (:native, :markowitz), pricing in (:dantzig, :devex, :steepest_edge)
            old = iteration_trace(Before, T, algorithm, method, backend, pricing)
            new = iteration_trace(After, T, algorithm, method, backend, pricing)
            @test isequal(old, new)
            push!(checks, Dict("case" => "$T/$algorithm/$method/$backend/$pricing",
                "states" => length(first(new)), "sha256" => bytes2hex(sha256(repr(new)))))
        end
    end
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), n in (16, 256)
        old, new = ratio_case(Before, T, n), ratio_case(After, T, n)
        @test isequal(old(), new())
        compare_time("ratio/$T/$n", old, new; repetitions=5)
    end
    compare_time("upper_set/1024", upper_case(Before, 1024), upper_case(After, 1024); repetitions=50)
    compare_time("markowitz_set/1024", markowitz_case(Before, 1024), markowitz_case(After, 1024); repetitions=50)
    @testset "Identical complete solver outcomes" begin
        for name in ("afiro", "adlittle", "sc50a", "kb2")
            path = name == "afiro" ? "test/fixtures/solver/afiro.mps" : "test/fixtures/solver/netlib/$name.mps"
            old_p, new_p = Before.read_mps(path), After.read_mps(path)
            for algorithm in (:dual, :primal), method in (:pfi, :bartels_golub), backend in (:native, :markowitz)
                opts = (; algorithm, basis_update=method, basis_refactorization=backend,
                    verbose=false, presolve=false, scaling=:off, iteration_limit=10000)
                old_opts, new_opts = Before.SolverOptions(; opts...), After.SolverOptions(; opts...)
                old = () -> Before.solve(old_p; options=old_opts)
                new = () -> After.solve(new_p; options=new_opts)
                @test isequal(solution_signature(old()), solution_signature(new()))
                compare_time("solve/$name/$algorithm/$method/$backend", old, new)
            end
            # Keep the original input and preprocessing cost visible in this audit.
            compare_time("parse/$name", () -> Before.read_mps(path), () -> After.read_mps(path))
            compare_time("presolve/$name", () -> Before.presolve_problem(old_p), () -> After.presolve_problem(new_p))
        end
    end
end
open(ARGS[2], "w") do io
    TOML.print(io, Dict("julia_version" => string(VERSION), "machine" => Sys.MACHINE,
        "threads" => Threads.nthreads(), "blas_threads" => BLAS.get_num_threads(),
        "before_source_hashes" => before_hashes, "after_source_hashes" => after_hashes,
        "measurements" => results, "iteration_checks" => checks); sorted=true)
end
