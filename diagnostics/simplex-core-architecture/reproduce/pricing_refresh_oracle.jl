using JSimplex, Test, SparseArrays, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/legacy_primal_preference_work_tests.jl")
const SOURCE=read(FILE,String)
const NODE=only(filter(x->x isa Expr && x.head==:macrocall &&
    x.args[1]==Symbol("@testset") && "Exhaustion after fresh pricing retains the refresh budget" in x.args,
    Meta.parseall(SOURCE).args))
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("source"=>pathof(JSimplex),"test_source_sha256"=>bytes2hex(sha256(SOURCE)),
     "mode"=>"unmodified_oracle_only","julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH)))
end
Core.eval(@__MODULE__,NODE)
