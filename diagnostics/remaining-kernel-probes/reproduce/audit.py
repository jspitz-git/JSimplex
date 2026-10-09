from pathlib import Path
import json,tomllib,statistics,shutil,hashlib
ROOT=Path(__file__).resolve().parents[3]
raw=ROOT/'.superpowers/remaining-kernel-probes';out=ROOT/'diagnostics/remaining-kernel-probes/results';out.mkdir(exist_ok=True)
jobs=['census3','fusion1','rows1','managers-plain1','managers-parts1','managers-parts2','pfi1','pfi2']
data={}
for name in jobs:
 p=raw/name;proc=json.loads((p/'process.json').read_text());assert proc['returncode']==0 and proc['sources_unchanged']
 text=(p/'run.log').read_text();assert 'ERROR:' not in text and 'Test Failed' not in text
 d=tomllib.loads((p/'result.toml').read_text());data[name]=d
 for fn in ['process.json','run.log','result.toml']:shutil.copy2(p/fn,out/(name+'-'+fn))
for name in ['census1','census2']:
 p=raw/name
 for fn in ['process.json','run.log','failed-source.jl']:shutil.copy2(p/fn,out/(name+'-'+fn))
r=data['census3'];assert r['status']=='OPTIMAL' and r['original_feasible'] and r['iterations']==54591
assert r['events_hash']=='6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb'
assert r['states_hash']=='1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743'
for name,n in [('fusion1',14),('rows1',8),('pfi1',24),('pfi2',24)]:
 rows=data[name]['cases'];assert len(rows)==n and all(r['equal'] for r in rows)
 assert all(all(b==0 for arm in r['bytes'] for b in arm) for r in rows)
def index(d):return {(r['history'],r['manager'],r['chain']):r for r in d['cases']}
a=index(data['managers-plain1']);b=index(data['managers-parts2']);expected={(h,m,k) for h in ['runtime-40000','fast0507-1000'] for m in ['pfi','ft','ss','bg','hh'] for k in [0,80,320]}
assert a.keys()==b.keys()==expected
for key,plain in a.items():
 instrumented=b[key];assert plain['update_storage']==instrumented['update_storage']
 assert len(plain['kernels'])==len(instrumented['kernels'])==4
 for x,y in zip(plain['kernels'],instrumented['kernels']):
  assert (x['mode'],x['rhs'])==(y['mode'],y['rhs'])
  assert x['result_hash']==y['result_hash'] and x['residual']<1e-8 and y['residual']<1e-8
c=index(data['managers-parts1']);assert c.keys()==expected
for key in expected:
 for x,y in zip(a[key]['kernels'],c[key]['kernels']):assert x['result_hash']==y['result_hash']
for name in ['managers-parts1','pfi1']:
 shutil.copy2(raw/name/'source.jl',out/(name+'-source.jl'))
import subprocess
assert subprocess.check_output(['git','diff','21a3fae','--','src'],cwd=ROOT)==b''
provenance={}
for name in jobs+['census1','census2']:
 f=raw/name/'preflight.json'
 provenance[name]={'manifest_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'files':json.loads(f.read_text())}
# Store common immutable digests once; per-attempt additions/changes remain explicit.
common=dict(next(iter(provenance.values()))['files'])
for attempt in provenance.values():
 common={p:h for p,h in common.items() if attempt['files'].get(p)==h}
for attempt in provenance.values():
 attempt['files']={p:h for p,h in attempt['files'].items() if p not in common}
(out/'provenance.json').write_text(json.dumps({'common_files':common,'attempts':provenance},indent=2)+'\n')
summary={'completed_jobs':jobs,'instrumentation_failures':['census1','census2'],'paired_kernel_hashes':len(a)*8,'all_pairs_equal':True,'no_production_changes':True}
(out/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
for key in sorted(a):
 if key[2]!=320:continue
 print(key)
 for r in b[key]['kernels']:
  if r['rhs'] not in ('unit','entering'):continue
  print(r['mode'], 'plain_ms=',1000*statistics.median(next(x for x in a[key]['kernels'] if (x['mode'],x['rhs'])==(r['mode'],r['rhs']))['seconds']), 'instrumented_ms=',1000*statistics.median(r['seconds']))
  for p in sorted(r['parts'],key=lambda p:p['exclusive_seconds_per_solve'],reverse=True)[:5]:print(round(p['exclusive_seconds_per_solve']*1000,4),p['statement'])
