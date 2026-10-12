using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/legacy_primal_direction_price_tests.jl")
const SOURCE=read(FILE,String)
const MODE=ARGS[1]
const OUT=ARGS[2]
const TITLE="A repeated price disagreement cannot renew the recovery budget"
const NEIGHBOR="Native price recovery is atomic and respects policy limits"
function extract(title)
 marker="@testset \""*title*"\" begin"
 marker*first(split(split(SOURCE,marker;limit=2)[2],"\n@testset";limit=2))
end
const TARGET=extract(TITLE)
const RECORDS=Dict[]
function state(ws)
 Dict("primal"=>copy(ws.primal),"costs"=>copy(ws.costs),"basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,"updates"=>length(ws.factorization.updates))
end
const SELECTED=MODE=="red" ? "" : TARGET*(MODE=="green" ? "\n"*extract(NEIGHBOR) : "")
const EXECUTED=replace(SELECTED,
 "        result=JSimplex._primal_iteration!(ws,()->false,0.0)"=>
 "        before=state(ws)\n        result=JSimplex._primal_iteration!(ws,()->false,0.0)\n        push!(RECORDS,Dict(\"manager\"=>string(manager),\"before\"=>before,\"after\"=>state(ws),\"cost\"=>ws.factorization.cost_btrans,\"correction\"=>ws.factorization.correction_btrans,\"total\"=>ws.factorization.total_btrans,\"hits\"=>ws.factorization.hits))")
const PRECISION=precision(BigFloat)
const ROUNDING=rounding(BigFloat)
@assert !ispath(OUT)
try
 if MODE=="red"
  @testset "Repeated price structural contract" begin
   @test occursin("ws=repeated_price_budget_fixture(manager;diagnostics)",TARGET)
   @test occursin("@test ws.factorization.cost_btrans==1",TARGET)
  end
 else
  @assert MODE in ("green","master")
  helper="function native_price_roundoff_fixture"*first(split(split(SOURCE,"function native_price_roundoff_fixture";limit=2)[2],"\n@testset";limit=2))
  adapter="mutable struct RepeatedPriceBudgetFactor"*first(split(split(SOURCE,"mutable struct RepeatedPriceBudgetFactor";limit=2)[2],"\n@testset";limit=2))
  Base.include_string(@__MODULE__,helper*"\n"*adapter,FILE)
  Base.include_string(@__MODULE__,EXECUTED,FILE)
  @testset "Selected state preservation" begin
   @test length(RECORDS)==4
   for rec in RECORDS
    @test rec["before"]==rec["after"]
   end
  end
 end
finally
 open(OUT,"w") do io
  TOML.print(io,Dict("source"=>pathof(JSimplex),"mode"=>MODE,"test_sha256"=>bytes2hex(sha256(SOURCE)),"target"=>TARGET,"selected"=>SELECTED,"executed"=>EXECUTED,"records"=>RECORDS,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>precision(BigFloat)==PRECISION && rounding(BigFloat)==ROUNDING))
 end
end
