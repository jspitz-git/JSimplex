"""Audit paired outcomes and traces, keeping partial observations distinct."""
from pathlib import Path
import hashlib,json,statistics,sys,tomllib
raw=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
def read(p):return tomllib.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for case in ('runtime','medium','cleanup'):
 pair=[read(raw/(case+'-'+arm+'.toml')) for arm in ('baseline','candidate')]
 for key in ('status','iterations','pivot_events','trace_sha256','input_sha256','algorithm','interval','events'):
  assert pair[0][key]==pair[1][key],(case,key)
 if case=='runtime':
  assert all(p['status']=='OPTIMAL' and p['original_primal_feasible'] for p in pair)
  assert pair[0]['objective']==pair[1]['objective']
 else:assert all(p['status']=='ITERATION_LIMIT' for p in pair)
 for arm in ('baseline','candidate'):
  folder=raw/(case+'-'+arm)
  process=json.loads((folder/'process.json').read_text())
  assert process['returncode']==0 and process['sources_unchanged']
  pins=json.loads((folder/'preflight.json').read_text())
  for rel,digest in pair[arm=='candidate']['source_files'].items():
   assert pins[str(Path(pair[arm=='candidate']['source_root'])/rel)]==digest
  assert any(Path(p).name=='paired.jl' for p in pins)
  for name in ('runtime.mps','medium.mps','medium-primal-handoff.bin','guard.py','julia.sh'):
   assert any(Path(p).name==name for p in pins)
  assert all(sha(Path(p))==digest for p,digest in pins.items()),'A pinned file changed'
 records.append(dict(case=case,baseline=pair[0],candidate=pair[1],
  measured_ratio=pair[1]['seconds']/pair[0]['seconds'],allocation_ratio=pair[1]['allocated_bytes']/pair[0]['allocated_bytes']))
external=read(raw/'external.toml')['cases']
assert len(external)==len({(p['id'],p['algorithm'],p['backend'],p['basis_update']) for p in external})==100
assert all(p['status']=='OPTIMAL' and p['original_primal_certified'] and p['objective_matches'] for p in external)
results=dict(pairs=records,external_unique_cases=100,
 note='One before/after observation per workload, not repeated speed estimates. Prefixes are iteration-limited; runtime is fully certified.')
(out/'paired-summary.json').write_text(json.dumps(results,indent=2)+'\n')
for r in records:print(r['case'],r['baseline']['seconds'],r['candidate']['seconds'],'ratio',r['measured_ratio'],'identical traces')
