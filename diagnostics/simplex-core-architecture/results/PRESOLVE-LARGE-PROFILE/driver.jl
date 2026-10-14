const LOAD_START=time_ns()
using JSimplex, SparseArrays, TOML, SHA
const D=@__DIR__
const ROOT=normpath(joinpath(D,"../../../.."))
const MODEL=ARGS[1]; const OUT=ARGS[2]
const OVERLAY=joinpath(ROOT,".superpowers/presolve-exact-cache/reference")
realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src/JSimplex.jl")) || error("wrong source")
MODEL in ("runtime","medium","test") || error("input not admitted")
Base.include(JSimplex,joinpath(D,"wrapper.jl"))
Base.include(JSimplex,joinpath(D,"controller.jl"))
elapsed()=(time_ns()-LOAD_START)/1e9
function save(name,x)
 path=joinpath(OUT,name);ispath(path)&&error("existing output")
 open(path,"w") do io;TOML.print(io,x);flush(io);end
end
metrics(t)=Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
dims(p)=[size(p.A,1),size(p.A,2),nnz(p.A)]
# Structured streaming hash: no large representation string and no raw struct padding.
function tag!(ctx,s)
 b=codeunits(s);SHA.update!(ctx,reinterpret(UInt8,[UInt64(length(b))]));SHA.update!(ctx,b)
end
function hashvalue!(ctx,x)
 tag!(ctx,string(typeof(x)))
 if x isa AbstractString || x isa Symbol
  tag!(ctx,string(x))
 elseif x === nothing
  return
 elseif x isa Union{Float64,Float32,Integer,Enum}
  SHA.update!(ctx,reinterpret(UInt8,[x]))
 elseif x isa SparseMatrixCSC
  hashvalue!(ctx,size(x));hashvalue!(ctx,x.colptr);hashvalue!(ctx,x.rowval);hashvalue!(ctx,x.nzval)
 elseif x isa AbstractArray
  hashvalue!(ctx,size(x))
  if eltype(x) <: Union{Float64,Float32,Integer,Enum} && isbitstype(eltype(x)) && x isa Array
   SHA.update!(ctx,reinterpret(UInt8,vec(x)))
  elseif eltype(x) == JSimplex.Bound{Float64}
   io=IOBuffer()
   for v in x
    write(io,v.value);write(io,v.bounded)
    position(io)>=65536 && SHA.update!(ctx,take!(io))
   end
   SHA.update!(ctx,take!(io))
  elseif eltype(x) == Union{Nothing,Float64}
   io=IOBuffer()
   for v in x
    write(io,v===nothing)
    v===nothing || write(io,v)
    position(io)>=65536 && SHA.update!(ctx,take!(io))
   end
   SHA.update!(ctx,take!(io))
  else
   for v in x;hashvalue!(ctx,v);end
  end
 else
  for f in fieldnames(typeof(x));hashvalue!(ctx,getfield(x,f));end
 end
 nothing
end
function digest(x)
 ctx=SHA.SHA2_256_CTX();hashvalue!(ctx,x);bytes2hex(SHA.digest!(ctx))
end
function owners(p)
 Any[p.A,p.A.colptr,p.A.rowval,p.A.nzval,
     (getfield(p,f) for f in fieldnames(typeof(p)) if getfield(p,f) isa AbstractArray && f!=:A)...]
end
function preserved(p,b,h)
 now=owners(p)
 digest(p)==b && length(now)==length(h) && all(a===b for (a,b) in zip(now,h))
end
struct BudgetStop <: Exception end
mutable struct Observer
 rep::Int
 serial::Int
end
function (o::Observer)(phase,round,index,current,timed)
 if phase==:start
  elapsed()>=100 && throw(BudgetStop())
  o.serial+=1
  save("start-$(o.rep)-$(o.serial).toml",Dict("rep"=>o.rep,"serial"=>o.serial,"round"=>round,"index"=>index,"input_dimensions"=>dims(current),"elapsed_seconds"=>elapsed()))
 else
  result=timed.value;failed=result isa JSimplex.PresolveFailure
  rec=merge(metrics(timed),Dict{String,Any}("rep"=>o.rep,"serial"=>o.serial,"round"=>round,"index"=>index,"input_dimensions"=>dims(current),"failure"=>failed,"elapsed_seconds"=>elapsed()))
  if failed
   rec["status"]=string(result.status);rec["message"]=result.message
  else
   rec["output_dimensions"]=dims(result[1]);rec["changed"]=result[2]
  end
  save("finish-$(o.rep)-$(o.serial).toml",rec)
 end
end
@noinline profiled(p,o)=JSimplex.profile_large_presolve(p,o)
@noinline public_presolve(p)=JSimplex.presolve_problem(p)
function main()
 meta=Dict{String,Any}("model"=>MODEL,"load_seconds"=>elapsed(),"errors"=>String[],"completed_profiles"=>0,"public_control_completed"=>false,"cooperative_stop"=>false)
 checks=Dict{String,Bool}();p=nothing;b="";held=Any[]
 ambient=(precision(BigFloat),rounding(BigFloat))
 try
  # Hash oracle distinguishes signed zero and bound finiteness, ignores struct padding.
  checks["hash_sensitivity"]=digest([0.])!=digest([-0.]) && digest(JSimplex.Bound{Float64}[JSimplex.Bound(0.)])!=digest(JSimplex.Bound{Float64}[JSimplex.Bound{Float64}(nothing)])
  checks["hash_equal_copy"]=digest([1.,2.])==digest(copy([1.,2.]))
  parsed=@timed read_mps("/home/jspitz/mps/"*MODEL*".mps";value_type=Float64)
  p=parsed.value;meta["parse"]=metrics(parsed);meta["input_dimensions"]=dims(p)
  save("parsed.toml",Dict("model"=>MODEL,"dimensions"=>dims(p),"parse"=>metrics(parsed),"elapsed_seconds"=>elapsed()))
  b=digest(p);held=owners(p);meta["input_sha256"]=b;expected=""
  for rep in 1:3
   elapsed()>=80 && (meta["cooperative_stop"]=true;break)
   o=Observer(rep,0);t=@timed profiled(p,o);result=t.value;sig=digest(result)
   same=isempty(expected)||sig==expected;expected=sig
   ok=preserved(p,b,held)
   checks["profile$(rep)_output_equal"]=same;checks["profile$(rep)_input_preserved"]=ok
   rec=Dict{String,Any}("rep"=>rep,"calls"=>o.serial,"whole_instrumented"=>metrics(t),"signature"=>sig,"result_type"=>string(typeof(result)),"input_preserved"=>ok,"output_equal"=>same)
   if result isa JSimplex.PresolveResult;rec["output_dimensions"]=dims(result.problem);rec["postsolve_steps"]=length(result.postsolve_stack);end
   save("profile-$rep.toml",rec);meta["completed_profiles"]=rep
   result=nothing;t=nothing
   same&&ok || error("profile correctness mismatch")
  end
  if !isempty(expected) && elapsed()<80
   save("public-start.toml",Dict("elapsed_seconds"=>elapsed()))
   t=@timed public_presolve(p);sig=digest(t.value)
   checks["public_output_equal"]=sig==expected;checks["public_input_preserved"]=preserved(p,b,held)
   save("public.toml",Dict("metrics"=>metrics(t),"signature"=>sig,"output_equal"=>checks["public_output_equal"],"input_preserved"=>checks["public_input_preserved"]))
   meta["public_control_completed"]=true
  end
 catch e
  if e isa BudgetStop;meta["cooperative_stop"]=true
  else;push!(meta["errors"],sprint(showerror,e,catch_backtrace()))
  end
 finally
  checks["ambient_unchanged"]=(precision(BigFloat),rounding(BigFloat))==ambient
  if p!==nothing && !isempty(b);checks["final_input_preserved"]=preserved(p,b,held);end
  meta["checks"]=checks;meta["all_passed"]=isempty(meta["errors"])&&all(values(checks));meta["elapsed_seconds"]=elapsed()
  meta["loaded_paths"]=Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if pathof(m)!==nothing)
  save("raw.toml",meta)
 end
 meta["all_passed"] || error("diagnostic failed; no retry")
 println(MODEL," completed profiles: ",meta["completed_profiles"]," public control: ",meta["public_control_completed"])
end
main()
