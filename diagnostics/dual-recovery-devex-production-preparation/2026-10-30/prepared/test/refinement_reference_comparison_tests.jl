# Frozen legacy numerical comparison; include after refinement_outcome_tests.jl.
# Test-only references; no whole-module clone or production method overwrite.
module RefinementReferenceComparison
using Test
using JSimplex
import ..RefinementOutcomeTests
const R = RefinementOutcomeTests
const J = JSimplex
include("support/devex_refinement_reference.jl")
function compare(sc,transposed)
    reference=R.exercise(RefinementReference.refine_basis_solve!,sc,transposed)
    ordinary=R.exercise(J.refine_basis_solve!,sc,transposed)
    detailed=R.exercise(J._refine_basis_solve_outcome!,sc,transposed)
    R.same_execution(reference,ordinary)
    R.same_execution(reference,detailed)
    @test reference.f.stop.calls==sc.stops
    @test reference.f.factor.forwards+reference.f.factor.backwards==sc.calls
    if isnothing(reference.failure)
        @test isnothing(ordinary.failure) && isnothing(detailed.failure)
        @test isequal(R.quality_fields(reference.value),R.quality_fields(ordinary.value))
        @test isequal(R.quality_fields(reference.value),R.quality_fields(detailed.value.quality))
    elseif sc.observer_reason==:never
        @test reference.failure===sc.failure && ordinary.failure===sc.failure && detailed.failure===sc.failure
    else
        @test reference.failure isa J.DiagnosticObserverFailure
        @test reference.failure.cause===sc.failure && ordinary.failure.cause===sc.failure && detailed.failure.cause===sc.failure
    end
end
function runtests()
    @testset "Original source and candidate have the same numeric execution" begin
        for T in (Float32,Float64),transposed in (false,true)
            names=T===Float64 ? (R.SIMPLE_CASES...,:nonfinite_wide_quality,:stop_before_wide) : R.SIMPLE_CASES
            for name in names
                compare(R.scenario(name,T),transposed)
            end
        end
        for T in (BigFloat,Rational{BigInt}),transposed in (false,true)
            compare(R.scenario(:reliable,T),transposed)
        end
    end
end
end
Base.invokelatest(RefinementReferenceComparison.runtests)
