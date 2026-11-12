module OptionalPresolveOptionsTests

using Test, JSimplex
import MathOptInterface as MOI

const J = JSimplex
const FLAGS = (:presolve_row_sparsification, :presolve_column_merging,
               :presolve_column_dominance)
const COMBINATIONS = [(row, merge, dominance) for row in (false, true),
    merge in (false, true), dominance in (false, true)]

flag_values(options) = ntuple(i -> getfield(options, FLAGS[i]), 3)

function same_options(before, after; changed...)
    for name in fieldnames(typeof(before))
        expected = haskey(changed, name) ? changed[name] : getfield(before, name)
        @test isequal(getfield(after, name), expected)
    end
end

@testset "Optional presolve defaults and positional compatibility" begin
    for T in (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt})
        options = SolverOptions(T)
        @test flag_values(options) === (false, false, false)
        old16 = typeof(options)(ntuple(i -> getfield(options, i), 16)...)
        old17 = typeof(options)(ntuple(i -> getfield(options, i), 17)...)
        same_options(options, old16)
        same_options(options, old17)
        if T <: Rational
            @test iszero(options.primal_tolerance)
            @test iszero(options.dual_tolerance)
            @test iszero(options.zero_tolerance)
        end
    end
    options = SolverOptions(native_pivot_policy=:threshold_one)
    old16 = typeof(options)(ntuple(i -> getfield(options, i), 16)...)
    old17 = typeof(options)(ntuple(i -> getfield(options, i), 17)...)
    same_options(options, old16; native_pivot_policy=:default)
    same_options(options, old17)
    for flags in COMBINATIONS
        full20 = typeof(options)(ntuple(i -> getfield(options, i), 17)..., flags...)
        @test flag_values(full20) === flags
        same_options(options, full20; NamedTuple{FLAGS}(flags)...)
    end
end

@testset "Independent optional presolve switches and recovery copies" begin
    for T in (Float32, Float64, BigFloat), flags in COMBINATIONS, presolve in (false, true)
        options = SolverOptions(T; NamedTuple{FLAGS}(flags)..., presolve,
            primal_tolerance=T(1 // 8), dual_tolerance=T(1 // 16),
            zero_tolerance=T(1 // 32), iteration_limit=79, time_limit=23.0,
            refactorization_interval=7, verbose=false, pricing=:devex,
            simplex_strategy=:adaptive, partial_pricing=true,
            native_pivot_policy=:threshold_one)
        @test flag_values(options) === flags
        same_options(options, SolverOptions(T, options))
        same_options(options, J._phase_options(options, :primal); algorithm=:primal)
        same_options(options, J._remaining_options(options; iterations=3,
            time_limit=19.0, algorithm=:primal); iteration_limit=76,
            time_limit=19.0, algorithm=:primal)
        same_options(options, J._remaining_options(options; iterations=80);
            iteration_limit=0)
        budget = (iteration_limit=31, iterations=4, time_limit_seconds=9.0)
        same_options(options, J._lp_auxiliary_options(options, budget);
            iteration_limit=27, time_limit=9.0, scaling=:off, presolve=false)
        same_options(options, J._copy_precision_options(T, options))
        for S in (Float32, Float64, BigFloat)
            converted = SolverOptions(S, options)
            @test flag_values(converted) === flags
            @test converted.primal_tolerance isa S
            @test isequal(converted.primal_tolerance, convert(S, options.primal_tolerance))
            same_options(converted, J._copy_precision_options(S, options))
        end
    end
end

@testset "Optional flags preserve floating tolerance values" begin
    for T in (Float32, Float64), flags in COMBINATIONS
        defaults = SolverOptions(T)
        options = SolverOptions(T; NamedTuple{FLAGS}(flags)...)
        for name in (:primal_tolerance, :dual_tolerance, :zero_tolerance)
            U = T === Float32 ? UInt32 : UInt64
            @test reinterpret(U, getfield(options, name)) ==
                  reinterpret(U, getfield(defaults, name))
        end
    end
    stored = setprecision(BigFloat, 384) do
        tolerance = BigFloat(1 // 10^7)
        SolverOptions(BigFloat; primal_tolerance=tolerance,
            dual_tolerance=2tolerance, zero_tolerance=tolerance / 1000,
            presolve_row_sparsification=true, presolve_column_merging=true,
            presolve_column_dominance=true)
    end
    setprecision(BigFloat, 128) do
        for copied in (SolverOptions(BigFloat, stored), J._phase_options(stored, :primal),
                J._remaining_options(stored; iterations=1),
                J._lp_auxiliary_options(stored,
                    (iteration_limit=20, iterations=1, time_limit_seconds=2.0)))
            @test flag_values(copied) === (true, true, true)
            for name in (:primal_tolerance, :dual_tolerance, :zero_tolerance)
                @test getfield(copied, name) === getfield(stored, name)
                @test precision(getfield(copied, name)) == 384
            end
        end
    end
    setprecision(BigFloat, 512) do
        copied = J._copy_precision_options(BigFloat, stored)
        @test flag_values(copied) === (true, true, true)
        for name in (:primal_tolerance, :dual_tolerance, :zero_tolerance)
            @test getfield(copied, name) == getfield(stored, name)
            @test precision(getfield(copied, name)) == 512
            @test getfield(copied, name) !== getfield(stored, name)
        end
    end
end

@testset "Optional presolve unsupported scalar rejection" begin
    for T in (Float16, Rational{Int}, Rational{BigInt}), name in FLAGS,
            presolve in (false, true)
        kwargs = NamedTuple{(name,)}((true,))
        @test_throws ArgumentError SolverOptions(T; kwargs..., presolve)
        options = SolverOptions(Float64; kwargs..., presolve)
        @test_throws ArgumentError SolverOptions(T, options)
        @test_throws ArgumentError J._copy_precision_options(T, options)
    end
end

@testset "MOI independent optional presolve attributes" begin
    for T in (Float32, Float64, BigFloat)
        optimizer = J.Optimizer{T}()
        @test flag_values(optimizer) === (false, false, false)
        for name in FLAGS
            attr = MOI.RawOptimizerAttribute(string(name))
            @test MOI.supports(optimizer, attr)
            @test MOI.get(optimizer, attr) === false
            @test_throws ArgumentError MOI.set(optimizer, attr, 1)
            @test_throws ArgumentError MOI.set(optimizer, attr, :on)
        end
        MOI.set(optimizer, MOI.RawOptimizerAttribute("presolve"), false)
        for flags in COMBINATIONS
            for (name, value) in zip(FLAGS, flags)
                MOI.set(optimizer, MOI.RawOptimizerAttribute(string(name)), value)
            end
            @test flag_values(optimizer) === flags
            @test flag_values(J._solver_options(optimizer)) === flags
            @test !J._solver_options(optimizer).presolve
            # Changing unrelated attributes must retain every independent switch.
            MOI.set(optimizer, MOI.TimeLimitSec(), 2.0)
            MOI.set(optimizer, MOI.Silent(), true)
            MOI.empty!(optimizer)
            @test flag_values(J._solver_options(optimizer)) === flags
            @test !J._solver_options(optimizer).presolve
            for (name, value) in zip(FLAGS, flags)
                @test MOI.get(optimizer, MOI.RawOptimizerAttribute(string(name))) === value
            end
        end
        @test flag_values(J.Optimizer{T}()) === (false, false, false)
    end
    for T in (Float16, Rational{Int}, Rational{BigInt})
        optimizer = J.Optimizer{T}()
        for name in FLAGS
            attr = MOI.RawOptimizerAttribute(string(name))
            @test_throws ArgumentError MOI.set(optimizer, attr, true)
            @test MOI.get(optimizer, attr) === false
            @test flag_values(J._solver_options(optimizer)) === (false, false, false)
        end
    end
end

end # module
