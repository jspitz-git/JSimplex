using Test,JSimplex
root=dirname(dirname(pathof(JSimplex)))
# Keep the allocation assertions intact, but run their entire testsets with
# normal compilation. Interpreter overhead is not a basis-manager allocation.
allocation_sets=Set(("Markowitz backend retains sparse storage and solve buffers",
    "Dense Markowitz input avoids a sparse staging copy",
    "Markowitz threshold respects stored BigFloat precision"))
mode=only(ARGS)
mode in ("semantic","compiled") || error("Expected semantic or compiled")
@testset "HH Markowitz $mode" begin
    files=mode=="compiled" ? ("huangfu_hall_tests.jl",) :
        ("huangfu_hall_precision_tests.jl","huangfu_hall_markowitz_tests.jl",
         "huangfu_hall_option_tests.jl","huangfu_hall_integration_tests.jl",
         "huangfu_hall_scalar_integration_tests.jl")
    for file in files
        include(joinpath(root,"test",file))
    end
    # Retain helper definitions and select complete top-level testsets.
    select = ex -> if ex isa Expr && ex.head === :macrocall && ex.args[1] === Symbol("@testset")
        name=ex.args[3]
        (name in allocation_sets)==(mode=="compiled") ? ex : nothing
    else
        ex
    end
    include(select,joinpath(root,"test/markowitz_tests.jl"))
end
