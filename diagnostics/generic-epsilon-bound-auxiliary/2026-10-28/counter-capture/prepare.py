from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');M=Path('/home/jspitz/JSimplex.jl');S=D/'MASTER-run';P=D/'counter-capture'
sys.path.insert(0,str(S));import common as c
c.need((S/'output/process.json').exists(),'MASTER must finish first');p=c.read('output/process.json');c.need(p['returncode']==1,'expected rejected actualMASTER source')
extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];h=c.host(extra);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);h['master_head']=c.git(['rev-parse','HEAD']);c.unchanged();P.mkdir()
for n in ['host-before.json','host-seed.json']:c.put(str(P/n),h)
for n in ['protected-before.json','environment.json']:shutil.copyfile(S/n,P/n)
changes=[]
name='generic_unit_perturb_residual_tests.jl';original=(M/'test'/name).read_text();needle=' @test all(after[k]["events"]<before[k]["events"] for k in 1:3)&&median(x["bytes"] for x in after)<median(x["bytes"] for x in before)'
block=r''' if T===Rational{BigInt}&&arm===:C
  println("COUNTER_CAPTURE_BEGIN UPR")
  Main.TOML.print(stdout,Dict("kind"=>"UPR","type"=>string(T),"scope"=>String(scope),"arm"=>String(arm),"n"=>n,"density"=>String(density),"shape"=>String(shape),"mode"=>String(mode),"before"=>before,"after"=>after,"events_predicate"=>all(after[k]["events"]<before[k]["events"] for k in 1:3),"bytes_predicate"=>median(x["bytes"] for x in after)<median(x["bytes"] for x in before)))
  println("\nCOUNTER_CAPTURE_END UPR");flush(stdout)
 end
'''
c.need(original.count(needle)==1,'UPR unique gate');text=original.replace(needle,block+needle);(P/name).write_text(text);c.need(text.replace(block,'')==original,'UPR exact inverse');changes.append(dict(file=name,original_sha256=c.sha(M/'test'/name),diagnostic_sha256=c.sha(P/name),insertion=block,gate_line=text.splitlines().index(needle)+1))
name='generic_dual_comparisons_tests.jl';original=(M/'test'/name).read_text();needle=' if expect_saving\n  @test all(100*after[i][1]<97*before[i][1]&&100*after[i][2]<97*before[i][2] for i in eachindex(before))'
block=r''' println("COUNTER_CAPTURE_BEGIN DUAL")
 Main.TOML.print(stdout,Dict("kind"=>"DUAL","type"=>string(T),"scope"=>String(scope),"pattern"=>String(pattern),"other"=>String(other),"expect_saving"=>expect_saving,"batch_size"=>8,"before"=>[collect(v) for v in before],"after"=>[collect(v) for v in after],"records"=>records,"fixture"=>batch_cost(prep),"snapshot"=>batch_cost(shot),"warmup"=>batch_cost(warm),"wrapper_warmup"=>batch_cost(wrapper_warmup),"wrapper"=>wrapper,"per_pair_bytes_predicate"=>[100*after[i][1]<97*before[i][1] for i in eachindex(before)],"per_pair_events_predicate"=>[100*after[i][2]<97*before[i][2] for i in eachindex(before)]))
 println("\nCOUNTER_CAPTURE_END DUAL");flush(stdout)
'''
c.need(original.count(needle)==1,'dual unique gate');text=original.replace(needle,block+needle);(P/name).write_text(text);c.need(text.replace(block,'')==original,'dual exact inverse');changes.append(dict(file=name,original_sha256=c.sha(M/'test'/name),diagnostic_sha256=c.sha(P/name),insertion=block,gate_line=text.splitlines().index('  @test all(100*after[i][1]<97*before[i][1]&&100*after[i][2]<97*before[i][2] for i in eachindex(before))')+1))
c.put(str(P/'source-inverse.json'),dict(accepted=True,source_commit=c.TARGET,changes=changes,numerical_checks_thresholds_warmups_samples_order_unchanged=True,no_GC_or_retry_or_filter=True,observation_only_after_measurements=True,observer_neutrality_not_proved=True))
files=[str(M/'test/generic_epsilon_bound_auxiliary_tests.jl'),str(P/'generic_unit_perturb_residual_tests.jl'),str(P/'generic_dual_comparisons_tests.jl')]
body='''using Test,JSimplex,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
@testset "Legacy allocation counter capture" begin
 for file in FILES
  println("INCLUDING ",file);flush(stdout);started=time_ns()
  include(file)
  println("FILE_FINISHED ",file," elapsed_seconds=",(time_ns()-started)/1e9);flush(stdout)
 end
end
println("COUNTER_CAPTURE_COMPLETE")
'''.replace('FILES',json.dumps(files))
(P/'tests.jl').write_text(body)
# This draft only prepares source. Separate reviewer-bound concrete guard/auditor admission remains mandatory.
(P/'PLAN.md').write_text('''# Bounded named counter diagnosis\n\nOriginal actualMASTER failures remain rejected; no release exception reused. Readonly actualsource717; ordinaryTest three complete files(newEBA plus two oldfiles), with only unconditional named logs AFTER existing3pairs and BEFORE unchanged strictassertions in privatecopies. No warmup/order/threshold/fixture/GC/filter/retry change. Source inverse exact. Per-file elapsed includes preparation; genericdual existing fixture/snapshot/warm/wrapper/reset/GCraw counters logged, UPR originalbefore/after wholecostdicts logged without creating newtimedpreparation stages. No customrecorder or manualtestsetstack. This is diagnosis, not replacement actualMASTERqualification; state/printing mayaffectnativeallocator, no observerneutrality or originalfailurecause inferred from a later pass. Singlefuture900s/892guard or concreteadmittedlimit, freshhost/fullgroups/refs, exactpins and independentadmission/completepostexitdataaudit before anyJulia. No production/test/envconfig edits; no oldbenchmark/auditor rerun.\n''')
shutil.copyfile(__file__,P/'prepare.py')
print('Countercapture private source prepared ONLY, no runtime admission orJulia')
