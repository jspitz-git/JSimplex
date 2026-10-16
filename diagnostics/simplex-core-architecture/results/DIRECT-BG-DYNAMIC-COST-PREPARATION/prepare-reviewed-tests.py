from pathlib import Path
E=Path(__file__).resolve().parent
for old,new in [('offline-tests.py','offline-tests-reviewed.py'),('prefix-tests.py','prefix-tests-reviewed.py'),('fix-red-generated.py','fix-green.py')]:
 s=(E/old).read_text().replace('from analysis import','from analysis_reviewed import').replace('import evidence,control','import evidence_reviewed as evidence, control_reviewed as control').replace('import evidence as e','import evidence_reviewed as e').replace('from control import','from control_reviewed import')
 s=s.replace('offline-tests.json','offline-tests-reviewed.json').replace('prefix-tests.json','prefix-tests-reviewed.json').replace('fix-red.json','fix-green.json').replace("(D/'control.py')","(D/'control_reviewed.py')").replace("print('Expected RED'","print('Remaining failures'")
 if new=='fix-green.py':
  pos=s.index("save(D/'fix-green.json'")
  s=s[:pos]+'''from analysis_reviewed import first_process_viable
fixtures=[dict(name=n) for n in ['sparse32','dense32','sparse96','dense96']]
a=dict(all_passed=True,pure_timeout=False,cells=[dict(fixture=f['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default',statistics=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,probe_memory_gate=True,faster_pairs=3)) for f in fixtures for b in ['native','markowitz']])
check('second_process_viable',first_process_viable(a,fixtures))
for key,value in [('time_median_gate',False),('allocation_gate',False),('memory_gate',False),('probe_memory_gate',False),('faster_pairs',2),('faster_pairs',True),('faster_pairs',8)]:
 bad=copy.deepcopy(a);bad['cells'][0]['statistics'][key]=value
 check('stop_'+key+'_'+str(value),not first_process_viable(bad,fixtures))
for key,value in [('all_passed',False),('pure_timeout',True),('cells',a['cells'][:-1]),('cells',a['cells'][::-1])]:
 bad=copy.deepcopy(a);bad[key]=value;check('stop_top_'+key+'_'+str(len(checks)),not first_process_viable(bad,fixtures))
check('all_regressions_fixed',all(checks.values()))
'''+s[pos:]
  s=s.replace("scope='Synthetic prefix behavior and source stop-gate RED; no numerical execution'","scope='Synthetic prefix regressions and conservative second-process admission GREEN; no numerical execution'")
 with (E/new).open('x') as f:f.write(s)
print('Canonical regression suites written')
