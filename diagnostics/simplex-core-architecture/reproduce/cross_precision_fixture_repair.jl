using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/bigfloat_integrity_tests.jl")
const SOURCE=read(FILE,String)
Base.include_string(@__MODULE__,first(split(SOURCE,"\n@testset")),FILE)
const MODEL_HELPER="function integrity_model_values" * first(split(split(SOURCE,"function integrity_model_values")[2],"\n@testset"))
Base.include_string(@__MODULE__,MODEL_HELPER,FILE)
const TITLE="""@testset "Cross-precision status uses the supplied tolerance" begin"""
const ORIGINAL=TITLE*first(split(split(SOURCE,TITLE)[2],"\n@testset"))
const CONSTRUCTOR="        problem, options = "*first(split(split(ORIGINAL,"        problem, options = ")[2],"        original_values = "))
const INITIAL_PRECISION=precision(BigFloat)
const INITIAL_ROUNDING=rounding(BigFloat)
@testset "Exact infeasibility fixture margin" begin
    Base.include_string(@__MODULE__,"let kind=:primal,interval=1\n"*CONSTRUCTOR*"\nend",FILE)
end
if ARGS[1]=="focused"
    titles=("Cross-precision status uses the supplied tolerance", "BigFloat options retain supplied tolerance values and precision")
    nodes=filter(n->n isa Expr && n.head==:macrocall && n.args[1]==Symbol("@testset") && any(t->t in n.args,titles),Meta.parseall(SOURCE).args)
    @assert length(nodes)==2
    @testset "Cross-precision fixture and supplied options" begin
        for node in nodes;Core.eval(@__MODULE__,node);end
    end
else
    @assert ARGS[1]=="margin"
end
@assert precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING
@assert !ispath(ARGS[2])
open(ARGS[2],"w") do io
    TOML.print(io,Dict("source"=>pathof(JSimplex),"test_sha256"=>bytes2hex(sha256(SOURCE)),
        "complete"=>true,"mode"=>ARGS[1],"globals_restored"=>true,
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
end
