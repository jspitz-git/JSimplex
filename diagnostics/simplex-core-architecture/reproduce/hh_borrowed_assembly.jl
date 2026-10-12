using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Libdl, Logging
const JS=JSimplex
const checks=Dict{String,Bool}()
const entries=Dict("workspace"=>0,"recompute"=>0,"public_assembly"=>0,"borrowed_explicit"=>0,"copy"=>0,"direct_F"=>0,"direct_B"=>0)
const records=Dict{String,Any}[]
const solves=Dict{String,Any}[]
const report=Dict{String,Any}("source"=>dirname(pathof(JS)),"julia"=>string(VERSION),"arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"precision"=>precision(BigFloat),"rounding"=>string(rounding(BigFloat)),"checks"=>checks,"entries"=>entries,"records"=>records,"solves"=>solves,"complete"=>false)
ck(k,v)=(checks[k]=v;v || error("S4-I gate: "*k);nothing)
bits(v)=string.(reinterpret(UInt64,Float64.(v));base=16,pad=16)
id(x)=string(objectid(x))
matrec(B)=Dict("m"=>size(B,1),"n"=>size(B,2),"colptr"=>copy(B.colptr),"rowval"=>copy(B.rowval),"bits"=>bits(B.nzval))
function val(x)
 if x isa SparseMatrixCSC;matrec(x)
 elseif x isa AbstractVector{Float64};bits(x)
 elseif x isa AbstractVector{<:Integer};copy(x)
 elseif x isa Bool || x isa Integer; x
 elseif x isa Float64;only(bits([x]))
 else;Dict(string(k)=>val(getfield(x,k)) for k in fieldnames(typeof(x)))
 end
end
function factorstate(f)
 Dict("base"=>val(f.base),"base_id"=>id(f.base),"updates_id"=>id(f.updates),"updates"=>[val(x) for x in f.updates],"shared"=>f.shared_update_count,"prepared"=>f.prepared_valid,"partial"=>bits(f.prepared_partial),"direction"=>bits(f.prepared_direction),"partial_id"=>id(f.prepared_partial),"direction_id"=>id(f.prepared_direction),"u_pool_entries"=>f.u_pool.entries,"v_pool_entries"=>f.v_pool.entries,"u_pool_size"=>length(f.u_pool.pairs),"v_pool_size"=>length(f.v_pool.pairs))
end
enc(x::Nothing)="nothing"
enc(x::Bool)=x
enc(x::Integer)=x isa UInt ? string(x) : x
enc(x::Float64)=only(bits([x]))
enc(x::JS.Bound)=isfinite(x) ? only(bits([JS.bound_value(x)])) : string(x)
enc(x::AbstractVector)=[enc(v) for v in x]
enc(x::Union{JS.SolverOptions,JS.NumericalPolicy})=Dict(string(k)=>enc(getfield(x,k)) for k in fieldnames(typeof(x)))
enc(x)=string(x)
function state(ws)
 d=ws.progress.diagnostics
 Dict("basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"mask"=>collect(ws.scratch.basic_mask),"point"=>bits(ws.primal),"rho"=>bits(ws.scratch.rho),"prices"=>bits(ws.reduced_costs),"costs"=>bits(ws.costs),"lower"=>enc(ws.lower),"upper"=>enc(ws.upper),"assembly"=>matrec(ws.scratch.basis_matrix),"array_ids"=>[id(getfield(ws.scratch.basis_matrix,n)) for n in (:colptr,:rowval,:nzval)],"start_ns"=>string(ws.progress.start_ns),"iterations"=>ws.iterations,"refactors"=>ws.refactorizations,"events"=>string.(JS.recent_events(d)),"counts"=>Dict(string(k)=>v for (k,v) in d.counts),"kernels"=>Dict(string(k)=>v for (k,v) in d.kernel_calls),"options"=>enc(ws.options),"policy"=>enc(ws.progress.numerical_policy),"row_scaling"=>bits(ws.progress.scaling.row_factors),"column_scaling"=>bits(ws.progress.scaling.column_factors),"pool_absent"=>isnothing(ws.scratch.pricing_pool),"hyper_absent"=>isnothing(ws.scratch.hypersparse))
end
function setbasis(ws,idx)
 st=fill(JS.AT_LOWER,7);st[idx].=JS.BASIC;ws.basis=JS.Basis(idx,st)
end
function direct(f,B,trans,label)
 entries[trans ? "direct_B" : "direct_F"]+=1;z=zeros(2);rhs=[1.0,2]
 trans ? JS.transpose_solve!(z,f,rhs) : JS.forward_solve!(z,f,rhs)
 M=trans ? transpose(Matrix(B)) : Matrix(B);res=norm(M*z-rhs,Inf);bound=64eps(Float64)*max(1,opnorm(M,Inf)*norm(z,Inf),norm(rhs,Inf))
 push!(solves,Dict("label"=>label,"matrix"=>matrec(B),"transpose"=>trans,"rhs"=>bits(rhs),"solution"=>bits(z),"residual"=>res,"bound"=>bound))
 ck(label*"_residual",all(isfinite,z) && res<=bound)
end
function recompute(ws,candidate)
 entries["recompute"]+=1
 candidate ? JS._s4i_recompute!(ws;refactorize=true) : JS.recompute!(ws;refactorize=true)
end
function lifecycle(candidate)
 side=candidate ? "candidate" : "reference";k=side*"_";r=Dict{String,Any}("side"=>side,"complete"=>false);push!(records,r)
 A=sparse([4.0 1 7 1 2;1 3 1 2 4]);p=LinearProblem(A,Float64[1,2,3,4,5];column_lower=zeros(5),column_upper=fill(Inf,5),row_lower=[1.0,2],row_upper=[1.0,2])
 o=SolverOptions(basis_update=:huangfu_hall,verbose=false,time_limit=30,iteration_limit=20)
 policy=JS.NumericalPolicy(Float64,o);diag=JS.SimplexDiagnostics(kernel_timing=true);progress=JS.SimplexProgressContext(p;diagnostics=diag,numerical_policy=policy)
 model=(matrec(p.A),bits(p.objective),enc(p.row_lower),enc(p.row_upper),enc(p.column_lower),enc(p.column_upper));r["model"]=Dict("A"=>model[1],"objective"=>model[2],"row_lower"=>model[3],"row_upper"=>model[4],"column_lower"=>model[5],"column_upper"=>model[6])
 entries["workspace"]+=1;ws=JS.initialize_workspace(p,o;progress);f=ws.factorization;initial=state(ws);r["initial"]=initial
 ck(k*"policy",!policy.solve_refinement && !policy.recovery && !policy.hypersparse && isnothing(diag.observer) && ws.options.basis_refactorization==:native && ws.options.simplex_strategy==:legacy)
 ck(k*"initial_work",diag.kernel_calls[:ftran]==diag.kernel_calls[:btran]==1 && diag.kernel_calls[:refactorization]==0 && initial["events"]==["refactor_initial"])
 cp=ws.scratch.basis_matrix.colptr;rv=ws.scratch.basis_matrix.rowval;nv=ws.scratch.basis_matrix.nzval
 native=f.refactor_workspace;controls=copy(native.control);r["controls"]=bits(controls)
 ck(k*"initial_owned",all(!Base.mightalias(getfield(native,n),getfield(ws.scratch.basis_matrix,n)) for n in (:colptr,:rowval,:nzval)))
 setbasis(ws,[1,2]);recompute(ws,candidate);r["B1"]=state(ws)
 entries["public_assembly"]+=1;public=JS.basis_matrix(ws);public_before=matrec(public)
 entries["copy"]+=1;saved=JS.copy_basis_factorization(f);saved_before=factorstate(saved)
 ck(k*"public_owned",all(!Base.mightalias(getfield(public,n),getfield(ws.scratch.basis_matrix,n)) for n in (:colptr,:rowval,:nzval)))
 setbasis(ws,[3,2]);entries["borrowed_explicit"]+=1;borrow=JS._basis_matrix!(ws);r["overwritten"]=state(ws)
 ck(k*"actual_overwrite",borrow===ws.scratch.basis_matrix && borrow.colptr===cp && borrow.rowval===rv && borrow.nzval===nv && Matrix(borrow)==[7.0 1;1 3])
 ck(k*"native_before_mutation",native.colptr==[0,2,4] && native.rowval==[0,1,0,1] && native.nzval==[4.0,1,1,3])
 direct(f,public,false,k*"live_B1_after_overwrite");direct(saved,public,true,k*"saved_B1_after_overwrite")
 ns=native.symbolic;nn=native.numeric;recompute(ws,candidate);r["B2"]=state(ws);r["same_pattern_symbolic_same"]=native.symbolic===ns
 ck(k*"symbolic_decision",(native.symbolic===ns)==candidate && native.numeric!==nn && f.refactor_workspace===native)
 ck(k*"same_controls",isequal(controls,native.control))
 setbasis(ws,[6,7]);recompute(ws,candidate);r["slack"]=state(ws)
 ck(k*"actual_shrink",length(rv)==length(nv)==2 && ws.scratch.basis_matrix.colptr===cp && ws.scratch.basis_matrix.rowval===rv && ws.scratch.basis_matrix.nzval===nv && Matrix(ws.scratch.basis_matrix)==[-1.0 0;0 -1])
 setbasis(ws,[4,5]);before=state(ws);fs=factorstate(f);ss=factorstate(saved);r["before_failure"]=before;r["factor_before_failure"]=fs;r["saved_before_failure"]=ss
 exception=nothing
 try;recompute(ws,candidate);catch e;exception=e;end
 after=state(ws);r["after_failure"]=after;r["factor_after_failure"]=factorstate(f);r["saved_after_failure"]=factorstate(saved);r["exception"]=isnothing(exception) ? "none" : string(typeof(exception));r["native_status"]=native.status
 ck(k*"singular",exception isa SingularException && native.status==1 && isnothing(f.refactor_workspace))
 ck(k*"retained_factor",isequal(fs,factorstate(f)) && isequal(ss,factorstate(saved)))
 ck(k*"saved_value_preservation",isequal(saved_before["base"],factorstate(saved)["base"]) && isempty(saved.updates))
 ck(k*"not_workspace_rollback",after["basis"]==[4,5] && after["mask"]==Bool[0,0,0,1,1,0,0] && Matrix(ws.scratch.basis_matrix)==[1.0 2;2 4])
 ck(k*"failure_no_publication",all(isequal(before[n],after[n]) for n in ("point","rho","prices","refactors","iterations","events","counts","start_ns","options","policy","lower","upper","row_scaling","column_scaling")))
 ck(k*"failure_kernel_only",all(after["kernels"][n]-before["kernels"][n]==(n=="refactorization" ? 1 : 0) for n in keys(before["kernels"])))
 ck(k*"total_work",all(v==(n in (:ftran,:btran,:refactorization) ? 4 : 0) for (n,v) in diag.kernel_calls) && ws.refactorizations==3 && ws.iterations==0)
 ck(k*"events",after["events"]==["refactor_initial","refactor_other","refactor_other","refactor_other"])
 ck(k*"owned_public_model",matrec(public)==public_before && model==(matrec(p.A),bits(p.objective),enc(p.row_lower),enc(p.row_upper),enc(p.column_lower),enc(p.column_upper)))
 ck(k*"clock_options_caches",all(isequal(initial[n],after[n]) for n in ("start_ns","options","policy","row_scaling","column_scaling")) && after["pool_absent"] && after["hyper_absent"])
 minus=sparse([-1.0 0;0 -1]);direct(f,minus,false,k*"live_slack_after_failure");direct(f,minus,true,k*"live_slack_transpose_after_failure");direct(saved,public,false,k*"saved_B1_after_failure");direct(saved,public,true,k*"saved_B1_transpose_after_failure")
 r["complete"]=true
end
function main()
 ck("globals",Threads.nthreads()==BLAS.get_num_threads()==1 && precision(BigFloat)==256 && rounding(BigFloat)==RoundNearest && !get_zero_subnormals())
 paths=unique(realpath.(filter(p->occursin("libumfpack",p),Libdl.dllist())));ck("native_one",length(paths)==1);report["native_path"]=only(paths);report["native_sha"]=bytes2hex(sha256(read(only(paths))));libs=TOML.parsefile(ARGS[2])["native_libraries"];ck("native_pin",get(libs,only(paths),"")==report["native_sha"])
 report["clone_sha"]=bytes2hex(sha256(read(ARGS[3])))
 with_logger(NullLogger()) do;lifecycle(false);lifecycle(true);end
 ck("budget",entries==Dict("workspace"=>2,"recompute"=>8,"public_assembly"=>2,"borrowed_explicit"=>2,"copy"=>2,"direct_F"=>6,"direct_B"=>6))
 ck("globals_preserved",Threads.nthreads()==BLAS.get_num_threads()==1 && precision(BigFloat)==256 && rounding(BigFloat)==RoundNearest && !get_zero_subnormals())
 report["complete"]=true
end
Base.include(JS,ARGS[3])
try;main();catch e;report["error"]=sprint(showerror,e);rethrow();finally;open(ARGS[1],"w") do io;TOML.print(io,report);end;println("S4-I ",count(identity,values(checks)),"/",length(checks)," checks ",entries);end
