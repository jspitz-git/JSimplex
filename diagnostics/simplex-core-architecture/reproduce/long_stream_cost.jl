# Isolate serialization cost on identical immutable metadata, outside solver time.
using Statistics
include("long_stream_tests.jl")
function old_write(io,r,stop)
 TOML.print(io,Dict("windows"=>[reference_row(r,:periodic,stop)]))
 nothing
end
new_write(io,r,stop)=long_write_window!(io,r,:periodic,stop)
function batch(writer,io,r,stop)
 truncate(io,0);seekstart(io);GC.gc(true)
 t=@timed for _ in 1:256
  writer(io,r,stop);flush(io)
 end
 Dict{String,Any}("seconds"=>t.time,"compile_seconds"=>t.compile_time,"bytes"=>t.bytes,
  "allocations"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime)
end
function main(output)
 r=LongRecorder(IOBuffer(),zeros(Int64,length(LONG_COUNTER_LABELS)))
 r.counters .= 123456789;r.metrics .= 123456789
 stop=r.window_start+UInt64(123456789)
 rows=Dict[]
 open(output*".windows.toml","w+") do io
  batch(old_write,io,r,stop);batch(new_write,io,r,stop)
  for pair in 1:6
   for writer in (isodd(pair) ? (old_write,new_write) : (new_write,old_write))
    row=batch(writer,io,r,stop);row["mode"]=writer===old_write ? "old" : "stream"
    row["pair"]=pair;@assert row["compile_seconds"]==0;push!(rows,row)
   end
  end
 end
 data=Dict("windows_per_batch"=>256,"pairs"=>6,"samples"=>rows)
 open(io->TOML.print(io,data),output,"w")
 for mode in ("old","stream")
  selected=filter(r->r["mode"]==mode,rows)
  println(mode," seconds=",median(r["seconds"] for r in selected),
   " bytes=",median(r["bytes"] for r in selected)," allocations=",median(r["allocations"] for r in selected))
 end
end
main(ARGS[1])
