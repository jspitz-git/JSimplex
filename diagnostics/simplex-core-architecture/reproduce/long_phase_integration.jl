using JSimplex,Test,SparseArrays,TOML,SHA
const JS=JSimplex
include("long_counters.jl");include("long_windows.jl");include("long_metadata.jl")
install_long_counters!(JS,dirname(pathof(JS)));install_long_event_sink!(JS)
install_long_metadata!(JS,dirname(pathof(JS)))
const R=LongRecorder(IOBuffer(),JS._lc_counts)
install_long_regions!(JS,dirname(pathof(JS)),R)
function check_integration()
 @testset "Actual phase hooks and interrupted recovery publication" begin
  stop=Ref(false);interrupt=Ref(false)
  trace=(event,ws)->begin
   interrupt[] && event==:checkpoint && (stop[]=true)
   nothing
  end
  diag=JS.SimplexDiagnostics(;observer=LongTraceObserver(R,trace))
  p=JS.LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0],row_upper=[1.0])
  options=JS.SolverOptions(;algorithm=:dual,simplex_strategy=:legacy,verbose=false)
  ws=JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;diagnostics=diag))
  JS._report_simplex_phase(ws,:I,:dual,nothing)
  @test R.phase==:auxiliary && R.region_depth==0
  JS._report_simplex_phase(ws,:II,:dual,nothing)
  @test R.phase==:phase_two
  @test JS._dual_optimize!(ws,JS._guard_stop_callback(()->false)).status==JS.OPTIMAL
  @test R.algorithm==:dual
  @test JS._primal_optimize!(ws,JS._guard_stop_callback(()->false)).status==JS.OPTIMAL
  @test R.algorithm==:primal && R.phase==:phase_two
  checkpoint=JS.checkpoint_basis(ws)
  trial=JS._recovery_trial(ws,checkpoint,()->false)
  @test !isnothing(trial)
  before=(copy(ws.primal),copy(ws.basis.basic_indices))
  reset_long_counters!(JS)
  interrupt[]=true
  @test !JS._publish_recovery!(ws,trial,:repair,()->stop[])
  @test stop[]
  @test long_counter_rows(JS)["committed_repair"]==0
  @test long_counter_rows(JS)["committed_checkpoint"]==0
  @test (ws.primal,ws.basis.basic_indices)==before
  interrupt[]=false;stop[]=false
  @test JS._publish_recovery!(ws,trial,:repair,()->stop[])
  @test long_counter_rows(JS)["committed_repair"]==1
  @test long_counter_rows(JS)["committed_checkpoint"]==1
  @test R.region_depth==0
  finish!(R)
 end
end
Base.invokelatest(check_integration)
