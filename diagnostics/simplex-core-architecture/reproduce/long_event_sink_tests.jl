using JSimplex,Test,SparseArrays,TOML
const JS=JSimplex
include("long_counters.jl")
include("long_windows.jl")
install_long_counters!(JS,dirname(pathof(JS)))
isdefined(Main,:install_long_event_sink!) && install_long_event_sink!(JS)
function check_sink()
 @testset "Owned recorder avoids duplicate history but preserves delivery" begin
  r=LongRecorder(IOBuffer(),JS._lc_counts)
  diag=JS.SimplexDiagnostics(;observer=r)
  ws=(iterations=1,progress=(iteration_offset=0,),problem=(A=spzeros(2,3),))
  JS._diagnostic_event!(diag,:pivot_completed,ws)
  @test r.accepted==1
  @test isempty(diag.events)
  @test all(iszero,values(diag.counts))
  @test_throws ArgumentError JS._diagnostic_event!(diag,:not_a_valid_event,ws)
  public_seen=Symbol[]
  public=JS.SimplexDiagnostics(;observer=(event,ws)->push!(public_seen,event))
  JS._diagnostic_event!(public,:pivot_completed,ws)
  @test public_seen==[:pivot_completed]
  @test JS.event_count(public,:pivot_completed)==1
  @test JS.recent_events(public)==[:pivot_completed]
  pending=Symbol[]
  stage=JS._StageObserver((progress=(diagnostics=diag,),),pending)
  candidate=merge(ws,(scratch=(pending_factor_update=true,post_iteration=:none),))
  stage(:pivot_completed,candidate)
  @test pending==[:pivot_completed] && r.accepted==1
  empty!(pending)
  @test r.accepted==1
  JS._diagnostic_event!(diag,:pivot_completed,candidate)
  @test r.accepted==2 && isempty(diag.events)
  seen=Symbol[]
  paired=JS.SimplexDiagnostics(;observer=LongTraceObserver(r,(event,ws)->push!(seen,event)))
  JS._diagnostic_event!(paired,:flip_completed,ws)
  @test r.accepted==3 && seen==[:flip_completed] && isempty(paired.events)
  failure=ErrorException("trace failure")
  throwing=JS.SimplexDiagnostics(;observer=LongTraceObserver(r,(event,ws)->throw(failure)))
  err=try JS._diagnostic_event!(throwing,:pivot_rejected,ws) catch e;e end
  @test err isa JS.DiagnosticObserverFailure && err.cause===failure
  # Keep the standard wrapper and exact exception identity for recorder errors.
  close(r.io)
  caught=try JS._diagnostic_event!(diag,:phase_one,ws) catch e;e end
  @test caught isa JS.DiagnosticObserverFailure
  @test caught.cause isa ArgumentError
 end
end
Base.invokelatest(check_sink)
