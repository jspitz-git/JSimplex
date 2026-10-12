using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/dual_pivot_consistency_tests.jl")
const SOURCE=read(FILE,String);const MODE=ARGS[1];const OUT=ARGS[2]
extract(title)=begin
 marker="@testset \""*title*"\" begin"
 marker*first(split(split(SOURCE,marker;limit=2)[2],"\n@testset";limit=2))
end
const TITLES=("Failed dual pivot recovery remains bounded and unpublished","Cancellation after dual refresh cannot publish a pivot")
const PREFIX=first(split(SOURCE,"\n@testset";limit=2))
const SELECTED=join(extract.(TITLES),"\n")*(MODE=="green" ? "\n"*extract("Consistent small dual pivots retain the direct path") : "")
const GLOBALS=(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
const SENTINEL=ErrorException("S6-AI forwarding sentinel")
struct ThrowingDualInner end
JS.forward_solve!(d,::ThrowingDualInner,r)=throw(SENTINEL)
JS._ordinary_forward_solve!(d,::ThrowingDualInner,r)=throw(SENTINEL)
JS.transpose_solve!(d,::ThrowingDualInner,r)=throw(SENTINEL)
JS._unit_transpose_rhs(::ThrowingDualInner,r,row::Int)=throw(SENTINEL)
JS._invalidate_prepared_destination!(::ThrowingDualInner,d)=throw(SENTINEL)
JS.refactorize!(::ThrowingDualInner,B)=throw(SENTINEL)
const MICRO=Dict{String,Any}[]
function microchecks()
 @testset "Pre-forward recovery accounting" begin
  inner=ThrowingDualInner()
  for kind in (:prepared,:ordinary,:unit,:metadata,:invalidate,:refactor,:consumed,:copy,:update)
   f=DualRecoveryFactor(inner);d=zeros(4)
   kind==:consumed && (f.hits=2)
   B=[1.0 1.0 0.0 0.0;1.0-2.0^-23 1.0+2.0^-23 0.0 0.0;0.0 0.0 1.0 0.0;0.0 0.0 0.0 1.0]
   caught=try
    kind==:prepared ? JS.forward_solve!(d,f,collect(dual_recovery_duplicate())) :
    kind==:ordinary ? JS._ordinary_forward_solve!(d,f,collect(dual_recovery_primal_rhs())) :
    kind in (:unit,:consumed) ? JS.transpose_solve!(d,f,collect(dual_recovery_unit())) :
    kind==:metadata ? JS._unit_transpose_rhs(f,collect(dual_recovery_unit()),2) :
    kind==:invalidate ? JS._invalidate_prepared_destination!(f,d) :
    kind==:refactor ? JS.refactorize!(f,B) :
    kind==:copy ? JS.copy_basis_factorization(f) : JS.replace_column!(f,d,2)
    nothing
   catch e;e end
   field=kind in (:prepared,:ordinary) ? :ftran : kind in (:unit,:consumed) ? :btran : kind==:invalidate ? :invalidations : kind==:refactor ? :refactors : kind==:copy ? :copies : kind==:update ? :updates_attempted : :metadata
   expected=kind==:copy ? "Unexpected recovery factor copy" : "Unexpected recovery factor update"
   propagated=kind in (:copy,:update) ? caught isa ErrorException && caught.msg==expected : caught===SENTINEL
   subtype=kind in (:prepared,:ordinary) ? getfield(f,kind)==1 : kind in (:unit,:consumed) ? f.unit==1 : true
   push!(MICRO,Dict("kind"=>string(kind),"propagated"=>propagated,"entry_count"=>getfield(f,field),"subtype"=>subtype,"hits"=>f.hits))
   @test propagated
   @test getfield(f,field)==1 && subtype
   @test f.hits==(kind==:consumed ? 2 : 0)
  end
 end
end
@assert MODE in ("green","master") && !ispath(OUT)
try
 @testset "Dual recovery structural contract" begin
  @test occursin("ws=dual_recovery_budget_workspace(;manager,policy,diagnostics)",extract(TITLES[1]))
  @test occursin("ws=dual_recovery_budget_workspace(;manager,diagnostics)",extract(TITLES[2]))
  @test occursin("function check_dual_recovery_work",PREFIX) && occursin("f.invalidations,f.metadata,f.hits,f.copies,f.updates_attempted",PREFIX)
 end
 Base.include_string(@__MODULE__,PREFIX,FILE)
 Base.include_string(@__MODULE__,SELECTED,FILE)
 MODE=="green" && Base.invokelatest(microchecks)
 @testset "Ambient state preserved" begin
  @test GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
 end
finally
 open(OUT,"w") do io
  TOML.print(io,Dict("source"=>pathof(JS),"mode"=>MODE,"test_sha256"=>bytes2hex(sha256(SOURCE)),"prefix"=>PREFIX,"selected"=>SELECTED,"micro"=>MICRO,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())))
 end
end
