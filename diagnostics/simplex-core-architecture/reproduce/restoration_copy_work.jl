using JSimplex,Test,TOML,SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
include(joinpath(ROOT,"test/restoration_alias_copy_tests.jl"))
# Intercept only the two cost copy sites in the actual parsed production body.
Core.eval(JS,:(const _rc_copy_count=Ref(0)))
Core.eval(JS,quote
    function _rc_forward!(a,b)
        _rc_copy_count[]+=1
        copyto!(a,b)
    end
end)
function rewrite_cost_copies(ex)
    ex isa Expr || return ex
    ex.head==:call && ex.args[1]==:copyto! && return Expr(:call,:_rc_forward!,ex.args[2:end]...)
    Expr(ex.head,map(rewrite_cost_copies,ex.args)...)
end
src=read(joinpath(ROOT,"src/simplex_perturbation.jl"),String)
pos=only(findall("function restore_perturbations!",src))
ex,_=Meta.parse(src,first(pos));sig=ex.args[1]
sig.head==:(::) && (sig=sig.args[1]);sig.args[1]=:_rc_counted_restore!
ex.args[2]=rewrite_cost_copies(ex.args[2]);Core.eval(JS,ex)
rows=Any[]
function workcases()
 @testset "One copy for proven disjoint identical destination" begin
  for T in (Float16,Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
      mode in (:alias,:detached,:self,:overlap_forward,:overlap_reverse,:inactive,:bounds)
   w,j,backing,events,failure=restoration_alias_fixture(T,mode)
   JS._rc_copy_count[]=0
   GC.@preserve backing Base.invokelatest(JS._rc_counted_restore!,w,j)
   expected=mode==:inactive ? 0 : mode in (:alias,:bounds) ? 1 : 2
   push!(rows,Dict("type"=>string(T),"mode"=>string(mode),"copies"=>JS._rc_copy_count[],"expected"=>expected))
   @test JS._rc_copy_count[]==expected
  end
 end
end
try
 Base.invokelatest(workcases)
finally
 @assert !ispath(only(ARGS))
 open(only(ARGS),"w") do io
  TOML.print(io,Dict("rows"=>rows,"source_sha256"=>bytes2hex(sha256(src)),
       "script_sha256"=>bytes2hex(sha256(read(@__FILE__)))))
 end
end
