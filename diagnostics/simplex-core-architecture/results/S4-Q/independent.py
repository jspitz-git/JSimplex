from pathlib import Path
import hashlib,json,tomllib,statistics,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-Q';raw=R/'.superpowers/simplex-core-architecture/S4-Q/cost-1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins=json.loads((E/'cost-1-pins.json').read_text());a=json.loads((E/'audit.json').read_text());r=tomllib.loads((raw/'report.toml').read_text());pre=json.loads((E/'preflight.json').read_text());P=json.loads((D/'results/S4-P/source-contract.json').read_text());checks={}
checks['full558_rehash']=len(pins['inventory'])==558 and all(sha(p)==v['sha256'] for p,v in pins['inventory'].items())
checks['all_P567_readtime_unchanged']=all(sha(p)==v for p,v in P['sha256'].items())
checks['raw_portable5']=all(sha(raw/n)==sha(E/('cost-1-'+n)) for n in ['report.toml','process.json','run.log','resources.jsonl','pins.json'])
checks['audit28_pass']=len(a['checks'])==28 and all(a['checks'].values())
checks['postexit_auditor_not_pin']=str(E/'audit.py') not in pins['inventory'] and sha(E/'audit.py')==a['auditor_sha256']
checks['user6_unchanged']=all(sha(p)==h for p,h in pre['user_hashes'].items())
checks['source_master_equal']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
ls=r['lifecycles'];checks['all96_compile0']=sum(3 for l in ls if not l['warmup'])==96 and all(t['compile_seconds']==t['recompile_seconds']==0 for l in ls if not l['warmup'] for t in l['timings'])
checks['captured_960outputs_46080values']=sum(len(l['output_bits']) for l in ls)==960 and sum(len(v) for l in ls for v in l['output_bits'])==46080
ok=True
for f in ['sparse','dense']:
 for slot,name in enumerate(['outer_paired_ratio','inner1_paired_ratio','inner2_paired_ratio']):
  vals=[]
  for rd in range(1,9):
   ref=next(l for l in ls if not l['warmup'] and l['fixture']==f and l['round']==rd and not l['candidate']);can=next(l for l in ls if not l['warmup'] and l['fixture']==f and l['round']==rd and l['candidate']);vals.append(can['timings'][slot]['seconds']/ref['timings'][slot]['seconds'])
  s=a['statistics'][f][name];ok &= s['median']==statistics.median(vals) and s['min']==min(vals) and s['max']==max(vals)
checks['six_ratio_series_preserved']=ok
checks['inner_dense_outlier_retained']=a['statistics']['dense']['inner2_paired_ratio']['max']>5 and '5.757909' in (D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md').read_text()
obj=dict(checks=checks,all_passed=all(checks.values()),scope='Separate author full558 and P567 rehash, raw5/field/stats checks; no auditor rerun or numerical calls',auditor_sha256=sha(E/'audit.py'),raw_sha256=sha(raw/'report.toml'))
with (E/'independent.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(checks);assert obj['all_passed']
