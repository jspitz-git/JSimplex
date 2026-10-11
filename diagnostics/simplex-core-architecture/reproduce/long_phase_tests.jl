using JSimplex,Test,SparseArrays,TOML
const JS=JSimplex
include("long_counters.jl");include("long_windows.jl")
install_long_counters!(JS,dirname(pathof(JS)))
function phase_tests()
 @testset "Authoritative phase and nested exclusive regions" begin
  io=IOBuffer();r=LongRecorder(io,JS._lc_counts)
  ws=(iterations=7,progress=(iteration_offset=11,),problem=(A=spzeros(3,5),))
  r(:phase_dual,ws)
  @test r.phase!=:phase_two # dual initialization precedes phase I or II
  r(:phase_auxiliary,ws)
  outer=long_enter!(r,:recovery);inner=long_enter!(r,:refactorization)
  r(:phase_dual,ws)
  @test LONG_SECTIONS[r.section]==:refactorization
  long_leave!(r,inner)
  @test LONG_SECTIONS[r.section]==:recovery
  long_leave!(r,outer)
  @test all(isdefined(Main,name) for name in (:long_report_phase!,:long_algorithm!,:long_cleanup!))
  if all(isdefined(Main,name) for name in (:long_report_phase!,:long_algorithm!,:long_cleanup!))
   long_report_phase!(r,:II,:dual,ws)
   @test r.phase==:phase_two && r.algorithm==:dual
   long_algorithm!(r,:primal,ws) # legacy reduced-LP cleanup has no phase callback
   @test r.phase==:phase_two && r.algorithm==:primal
   long_cleanup!(r,ws.problem,23)
   cleanup=long_enter!(r,:cleanup_entry)
   @test r.cleanup && r.phase==:cleanup
   @test r.iteration==23 && r.rows==3 && r.columns==5
   init=long_enter!(r,:initialization)
   long_report_phase!(r,:II,:dual,ws)
   @test LONG_SECTIONS[r.section]==:initialization
   long_leave!(r,init)
   @test LONG_SECTIONS[r.section]==:cleanup_entry
   long_algorithm!(r,:dual,ws)
   @test r.phase==:cleanup && r.algorithm==:dual
   @test LONG_SECTIONS[r.section]==:cleanup_steps
   recovery=long_enter!(r,:recovery);factor=long_enter!(r,:refactorization)
   long_report_phase!(r,:I,:primal,ws)
   @test LONG_SECTIONS[r.section]==:refactorization
   long_leave!(r,factor);@test LONG_SECTIONS[r.section]==:recovery
   long_leave!(r,recovery);@test LONG_SECTIONS[r.section]==:cleanup_steps
   cert=long_enter!(r,:certification)
   @test LONG_SECTIONS[r.section]==:certification
   long_leave!(r,cert);long_leave!(r,cleanup)
   @test LONG_SECTIONS[r.section]==:cleanup_steps
   finish!(r)
   data=TOML.parse(String(take!(io)))
   @test all(abs(sum(w["exclusive_nanoseconds"])-w["seconds"]*1e9)<=2 for w in data["windows"])
   @test r.region_depth==0
  end
 end
end
Base.invokelatest(phase_tests)
