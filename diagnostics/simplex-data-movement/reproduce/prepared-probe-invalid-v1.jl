using JSimplex,Random,Statistics,TOML,Test
old_hh(d,p,o)=(all(isfinite,d),isequal(d,p))
function fused_hh(d::Vector{T},p,o) where T
 valid=true;equal=true
 @inbounds @simd for i in eachindex(d,p)
  x=d[i];valid &= isfinite(x);equal &= isequal(x,p[i])
 end
 valid,equal
end
function old_tri(d,p,o)
 all(isfinite,d) && all(isfinite,p) || return false
 copyto!(o,d);true
end
function fused_tri(d,p,o)
 valid=true
 @inbounds @simd for i in eachindex(d,p,o)
  x=d[i];valid &= isfinite(x)&isfinite(p[i]);o[i]=x
 end
 valid
end
function sample(f,d,p,o,reps)
 f(d,p,o);GC.gc();@timed for _ in 1:reps;f(d,p,o);end
end
function main(out)
 @assert !ispath(out);records=[]
 for T in (Float32,Float64), n in (2048,32768,360982),density in (0.01,1.0),kind in (:hh_hit,:hh_miss_first,:hh_miss_last,:tri)
  rng=MersenneTwister(85);d=randn(rng,T,n);d[rand(rng,n).>density].=zero(T);p=copy(d);o=similar(d)
  kind==:hh_miss_first && (p[1]=d[1]+one(T));kind==:hh_miss_last && (p[end]=d[end]+one(T))
  old=kind==:tri ? old_tri : old_hh;new=kind==:tri ? fused_tri : fused_hh
  @test isequal(old(d,p,o),new(d,p,o))
  oldtimes=[];newtimes=[];oldbytes=[];newbytes=[];reps=max(20,2_000_000÷n)
  for round in 1:13
   for flag in (isodd(round) ? (false,true) : (true,false))
    t=sample(flag ? new : old,d,p,o,reps);@assert t.compile_time==0
    push!(flag ? newtimes : oldtimes,t.time/reps);push!(flag ? newbytes : oldbytes,t.bytes/reps)
   end
  end
  r=Dict("type"=>string(T),"length"=>n,"density"=>density,"kind"=>string(kind),"old_seconds"=>oldtimes,"new_seconds"=>newtimes,"old_bytes"=>oldbytes,"new_bytes"=>newbytes,"ratio"=>median(newtimes)/median(oldtimes));push!(records,r)
  println(T," ",n," ",density," ",kind," ",r["ratio"]);flush(stdout)
 end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
main(only(ARGS))
