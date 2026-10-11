# Integration gate: assert actual package source, then existing backend contracts
# and the same exact-output/allocation regression on the integrated checkout.
using JSimplex, Test
@assert realpath(dirname(pathof(JSimplex))) == realpath("/home/jspitz/JSimplex.jl/src")
include(joinpath(dirname(dirname(pathof(JSimplex))),"test","huangfu_hall_markowitz_tests.jl"))
include(joinpath(@__DIR__,"hh_triplet_checks.jl"))
