# Throwaway locality prototype: never installed as a production method.
using JSimplex,SparseArrays,LinearAlgebra,Serialization,Random,Statistics,TOML
const JS=JSimplex
function rowindex(A)
 m,n=size(A);ptr=ones(Int,m+1)
 for r in A.rowval;ptr[r+1]+=1;end
 ptr[1]=1
 for r in 1:m;ptr[r+1]+=ptr[r]-1;end
 cursor=copy(ptr);pos=Vector{Int}(undef,nnz(A));cols=similar(pos)
 for c in 1:n,p in nzrange(A,c)
  r=A.rowval[p];k=cursor[r];pos[k]=p;cols[k]=c;cursor[r]+=1
 end
 (ptr,pos,cols)
end
function rowwise!(lo,hi,A,x,index)
 ptr,pos,cols=index;T=eltype(x)
 for r in eachindex(lo)
  l=h=zero(T)
  for k in ptr[r]:ptr[r+1]-1
   pl,ph=JS._primal_product_bounds(A.nzval[pos[k]],x[cols[k]])
   l,_=JS._primal_sum_bounds(l,pl);_,h=JS._primal_sum_bounds(h,ph)
  end
  lo[r]=l;hi[r]=h
 end
 lo,hi
end
baseline!(lo,hi,A,x,index)=JS._primal_row_bounds!(lo,hi,A,x)
function batch(f,lo,hi,A,x,index,n)
 for _ in 1:n;f(lo,hi,A,x,index);end
 nothing
end
function measure(name,A,x)
 build=@timed rowindex(A);index=build.value
 setup_seconds=Float64[];setup_bytes=Int[]
 for _ in 1:5
  GC.gc();sample=@timed rowindex(A);@assert sample.compile_time==0
  push!(setup_seconds,sample.time);push!(setup_bytes,sample.bytes)
 end
 m=size(A,1);lo=zeros(eltype(A),m);hi=similar(lo)
 baseline!(lo,hi,A,x,index);rl=copy(lo);rh=copy(hi)
 rowwise!(lo,hi,A,x,index);@assert isequal(lo,rl)&&isequal(hi,rh)
 # Reuse immutable structural indexing with changed values and changed point.
 values=copy(A.nzval);point=copy(x)
 for scale in (0.0,-1.0,2.0)
  A.nzval .= values .* scale;x .= point .* scale
  baseline!(lo,hi,A,x,index);copyto!(rl,lo);copyto!(rh,hi)
  rowwise!(lo,hi,A,x,index);@assert isequal(lo,rl)&&isequal(hi,rh)
 end
 copyto!(A.nzval,values);copyto!(x,point)
 fs=(baseline!,rowwise!);ts=[Float64[],Float64[]];bs=[Int[],Int[]]
 for f in fs;batch(f,lo,hi,A,x,index,5);end
 for round in 1:11,k in (isodd(round) ? (1,2) : (2,1))
  GC.gc();t=@timed batch(fs[k],lo,hi,A,x,index,5);@assert t.compile_time==0
  push!(ts[k],t.time/5);push!(bs[k],t.bytes÷5)
 end
 saved=median(ts[1])-median(ts[2])
 d=Dict("name"=>name,"type"=>string(eltype(A)),"rows"=>m,"columns"=>size(A,2),"nonzeros"=>nnz(A),"seconds"=>ts,"bytes"=>bs,"candidate_ratio"=>median(ts[2])/median(ts[1]),"index_bytes"=>Base.summarysize(index),"build_seconds"=>build.time,"build_compile_seconds"=>build.compile_time,"build_bytes"=>build.bytes,"warm_setup_seconds"=>setup_seconds,"warm_setup_bytes"=>setup_bytes,"break_even_calls"=>saved>0 ? median(setup_seconds)/saved : -1.0,"equal"=>true)
 println(name," ",eltype(A)," ratio=",d["candidate_ratio"]," index=",d["index_bytes"]);flush(stdout);d
end
function main(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 records=[];rng=MersenneTwister(1834)
 for T in (Float32,Float64),kind in (:diagonal,:sparse,:dense)
  A=kind==:diagonal ? spdiagm(0=>ones(T,20000)) : kind==:sparse ? sprand(rng,T,20000,2000,0.002) : sparse(rand(rng,T,512,512))
  x=randn(rng,T,size(A,2));push!(records,measure(string(kind),A,x))
 end
 for origin in ("primal","dual")
  d=deserialize(".superpowers/primal-certificate-work/capture/medium-"*origin*".bin")
  push!(records,measure("medium-"*origin,d.problem.A,copy(d.primal)));GC.gc(true)
 end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
main(only(ARGS))
