"""Exclusive author-independent S5-L provenance and hash verification, offline."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';L=D/'results/S5-L';K=L.parent/'S5-K'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
e=read(L/'evidence.json');p=read(L/'source-provenance.json');h=read(L/'host-before.json');cl=read(K/'closure.json');c=(L/'candidate.jl').read_text();source=(R/'test/adaptive_pricing_lifecycle_tests.jl').read_text()
checks={'full_fresh_inventory':all(sha(p)==v for p,v in e['sha256'].items()),'twenty_source_checks':e['all_passed'] and len(e['checks'])==20,'helpers_inverse':all(c.count(x['source_text'])==1 and source.splitlines(keepends=True)[x['start_line']-1:][:len(x['source_text'].splitlines())]==x['source_text'].splitlines(keepends=True) for x in p['helpers']),'candidate_hash':sha(L/'candidate.jl')==p['candidate_sha256'],'schema40_15_19':len(e['candidate_checks'])==40 and len(e['candidate_observations'])==15 and len(e['pricing_fields'])==19,'K_closure12_preserved':cl['all_passed'] and len(cl['checks'])==12 and all(sha(R/p)==v for p,v in cl['sha256'].items()),'user6_unchanged':len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items()),'src_test_CI_master_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()==h['master']}
files=[L/'evidence.json',L/'candidate.jl',L/'prepare.py',L/'source_check.py',L/'source-provenance.json',Path(__file__).resolve(),D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-qualification.md']
x={'checks':checks,'all_passed':all(checks.values()),'inventory_count':len(e['sha256']),'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (L/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
