"""Independent final OFFLINE source/hash/count review; no Julia or control-script execution."""
from pathlib import Path
import ast,hashlib,json,re,sys,importlib.util
H=Path(__file__).resolve().parent;R=H.parents[3];C=R/'diagnostics/direct-bg-blocked-update/reproduce'
checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
sites=rd(H/'assertion-sites.json');transform=rd(H/'test-transform.json')
ck('site_universe',set(sites)=={f'{p}{i:03d}' for p,n in [('P',94),('N',26),('L',40)] for i in range(1,n+1)})
for name,prefix in [('panel-tests.jl','P'),('numerical-tests.jl','N'),('lifecycle-tests.jl','L')]:
 orig=(C/name).read_text();clone=(H/name).read_text();m=transform[name]
 ck('frozen_hash_'+name,sha(C/name)==m['sha256']);ck('clone_hash_'+name,sha(H/name)==m['clone_sha256'])
 occurrences=list(re.finditer(r'@test_throws\b|@test\b',orig))
 ck('inventory_count_'+name,len(occurrences)==len(m['changes'][0]['sites']))
 for i,x in enumerate(occurrences,1):
  sid=f'{prefix}{i:03d}';line=orig.count('\n',0,x.start())+1
  ck('source_map_'+sid,sites[sid]==dict(file=name,line=line,kind=x.group(),source_line=orig.splitlines()[line-1]))
 for c in reversed(m['changes'][1:]):
  ck('inverse_substitution_'+name+'_'+str(len(checks)),clone.count(c['new'])==c['count']);clone=clone.replace(c['new'],c['old'])
 clone=clone.replace('using ..HarnessRecords: @check, @checkthrows\nimport ..HarnessRecords\nusing Test','using Test')
 def restore(x):return sites[x.group(2)]['kind']
 clone=re.sub(r'(@checkthrows|@check) "([PNL][0-9]{3})"',restore,clone)
 ck('exact_inverse_'+name,clone==orig)
for p in H.glob('*.py'):
 a=ast.parse(p.read_text());ck('python_syntax_'+p.name,True)
 if p.name in ['oracle.py','control.py','audit.py','launch.py','seal.py','outer.py','post-return.py']:
  ck('no_optimized_away_checks_'+p.name,not any(isinstance(n,ast.Assert) for n in ast.walk(a)))
spec=importlib.util.spec_from_file_location('reviewed_pure_oracle',H/'oracle.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
expected={f'P{i:03d}':1 for i in range(1,95)}
for lo,hi,n in [(1,1,5),(13,13,2),(15,15,4),(16,18,10),(19,20,5760),(21,26,10),(27,27,3),(34,45,4),(62,64,3),(66,66,2),(85,91,3)]:
 for i in range(lo,hi+1):expected[f'P{i:03d}']=n
ck('fixed_panel_occurrences',o.panel_counts()==expected)
schedule=rd(H/'schedule.json');fixtures=rd(C/'fixtures.json')['fixtures']
ck('fixture_order_and_metadata',schedule['fixtures']==[dict(name=f['name'],n=f['n'],updates=len(f['steps']),pivot_agreement=f['pivot_agreement'],minimum_panels=f['minimum_panels']) for f in fixtures])
ck('unit_roster',schedule['units']==['panel','lifecycle']+[f['name']+'/'+b for f in fixtures for b in ['native','markowitz']])
ck('six_RED_identities',schedule['expected_red_units']==[f+'/'+b for f in ['dense96','dense256','dense96-long32'] for b in ['native','markowitz']])
ck('stream_API_budget',len(fixtures)==13 and sum(len(f['steps']) for f in fixtures)==128 and 4*128==512 and 12*128==1536)
stages=rd(H/'stages.json');ck('same_ordinary_stage',stages['red']==stages['green'])
for label,s in stages.items():
 root=Path(s['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck('stage_membership_'+label,actual==set(s['sha256']) and not any(p.is_symlink() for p in root.rglob('*')))
 ck('stage_hashes_'+label,all(sha(root/n)==v for n,v in s['sha256'].items()))
 ck('ordinary_factory_'+label,sha(root/'src/direct-factor.jl')==sha(R/'diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl'))
 ck('ordinary_export_'+label,sha(root/'src/factor-export.jl')==sha(R/'diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl'))
manifest=rd(C/'overlay-manifest.json');ck('accepted_stage_manifest',stages['red']['path']==manifest['stage'] and stages['red']['sha256']==manifest['stage_sha256'])
q=rd(H.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')/'review.json')
ck('Task2_offline_acceptance',q['accepted'] is True and q['runtime_acceptance'] is False and q['numerical_acceptance'] is False)
ck('Task2_review_hashes',all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in q['sha256'].items()))
d=(H/'driver.jl').read_text();ck('top_level_includes',d.rfind('include(')<d.index('function main()'))
ck('single_common_suite_calls',d.count('run_task1_tests')==d.count('run_lifecycle')==1 and 'reference_route=RED' in d)
ck('raw_before_exit',d.index('save("raw.toml"')<d.index('exit(valid'))
ck('no_runtime_artifacts',not (H/'runs').exists() and not (H/'outers').exists())
pins=rd(H/'preparation-pins-reviewed.json');required=rd(H/'required-paths-reviewed.json')['paths']
ck('exact_preparation_membership',set(required)==set(pins['sha256']) and len(required)==len(set(required)))
ck('preparation_hashes',all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in pins['sha256'].items()))

# Exercise only the pure, new event-accounting function; no numerical algorithm.
base=dict(event_begin=1,event_finish=1,finish=1,event_scalar_suffix=1,event_scalar_pivot=1,pivot=1)
ck('scalar_event_accounting',o.trace_counts(base,1)['N001']==1)
for label,changes in [('unknown',{'unknown_event':1}),('missing_finish',{'event_finish':0}),('lost_pivot',{'pivot':2}),('pure_without_rows',{'event_pure':1}),('panel_without_eligibility',{'event_panel_begin':1,'event_panel_commit':1,'event_panel_pivot':8,'pivot':9})]:
 try:o.trace_counts(dict(base,**changes),1)
 except ValueError:ck('reject_event_'+label,True)
 else:ck('reject_event_'+label,False)
valid_panel=dict(event_begin=1,event_finish=1,finish=1,event_panel_begin=1,event_panel_commit=1,event_eligibility=1,event_panel_pivot=8,pivot=8)
ck('eight_step_panel_accounting',o.trace_counts(valid_panel,1)['N001']==8)
runtime=rd(H/'runtime-inputs-complete.json')['inventory']
ck('runtime_binding_hashes',all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in runtime.items()))
ck('156_preparation_inputs',len(pins['sha256'])==156)

record=dict(all_passed=True,checks=checks,site_count=160,panel_assertions=sum(expected.values()),sha256={str(H/'preparation-pins-reviewed.json'):sha(H/'preparation-pins-reviewed.json'),**pins['sha256']},scope=__doc__,runtime_acceptance=False,numerical_acceptance=False,performance_acceptance=False)
with (H/'reviewer-final-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('Independent OFFLINE source/hash/count checks PASS',len(checks),'panel assertions',sum(expected.values()))
