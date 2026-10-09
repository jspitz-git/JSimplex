# Diagnostic statement attribution on identical, recorded column histories.
using JSimplex,SparseArrays,LinearAlgebra,Serialization,TOML,Statistics,SHA
const JS=JSimplex
const LABELS=String[]
@eval JS begin
 const _kp_calls=zeros(Int,256);const _kp_ns=zeros(UInt64,256);const _kp_exclusive=zeros(UInt64,256)
 const _kp_child=zeros(UInt64,64);const _kp_depth=Ref(0)
 @inline function _kp_start()
  d=(_kp_depth[]+=1);_kp_child[d]=0;(time_ns(),d)
 end
 @inline function _kp_end(id,t)
  start,d=t;elapsed=time_ns()-start;_kp_calls[id]+=1;_kp_ns[id]+=elapsed
  _kp_exclusive[id]+=elapsed-_kp_child[d]
  d>1&&(_kp_child[d-1]+=elapsed);_kp_depth[]-=1;nothing
 end
 function _kp_reset()
  fill!(_kp_calls,0);fill!(_kp_ns,0);fill!(_kp_exclusive,0);@assert _kp_depth[]==0
 end
end
function instrument(name,file,matchtext="")
 s=read(joinpath(dirname(pathof(JS)),file),String);offset=1;chosen=nothing
 while true
  at=findnext("function "*string(name)*"(",s,offset);isnothing(at)&&break
  ex,offset=Meta.parse(s,first(at))
  if occursin(matchtext,string(ex.args[1]));chosen=ex;break;end
 end
 @assert !isnothing(chosen) (name,matchtext)
 body=chosen.args[2];statements=Any[]
 # Keep function-level bindings when statements are wrapped in try scopes.
 locals=Symbol[]
 for stmt in body.args
  stmt isa Expr && stmt.head==:(=) && stmt.args[1] isa Symbol && push!(locals,stmt.args[1])
 end
 isempty(locals)||push!(statements,Expr(:local,unique(locals)...))
 for stmt in body.args
  if stmt isa LineNumberNode;push!(statements,stmt);continue;end
  push!(LABELS,string(name)*":"*first(replace(string(stmt),'\n'=>' '),220));id=length(LABELS);token=gensym(:token)
  push!(statements,quote
   local $token=_kp_start()
   try;$stmt;finally;_kp_end($id,$token);end
  end)
 end
 chosen.args[2]=Expr(:block,statements...);Core.eval(JS,chosen)
end
function install()
 for (n,f,m) in ((:forward_solve!,"factorization.jl","StridedVector"),(:transpose_solve!,"factorization.jl","PFIFactorization"),
 (:_triangular_forward_solve!,"triangular_factorization.jl","StridedVector"),(:_finish_triangular_forward!,"triangular_factorization.jl",""),
 (:transpose_solve!,"triangular_factorization.jl","AbstractTriangularBasisFactorization"),(:_finish_triangular_transpose!,"triangular_factorization.jl",""),
 (:_hh_forward!,"huangfu_hall_factorization.jl",""),(:transpose_solve!,"huangfu_hall_factorization.jl","HuangfuHallFactorization"))
  instrument(n,f,m)
 end
end
function fillcolumn!(rhs,A,col)
 fill!(rhs,0.0);for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end;rhs
end
function runbatch(f,fac,y,rhs,n)
 for _ in 1:n;f(y,fac,rhs);end
end
function measure(fac,A,basis,entering,row,label,chain,instrumented)
 m=length(basis);rhs=zeros(m);y=zeros(m);records=[];B=A[:,basis]
 for mode in (:ftran,:btran),kind in (mode==:ftran ? (:entering,:dense) : (:unit,:dense))
  kind==:entering ? fillcolumn!(rhs,A,entering) : kind==:unit ? (fill!(rhs,0);rhs[row]=1) : (rhs .= sin.(Float64.(1:m)))
  f=mode==:ftran ? JS._ordinary_forward_solve! : JS.transpose_solve!
  f(y,fac,rhs);reference=copy(y)
  residual=norm((mode==:ftran ? B*y : transpose(B)*y)-rhs,Inf)/(opnorm(B,mode==:ftran ? Inf : 1)*norm(y,Inf)+norm(rhs,Inf))
  @assert isfinite(residual)&&residual<1e-8
  runbatch(f,fac,y,rhs,5);ts=Float64[];bs=Int[];JS._kp_reset()
  for round in 1:9
   GC.gc();t=@timed runbatch(f,fac,y,rhs,10);@assert t.compile_time==0&&isequal(y,reference)
   push!(ts,t.time/10);push!(bs,t.bytes÷10)
  end
  parts=[Dict("statement"=>LABELS[i],"calls_per_solve"=>JS._kp_calls[i]/90,"inclusive_seconds_per_solve"=>JS._kp_ns[i]/90e9,"exclusive_seconds_per_solve"=>JS._kp_exclusive[i]/90e9) for i in eachindex(LABELS) if JS._kp_calls[i]>0]
  push!(records,Dict("mode"=>string(mode),"rhs"=>string(kind),"rhs_nonzeros"=>count(!iszero,rhs),"solution_nonzeros"=>count(!iszero,y),"seconds"=>ts,"bytes"=>bs,"residual"=>residual,"parts"=>parts,"result_hash"=>bytes2hex(sha256(reinterpret(UInt8,y)))))
 end
 storage=fac isa JS.HuangfuHallFactorization ? sum(t->length(t.u_values)+length(t.v_values),fac.updates;init=0) : fac isa JS.PFIFactorization ? sum(t->length(t.values),fac.updates;init=0) : sum(c->length(c.values),fac.upper;init=0)+sum(JS._update_storage_count,fac.updates;init=0)
 Dict("manager"=>label,"chain"=>chain,"rows"=>m,"basis_nonzeros"=>nnz(B),"update_storage"=>storage,"factor_bytes"=>Base.summarysize(fac),"kernels"=>records,"instrumented"=>instrumented)
end
function main(out,instrumented)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 records=[]
 for history in ("runtime-40000","fast0507-1000")
  file="/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/histories/"*history*".bin"
  data=deserialize(file);@assert bytes2hex(open(sha256,data.input))==data.input_sha256
  A=hcat(data.A,spdiagm(0=>-ones(size(data.A,1))))
  for (label,F) in (("pfi",JS.PFIFactorization),("ft",JS.ForrestTomlinFactorization),("ss",JS.SuhlSuhlFactorization),("bg",JS.BartelsGolubFactorization),("hh",JS.HuangfuHallFactorization))
   basis=copy(data.basis);construct=@timed F(A[:,basis]);fac=construct.value;rhs=zeros(length(basis));direction=similar(rhs)
   for k in 0:320
    if k>0
     row,entering=data.steps[k];fillcolumn!(rhs,A,entering)
     JS.forward_solve!(direction,fac,rhs);JS.replace_column!(fac,direction,row;zero_tolerance=SolverOptions().zero_tolerance);basis[row]=entering
    end
    if k in (0,80,320)
     row,entering=data.steps[k+1]
     r=measure(fac,A,basis,entering,row,label,k,instrumented);r["history"]=history;r["history_sha256"]=bytes2hex(open(sha256,file));r["constructor_seconds"]=construct.time;r["constructor_compile_seconds"]=construct.compile_time
     push!(records,r);println(history," ",label," chain=",k," storage=",r["update_storage"]);flush(stdout)
     open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
    end
   end
   GC.gc(true)
  end
 end
end
instrumented=length(ARGS)>1&&ARGS[2]=="instrumented"
instrumented&&install()
Base.invokelatest(main,ARGS[1],instrumented)
