# Run the existing cleanup-pricing assertion identically on either source tree.
using JSimplex,Test,SparseArrays,LinearAlgebra
path=joinpath(dirname(dirname(pathof(JSimplex))),"test","dual_simplex_tests.jl")
source=read(path,String)
first_index=first(findfirst("@testset \"Original costs are optimized from a perturbed primal-feasible basis\"",source))
last_index=first(findnext("\n@testset",source,first_index+1))-1
Base.include_string(Main,source[first_index:last_index],path)
