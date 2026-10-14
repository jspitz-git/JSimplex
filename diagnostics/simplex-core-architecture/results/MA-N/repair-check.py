"""New offline synthetic checks. No Julia and no launcher execution."""
from pathlib import Path
import json,copy,importlib.util,hashlib,ast
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mam_audit',D/'audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
fixtures=json.loads((D.parent/'MA-L/fixtures.json').read_text())['fixtures'];cases=[f for f in fixtures if f['cost']]
raw=dict(index=1,errors=[],ambient_restored=True,trace_cleared=True,load_seconds=1.,qualification_seconds=1.,first_calls_seconds=1.,cost_body_seconds=1.,costs=[])
for ci,f in enumerate(cases,1):
 ws=[]
 for pair in range(1,11):
  sides=['reference','candidate'] if (1+ci+pair)%2==0 else ['candidate','reference']
  for order,side in enumerate(sides,1):ws.append(dict(pair=pair,order=order,side=side,phase='warm' if pair<=3 else 'measured',seconds=1.,bytes=100,events=10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,true_count=128*int(f['expected'])))
 raw['costs'].append(dict(id=f['id'],expected=f['expected'],**{'class':f['cost']},preservation_checks=22,first=[dict(side=s,seconds=1.,result=f['expected']) for s in ['reference','candidate']],windows=ws))
red=dict(records=[dict(type='Pass',expression='ok') for _ in range(8)]+[dict(type='Fail',expression='(MAL_TRACE[]).scratch == 1') for _ in range(2)])
green=dict(records=[dict(type='Pass',expression='ok') for _ in range(3787)])
checks={'valid_schema':all(audit.validate_raw(raw,1,red,green).values())}
mutations=[('missing_case',lambda r:r['costs'].pop()),('wrong_id',lambda r:r['costs'][0].update(id='wrong')),('input_count',lambda r:r['costs'][0].update(preservation_checks=21)),('wrong_output',lambda r:r['costs'][0]['windows'][0].update(true_count=-1)),('wrong_order',lambda r:r['costs'][0]['windows'][0].update(order=2)),('missing_window',lambda r:r['costs'][0]['windows'].pop()),('compilation',lambda r:r['costs'][0]['windows'][8].update(compile_seconds=1.)),('nan_time',lambda r:r['costs'][0]['windows'][0].update(seconds=float('nan'))),('negative_bytes',lambda r:r['costs'][0]['windows'][0].update(bytes=-1)),('wrong_class',lambda r:r['costs'][0].update(**{'class':'bad'})),('exception',lambda r:r['errors'].append('bad')),('ambient',lambda r:r.update(ambient_restored=False)),('trace',lambda r:r.update(trace_cleared=False))]
for name,fn in mutations:
 r=copy.deepcopy(raw);fn(r);checks[name+'_rejected']=not all(audit.validate_raw(r,1,red,green).values())
bad=copy.deepcopy(red);bad['records'][-1]['expression']='wrong';checks['unexpected_RED_rejected']=not all(audit.validate_raw(raw,1,bad,green).values())
checks['missing_GREEN_rejected']=not all(audit.validate_raw(raw,1,red,None).values())
rows=audit.aggregate([raw,raw,raw]);checks['equal_target_rejected']=all(not x['accepted'] for x in rows if x['target']);checks['equal_controls_accepted']=all(x['accepted'] for x in rows if not x['target'])
winner=copy.deepcopy(raw)
for c in winner['costs']:
 for w in c['windows']:
  if w['side']=='candidate':w.update(seconds=.9,bytes=90,events=9)
checks['all_benefit_accepted']=all(x['accepted'] for x in audit.aggregate([winner,winner,winner]))
loser=copy.deepcopy(winner)
for c in loser['costs']:
 for w in c['windows']:
  if w['side']=='candidate':w['bytes']=101
checks['allocation_regression_rejected']=all(not x['accepted'] for x in audit.aggregate([loser,loser,loser]))
checks['guard_byte_identical']=(D/'guard.py').read_bytes()==(D.parent/'MA-J/guard.py').read_bytes()
checks['canonical_loads']=all(n in (D/'driver.jl').read_text() for n in json.loads((D.parent/'MA-L/qualification-inputs.json').read_text())['canonical_load_order'])
for n in ('launcher.py','audit.py','guard.py'):ast.parse((D/n).read_text())
checks['python_parse']=True
import tempfile
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'raw';p.write_text('original');pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest()}
 checks['bound_raw_accepted']=audit.bindings_match(pins)
 p.write_text('changed');checks['changed_raw_rejected']=not audit.bindings_match(pins)
 p.unlink();checks['missing_raw_rejected']=not audit.bindings_match(pins)
checks['aggregate_revalidates']='stage(i)' in (D/'audit.py').read_text() and 'bindings_match(s' in (D/'audit.py').read_text()
checks['loaded_module_paths_bound']='loaded_paths_pinned' in (D/'audit.py').read_text() and 'Base.loaded_modules' in (D/'driver.jl').read_text()
checks['dependency_roots_complete']=not json.loads((D/'dependency-roots.json').read_text())['missing']
# Real failed RED is immutable evidence; validate only its exact source assertion.
import tomllib
actual=tomllib.loads((D.parent/'MA-M/run-1/red.toml').read_text())
checks['actual_RED_new_gate_accepts']=all(audit.validate_raw(raw,1,actual,green).values())
checks['actual_RED_old_literal_rejects']=any(r['type']=='Fail' and r['expression']!='MAL_TRACE[].scratch == 1' for r in actual['records'])
for label,change in [('missing',lambda r:r['records'].pop()),('extra',lambda r:r['records'].append(dict(type='Fail',expression='(MAL_TRACE[]).scratch == 1'))),('error',lambda r:r['records'][-1].update(type='Error')),('broken',lambda r:r['records'][-1].update(type='Broken')),('unparenthesized',lambda r:r['records'][-1].update(expression='MAL_TRACE[].scratch == 1')),('unrelated',lambda r:r['records'][-1].update(expression='other == 1'))]:
 r=copy.deepcopy(actual);change(r);checks['actual_RED_'+label+'_rejected']=not all(audit.validate_raw(raw,1,r,green).values())
inverse=json.loads((D/'inverse.json').read_text())
for n,rec in inverse.items():
 text=(D/n).read_text()
 for e in reversed(rec['edits']):
  if text.count(e['new'])!=e['count']:raise ValueError('inverse multiplicity '+n)
  text=text.replace(e['new'],e['old'])
 checks[n+'_exact_inverse']=text==Path(rec['source']).read_text()
commands=json.loads((D/'commands.json').read_text());oldcmd=json.loads((D.parent/'MA-M/commands-reviewed.json').read_text())
checks['commands_path_only']=all(cmd[:7]==oldcmd[i][:7] and cmd[7]==str(D/'driver.jl') and cmd[8]==i and cmd[9]==str(D/f'run-{i}') for i,cmd in commands.items())
checks['no_outputs_or_launch_admission']=not any((D/n).exists() for n in ('run-1','sequence-reservation.json','admission-review.json'))
record=dict(all_passed=all(checks.values()),checks=checks,scope='Synthetic Python schema/statistical checks only, no Julia/launcher/old script execution',sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('driver.jl','launcher.py','audit.py','guard.py','commands.json','admission.md','repair-check.py')})
with (D/'repair-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(checks));
if not record['all_passed']:raise ValueError('preparation checks failed')
