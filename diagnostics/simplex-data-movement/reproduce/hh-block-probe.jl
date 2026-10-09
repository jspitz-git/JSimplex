using JSimplex,Random,Statistics,TOML,Test
old_hh(d,p,o)=(all(isfinite,d),isequal(d,p))
function block_hh(direction::Vector{T},prepared::Vector{T},valid::Bool) where {T<:Union{Float32,Float64}}
    valid && length(direction) == length(prepared) || return (all(isfinite,direction),false)
    finite = true
    matched = true
    count = length(direction)
    first_index = 1
    while first_index <= count
        last_index = min(first_index + 127, count)
        @inbounds @simd for index in first_index:last_index
            value = direction[index]
            finite &= isfinite(value)
            matched &= isequal(value,prepared[index])
        end
        if !matched
            @inbounds @simd for index in (last_index+1):count
                finite &= isfinite(direction[index])
            end
            return finite,false
        end
        first_index = last_index+1
    end
    return finite,matched
end

new_hh(d,p,o)=block_hh(d,p,true)
function sample(f,d,p,o,reps)
 f(d,p,o);GC.gc()
 @timed for iteration in 1:reps
  d[2]=p[2]=isodd(iteration) ? one(eltype(d)) : -one(eltype(d))
  Base.donotdelete(f(d,p,o),o)
 end
end
function main(out)
 @assert !ispath(out);records=[]
 for T in (Float32,Float64), n in (8,64,2048,32768,360982),density in (0.01,1.0),kind in (:hh_hit,:hh_miss_first,:hh_miss_early,:hh_miss_middle,:hh_miss_last)
  rng=MersenneTwister(85);d=randn(rng,T,n);d[rand(rng,n).>density].=zero(T);p=copy(d);o=similar(d)
  kind==:hh_miss_early && (p[3]=d[3]+one(T))
  kind==:hh_miss_first && (p[1]=d[1]+one(T));kind==:hh_miss_middle && (p[n÷2]=d[n÷2]+one(T));kind==:hh_miss_last && (p[end]=d[end]+one(T))
  entry=JSimplex.PreparedTriangularSpike{T}(nothing,o,p)
  old=kind==:tri ? ((d,p,o)->begin;entry.destination=nothing;invoke(JSimplex._finish_prepared_spike!,Tuple{JSimplex.PreparedTriangularSpike,Any},entry,d);entry.destination===d;end) : old_hh
  new=kind==:tri ? ((d,p,o)->begin;entry.destination=nothing;JSimplex._finish_prepared_spike!(entry,d);entry.destination===d;end) : new_hh
  @test isequal(old(d,p,o),new(d,p,o))
  times=[Float64[],Float64[]];allocs=[Float64[],Float64[]];reps=max(20,2_000_000÷n)
  for round in 1:13
   for k in (isodd(round) ? (1,2) : (2,1))
    t=sample(k==1 ? old : new,d,p,o,reps);@assert t.compile_time==0
    push!(times[k],t.time/reps);push!(allocs[k],t.bytes/reps)
   end
  end
  r=Dict("type"=>string(T),"length"=>n,"density"=>density,"kind"=>string(kind),"old_seconds"=>times[1],"new_seconds"=>times[2],"old_bytes"=>allocs[1],"new_bytes"=>allocs[2],"ratio"=>median(times[2])/median(times[1]));push!(records,r)
  println(T," ",n," ",density," ",kind," ",r["ratio"]);flush(stdout)
 end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
main(only(ARGS))
