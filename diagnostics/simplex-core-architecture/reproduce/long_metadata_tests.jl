using JSimplex,Test,SparseArrays,TOML
const JS=JSimplex
include("long_counters.jl")
include("long_windows.jl")
install_long_counters!(JS,dirname(pathof(JS)))
install_long_event_sink!(JS)
isfile(joinpath(@__DIR__,"long_metadata.jl")) && include("long_metadata.jl")
isdefined(Main,:install_long_metadata!) && install_long_metadata!(JS,dirname(pathof(JS)))
function check_recovery_counters()
 @testset "Committed recovery metadata and discarded work" begin
  r=LongRecorder(IOBuffer(),JS._lc_counts)
  diag=JS.SimplexDiagnostics(;observer=r)
  names=("committed_restore_checkpoint","committed_repair","committed_checkpoint","committed_pricing_reset","discarded_metadata_events","pricing_scanned_entries","pricing_scored_entries","pricing_full_scan","pricing_block_scan","pricing_pool_hit")
  @test all(name in LONG_COUNTER_LABELS for name in names)
  if all(name in LONG_COUNTER_LABELS for name in names)
   for reason in (:restore_checkpoint,:repair,:checkpoint,:pricing_reset)
    JS._record_recovery!(diag,reason)
    @test long_counter_rows(JS)["committed_"*string(reason)]==1
   end
   @test r.accepted==0 && isempty(diag.events)
   public=JS.SimplexDiagnostics()
   JS._record_recovery!(public,:checkpoint)
   @test JS.event_count(public,:checkpoint)==1
   @test long_counter_rows(JS)["committed_checkpoint"]==1
   p=JS.LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0],row_upper=[1.0])
   ws=JS.initialize_workspace(p,JS.SolverOptions(;simplex_strategy=:legacy,verbose=false);
    progress=JS.SimplexProgressContext(p;diagnostics=diag))
   candidate=JS._candidate_workspace(ws)
   pending=candidate.progress.diagnostics.observer.pending
   append!(pending,[:pivot_completed,:correction,:pricing])
   reset_long_recorder!(r)
   JS._discard_candidate!(ws,candidate)
   @test isempty(pending)
   @test long_counter_rows(JS)["discarded_metadata_events"]==2
   @test r.accepted==0
   reset_long_recorder!(r)
   JS._record_full_pricing!(diag,10,7)
   pool=(scanned_entries=13,scored_entries=8,full_scans=2,block_scans=3)
   JS._record_pricing_work!(candidate.progress.diagnostics,pool,(10,7,1,1),4)
   JS._record_pricing_work!(diag,pool,(13,8,2,3),4)
   c=long_counter_rows(JS)
   @test [c[k] for k in names[6:end]]==[13,8,2,2,1]
   @test all(iszero,values(diag.counts))
   JS._record_full_pricing!(public,11,9)
   @test public.counts[:pricing_scanned_entries]==11
   @test public.counts[:pricing_scored_entries]==9
   storage=JS._lc_counts
   reset_long_recorder!(r)
   @test all(iszero,storage) && JS._lc_counts===storage
  end
 end
end
Base.invokelatest(check_recovery_counters)
