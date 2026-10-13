"""Exclusive author-independent verification of S5-K frozen source/evidence."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';K=D/'results/S5-K';J=K.parent/'S5-J'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
e=read(K/'evidence.json');j=read(J/'evidence.json');host=read(K/'host-before.json');cl=read(J/'closure.json')
checks={'full_fresh_inventory':all(sha(p)==v for p,v in e['sha256'].items()),'twenty_checks':e['all_passed'] and len(e['checks'])==20,'J_closure12_bindings':cl['all_passed'] and len(cl['checks'])==12 and all(sha(R/p)==v for p,v in cl['sha256'].items()),'J_raw_reuse_bound':sha(J/'evidence.json')==e['historical_evidence_sha256'],'schema_recount':e['schema']['reference_slots']==len(['live','trial','factor','problem','options','progress','pricing','policy','history','journal','sentinel'])+9 and e['schema']['copied_entries_tiny_fixture']==6 and e['schema']['post_unwind_vector_entries']==17,'user6_unchanged':len(host['user_hashes'])==6 and all(sha(p)==v for p,v in host['user_hashes'].items()),'src_test_CI_master_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()==host['master']}
files=[K/'evidence.json',K/'source_contract.py',Path(__file__).resolve(),D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-ORACLE.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-preparation.md']
x={'checks':checks,'all_passed':all(checks.values()),'inventory_count':len(e['sha256']),'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (K/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
