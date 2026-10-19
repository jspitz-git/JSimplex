from pathlib import Path
import ast,json,hashlib,sys
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import control as c,oracle as o
s=(D/'driver.jl').read_text();ops=(D/'operations.jl').read_text()
checks={
 'five_cases_60_rows':len(o.CASES)==5 and len(o.SCHEDULE)==60,
 'seven_preparation_69_payload':len(o.PREPARATION)==7 and len(o.PAYLOAD)==69,
 'structural_350':sum(o.COUNTS)==350 and o.COUNTS==(7,300,10,26,7),
 'source_budget204':4*12*3+12*5==204,
 'top_level_two_side_loads':s.index('const REFERENCE_LOAD=@timed include')<s.index('module ZeroDriver') and s.index('const CANDIDATE_LOAD=@timed include')<s.index('module ZeroDriver'),
 'one_custom_test_owner':s.count('recorder.jl')==1 and all('recorder.jl' not in (D/n).read_text() for n in ('reference-side.jl','candidate-side.jl')),
 'no_old_test_invocation':'run_task1_tests(' not in s+ops,
 'tests_after_measurement':s.index('tc=@timed tests()')>s.index('save(output,"snapshot-after.toml"'),
 'constructor_observable': 'counter_sink=Ref(K.BGPanelCounts())' in ops and 'obs["fresh_owner"]=sink[] !== previous' in ops,
 'constructor_mixed_dictionary':'Dict{String,Any}("counters"=>collect(K.counts(v)))' in ops,
 'all_canonical_controls_python_syntax':True,
 'candidate_unchanged':c.sha(c.PROBE/'panel.jl')=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295',
 'candidate_tests_unchanged':c.sha(c.PROBE/'zero-counts-tests.jl')=='927789cf6260b52694bdc258529696a62af3ab338744a32b4564dd6aad0dae6f',
 'initial1104_extended1298':c.rd(D/'tests.json')['count']==1104 and c.rd(D/'tests-extended.json')['count']==1298,
 'no_run_or_outer':not (D/'runs').exists() and not (D/'outers').exists(),
 'phase_300':c.config('zero-counts-300')['seconds']==300,
 'copied_controls_exact':all(c.sha(D/n)==v['sha256']==c.sha(v['source']) for n,v in c.rd(D/'copied-files.json').items()),
 '277_groups':len(c.rd(D/'historical-groups.json')['groups'])==277,
}
for n in ('control.py','outer.py','seal.py','launch.py','audit.py','oracle.py','guard.py','supervisor.py','post-return.py','tests-extended.py'):ast.parse((D/n).read_text())
c.validate_probe()
paths=[p for p in D.iterdir() if p.is_file()]
v=dict(all_passed=all(checks.values()),checks=checks,julia_invoked=False,sha256={str(p):c.sha(p) for p in sorted(paths)})
c.save(D/'source-check.json',v)
print(json.dumps({'all_passed':v['all_passed'],'checks':len(checks),'bindings':len(paths)}))
if not v['all_passed']:raise RuntimeError('Source check failed')
