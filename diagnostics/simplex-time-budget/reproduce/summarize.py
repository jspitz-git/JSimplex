from pathlib import Path
import json,tomllib,hashlib,shutil,sys
ROOT=Path(__file__).resolve().parents[3];RAW=ROOT/'.superpowers/time-budget';OUT=ROOT/'diagnostics/simplex-time-budget/results'
groups={
 'setup':{'presolve_problem','postsolve_primal','initialize_workspace'},
 'basis':{'_pipeline_basis_solve!','_basis_matrix!','_replace_pivot_column!','refactorize!'},
 'reconstruction':{'recompute!'},
 'selection':{'_primal_entering','_primal_ratio','dual_edge_selection','price!','_configured_dual_ratio_test','dual_ratio_test','_bound_flipping_ratio_test'},
 'weight_updates':{'_primal_update_steepest!','update_dual_pricing_weights!','update_dse!'},
 'values_and_flips':{'_apply_bound_flips!','update_duals!','update_primals!','apply_primal_pivot!'},
 'projection_other':{'_project_postsolve_basis!'},
 'observer':{'observer'},
 'iteration_other':{'_primal_iteration_unchecked!','_dual_iteration_unchecked!'},
 'outer_other':{'outer_unattributed','cleanup_original'},
}
OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for case in ('medium-dual','medium-primal','cleanup-dual','cleanup-primal'):
 folder=RAW/(case+('-2' if case=='cleanup-dual' else '-1'))
 if not (folder/'census.toml').exists() or not (folder/'process.json').exists():continue
 process=json.loads((folder/'process.json').read_text())
 assert process['returncode']==0 and process['sources_unchanged'],(case,process)
 pins=json.loads((folder/'preflight.json').read_text())
 for path,want in pins.items():
  source=Path(path)
  if source.is_relative_to(ROOT/'src'):
   assert hashlib.sha256(source.read_bytes()).hexdigest()==want,path
 modes=('plain','census') if case.startswith('cleanup') else ('plain','profile','census')
 rec={name:tomllib.loads((folder/(name+'.toml')).read_text()) for name in modes}
 for name in modes[1:]:
  for key in ('status','iterations','events_hash','states_hash','events'):assert rec['plain'][key]==rec[name][key],(case,name,key)
 c=rec['census'];assert c['status']=='ITERATION_LIMIT'
 sums={}
 for row in c['counters']:
  matches=[k for k,v in groups.items() if row['function'] in v];assert len(matches)<=1
  group=matches[0] if matches else 'numerical_checks_recovery'
  sums[group]=sums.get(group,0)+row['exclusive_seconds']
 total=sum(sums.values());outer=next(r['inclusive_seconds'] for r in c['counters'] if r['function']=='outer_unattributed')
 assert abs(total-outer)<1e-5
 r=dict(case=case,seconds={k:v['seconds'] for k,v in rec.items()},compile_seconds={k:v['compile_seconds'] for k,v in rec.items()},gc_seconds={k:v['gc_seconds'] for k,v in rec.items()},iterations=c['iterations'],exclusive_groups=sums,top_functions=sorted(c['counters'],key=lambda x:-x['exclusive_seconds']),events=c['events'],phases=c['phases'])
 rows.append(r)
 target=OUT/case;target.mkdir(exist_ok=True)
 for pattern in ('*.toml','*.txt','process.json','preflight.json','run.log'):
  for p in folder.glob(pattern):shutil.copyfile(p,target/p.name)
 print(case,r['seconds'],'compile',r['compile_seconds'])
 for f in r['top_functions'][:12]:print(' ',f['function'],f['calls'],round(f['exclusive_seconds'],3),round(f['inclusive_seconds'],3))
(OUT/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Completed comparisons',len(rows))

if "--require-complete" in sys.argv:
 assert len(rows)==4,"Incomplete four-case matrix"
 assert json.loads((RAW/'complete.json').read_text())['complete']
 metadata=RAW/'metadata-1'
 mp=json.loads((metadata/'process.json').read_text())
 assert mp['returncode']==0 and mp['sources_unchanged']
 handoffs=tomllib.loads((metadata/'handoffs.toml').read_text())['handoffs']
 assert {h['origin'] for h in handoffs}=={'dual','primal'}
 for h in handoffs:
  assert h['options']['refactorization_interval']=='160'
  assert h['options']['basis_update']=='huangfu_hall'
  assert h['options']['basis_refactorization']=='native'
  rec=tomllib.loads((OUT/('cleanup-'+h['origin'])/'plain.toml').read_text())
  assert rec['iterations']==h['iterations']+256
  assert rec['input_sha256']==h['sha256']
 for name in ('handoffs.toml','process.json','preflight.json','run.log'):
  dest=OUT/'metadata';dest.mkdir(exist_ok=True);shutil.copyfile(metadata/name,dest/name)
 failed=RAW/'cleanup-dual-1';dest=OUT/'cleanup-dual-sampling-stall';dest.mkdir(exist_ok=True)
 assert json.loads((failed/'process.json').read_text())['returncode']!=0
 previous=tomllib.loads((failed/'plain.toml').read_text())
 repeated=tomllib.loads((OUT/'cleanup-dual/plain.toml').read_text())
 for key in ('status','iterations','events_hash','states_hash','events'):
  assert previous[key]==repeated[key],('repeated cleanup reference',key)
 for name in ('plain.toml','warm.toml','calibration.toml','process.json','preflight.json','run.log','sampling-stall.json'):
  shutil.copyfile(failed/name,dest/name)
 inventory=[]
 for folder in sorted(RAW.glob('*-*/')):
  process_path=folder/'process.json'
  process=json.loads(process_path.read_text()) if process_path.exists() else {}
  inventory.append(dict(attempt=folder.name,returncode=process.get('returncode'),sources_unchanged=process.get('sources_unchanged'),has_census=(folder/'census.toml').exists()))
 (OUT/'audit.json').write_text(json.dumps(dict(completed_cases=len(rows),all_trajectories_match=True,exclusive_times_reconciled=True,attempts=inventory),indent=2)+'\n')
