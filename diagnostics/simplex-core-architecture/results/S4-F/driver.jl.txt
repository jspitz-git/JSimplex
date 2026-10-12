using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Libdl
const JS=JSimplex
const checks=Dict{String,Bool}()
const entries=Dict("setup"=>0,"refactor"=>0,"solve"=>0,"metadata"=>0,"graph"=>0)
const records=Dict{String,Any}[]
const output=ARGS[1]
const report=Dict{String,Any}("scope"=>"S4-F new native component qualification only; no HH/public solver", "source"=>dirname(pathof(JS)),"julia"=>string(VERSION),"arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"entries"=>entries,"checks"=>checks,"records"=>records,"complete"=>false)
function save()
 open(output,"w") do io;TOML.print(io,report);end
end
function ck(k,v)
 checks[k]=v
 v || (save();error("S4-F gate: "*k))
end
bits(v)=string.(reinterpret(UInt64,Float64.(v));base=16,pad=16)
matrec(B)=Dict("m"=>size(B,1),"n"=>size(B,2),"colptr"=>copy(B.colptr),"rowval"=>copy(B.rowval),"bits"=>bits(B.nzval))
function metrics(t)
 Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
full2(a,b,c,d)=SparseMatrixCSC(2,2,[1,3,5],[1,2,1,2],Float64[a,c,b,d])
function fixtures(i)
 if i==1;return full2(4,1,1,3),full2(5,1,1,4),true
 elseif i==2;return full2(1,2,3,4),full2(2.0^-20,2,3,4),true
 elseif i==3;return full2(4,0,1,3),full2(4,2,1,3),true
 elseif i==4;return full2(4,1,1,3),spdiagm(0=>[4.0,3]),false
 elseif i==5;return full2(4,1,1,3),spdiagm(0=>[2.0,3,4]),false
 else;return full2(4,1,1,3),full2(1,2,2,4),true
 end
end
function qualified_side(i,side,B0,B1,reuse_expected)
 key="case$(i)_$(side)_";rec=Dict{String,Any}("case"=>i,"side"=>side,"B0"=>matrec(B0),"B1"=>matrec(B1));push!(records,rec)
 original=copy(B1);entries["setup"]+=1;t=@timed lu(B0);F=t.value;rec["setup_metrics"]=metrics(t)
 controls=copy(F.control);rec["controls_bits"]=bits(controls)
 ck(key*"refinement_disabled",F.control[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP]==0)
 old_symbolic=getfield(F,:symbolic);old_numeric=getfield(F,:numeric)
 ck(key*"valid_initial_symbolic",!SparseArrays.UMFPACK._isnull(old_symbolic))
 pattern=JS._same_umfpack_pattern(F,B1);ck(key*"pattern_expected",pattern==reuse_expected)
 reuse=side=="candidate" && pattern;rec["reuse"]=reuse;rec["pattern"]=pattern
 exception=nothing;entries["refactor"]+=1
 t=@timed try;lu!(F,B1;reuse_symbolic=reuse);catch e;exception=e;nothing;end
 rec["refactor_metrics"]=metrics(t);rec["exception"]=isnothing(exception) ? "none" : string(typeof(exception))
 rec["status"]=F.status;rec["native_after"]=Dict("m"=>F.m,"n"=>F.n,"colptr"=>copy(F.colptr),"rowval"=>copy(F.rowval),"bits"=>bits(F.nzval))
 rec["symbolic_same"]=getfield(F,:symbolic)===old_symbolic;rec["numeric_same"]=getfield(F,:numeric)===old_numeric
 ck(key*"controls_preserved",isequal(F.control,controls))
 ck(key*"symbolic_identity",rec["symbolic_same"]==reuse)
 ck(key*"numeric_rebuilt",!rec["numeric_same"])
 ck(key*"native_owns_target",F.colptr!==B1.colptr && F.rowval!==B1.rowval && F.nzval!==B1.nzval && !Base.mightalias(F.colptr,B1.colptr) && !Base.mightalias(F.rowval,B1.rowval) && !Base.mightalias(F.nzval,B1.nzval))
 ck(key*"native_target",F.m==size(original,1) && F.n==size(original,2) && F.colptr==original.colptr.-1 && F.rowval==original.rowval.-1 && isequal(F.nzval,original.nzval))
 if i==6
  ck(key*"expected_singular",exception isa SingularException)
  rec["failed_candidate_discarded"]=true
  old_symbolic=nothing;old_numeric=nothing;F=nothing
  return rec
 end
 ck(key*"successful_refactor",isnothing(exception) && issuccess(F))
 fill!(B1.nzval,NaN);fill!(B1.rowval,-29)
 entries["metadata"]+=1
 L,U,p,q,s=getproperty(F,Symbol(":"))
 ck(key*"permutations",sort(p)==collect(1:length(p)) && sort(q)==collect(1:length(q)))
 A=Matrix(original);scaled=(s.*A)[p,q];E=Matrix(L*U)-scaled
 bound=64eps(Float64)*max(1,opnorm(L,Inf)*opnorm(U,Inf),opnorm(scaled,Inf))
 rec["factor_bound"]=bound;rec["factor_residual"]=opnorm(E,Inf)
 rec["exact_factor_residual"]=string.(vec(Rational{BigInt}.(Matrix(L))*Rational{BigInt}.(Matrix(U))-(Rational{BigInt}.(s).*Rational{BigInt}.(A))[p,q]))
 ck(key*"fixed_scaling_convention",all(isfinite,E) && opnorm(E,Inf)<=bound)
 rec["L"]=matrec(L);rec["U"]=matrec(U);rec["p"]=p;rec["q"]=q;rec["scaling_bits"]=bits(s)
 rhs=collect(1.0:size(A,1));entries["solve"]+=1;tx=@timed F\rhs;x=tx.value
 entries["solve"]+=1;ty=@timed transpose(F)\rhs;y=ty.value
 rec["forward_metrics"]=metrics(tx);rec["transpose_metrics"]=metrics(ty);rec["x_bits"]=bits(x);rec["y_bits"]=bits(y)
 for (name,M,z) in (("forward",A,x),("transpose",transpose(A),y))
  residual=norm(M*z-rhs,Inf);lim=64eps(Float64)*max(1,opnorm(M,Inf)*norm(z,Inf),norm(rhs,Inf))
  rec[name*"_residual"]=residual;rec[name*"_bound"]=lim
  rec[name*"_exact_residual"]=string.(Rational{BigInt}.(M)*Rational{BigInt}.(z)-Rational{BigInt}.(rhs))
  ck(key*name*"_equation",all(isfinite,z) && residual<=lim)
 end
 ck(key*"borrowed_input_overwrite_safe",F.colptr==original.colptr.-1 && F.rowval==original.rowval.-1 && isequal(F.nzval,original.nzval))
 ck(key*"controls_after_solves",isequal(F.control,controls))
 old_symbolic=nothing;old_numeric=nothing
 entries["graph"]+=1;rec["reachable_julia_bytes"]=Base.summarysize(F)
 rec["native_retained_bytes"]="unavailable; no native memory bound inferred"
 rec
end
function main()
 ck("single_threads",Threads.nthreads()==BLAS.get_num_threads()==1)
 pre=TOML.parsefile(ARGS[2]);paths=String[]
 for path in Libdl.dllist()
  occursin("libumfpack",path) && push!(paths,realpath(path))
 end
 ck("one_native_library",length(unique(paths))==1)
 report["native_path"]=only(unique(paths));report["native_sha256"]=bytes2hex(sha256(read(report["native_path"])))
 ck("native_prelaunch_hash",get(pre["native_libraries"],report["native_path"],"")==report["native_sha256"])
 for i in 1:6
  a,b,expected=fixtures(i);c=copy(a);e=copy(b)
  ck("case$(i)_separate_input_arrays",all(!Base.mightalias(getfield(a,f),getfield(c,f)) && !Base.mightalias(getfield(b,f),getfield(e,f)) for f in (:colptr,:rowval,:nzval)))
  r=qualified_side(i,"reference",a,b,expected);s=qualified_side(i,"candidate",c,e,expected)
  if i<6
   r["paired_equal"]=Dict(k=>isequal(r[k],s[k]) for k in ("L","U","p","q","scaling_bits","x_bits","y_bits"))
  end
  save()
 end
 ck("complete_call_budget",entries==Dict("setup"=>12,"refactor"=>12,"solve"=>20,"metadata"=>10,"graph"=>10))
 ck("record_budget",length(records)==12)
 report["complete"]=true;save()
 println("S4-F completed: ",length(checks)," checks, entries=",entries)
end
try
 main()
catch e
 report["error"]=sprint(showerror,e);save();rethrow()
end
