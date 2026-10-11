using Test,TOML
include("long_counters.jl")
include("long_windows.jl")
function reference_row(r,reason,end_ns)
 Dict("reason"=>string(reason),"phase"=>string(r.phase),"algorithm"=>string(r.algorithm),
  "iteration"=>r.iteration,"offset"=>r.offset,"rows"=>r.rows,"columns"=>r.columns,"nnz"=>r.nonzeros,
  "accepted_steps"=>r.accepted-r.previous_accepted,"rejected_candidates"=>r.rejected-r.previous_rejected,
  "seconds"=>Float64(end_ns-r.window_start)/1e9,"counter_deltas"=>r.counters-r.previous_counts,
  "exclusive_nanoseconds"=>r.metrics[:,1],"exclusive_bytes"=>r.metrics[:,2],
  "exclusive_allocations"=>r.metrics[:,3],"exclusive_gc_nanoseconds"=>r.metrics[:,4])
end
function test_stream()
 @testset "Streaming serialization preserves complete window schema" begin
  r=LongRecorder(IOBuffer(),zeros(Int64,length(LONG_COUNTER_LABELS)))
  r.counters .= eachindex(r.counters);r.previous_counts .= -3
  r.metrics .= reshape(collect(1:length(r.metrics)),size(r.metrics))
  r.phase=Symbol("phase\"with\\escapes");r.algorithm=:primal
  r.iteration=123;r.offset=456;r.rows=64;r.columns=128;r.nonzeros=256
  r.accepted=1030;r.previous_accepted=1024;r.rejected=5;r.previous_rejected=2
  stop=r.window_start+UInt64(123456789)
  expected=reference_row(r,:periodic,stop)
  io=IOBuffer();long_write_window!(io,r,:periodic,stop)
  @test only(TOML.parse(String(take!(io)))["windows"])==expected
  @test r.previous_counts==fill(-3,length(r.counters))
  @test r.metrics==reshape(collect(1:length(r.metrics)),size(r.metrics))
  @test r.previous_accepted==1024
  long_emit!(r,:periodic)
  @test r.previous_counts==r.counters
  @test r.previous_accepted==r.accepted
  @test r.metrics[end,1]>0
  tail=finish!(r)
  rows=TOML.parse(String(take!(r.io)))["windows"]
  @test length(rows)==tail["windows"]==2
  @test rows[end]["reason"]=="final_partial"
  @test all(iszero,rows[end]["counter_deltas"])
 end
end
test_stream()
