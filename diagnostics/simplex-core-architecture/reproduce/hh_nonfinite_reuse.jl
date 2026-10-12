using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Libdl
const JS=JSimplex
const checks=Dict{String,Bool}()
const entries=Dict("constructor"=>0,"refactor"=>0,"FTRAN"=>0,"BTRAN"=>0)
const records=Dict{String,Any}[]
const solves=Dict{String,Any}[]
const report=Dict{String,Any}("scope"=>"S4-K nonfinite internal HH refactor boundary", "source"=>dirname(pathof(JS)),"julia"=>string(VERSION),"arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"precision"=>precision(BigFloat),"rounding"=>string(rounding(BigFloat)),"checks"=>checks,"entries"=>entries,"records"=>records,"solves"=>solves,"complete"=>false)
function save();open(ARGS[1],"w") do io;TOML.print(io,report);end;end
function ck(k,v);checks[k]=v;v || error("S4-K gate: "*k);end
bits(v)=string.(reinterpret(UInt64,Float64.(v));base=16,pad=16)
matrec(B)=Dict("m"=>size(B,1),"n"=>size(B,2),"colptr"=>copy(B.colptr),"rowval"=>copy(B.rowval),"bits"=>bits(B.nzval))
full(a)=SparseMatrixCSC(2,2,[1,3,5],[1,2,1,2],Float64[a,1,1,3])
id(x)=string(objectid(x))
function value(x)
 if x isa SparseMatrixCSC;return matrec(x)
 elseif x isa AbstractVector{Float64};return bits(x)
 elseif x isa AbstractVector{<:Integer};return copy(x)
 elseif x isa Bool || x isa Integer;return x
 elseif x isa Float64;return only(bits([x]))
 else;return Dict(string(k)=>value(getfield(x,k)) for k in fieldnames(typeof(x)))
 end
end
function pool(p)
 Dict("id"=>id(p),"pairs_id"=>id(p.pairs),"entries"=>p.entries,"pairs"=>[Dict("indices"=>copy(a),"bits"=>bits(b),"index_id"=>id(a),"value_id"=>id(b)) for (a,b) in p.pairs])
end
function snap(f)
 Dict("base"=>value(f.base),"base_id"=>id(f.base),"updates"=>[value(t) for t in f.updates],"updates_id"=>id(f.updates),"shared"=>f.shared_update_count,"prepared_valid"=>f.prepared_valid,"partial"=>bits(f.prepared_partial),"direction"=>bits(f.prepared_direction),"partial_id"=>id(f.prepared_partial),"direction_id"=>id(f.prepared_direction),"u_pool"=>pool(f.u_pool),"v_pool"=>pool(f.v_pool))
end
function retained_solve(f,B,trans,label)
 rhs=[1.0,2];z=zeros(2);entries[trans ? "BTRAN" : "FTRAN"]+=1
 if trans;JS.transpose_solve!(z,f,rhs);else;JS.forward_solve!(z,f,rhs);end
 M=trans ? transpose(Matrix(B)) : Matrix(B)
 residual=norm(M*z-rhs,Inf);bound=64eps(Float64)*max(1,opnorm(M,Inf)*norm(z,Inf),norm(rhs,Inf))
 push!(solves,Dict("label"=>label,"matrix"=>matrec(B),"transpose"=>trans,"rhs_bits"=>bits(rhs),"solution_bits"=>bits(z),"residual"=>residual,"bound"=>bound))
 ck(label*"_residual",all(isfinite,z) && residual<=bound)
end
function onecase(candidate,word,label)
 r=Dict{String,Any}("label"=>label,"candidate"=>candidate,"complete"=>false);push!(records,r)
 B0=full(4);target=full(reinterpret(Float64,word));r["B0"]=matrec(B0);r["target"]=matrec(target)
 ck(label*"_input_bits",reinterpret(UInt64,target.nzval[1])==word && target.colptr==[1,3,5] && target.rowval==[1,2,1,2])
 entries["constructor"]+=1;f=JS.HuangfuHallFactorization(B0)
 native=f.refactor_workspace;ns=native.symbolic;nn=native.numeric;control=copy(native.control)
 r["control_before"]=bits(control);r["before"]=snap(f)
 ck(label*"_owned_inputs",all(!Base.mightalias(getfield(native,n),getfield(target,n)) && !Base.mightalias(getfield(native,n),getfield(B0,n)) && !Base.mightalias(getfield(f.base.lower,n),getfield(target,n)) && !Base.mightalias(getfield(f.base.upper,n),getfield(target,n)) for n in (:colptr,:rowval,:nzval)))
 ck(label*"_default_native",!SparseArrays.UMFPACK._isnull(ns) && control[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP]==0)
 r["pattern_before"]=JS._same_umfpack_pattern(native,target);ck(label*"_pattern",r["pattern_before"])
 err=nothing;entries["refactor"]+=1
 try
  candidate ? JS._s4k_refactorize!(f,target) : JS.refactorize!(f,target)
 catch e
  err=e
 end
 r["exception"]=isnothing(err) ? "none" : string(typeof(err));r["message"]=isnothing(err) ? "none" : sprint(showerror,err)
 r["native_status"]=native.status;r["symbolic_same"]=native.symbolic===ns;r["numeric_same"]=native.numeric===nn
 r["control_after"]=bits(native.control);r["after"]=snap(f);r["discarded"]=isnothing(f.refactor_workspace)
 r["native_after"]=Dict("m"=>native.m,"n"=>native.n,"colptr"=>copy(native.colptr),"rowval"=>copy(native.rowval),"bits"=>bits(native.nzval))
 qualified=err isa SingularException || err isa JS._UnreliableBasisSolve || (err isa ArgumentError && err.msg=="invalid matrix")
 ck(label*"_qualified_rejection",qualified)
 ck(label*"_discarded",r["discarded"])
 ck(label*"_owned_preservation",isequal(r["before"],r["after"]))
 ck(label*"_controls_preserved",isequal(control,native.control))
 ck(label*"_caller_preserved",isequal(r["target"],matrec(target)) && isequal(r["B0"],matrec(B0)))
 retained_solve(f,B0,false,label*"_FTRAN");retained_solve(f,B0,true,label*"_BTRAN")
 r["complete"]=true
end
function main()
 ck("single_threads",Threads.nthreads()==BLAS.get_num_threads()==1)
 prec=precision(BigFloat);rnd=rounding(BigFloat)
 report["clone_sha256"]=bytes2hex(sha256(read(ARGS[3])))
 libs=TOML.parsefile(ARGS[2])["native_libraries"];paths=unique(realpath.(filter(p->occursin("libumfpack",p),Libdl.dllist())))
 ck("one_native_library",length(paths)==1);report["native_path"]=only(paths);report["native_sha256"]=bytes2hex(sha256(read(only(paths))))
 ck("native_pinned",get(libs,only(paths),"")==report["native_sha256"])
 onecase(false,UInt64(0x7ff0000000000000),"inf_reference")
 onecase(true,UInt64(0x7ff0000000000000),"inf_candidate")
 onecase(false,UInt64(0x7ff8000000000000),"nan_reference")
 onecase(true,UInt64(0x7ff8000000000000),"nan_candidate")
 ck("budget",entries==Dict("constructor"=>4,"refactor"=>4,"FTRAN"=>4,"BTRAN"=>4))
 ck("ambient_preserved",precision(BigFloat)==prec && rounding(BigFloat)==rnd && Threads.nthreads()==BLAS.get_num_threads()==1)
 report["complete"]=true;save();println("S4-K complete ",length(checks)," checks; ",entries)
end
Base.include(JS,ARGS[3])
try;main();catch e;report["error"]=sprint(showerror,e);save();rethrow();end
