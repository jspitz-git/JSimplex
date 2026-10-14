const LOAD_START=time_ns()
using JSimplex, SparseArrays, TOML
const D=@__DIR__
const ROOT=normpath(joinpath(D,"../../../.."))
const INDEX=parse(Int,ARGS[1]); const SIDE=ARGS[2]; const OUT=ARGS[3]
const OVERLAY=joinpath(ROOT,".superpowers/presolve-exact-cache",SIDE)
realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src/JSimplex.jl")) || error("wrong package source")
include(joinpath(D,"cores.jl"))
const REF=CacheExperiment.reference_reduce
const CAND=CacheExperiment.candidate_reduce
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
function basic(::Type{T},mode) where T
 A=sparse(T[1 1 0;0 1 1;1 2 1])
 lo=mode=="impossible" ? T[1,0,4] : mode=="necessary" ? T[1,0,2] : T[1,0,0]
 up=mode=="impossible" ? [T(2),T(1),nothing] : T[2,1,3]
 LinearProblem(A,ones(T,3);row_lower=lo,row_upper=up)
end
function compare_case(id,p;expected_rows=nothing,failure=false,identity=false)
 b=token(p);h=owners(p);r=REF(p);c=CAND(p);actual=JSimplex.reduce_dependent_rows(p)
 check(id*"_exact",token(r)==token(c)==token(actual))
 check(id*"_input_owners_values",preserved(p,b,h))
 if failure;check(id*"_infeasible",r isa JSimplex.PresolveFailure && r.status==INFEASIBLE)
 elseif expected_rows!==nothing;check(id*"_rows",size(r.problem.A,1)==expected_rows)
 end
 identity && check(id*"_identity",r.problem===p && c.problem===p && actual.problem===p)
 nothing
end
function correctness()
 for T in (Float64,Float32,BigFloat,Q), mode in ("removable","necessary","impossible")
  compare_case(string(T)*"_"*mode,basic(T,mode);expected_rows=mode=="removable" ? 2 : mode=="necessary" ? 3 : nothing,failure=mode=="impossible")
 end
 A=SparseMatrixCSC(2,2,[1,3,5],[1,2,1,2],[-0.0,1.0,0.0,1.0])
 compare_case("stored_signed_zeros",LinearProblem(A,ones(2);row_upper=[0.,2.]);expected_rows=2)
 compare_case("finite_extremes",LinearProblem(sparse([nextfloat(0.0) 0.;0. floatmax(Float64)]),ones(2);row_upper=[1.,1.]);expected_rows=2)
 compare_case("row_cutoff",LinearProblem(spdiagm(0=>ones(257)),ones(257);row_upper=ones(257));identity=true)
 compare_case("nnz_cutoff",LinearProblem(sparse(ones(101,101)),ones(101);row_upper=ones(101));identity=true)
 for v in (Inf,NaN)
  p=basic(Float64,"removable");p.A.nzval[1]=v;b=token(p);h=owners(p)
  errors=map((REF,CAND)) do f
   try;"RETURN:"*repr(token(f(p)));catch e;"THROW:"*string(typeof(e))*":"*sprint(showerror,e);end
  end
  check("nonfinite_"*string(v),errors[1]==errors[2] && preserved(p,b,h))
 end
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
@noinline batch(f,p)=ntuple(_->f(p),Val(4))
function cost_core(id,p)
 b=token(p);h=owners(p);r=REF(p);expected=token(r)
 vals=filter(!iszero,p.A.nzval)
 rec=Dict{String,Any}("id"=>id,"rows"=>size(p.A,1),"columns"=>size(p.A,2),"nnz"=>nnz(p.A),"nonzero_values"=>length(vals),"distinct_values"=>length(unique(vals)),"windows"=>Any[])
 for rep in 1:10
  for side in (isodd(rep+INDEX) ? ("reference","candidate") : ("candidate","reference"))
   f=side=="reference" ? REF : CAND
   t=@timed batch(f,p)
   push!(rec["windows"],merge(metrics(t),Dict("side"=>side,"rep"=>rep,"measured"=>rep>3,"calls"=>4,"outputs_equal"=>all(x->token(x)==expected,t.value),"input_preserved"=>preserved(p,b,h))))
  end
 end
 save("core-"*id*".toml",rec)
 check("core_"*id,all(w->w["outputs_equal"]&&w["input_preserved"]&&(!w["measured"]||(w["compile_seconds"]==0&&w["recompile_seconds"]==0)),rec["windows"]))
end
@noinline public_solve(p,o)=solve(p;options=o)
function cost_public(f,p)
 b=token(p);h=owners(p);o=SolverOptions(Float64;algorithm=Symbol(f["algorithm"]),time_limit=10.,iteration_limit=2000)
 t=@timed public_solve(p,o);r=t.value;sig=signature(r)
 rec=Dict{String,Any}("id"=>f["id"],"side"=>SIDE,"cold"=>metrics(t),"signature"=>repr(sig),"status"=>string(r.status),"objective"=>something(r.objective_value,NaN),"options"=>repr(token(o)),"windows"=>Any[])
 oracle=r.status==OPTIMAL && r.objective_value!==nothing && isapprox(r.objective_value,f["expected"];rtol=1e-7,atol=1e-7)
 if !oracle;save("solve-"*f["id"]*".toml",rec);check("public_oracle_"*f["id"],false);end
 for rep in 1:10
  t=@timed public_solve(p,o)
  push!(rec["windows"],merge(metrics(t),Dict("rep"=>rep,"measured"=>rep>3,"outputs_equal"=>signature(t.value)==sig,"input_preserved"=>preserved(p,b,h))))
 end
 save("solve-"*f["id"]*".toml",rec)
 check("public_"*f["id"],oracle&&all(w->w["outputs_equal"]&&w["input_preserved"]&&(!w["measured"]||(w["compile_seconds"]==0&&w["recompile_seconds"]==0)),rec["windows"]))
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
  correctness()
  config=TOML.parsefile(joinpath(D,"cases.toml"))
  for f in config["cases"]
   p=read_mps(joinpath(ROOT,f["path"]);value_type=Float64)
   cost_core(f["id"],p);cost_public(f,p)
  end
  for kind in ("sparse","dense"), unique in (false,true)
   cost_core(kind*(unique ? "-unique" : "-repeated"),synthetic(kind,unique))
  end
 catch e
  push!(meta["errors"],sprint(showerror,e,catch_backtrace()))
 finally
  CHECKS["ambient_unchanged"]=(precision(BigFloat),rounding(BigFloat))==ambient
  meta["checks"]=CHECKS;meta["all_passed"]=isempty(meta["errors"])&&all(values(CHECKS))
  meta["loaded_paths"]=Dict(string(id)=>realpath(pathof(m)) for (id,m) in Base.loaded_modules if pathof(m)!==nothing)
  save("raw.toml",meta)
 end
 meta["all_passed"] || error("experiment failed; retain raw, no retry")
 println("All ",length(CHECKS)," checks passed; eight paired component cases and four public solves.")
end
main()
