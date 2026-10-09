"""Archive compact evidence and verify paired guard-cost captures."""
from pathlib import Path
import hashlib,json,tomllib,shutil,statistics
ROOT=Path.cwd()
RAW=ROOT/'.superpowers/dual-pricing-residual'
OUT=ROOT/'diagnostics/dual-pricing-residual/results'
OUT.mkdir(exist_ok=True)
records=[]
for case in ('fast0507-dual','medium-dual','medium-primal','runtime-dual'):
 a=tomllib.loads((RAW/'capture'/case/'result.toml').read_text())
 b=tomllib.loads((RAW/'capture-after'/case/'result.toml').read_text())
 for key in ('input_sha256','algorithm','status','message','iterations','refactorizations','events_hash','states_hash','counts'):
  assert a[key]==b[key],(case,key)
 for key in ('objective','original_feasible'):
  assert a.get(key)==b.get(key),(case,key)
 if a['status']=='OPTIMAL':assert a['original_feasible']
 for key in ('dual_row_residual','dual_direction_residual','primal_point_certificate'):
  assert a['guard_calls'].get(key)==b['guard_calls'].get(key),(case,key)
 delta=a['guard_calls']['finite_workspace']-b['guard_calls']['finite_workspace']
 assert delta>=0
 if case.endswith('dual'):assert delta>0
 else:assert delta==0
 row=dict(case=case,status=a['status'],iterations=a['iterations'],finite_checks_before=a['guard_calls']['finite_workspace'],finite_checks_after=b['guard_calls']['finite_workspace'],checks_saved=delta,seconds_before=a['seconds'],seconds_after=b['seconds'],compile_seconds_before=a['compile_seconds'],compile_seconds_after=b['compile_seconds'],events_hash=a['events_hash'],states_hash=a['states_hash'])
 records.append(row)
 for arm in ('capture','capture-after'):
  shutil.copyfile(RAW/arm/case/'result.toml',OUT/(arm+'-'+case+'.toml'))
for job in ('prototype','contiguous-prototype','snapshots','weights-bench'):
 d=tomllib.loads((RAW/job/'results.toml').read_text())
 for r in d['cases']:
  assert all(v==0 for v in r['old_bytes']+r['new_bytes'])
  assert r['ratio']==statistics.median(r['new_seconds'])/statistics.median(r['old_seconds'])
 shutil.copyfile(RAW/job/'results.toml',OUT/(job+'.toml'))
provenance=[]
for job in ('prototype','contiguous-prototype','capture','snapshots','budget-before','budget-after','targeted','weights-bench','semantic','capture-after','project-suite'):
 p=json.loads((RAW/job/'process.json').read_text());assert p['sources_unchanged']
 if job=='budget-before':
  log=(RAW/job/'run.log').read_text()
  assert p['returncode']==1 and log.count('Evaluated: 2 == 1')==3
  assert '6 passed, 3 failed, 0 errored, 0 broken' in log
 elif job=='project-suite':
  log=(RAW/job/'run.log').read_text()
  assert p['returncode']==75 and 'wall-time guard; terminating owned process group' in log
  assert 'Test Failed' not in log and 'Error During Test' not in log
 else:assert p['returncode']==0,(job,p)
 manifest_path=RAW/job/'preflight.json';manifest=json.loads(manifest_path.read_text())
 sources={str(Path(k).relative_to(ROOT)):v for k,v in manifest.items() if k.startswith(str(ROOT/'src')+'/')}
 digest=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
 (OUT/('source-'+digest+'.json')).write_text(json.dumps(sources,indent=2)+'\n')
 scripts={str(Path(k).relative_to(ROOT)):v for k,v in manifest.items() if k.startswith(str(ROOT/'diagnostics/dual-pricing-residual/reproduce')+'/')}
 provenance.append(dict(job=job,process=p,preflight_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),source_digest=digest,script_hashes=scripts,environment_hashes={k:v for k,v in manifest.items() if Path(k).name in ('Project.toml','Manifest.toml','LocalPreferences.toml')},log_sha256=hashlib.sha256((RAW/job/'run.log').read_bytes()).hexdigest()))
 if job in ('budget-before','budget-after','targeted','semantic','project-suite'):
  shutil.copyfile(RAW/job/'run.log',OUT/(job+'.log'))
(OUT/'paired-audit.json').write_text(json.dumps(records,indent=2)+'\n')
(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps(records,indent=2))
