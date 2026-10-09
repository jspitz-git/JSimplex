from pathlib import Path
import hashlib,itertools,json,statistics,subprocess,tomllib,sys
root=Path(__file__).resolve().parents[3]
p=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
expected_jobs=['predicate-final','production-kernel','semantic','external']+[f'{case}-{arm}' for case in ('fast','medium','runtime') for arm in ('baseline','candidate')]
assert json.loads((p/'validation-current.json').read_text()).get('completed') is True
records=json.loads((p/'validation.json').read_text())
assert [r['job'] for r in records]==expected_jobs
assert all(r['returncode']==0 for r in records)
processes={j:json.loads((p/j/'process.json').read_text()) for j in expected_jobs}
assert all(r['returncode']==0 and r['sources_unchanged'] for r in processes.values())
candidate_root=Path(processes['predicate-final']['effective_project'])
baseline_root=Path(processes['fast-baseline']['effective_project'])
assert '295    295' in (p/'predicate-final/run.log').read_text()
assert '15689  15689' in (p/'semantic/run.log').read_text()
external=tomllib.loads((p/'external.toml').read_text())
manifest=tomllib.loads((root/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').read_text())['cases']
key=lambda r:(r['id'],r['backend'],r['algorithm'],r['basis_update'])
want=set(itertools.product([r['id'] for r in manifest],('native','markowitz'),('primal','dual'),('pfi','forrest_tomlin','suhl_suhl','bartels_golub','huangfu_hall')))
assert len(external['cases'])==len(want)==100
assert {key(r) for r in external['cases']}==want
inputs={r['id']:r for r in manifest}
for r in external['cases']:
 assert r['status']=='OPTIMAL' and r['original_primal_certified'] and r['objective_matches']
 assert r['input_sha256']==inputs[r['id']]['sha256']
 assert r['reference_objective']==inputs[r['id']]['objective']
assert external['julia_threads']==external['blas_threads']==1
pairs=[];source_sets={}
for case,n in [('fast',10),('medium',2),('runtime',1)]:
 a=tomllib.loads((p/f'{case}-baseline.toml').read_text());b=tomllib.loads((p/f'{case}-candidate.toml').read_text())
 assert len(a['cases'])==len(b['cases'])==n
 for arm,d in [('baseline',a),('candidate',b)]:
  if arm in source_sets:assert source_sets[arm]==d['source_hashes']
  source_sets[arm]=d['source_hashes']
 for x,y in zip(a['cases'],b['cases']):
  ignore={'seconds_instrumented'}
  assert {k:v for k,v in x.items() if k not in ignore}=={k:v for k,v in y.items() if k not in ignore},(case,x['algorithm'],x['manager'])
  assert x['status']==('ITERATION_LIMIT' if case=='medium' else 'OPTIMAL')
  if case!='medium':assert x['original_feasible'] and y['original_feasible']
  pairs.append(dict(case=case,shared={k:v for k,v in x.items() if k not in ignore},baseline_seconds_instrumented=x['seconds_instrumented'],candidate_seconds_instrumented=y['seconds_instrumented']))
assert len(pairs)==13
for job in expected_jobs:
 pins=json.loads((p/job/'preflight.json').read_text())
 for name,digest in source_sets['candidate'].items():
  assert pins[str(candidate_root/name)]==digest,(job,name)
 if job.endswith('-baseline'):
  for name,digest in source_sets['baseline'].items():
   assert pins[str(baseline_root/name)]==digest,(job,name)

assert set(source_sets['baseline'])==set(source_sets['candidate'])
changed=[k for k in source_sets['baseline'] if source_sets['baseline'][k]!=source_sets['candidate'][k]]
assert set(changed)=={'src/simplex.jl','src/primal_simplex.jl','src/dual_simplex.jl'}
for name,digest in source_sets['baseline'].items():
 raw=subprocess.check_output(['git','show','6b891d0:'+name],cwd=root)
 assert hashlib.sha256(raw).hexdigest()==digest,name
kernels=tomllib.loads((p/'production-kernel.toml').read_text())['measurements']
assert len(kernels)==32
kernel_summary=[]
for r in kernels:
 if r['kind']=='primal':assert r['candidate_kind']=='production'
 assert len(r['reference_seconds'])==len(r['candidate_seconds'])==9
 assert set(r['reference_bytes'])==set(r['candidate_bytes'])=={0}
 a=statistics.median(r['reference_seconds']);b=statistics.median(r['candidate_seconds'])
 kernel_summary.append({**{k:v for k,v in r.items() if not k.endswith('_seconds') and not k.endswith('_bytes')},'reference_median_us':a*1e6,'candidate_median_us':b*1e6,'reduction_percent':100*(1-b/a),'reference_range_us':[min(r['reference_seconds'])*1e6,max(r['reference_seconds'])*1e6],'candidate_range_us':[min(r['candidate_seconds'])*1e6,max(r['candidate_seconds'])*1e6]})
summary=dict(baseline='6b891d0',source_changes=changed,all_jobs_passed=True,predicate_tests=295,semantic_tests=15689,external_cases=100,paired_cases=13,paired_results_identical=True,kernels=kernel_summary,pairs=pairs,source_hashes=source_sets,environment={k:v for k,v in external.items() if k not in ('cases','source_sha256')},processes=processes)
output.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('source_hashes','kernels','pairs','processes')},indent=2))
for pair in pairs:print(pair['case'],pair['shared']['manager'],pair['shared']['algorithm'],pair['shared']['iterations'],pair['baseline_seconds_instrumented'],pair['candidate_seconds_instrumented'])
