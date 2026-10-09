using JSimplex,SparseArrays,Serialization,TOML,Statistics,SHA,LinearAlgebra
const JS=JSimplex
function restored_factor(d)
 m=size(d.problem.A,1)
 JS.HuangfuHallFactorization{Float64,Nothing,:native}(d.factor_base,copy(d.factor_updates),zeros(m),zeros(m),zeros(m),zeros(m),false,nothing,JS.HHUnitWorkspace(m,Float64),length(d.factor_updates),JS.HHPool(Float64),JS.HHPool(Float64),JS.HHExtractWorkspace())
end
function measure(file)
 d=deserialize(file);f=restored_factor(d);m,n=size(d.problem.A);rngrhs=sin.(Float64.(1:m));unit=zeros(m);unit[clamp(d.selected_row,1,m)]=1.0;y=zeros(m)
 records=[]
 for mode in (:ftran,:btran),kind in (:unit,:dense)
  rhs=kind==:unit ? unit : rngrhs
  call=mode==:ftran ? JS._ordinary_forward_solve! : JS.transpose_solve!
  call(y,f,rhs);ref=copy(y);times=[];allocs=[]
  for _ in 1:9
   GC.gc();t=@timed for _ in 1:10;call(y,f,rhs);end
   @assert t.compile_time==0 && isequal(y,ref)
   push!(times,t.time/10);push!(allocs,t.bytes/10)
  end
  push!(records,Dict("mode"=>string(mode),"rhs"=>string(kind),"seconds"=>times,"bytes"=>allocs))
 end
 Dict("snapshot"=>file,"sha256"=>bytes2hex(open(sha256,file)),"algorithm"=>string(d.options.algorithm),"iteration"=>d.iteration,"offset"=>d.iteration_offset,"phase"=>string(d.reason),"rows"=>m,"columns"=>n,"updates"=>length(f.updates),"lower_nonzeros"=>nnz(f.base.lower),"upper_nonzeros"=>nnz(f.base.upper),"update_nonzeros"=>sum(t->length(t.u_values)+length(t.v_values),f.updates;init=0),"kernels"=>records)
end
function main(root,out)
 @assert !ispath(out);records=[]
 for (alg,files) in (("primal",("phase_one-first.bin","phase_primal-first.bin","certification-first.bin")),("dual",("phase_auxiliary-first.bin","phase_dual-latest.bin","certification-first.bin")))
  for file in files
   path=joinpath(root,alg,"attempt-1","reports",file);push!(records,measure(path));GC.gc(true)
   println(alg," ",file," iter=",records[end]["iteration"]," updates=",records[end]["updates"]);flush(stdout)
  end
 end
 open(out,"w") do io;TOML.print(io,Dict("snapshots"=>records));end
end
main(ARGS...)
