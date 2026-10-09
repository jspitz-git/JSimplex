from pathlib import Path
import hashlib,json,tomllib,statistics,csv,re
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'.superpowers/simplex-data-movement';DEST=ROOT/'diagnostics/simplex-data-movement/results'
DEST.mkdir(exist_ok=True)
def read(path):return tomllib.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
# Compare the current full run against the already certified frozen trajectory.
ref=read(ROOT/'.superpowers/dual-pricing-residual/capture-after/runtime-dual/result.toml')
current=read(RAW/'runtime-final-v2/solve/result.toml')
for key in ('iterations','refactorizations','events_hash','states_hash','objective','input_sha256'):
 assert current[key]==ref[key],(key,current[key],ref[key])
assert current['status']=='OPTIMAL' and current['original_feasible']
# The two origins must have the same recorded per-pivot fingerprint in each pair.
paired=read(RAW/'cleanup-pair-final/results.toml')['cases']
assert len(paired)==4
for origin in ('primal','dual'):
 rows=[r for r in paired if r['origin']==origin];assert len(rows)==2
 assert sorted(r['baseline'] for r in rows)==[False,True]
 baseline=next(r for r in rows if r['baseline'])
 originals=[r for r in read(Path(baseline['reused_from']))['cases'] if r['origin']==origin and r['baseline']]
 assert len(originals)==1 and {k:v for k,v in baseline.items() if k!='reused_from'}==originals[0]
 for key in ('iterations','status','events_hash','states_hash'):assert rows[0][key]==rows[1][key],(origin,key)
 assert all(r['certificate']['verdict'] for r in rows)
ext=read(RAW/'external/results.toml')['cases'];assert len(ext)==100
combos={(r['id'],r['algorithm'],r['basis_update'],r['backend']) for r in ext}
assert len(combos)==100
assert all(r['status']=='OPTIMAL' and r['original_primal_certified'] and r['objective_matches'] for r in ext)
# All external cases must retain the previous certified numerical outcome.
previous=read(ROOT/'.superpowers/simplex-shared-work/external.toml')['cases']
key=lambda r:(r['id'],r['algorithm'],r['basis_update'],r['backend'])
previous={key(r):r for r in previous};assert len(previous)==100
for row in ext:
 for field in ('input_sha256','iterations','status','objective'):
  assert row[field]==previous[key(row)][field],(key(row),field)
# A nonzero exit must be one of the documented red tests or diagnostic failures.
expected_failures={'certificate-bench':143,'certificate-red':1,
 'fallback-budget-red':1,'prepared-budget-red':1,'manager-regressions':1,'project-suite':75,'runtime-final':1}
assert all((RAW/job/'process.json').exists() for job in expected_failures)
final_jobs=('final-focused','final-budget','prepared-final-bench','certificate-bench-final',
 'manager-regressions-compiled','semantic-final','external','cleanup-pair-final','runtime-final-v2')
final_source={str(p):sha(p) for p in sorted((ROOT/'src').rglob('*.jl'))}
for job in final_jobs:
 process=json.loads((RAW/job/'process.json').read_text())
 assert process['returncode']==0 and process['sources_unchanged'],job
 pin=json.loads((RAW/job/'preflight.json').read_text())
 assert all(pin[k]==v for k,v in final_source.items()),job
provenance=[]
for path in sorted(RAW.glob('*/process.json')):
 process=json.loads(path.read_text());assert process['sources_unchanged'],path
 assert process['returncode']==expected_failures.get(path.parent.name,0),path
 pin=path.with_name('preflight.json');mapping=json.loads(pin.read_text())
 source={k:v for k,v in mapping.items() if k.startswith(str(ROOT/'src')+'/')}
 provenance.append(dict(log_sha256=sha(path.with_name('run.log')),job=path.parent.name,returncode=process['returncode'],process_sha256=sha(path),preflight_sha256=sha(pin),source_digest=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()))
(DEST/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
for label,path in [('prepared',RAW/'prepared-final-bench/results.toml'),('certificate',RAW/'certificate-bench-final/results.toml')]:
 rows=read(path)['cases']
 with (DEST/(label+'.csv')).open('w',newline='') as f:
  fields=['type','length','dimension','density','kind','old_microseconds','new_microseconds','ratio','old_bytes','new_bytes']
  w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader()
  for r in rows:
   d={k:r[k] for k in fields if k in r}
   d.update(old_microseconds=statistics.median(r['old_seconds'])*1e6,new_microseconds=statistics.median(r['new_seconds'])*1e6,old_bytes=statistics.median(r['old_bytes']),new_bytes=statistics.median(r['new_bytes']))
   w.writerow(d)
for name,path in [('prepared-samples.toml',RAW/'prepared-final-bench/results.toml'),('certificate-samples.toml',RAW/'certificate-bench-final/results.toml'),('runtime-final.toml',RAW/'runtime-final-v2/solve/result.toml'),('cleanup-pairs.toml',RAW/'cleanup-pair-final/results.toml'),('late-factors.toml',RAW/'late-hh-kernels/results.toml'),('external.toml',RAW/'external/results.toml')]:
 (DEST/name).write_bytes(path.read_bytes())
for case in ('medium-dual','medium-primal','cleanup-dual','cleanup-primal'):
 (DEST/('inventory-'+case+'.toml')).write_bytes((RAW/'medium-baseline'/(case+'.toml')).read_bytes())
# Archive readable validation evidence, including the unsuccessful whole-suite run.
for job in ('final-focused','final-budget','manager-regressions-compiled','semantic-final','external','project-suite','manager-regressions'):
 (DEST/(job+'.log')).write_bytes((RAW/job/'run.log').read_bytes())
counts={'final-focused':(252,252),'final-budget':(14,14),
 'manager-regressions-compiled':(4091,4091),'semantic-final':(15689,15689),'external':(305,305)}
for job,(passed,total) in counts.items():
 log=(RAW/job/'run.log').read_text()
 if job=='final-focused':
  # Four top-level testsets: 12 + 136 + 2 + 102.
  assert all(re.search(r"\b"+str(n)+r"\s+"+str(n)+r"\b",log) for n in (12,136,2,102)),job
 else:assert re.search(r'\b'+str(passed)+r'\s+'+str(total)+r'\b',log),job
summary=dict(final_source_sha256=final_source,assertions=counts,
 external_unique_cases=len(combos),external_numerical_matches=100,
 full_runtime_fingerprint_matches=True,cleanup_origins_fingerprint_matches=['primal','dual'],
 full_project_suite='INCOMPLETE: diagnostic guard expired during LLVM compilation',
 expected_unsuccessful_attempts=expected_failures,
 reference_files_sha256={str(p):sha(p) for p in (ROOT/'.superpowers/dual-pricing-residual/capture-after/runtime-dual/result.toml',ROOT/'.superpowers/simplex-shared-work/external.toml',RAW/'cleanup-pair/results.toml')})
(DEST/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print('AUDIT OK: full runtime fingerprint, both cleanup origins,100unique external optima,and pinned process records')
