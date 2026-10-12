using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Libdl
const JS=JSimplex
const out=ARGS[1]
const checks=Dict{String,Bool}()
const entries=Dict("constructor"=>0,"copy"=>0,"update"=>0,"refactor"=>0,"FTRAN"=>0,"BTRAN"=>0)
const records=Dict{String,Any}[]
const solves=Dict{String,Any}[]
const report=Dict{String,Any}("scope"=>"S4-G two HH lifecycles only; diagnostic candidate source clone", "source"=>dirname(pathof(JS)),"julia"=>string(VERSION),"arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"precision"=>precision(BigFloat),"rounding"=>string(rounding(BigFloat)),"checks"=>checks,"entries"=>entries,"records"=>records,"solves"=>solves,"complete"=>false)
function save();open(out,"w") do io;TOML.print(io,report);end;end
function ck(k,v);checks[k]=v;v || (save();error("S4-G gate: "*k));end
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
function history(f);[value(t) for t in f.updates];end
function pool(p);Dict("entries"=>p.entries,"pairs"=>[Dict("indices"=>copy(a),"bits"=>bits(b),"index_id"=>id(a),"value_id"=>id(b)) for (a,b) in p.pairs]);end
function snap(f)
 Dict("base"=>value(f.base),"base_id"=>id(f.base),"updates"=>history(f),"updates_id"=>id(f.updates),"record_ids"=>id.(f.updates),"shared"=>f.shared_update_count,"prepared_valid"=>f.prepared_valid,"partial"=>bits(f.prepared_partial),"direction"=>bits(f.prepared_direction),"partial_id"=>id(f.prepared_partial),"direction_id"=>id(f.prepared_direction),"u_pool"=>pool(f.u_pool),"v_pool"=>pool(f.v_pool))
end
function solvecheck(f,B,rhs,trans,label)
 entries[trans ? "BTRAN" : "FTRAN"]+=1
 z=zeros(2)
 if trans;JS.transpose_solve!(z,f,rhs);else;JS.forward_solve!(z,f,rhs);end
 M=trans ? transpose(Matrix(B)) : Matrix(B)
 res=norm(M*z-rhs,Inf);bound=64eps(Float64)*max(1,opnorm(M,Inf)*norm(z,Inf),norm(rhs,Inf))
 push!(solves,Dict("label"=>label,"matrix"=>matrec(B),"transpose"=>trans,"rhs_bits"=>bits(rhs),"solution_bits"=>bits(z),"residual"=>res,"bound"=>bound,"exact_residual"=>string.(Rational{BigInt}.(M)*Rational{BigInt}.(z)-Rational{BigInt}.(rhs))))
 ck(label*"_fixed_residual",all(isfinite,z) && res<=bound)
 z
end
function upd(f,B,rhs,label)
 z=solvecheck(f,B,rhs,false,label)
 ck(label*"_genuine_prepared",f.prepared_valid && isequal(z,f.prepared_direction))
 entries["update"]+=1;JS.replace_column!(f,z,1)
 ck(label*"_consumed",!f.prepared_valid)
end
function refact(f,B,candidate)
 entries["refactor"]+=1
 candidate ? JS._s4g_refactorize!(f,B) : JS.refactorize!(f,B)
end
function lifecycle(candidate)
 side=candidate ? "candidate" : "reference";k=side*"_"
 r=Dict{String,Any}("side"=>side);push!(records,r)
 B0=full(4);B1=full(5);B2=full(6);B3=full(7);B4=full(8)
 r["matrices"]=Dict("B$(i-1)"=>matrec(B) for (i,B) in enumerate((B0,B1,B2,B3,B4)))
 entries["constructor"]+=1;f=JS.HuangfuHallFactorization(B0)
 native=f.refactor_workspace;old_symbolic=getfield(native,:symbolic);old_numeric=getfield(native,:numeric);controls=copy(native.control)
 r["control_bits"]=bits(controls)
 ck(k*"initial_native",!SparseArrays.UMFPACK._isnull(old_symbolic) && controls[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP]==0)
 upd(f,B0,[5.0,1],k*"update1")
 entries["copy"]+=1;s=JS.copy_basis_factorization(f)
 shared=s.updates[1];base0=s.base
 ck(k*"saved_shared",s.base===f.base && s.updates!==f.updates && s.updates[1]===f.updates[1] && f.shared_update_count==s.shared_update_count==1)
 ck(k*"saved_private",isnothing(s.refactor_workspace) && all(getfield(s,n)!==getfield(f,n) && !Base.mightalias(getfield(s,n),getfield(f,n)) for n in (:work,:auxiliary,:prepared_partial,:prepared_direction)) && s.extract_workspace!==f.extract_workspace && s.unit_workspace!==f.unit_workspace && s.u_pool!==f.u_pool && s.v_pool!==f.v_pool)
 upd(f,B1,[6.0,1],k*"update2")
 private=f.updates[2];saved_before=snap(s);r["saved_before_success"]=saved_before
 ck(k*"private_suffix",length(f.updates)==2 && f.shared_update_count==1 && length(s.updates)==1 && f.updates[1]===shared)
 solvecheck(f,B2,[1.0,2],false,k*"live_B2_before_success")
 r["live_before_success"]=snap(f)
 ck(k*"prepared_before_success",f.prepared_valid)
 expectedB3=copy(B3);refact(f,B3,candidate)
 r["live_after_success"]=snap(f);r["saved_after_success"]=snap(s)
 ck(k*"success_publish",f.base!==base0 && isempty(f.updates) && f.shared_update_count==0 && !f.prepared_valid)
 ck(k*"saved_unchanged_success",isequal(saved_before,snap(s)) && s.base===base0 && s.updates[1]===shared)
 ck(k*"private_retired",length(f.u_pool.pairs)==length(f.v_pool.pairs)==1 && f.u_pool.pairs[1][1]===private.u_indices && f.u_pool.pairs[1][2]===private.u_values && f.v_pool.pairs[1][1]===private.v_indices && f.v_pool.pairs[1][2]===private.v_values)
 ck(k*"shared_not_retired",all(a!==shared.u_indices && b!==shared.u_values for (a,b) in f.u_pool.pairs) && all(a!==shared.v_indices && b!==shared.v_values for (a,b) in f.v_pool.pairs))
 r["success_symbolic_same"]=native.symbolic===old_symbolic;r["success_numeric_same"]=native.numeric===old_numeric
 ck(k*"native_identity",f.refactor_workspace===native && r["success_symbolic_same"]==candidate && !r["success_numeric_same"])
 ck(k*"controls_success",isequal(native.control,controls))
 ck(k*"caller_not_aliased",all(!Base.mightalias(getfield(native,n),getfield(B3,n)) && !Base.mightalias(getfield(f.base.lower,n),getfield(B3,n)) && !Base.mightalias(getfield(f.base.upper,n),getfield(B3,n)) for n in (:colptr,:rowval,:nzval)))
 fill!(B3.nzval,NaN);fill!(B3.rowval,-29);fill!(B3.colptr,-31)
 ck(k*"native_after_poison",native.colptr==expectedB3.colptr.-1 && native.rowval==expectedB3.rowval.-1 && isequal(native.nzval,expectedB3.nzval))
 solvecheck(f,expectedB3,[1.0,2],true,k*"live_B3_transpose")
 solvecheck(s,B1,[1.0,2],false,k*"saved_B1_forward_success")
 solvecheck(s,B1,[1.0,2],true,k*"saved_B1_transpose_success")
 upd(f,expectedB3,[8.0,1],k*"update3")
 solvecheck(f,B4,[1.0,3],false,k*"prepare_before_failure")
 ck(k*"valid_before_failure",f.prepared_valid)
 before=snap(f);saved_failure=snap(s);r["live_before_failure"]=before;r["saved_before_failure"]=saved_failure
 oldbase=f.base;oldhistory=copy(f.updates);pp=f.prepared_partial;pd=f.prepared_direction;ns=native.symbolic;nn=native.numeric
 singular=SparseMatrixCSC(2,2,[1,3,5],[1,2,1,2],[1.0,2,2,4]);exception=nothing
 try;refact(f,singular,candidate);catch e;exception=e;end
 r["exception"]=isnothing(exception) ? "none" : string(typeof(exception));r["failure_status"]=native.status
 r["failure_symbolic_same"]=native.symbolic===ns;r["failure_numeric_same"]=native.numeric===nn
 r["live_after_failure"]=snap(f);r["saved_after_failure"]=snap(s)
 ck(k*"expected_singular",exception isa SingularException && native.status==1)
 ck(k*"failed_backend_discard",isnothing(f.refactor_workspace) && (native.symbolic===ns)==candidate && native.numeric!==nn)
 ck(k*"failed_state_owned_values",isequal(before,snap(f)) && isequal(saved_failure,snap(s)))
 ck(k*"failed_state_identities",f.base===oldbase && all(a===b for (a,b) in zip(f.updates,oldhistory)) && f.prepared_partial===pp && f.prepared_direction===pd && s.base===base0 && s.updates[1]===shared)
 ck(k*"controls_failure",isequal(native.control,controls))
 solvecheck(f,B4,[1.0,2],false,k*"live_B4_forward_failure")
 solvecheck(f,B4,[1.0,2],true,k*"live_B4_transpose_failure")
 solvecheck(s,B1,[1.0,2],false,k*"saved_B1_forward_failure")
 solvecheck(s,B1,[1.0,2],true,k*"saved_B1_transpose_failure")
 r["complete"]=true
end
function main()
 ck("single_threads",Threads.nthreads()==BLAS.get_num_threads()==1)
 initial_precision=precision(BigFloat);initial_rounding=rounding(BigFloat)
 clone=ARGS[3];report["clone_sha256"]=bytes2hex(sha256(read(clone)))
 libs=TOML.parsefile(ARGS[2])["native_libraries"];paths=unique(realpath.(filter(p->occursin("libumfpack",p),Libdl.dllist())))
 ck("one_native_library",length(paths)==1);report["native_path"]=only(paths);report["native_sha256"]=bytes2hex(sha256(read(only(paths))))
 ck("native_pinned",get(libs,only(paths),"")==report["native_sha256"])
 lifecycle(false);save();lifecycle(true)
 ck("budget",entries==Dict("constructor"=>2,"copy"=>2,"update"=>6,"refactor"=>4,"FTRAN"=>16,"BTRAN"=>8))
 ck("ambient_preserved",precision(BigFloat)==initial_precision && rounding(BigFloat)==initial_rounding && Threads.nthreads()==BLAS.get_num_threads()==1)
 report["implicit_native_scale_solves_upper_bound"]=4;report["implicit_native_scale_solves_observed"]="not instrumented"
 report["complete"]=true;save();println("S4-G complete ",length(checks)," checks; ",entries)
end
Base.include(JS,ARGS[3])
try;main();catch e;report["error"]=sprint(showerror,e);save();rethrow();end
