using Test,JSimplex
include(joinpath(dirname(dirname(pathof(JSimplex))),"test/legacy_primal_balanced_point_tests.jl"))
include(joinpath(@__DIR__,"working_point_semantics.jl"))
