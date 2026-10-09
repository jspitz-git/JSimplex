using JSimplex, InteractiveUtils, TOML, Statistics, Random, LinearAlgebra, Test
const JS=JSimplex
let source=read(joinpath(dirname(pathof(JS)),"primal_row_certification.jl"),String)
 for (old,new) in (("_native_row_sum_pair","_probe_row_sum_pair"),("_native_row_product_pair","_probe_row_product_pair"))
  ex,_=Meta.parse(source,first(findfirst("function "*old*"(",source)))
  body=replace(string(ex),old=>new)
  body=replace(body,"ldexp(nextfloat(zero(T)), precision(T))"=>"(T(2)*floatmin(T))",
   "ldexp(nextfloat(zero(T)), 2 * precision(T))"=>"(T(4)*floatmin(T)/eps(T))")
  @assert !occursin("ldexp",body)
  Core.eval(JS,:(Base.@inline $(Meta.parse(body))))
 end
end
Base.@noinline function batch(f,x,y,out)
 for i in eachindex(x)
  result=f(x[i],y[i]);out[i]=isnothing(result) ? zero(eltype(x)) : result[1]+result[2]
 end
 Base.donotdelete(out)
end
function main(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 rows=[];rng=MersenneTwister(591)
 for T in (Float32,Float64)
  @test T(2)*floatmin(T)==ldexp(nextfloat(zero(T)),precision(T))
  @test T(4)*floatmin(T)/eps(T)==ldexp(nextfloat(zero(T)),2*precision(T))
  tiny=nextfloat(zero(T));v=T[0,-0.0,1,-1,tiny,-tiny,floatmin(T),2*floatmin(T),floatmax(T),Inf,-Inf,NaN]
  for limit in (T(2)*floatmin(T),T(4)*floatmin(T)/eps(T))
   append!(v,T[prevfloat(limit),limit,nextfloat(limit),-limit])
  end
  for (name,fs) in (("sum",(JS._native_row_sum_pair,JS._probe_row_sum_pair)),("product",(JS._native_row_product_pair,JS._probe_row_product_pair)))
   for a in v,b in v;@test isequal(fs[1](a,b),fs[2](a,b));end
   open(out*"-"*name*"-"*string(T)*"-llvm.txt","w") do io
    code_llvm(io,fs[1],Tuple{T,T};debuginfo=:none)
   end
   for zero_heavy in (false,true)
    n=100000;x=randn(rng,T,n);y=randn(rng,T,n);buffer=similar(x)
    zero_heavy && (x[1:4:end].=0;y[1:3:end].=1)
    for i in eachindex(x);@test isequal(fs[1](x[i],y[i]),fs[2](x[i],y[i]));end
    times=[Float64[],Float64[]];bytes=[Int[],Int[]]
    for f in fs;batch(f,x,y,buffer);end
    for round in 1:11,k in (isodd(round) ? (1,2) : (2,1))
     GC.gc();t=@timed batch(fs[k],x,y,buffer);@assert t.compile_time==0
     push!(times[k],t.time);push!(bytes[k],t.bytes)
    end
    r=Dict("name"=>name,"type"=>string(T),"zero_heavy"=>zero_heavy,"size"=>n,"seconds"=>times,"bytes"=>bytes,"speedup"=>median(times[1])/median(times[2]))
    push!(rows,r);println(r);flush(stdout)
   end
  end
 end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>rows));end
end
Base.invokelatest(main,only(ARGS))
