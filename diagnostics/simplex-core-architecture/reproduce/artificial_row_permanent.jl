using JSimplex, Test, TOML, SHA, LinearAlgebra
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/native_artificial_row_tests.jl")
const SOURCE=read(FILE,String)
if ARGS[1]=="red"
    Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),FILE)
    title="Artificial-row recovery respects budgets and preserves the original on cancellation"
    node=only(filter(x->x isa Expr && x.head==:macrocall && x.args[1]==Symbol("@testset") && title in x.args,Meta.parseall(SOURCE).args))
    Core.eval(@__MODULE__,node)
else
    @assert ARGS[1]=="focused"
    include(FILE)
end
@assert !ispath(ARGS[2])
open(ARGS[2],"w") do io
 TOML.print(io,Dict("source"=>pathof(JSimplex),"test_sha256"=>bytes2hex(sha256(SOURCE)),
   "complete"=>true,"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
end
