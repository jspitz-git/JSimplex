"""Offline lexical contract only. Never imports or executes Julia or old scripts."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
s=(D/'driver.jl').read_text(); r=(D/'REPORT.md').read_text()
checks={
 'original_macro': 'bytes = @allocated K._bgb_eligibility(f,1)' in s,
 'original_reassignment': 'f = replacement\n    return (bytes, f === replacement)' in s,
 'event_separate': 'events = @allocations K._bgb_eligibility(f,1)' in s,
 'concrete_signature': 'function concrete_call(f::Carrier)::Decision' in s,
 'concrete_bytes': 'Base.allocated(concrete_call, input)' in s,
 'concrete_events': 'Base.allocations(concrete_call, input)' in s,
 'full_result_sink': 'sink[] = concrete_call(f)' in s and 'sink[] = K._bgb_eligibility(f,1)' in s,
 'all_decision_fields': all(x in s for x in ('d.start == 1','d.count == 0','!d.accepted','d.reason === :dimensions','d.finite','d.counters == ntuple')),
 'fixed_schedule': 'for pair in 1:4' in s and '[("first",0,1),("first",0,2),("warm",0,2),("warm",0,1)]' in s,
 'empty_output': 'isempty(readdir(output))' in s,
 'record_before_assert': s.index('save(output,"record-$index.toml",row)') < s.index('require(row["assignment_ok"]'),
 'prefix_finally': 'finally\n        save(output,"raw.toml",raw)' in s,
 'preparation_records': all('"'+n+'.toml"' in s for n in ['load','setup','snapshot-before','snapshot-after']),
 'six_outer_fields': all('"'+k+'"' in s for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']),
 'cache_all_fields': 'fieldnames(typeof(cache))' in s,
 'owners_both_inputs': 'unchanged(before[1],after_cost.value[1])' in s and 'unchanged(before[2],after_cost.value[2])' in s,
 'no_run_entry': 'run_task1_tests()' not in s,
 'no_gc_eval_query': all(t not in s for t in ('GC.gc(', '@eval', 'invokelatest(', 'code_typed(', 'macroexpand(')),
 'no_zero_oracle_rewrite': 'inner_bytes"]==0' not in s,
 'scope_limitations': all(t in r for t in ['NOT the full original','TWO SEPARATE','60 eligibility','not a complete','not measured causes','not an executable']),
}
if not all(checks.values()):raise RuntimeError(checks)
result=dict(all_passed=True,checks=checks,sha256={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['driver.jl','REPORT.md','source_check.py']},scope='lexical source contract only; Julia UNEXECUTED')
with (D/'source-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),all_passed=True)))
