"""Exclusive S5-L closure after independent acceptance, before fail-fast publication."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';L=D/'results/S5-L';K=L.parent/'S5-K';G=L.parent/'S5-G'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
e=read(L/'evidence.json');i=read(L/'independent.json');h=read(L/'host-before.json');a=read(L/'review-acceptance.json');prov=read(L/'source-provenance.json')
fix=read(L/'review-fix.json') if (L/'review-fix.json').exists() else {'before_sha256':{},'after_sha256':{},'all_passed':True}
def original(p):
 path=Path(p)
 if path.is_absolute() and not path.is_relative_to(R):return path
 rel=str(path.relative_to(R)) if path.is_absolute() else p
 return L/(Path(rel).name+'.before-review') if rel in fix['before_sha256'] else R/rel
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  raw=(p/'stat').read_text();f=raw[raw.rindex(')')+2:].split()
  if int(f[2]) in {53479,53481,52772,52774,49081,49084,23249,23257} or (p/'comm').read_text().strip()=='julia':matches.append({'pid':p.name,'pgid':f[2],'start_ticks':f[19],'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
prior={}
for p,v in read(K/'closure.json')['sha256'].items():
 dest=L/(Path(p).name+'.before-L') if p.endswith('/STATUS.md') or p.endswith('2026-10-11-simplex-core-architecture.md') else R/p
 prior[p]=sha(dest)==v
checks={
 'source20_PASS':e['all_passed'] and len(e['checks'])==20,
 'independent9_PASS':i['all_passed'] and len(i['checks'])==9,
 'full141_original_inventory':len(e['sha256'])==141 and all(sha(original(p))==v for p,v in e['sha256'].items()),
 'independent_artifact_bindings':all(sha(original(p))==v for p,v in i['sha256'].items()),
 'original_candidate_provenance':sha(original(str(L/'candidate.jl')))==prov['candidate_sha256'],
 'review_fix_if_any':fix['all_passed'] and all(sha(R/p)==v for p,v in fix['after_sha256'].items()),
 'K_closure_preserved':all(prior.values()),
 'user6_unchanged':len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items()),
 'source_test_CI_master_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()==h['master'],
 'fresh_fullgroups_absent':not matches and boot==h['boot_id'],
 'review_accepted':a['accepted'] and not a['unresolved_findings'] and sha(D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION-REVIEW.md')==a['sha256'],
 'G_false_plus_supplement':not read(G/'audit.json')['all_passed'] and read(G/'outcome-supplement.json')['all_passed']}
files=[p for p in L.rglob('*') if p.is_file()]+[D/'STATUS.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-qualification.md']
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':boot,'matches':matches,'K_closure_reconciliation':prior,'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (L/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
