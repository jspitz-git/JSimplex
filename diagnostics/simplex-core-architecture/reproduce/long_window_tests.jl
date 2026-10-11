using JSimplex,Test,SparseArrays,TOML
const JS=JSimplex
const implementation=joinpath(@__DIR__,"long_windows.jl")
@testset "Long chronological windows implementation" begin
 @test isfile(implementation)
end
include("long_counters.jl")
include(implementation)
install_long_counters!(JS,dirname(pathof(JS)))
function window_tests()
 @testset "Bounded chronological recorder" begin
  io=IOBuffer();r=LongRecorder(io,JS._lc_counts)
  ws=(iterations=0,progress=(iteration_offset=17,),problem=(A=spzeros(2,3),))
  r(:phase_auxiliary,ws)
  for i in 1:1024
   r(:pivot_completed,merge(ws,(iterations=i,)))
  end
  @test r.accepted==1024
  @test r.windows==2 # initial phase transition and periodic window
  r(:phase_cleanup,merge(ws,(iterations=1024,)))
  r(:phase_primal,merge(ws,(iterations=1024,)))
  @test r.algorithm==:primal && r.phase==:cleanup
  old=long_enter!(r,:recovery)
  err=ErrorException("region sentinel")
  caught=try
   try;throw(err);finally;long_leave!(r,old);end
  catch e;e end
  @test caught===err
  @test LONG_SECTIONS[r.section]==:cleanup_steps
  old_counts=r.previous_counts;old_metrics=r.metrics
  finish!(r)
  @test r.previous_counts===old_counts && r.metrics===old_metrics
  @test !hasfield(typeof(r),:workspace)
  data=TOML.parse(String(take!(io)))
  @test data["windows"][2]["accepted_steps"]==1024
  @test data["windows"][2]["iteration"]==1024
  @test data["windows"][2]["offset"]==17
  @test data["windows"][2]["algorithm"]=="dual"
  @test data["windows"][2]["phase"]=="auxiliary"
  @test all(w["seconds"]>=0 for w in data["windows"])
  @test all(w["counter_deltas"]==zeros(Int,length(LONG_COUNTER_LABELS)) for w in data["windows"])
  # Use actual staging dispatch: a deferred completion only reaches the live
  # recorder on commit, while work events can be forwarded immediately.
  io2=IOBuffer();r2=LongRecorder(io2,JS._lc_counts)
  diag=JS.SimplexDiagnostics(;observer=r2)
  live=(progress=(diagnostics=diag,),)
  pending=Symbol[];stage=JS._StageObserver(live,pending)
  candidate=merge(ws,(scratch=(pending_factor_update=true,post_iteration=:none),))
  stage(:pivot_completed,candidate)
  @test r2.accepted==0 && pending==[:pivot_completed]
  empty!(pending) # discard must not become accepted work
  @test r2.accepted==0
  JS._diagnostic_event!(diag,:pivot_completed,candidate)
  @test r2.accepted==1
  @test length(r2.previous_counts)==length(LONG_COUNTER_LABELS)
  finish!(r2)
 end
end
Base.invokelatest(window_tests)
