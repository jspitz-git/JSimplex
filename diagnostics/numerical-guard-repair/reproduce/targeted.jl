using JSimplex, Test
const ROOT = dirname(dirname(pathof(JSimplex)))
@testset "Complementarity certificate regressions" begin
    for file in ("native_complementarity_rows_tests.jl", "native_certificate_recovery_tests.jl",
                 "exact_primal_rows_tests.jl", "certification_allocation_tests.jl")
        include(joinpath(ROOT, "test", file))
    end
end
