using JSimplex,Test,TOML,SHA,LinearAlgebra
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/dual_pivot_consistency_tests.jl")
const SOURCE=read(FILE,String)
if ARGS[1]=="red"
    Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),FILE)
    titles=("Failed dual pivot recovery remains bounded and unpublished","Cancellation after dual refresh cannot publish a pivot")
    nodes=filter(x->x isa Expr && x.head==:macrocall && x.args[1]==Symbol("@testset") && any(t->t in x.args,titles),Meta.parseall(SOURCE).args)
    @assert length(nodes)==2
    @testset "Original public calls miss explicit retry boundary" begin
        for n in nodes;Core.eval(@__MODULE__,n);end
    end
else
    @assert ARGS[1]=="focused"
    include(FILE)
end
@assert !ispath(ARGS[2])
open(ARGS[2],"w") do io
    TOML.print(io,Dict("source"=>pathof(JSimplex),"test_sha256"=>bytes2hex(sha256(SOURCE)),"complete"=>true,
       "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
end
