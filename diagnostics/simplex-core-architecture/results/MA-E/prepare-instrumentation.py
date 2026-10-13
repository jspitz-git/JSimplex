from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/MA-E');O=D.parent/'MA-D';original=(O/'candidate-tests-reviewed.jl').read_text();s=original
insertion='''const MAE_COMPARE_METRICS = Any[]
const MAE_FULL_METRICS = Any[]
function mae_metric(t)
    Dict("seconds"=>t.time,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
function mae_full(f,args...)
    t=@timed f(args...)
    push!(MAE_FULL_METRICS,mae_metric(t))
    return t.value
end
'''
replacements=[('const PV = J.PackedFactorVector\n','const PV = J.PackedFactorVector\n'+insertion),('    ea = outcome(reference!, a, upper, diagonal, count)\n    eb = outcome(J._markowitz_upper_solve!, b, upper, diagonal, count)\n','    ta = @timed outcome(reference!, a, upper, diagonal, count)\n    tb = @timed outcome(J._markowitz_upper_solve!, b, upper, diagonal, count)\n    ea,eb = ta.value,tb.value\n    push!(MAE_COMPARE_METRICS,Dict("reference"=>mae_metric(ta),"candidate"=>mae_metric(tb)))\n'),('out=J.forward_solve(factor,rhs)','out=mae_full(J.forward_solve,factor,rhs)'),('J.forward_solve!(out,f,rhs)','mae_full(J.forward_solve!,out,f,rhs)'),('J.forward_solve!(inplace,f,inplace)','mae_full(J.forward_solve!,inplace,f,inplace)')]
for a,b in replacements:
 if s.count(a)!=1:raise ValueError(a)
 s=s.replace(a,b)
back=s
for a,b in reversed(replacements):back=back.replace(b,a)
if back!=original:raise ValueError('inverse')
(D/'tests-instrumented.jl').write_text(s)
(D/'test-instrumentation.json').write_text(json.dumps({'inverse_equal':True,'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'instrumented_sha256':hashlib.sha256(s.encode()).hexdigest(),'replacements':replacements,'compare_pairs':77,'full_calls':30,'scope':'same calls, first-use diagnostic timings with compilation allowed; not warmed benchmark. Rational last3 compare pairs are8/2048/8limbs;30full metrics include128/512/128precision sequence. Two fixed-size log vectors bounded77/30, pushes outside windows.'},indent=2)+'\n')
p=D/'driver.jl';s=p.read_text().replace('Base.include(Main,joinpath(cfg["root"],"test/markowitz_ma_upper_tests.jl"))','Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))').replace('raw["tests"]=snapshot(ts);raw["counts"]=total(ts)','raw["tests"]=snapshot(ts);raw["counts"]=total(ts)\n            if isdefined(Main,:MarkowitzMAUpperTests)\n                raw["compare_metrics"]=Main.MarkowitzMAUpperTests.MAE_COMPARE_METRICS\n                raw["full_metrics"]=Main.MarkowitzMAUpperTests.MAE_FULL_METRICS\n            end');p.write_text(s)
p=D/'auditor.py';s=p.read_text().replace("if stage=='red':require(raw['records']==[],'RED work');return True","if stage in ('red','qualification'):\n  require(len(raw['compare_metrics'])==(0 if stage=='red' else 77) and len(raw['full_metrics'])==(0 if stage=='red' else 30),'instrumented call counts')\n  for pair in raw['compare_metrics']:\n   metric(pair['reference']);metric(pair['candidate'])\n  for m in raw['full_metrics']:metric(m)\n if stage=='red':require(raw['records']==[],'RED work');return True")
p.write_text(s)
