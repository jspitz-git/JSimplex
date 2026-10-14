const LOAD_START=time_ns()
using JSimplex, SparseArrays, TOML
const D=@__DIR__
const ROOT=normpath(joinpath(D,"../../../.."))
const INDEX=parse(Int,ARGS[1]); const SIDE=ARGS[2]; const OUT=ARGS[3]
const OVERLAY=joinpath(ROOT,".superpowers/presolve-exact-cache",SIDE)
realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src/JSimplex.jl")) || error("wrong package source")
const Q=Rational{BigInt}
token(x::Union{Float32,Float64})=bitstring(x)
token(x::BigFloat)=(string(Q(x)),precision(x),iszero(x)&&signbit(x))
token(x::Q)=string(x)
token(x::Union{Integer,Enum,Symbol,AbstractString,Nothing})=string(x)
token(x::SparseMatrixCSC)=(size(x),token(x.colptr),token(x.rowval),token(x.nzval))
token(x::AbstractArray)=map(token,x)
token(x)=map(f->token(getfield(x,f)),fieldnames(typeof(x)))
function owners!(a,x)
 if x isa BigInt || x isa BigFloat;push!(a,x)
 elseif x isa SparseMatrixCSC;push!(a,x);owners!(a,x.colptr);owners!(a,x.rowval);owners!(a,x.nzval)
 elseif x isa AbstractArray;push!(a,x);foreach(y->owners!(a,y),x)
 elseif !(x isa Union{Number,Enum,Symbol,AbstractString,Nothing}) || x isa Q
  for f in fieldnames(typeof(x));owners!(a,getfield(x,f));end
 end
 a
end
owners(x)=owners!(Any[],x)
function preserved(p,before,held)
 now=owners(p)
 token(p)==before && length(now)==length(held) && all(a===b for (a,b) in zip(now,held))
end
function metrics(t)
 Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function save(name,x)
 path=joinpath(OUT,name);ispath(path)&&error("existing result")
 open(path,"w") do io;TOML.print(io,x);end
end
const CHECKS=Dict{String,Bool}()
function check(name,v)
 CHECKS[name]=v
 v || error("failed: "*name)
end
function signature(s)
 (string(s.status),token(s.objective_value),token(s.primal),s.statistics.iterations,s.statistics.refactorizations,s.message)
end
function synthetic(kind,unique)
 n=kind=="sparse" ? 24 : 16
 A=zeros(n,n)
 for j in 1:n,i in 1:n
  if kind=="dense" || i==j || i==j+1
   A[i,j]=i==j ? (unique ? 32+(i+17*j)/1024 : 32.) : (unique ? (i+17*j)/1024 : 0.5)
  end
 end
 LinearProblem(sparse(A),ones(n);row_upper=fill(100.,n))
end
@noinline presolve(p)=JSimplex.presolve_problem(p)
function cost_case(id,p)
 b=token(p);h=owners(p)
 t=@timed presolve(p);r=t.value;expected=token(r)
 rec=Dict{String,Any}("id"=>id,"side"=>SIDE,"cold"=>metrics(t),"signature"=>repr(expected),"cold_type"=>string(typeof(r)),"windows"=>Any[],"gc_warmup"=>Any[])
 rec["cold_input_preserved"]=preserved(p,b,h)
 for rep in 1:10
  if rep==4
   # Explicit untimed collection warms finalizer/GC paths; not an explanation
   # of the prior delayed compilation, and not part of steady-call throughput.
   g=@timed GC.gc();push!(rec["gc_warmup"],metrics(g))
  end
  t=@timed presolve(p)
  push!(rec["windows"],merge(metrics(t),Dict("rep"=>rep,"measured"=>rep>3,"outputs_equal"=>token(t.value)==expected,"input_preserved"=>preserved(p,b,h))))
 end
 save("presolve-"*id*".toml",rec)
 check(id,r isa JSimplex.PresolveResult && rec["cold_input_preserved"] && all(w->w["outputs_equal"]&&w["input_preserved"]&&(!w["measured"]||(w["compile_seconds"]==0&&w["recompile_seconds"]==0)),rec["windows"]))
end
function main()
 meta=Dict{String,Any}("index"=>INDEX,"side"=>SIDE,"load_seconds"=>(time_ns()-LOAD_START)/1e9,"errors"=>String[])
 ambient=(precision(BigFloat),rounding(BigFloat))
 try
  check("selected_package",realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src/JSimplex.jl")))
  method=which(JSimplex.reduce_dependent_rows,Tuple{LinearProblem{Float64}})
  meta["method_file"]=string(method.file);meta["method_line"]=method.line
  check("public_method_origin",realpath(string(method.file))==realpath(joinpath(OVERLAY,"src/presolve_dependencies.jl")))
  check("public_method_route",SIDE=="candidate" ? method.sig==Tuple{typeof(JSimplex.reduce_dependent_rows),LinearProblem{Float64}} : method.sig isa UnionAll)
  for f in TOML.parsefile(joinpath(D,"cases.toml"))["cases"]
   cost_case(f["id"],read_mps(joinpath(ROOT,f["path"]);value_type=Float64))
  end
  for kind in ("sparse","dense"), unique in (false,true)
   cost_case(kind*(unique ? "-unique" : "-repeated"),synthetic(kind,unique))
  end
 catch e
  push!(meta["errors"],sprint(showerror,e,catch_backtrace()))
 finally
  CHECKS["ambient_unchanged"]=(precision(BigFloat),rounding(BigFloat))==ambient
  meta["checks"]=CHECKS;meta["all_passed"]=isempty(meta["errors"])&&all(values(CHECKS))
  meta["loaded_paths"]=Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if pathof(m)!==nothing)
  save("raw.toml",meta)
 end
 meta["all_passed"] || error("pipeline experiment failed; no retry")
 println("All ",length(CHECKS)," checks passed; eight whole-presolve cases.")
end
main()
