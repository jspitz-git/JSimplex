"""Audit complete guarded jobs and export compact measurement evidence."""
from pathlib import Path
import hashlib,json,re,shutil,tomllib,statistics,csv,itertools,math
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'.superpowers/basis-kernel-savings'
DEST=ROOT/'diagnostics/basis-kernel-savings/results'
completed=['pfi-production2','upper-production1','upper-production2','hh-compact2','compiled-final','semantic','external','pfi-baseline','pfi-production','bartels_golub-baseline','bartels_golub-production','pfi-zero-batch','upper-zero-batch','hh-total-batch','hh-isolated-allocations']
DEST.mkdir(parents=True,exist_ok=True)
assert (RAW/'validation-complete.json').is_file()
jobs=['pfi-safe1','upper1','upper-reference','green','compiled','pfi-production1','hh-compact1',*completed]
provenance={}
for name in jobs:
 d=RAW/name;p=json.loads((d/'process.json').read_text())
 assert p['returncode']==0 and p['sources_unchanged'],name
 pre=json.loads((d/'preflight.json').read_text())
 p['preflight_sha256']=hashlib.sha256((d/'preflight.json').read_bytes()).hexdigest()
 p['relevant_hashes']={k:v for k,v in pre.items() if '/src/' in k or 'basis-kernel-savings/reproduce' in k or k.endswith(('runtime.mps','external-inputs.toml','runtime-40000.bin','fast0507-1000.bin','julia.sh','guard.py','Project.toml','LocalPreferences.toml','Manifest.toml'))}
 log=(d/'run.log').read_text();match=re.search(r'Maximum resident set size \(kbytes\): (\d+)',log)
 p['max_rss_kib']=int(match[1]) if match else None
 provenance[name]=p
 if (d/'result.toml').is_file():shutil.copyfile(d/'result.toml',DEST/(name+'.toml'))
 if name in ('compiled-final','semantic','upper-reference','green','external'):
  shutil.copyfile(d/'run.log',DEST/(name+'.log'))
for name,label,count in [('compiled-final','Basis kernel compiled regressions',4910),('semantic','Native terminal certificate semantic regressions',15689),('external','External LP relaxations: native and Markowitz basis managers',305)]:
 assert re.search(re.escape(label)+r'\s*\|\s*'+str(count)+r'\s+'+str(count)+r'\s',(RAW/name/'run.log').read_text()),name
for name in ('red','red2'):
 d=RAW/name;p=json.loads((d/'process.json').read_text());assert p['returncode']!=0 and p['sources_unchanged']
 provenance[name]=p;shutil.copyfile(d/'run.log',DEST/(name+'.log'))
# Preserve the initial test-harness failure separately from the intended red test.
provenance['red']['classification']='Test harness used unsupported copy(f); initial expected mismatch checks also failed.'
provenance['red2']['classification']='552 passed, 12 intended DimensionMismatch-vs-BoundsError failures before the PFI change.'
keys=['history','manager','chain','mode','rhs']
def expected_grid(group):
 managers={'pfi':['pfi'],'upper':['ft','ss','bg'],'hh':['hh']}[group]
 return set(itertools.product(('runtime-40000','fast0507-1000'),managers,(0,80,320),('ftran','btran'),('actual','dense')))
def verify_grid(rows,group,rounds,zero_bytes=True):
 expected=expected_grid(group)
 seen=[tuple(r.get(k,group) for k in keys) for r in rows]
 assert len(seen)==len(set(seen)) and set(seen)==expected,(group,'grid')
 for r in rows:
  assert r['equal'] and len(r['bytes'])==len(r['seconds'])==2
  assert all(len(arm)==rounds and all(isinstance(b,int) and b>=0 and (not zero_bytes or b==0) for b in arm) for arm in r['bytes'])
  assert all(len(arm)==rounds and all(math.isfinite(t) and t>0 for t in arm) for arm in r['seconds'])
  ratio=statistics.median(r['seconds'][1])/statistics.median(r['seconds'][0])
  assert math.isclose(r['ratio'],ratio,rel_tol=1e-14),(group,'ratio')
summary=[]
for group,count in [('pfi',24),('upper',72),('hh',24)]:
 names={'pfi':['pfi-production1','pfi-production2'],'upper':['upper-production1','upper-production2'],'hh':['hh-compact1','hh-compact2']}[group]
 pairs=[]
 for name in names:
  rows=tomllib.loads((RAW/name/'result.toml').read_text())['cases'];assert len(rows)==count
  verify_grid(rows,group,11)
  seen=set()
  for r in rows:
   key=tuple(r.get(k,group) for k in keys);assert key not in seen;seen.add(key)
   assert r['equal'] and all(b==0 for arm in r['bytes'] for b in arm),(name,key)
   assert all(len(arm)==11 for arm in r['seconds'])
   summary.append(dict(zip(keys,key),process=name,ratio=r['ratio'],baseline_ms=1000*statistics.median(r['seconds'][0]),candidate_ms=1000*statistics.median(r['seconds'][1])))
  pairs.append(seen)
 assert pairs[0]==pairs[1]
manifest=tomllib.loads((ROOT/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').read_text())['cases']
entries={r['id']:r for r in manifest}
expected_external=set(itertools.product(entries,('native','markowitz'),('primal','dual'),('pfi','huangfu_hall','forrest_tomlin','suhl_suhl','bartels_golub')))
external=tomllib.loads((RAW/'external/result.toml').read_text())['cases'];assert len(external)==100
assert len({(x['id'],x['backend'],x['algorithm'],x['basis_update']) for x in external})==100
assert {(x['id'],x['backend'],x['algorithm'],x['basis_update']) for x in external}==expected_external
for x in external:
 e=entries[x['id']]
 assert x['input_sha256']==e['sha256'] and x['reference_objective']==e['objective']
 assert abs(x['objective']-e['objective'])<=max(1e-7,1e-8*max(abs(x['objective']),abs(e['objective'])))
assert all(x['status']=='OPTIMAL' and x['original_primal_certified'] and x['objective_matches'] for x in external)
for manager in ('pfi','bartels_golub'):
 a,b=[tomllib.loads((RAW/(manager+'-'+m)/'result.toml').read_text()) for m in ('baseline','production')]
 for r,mode in zip((a,b),('baseline','production')):
  assert r['mode']==mode and r['manager']==manager
  assert r['input_sha256']=='d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
 for k in ('events_hash','states_hash','iterations','refactorizations','events','objective'):
  assert a[k]==b[k],(manager,k)
 assert all(x['status']=='OPTIMAL' and x['original_feasible'] for x in (a,b))
 assert abs(a['objective']-51425691.7621)<1
with (DEST/'kernel-medians.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator="\n");w.writeheader();w.writerows(summary)
for group,count in [('pfi',24),('upper',72)]:
 rows=tomllib.loads((RAW/(group+'-zero-batch')/'result.toml').read_text())['cases']
 verify_grid(rows,group,1)
 assert len(rows)==count and all(r['equal'] and all(b==0 for arm in r['bytes'] for b in arm) for r in rows)
 assert all(all(len(arm)==1 for arm in r['seconds']) for r in rows)
hh_totals=tomllib.loads((RAW/'hh-total-batch/result.toml').read_text())['cases']
verify_grid(hh_totals,'hh',11,zero_bytes=False)
for r in hh_totals:
 expected=16 if r['history']=='fast0507-1000' and r['chain'] in (0,80) else 0
 assert all(all(b==expected for b in arm) for arm in r['bytes'])
 assert r['batch_count']>0
hh_isolated=tomllib.loads((RAW/'hh-isolated-allocations/result.toml').read_text())['cases']
verify_grid(hh_isolated,'hh',11)
d=RAW/'hh-zero-batch';p=json.loads((d/'process.json').read_text())
assert p['returncode']==1 and p['sources_unchanged']
assert 'AssertionError: t.bytes == 0' in (d/'run.log').read_text()
partial=tomllib.loads((d/'result.toml').read_text())['cases']
assert len(partial)==12 and all(r['history']=='runtime-40000' for r in partial)
p['classification']='Diagnostic HH assertion exposed 16-byte fixed batch overhead hidden by integer averaging. Partial report is not a completed experiment. See total-batch and isolated-allocation follow-ups.'
provenance['hh-zero-batch']=p
shutil.copyfile(d/'run.log',DEST/'hh-zero-batch-failed.log')
shutil.copyfile(d/'result.toml',DEST/'hh-zero-batch-partial.toml')
provenance['bartels_golub-baseline']['classification']='OPTIMAL with original feasibility after original-LP retry. One-second SIGUSR1 profiling intervention makes full timing diagnostic only; retry trigger was not captured by the quiet logger.'
for name in ('run.log','profile-peek.json'):
 shutil.copyfile(RAW/'bartels_golub-baseline'/name,DEST/('bg-baseline-'+name))
if (RAW/'red/test-source.jl').exists():shutil.copyfile(RAW/'red/test-source.jl',DEST/'red-test-source.jl')
(DEST/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({'successful_jobs':len(jobs),'preserved_red_attempts':2,'repeated_kernel_cells':len(summary),'external_solutions':len(external),'full_runtime_pairs':2,'production_exact_zero_batch_cells':96,'hh_isolated_zero_batch_cells':24,'preserved_HH_allocation_probe_failure':1},indent=2))
