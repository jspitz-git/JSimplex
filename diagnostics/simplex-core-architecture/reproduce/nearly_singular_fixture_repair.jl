using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/solver_tests.jl")
const SOURCE=read(FILE,String)
const MODE=ARGS[1]
const OUT=ARGS[2]
const TITLE="A nearly singular bounded model has no recession ray"
const TITLES=[TITLE,"Floating status certificates reject unresolved roundoff","Rounded dependent rows cannot certify a feasible primal origin","Original objective cancellation cannot certify a false optimum"]
function extract(title)
 marker="@testset \""*title*"\" begin"
 tail=split(SOURCE,marker;limit=2)[2]
 marker*first(split(tail,"\n@testset";limit=2))
end
const SELECTED=if MODE=="red"
 first(split(extract(TITLE),"    for T in (Float32, Float64, BigFloat, Rational{BigInt})";limit=2))*"end\n"
elseif MODE=="green"
 join(extract.(TITLES),"\n")
elseif MODE=="master"
 extract(TITLE)
else
 error("unknown mode")
end
MODE=="red" && @assert !occursin("solve(",SELECTED)
const INITIAL_PRECISION=precision(BigFloat)
const INITIAL_ROUNDING=rounding(BigFloat)
@assert !ispath(OUT)
try
 Base.include_string(@__MODULE__,SELECTED,FILE)
finally
 open(OUT,"w") do io
  TOML.print(io,Dict("source"=>pathof(JSimplex),"mode"=>MODE,
   "test_sha256"=>bytes2hex(sha256(SOURCE)),"selected_sha256"=>bytes2hex(sha256(SELECTED)),
   "selected_source"=>SELECTED,"titles"=>MODE=="green" ? TITLES : [TITLE],
   "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
   "globals_preserved"=>precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING))
 end
end
