using Test, JSimplex
reference_path = joinpath(pwd(), "test", "generic_primal_threshold_tests.jl")
source = read(reference_path, String)
parts = split(source, "@testset \"Generic primal thresholds\" begin"; limit=2)
length(parts) == 2 || error("Reference source layout changed")
include_string(Main, first(parts) * "\nend\n", reference_path)
contracts_path = joinpath(pwd(), "test", "primal_ratio_overflow_tests.jl")
contracts = read(contracts_path, String)
occursin("JSimplex._primal_ratio(", contracts) || error("No ratio contracts found")
# Apply the existing explicit expected outcomes to the frozen reference helper.
# Actual pivot/iteration assertions still exercise the unchanged production code.
contracts = replace(contracts, "JSimplex._primal_ratio(" => "GenericPrimalThresholdTests.Reference._primal_ratio(")
@testset "Updated reference overflow contract" begin
    include_string(Main, contracts, contracts_path)
end
