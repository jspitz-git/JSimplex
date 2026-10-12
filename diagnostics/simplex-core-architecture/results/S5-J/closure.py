"""Exclusive S5-J closure after independent review and before fail-fast publication."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';J=D/'results/S5-J';I=J.parent/'S5-I';G=J.parent/'S5-G'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
e=read(J/'evidence.json');ind=read(J/'independent.json');host=read(J/'host-before.json');review=read(J/'review-acceptance.json');amend=read(J/'review-fix.json')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  s=(q/'stat').read_text();f=s[s.rindex(')')+2:].split()
  if int(f[2]) in {53479,53481,52772,52774,49081,49084,23249,23257} or (q/'comm').read_text().strip()=='julia':matches.append({'pid':q.name,'pgid':f[2],'start_ticks':f[19],'boot_id':boot,'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
prior={}
for p,v in read(I/'closure.json')['sha256'].items():
 target=J/(Path(p).name+'.before-J') if p.endswith('/STATUS.md') or p.endswith('2026-10-11-simplex-core-architecture.md') else R/p
 prior[p]=sha(target)==v
checks={
 'source21_PASS':e['all_passed'] and len(e['checks'])==21,
 'independent8_PASS':ind['all_passed'] and len(ind['checks'])==8,
 'full97_current':len(e['sha256'])==97 and all(sha(p)==v for p,v in e['sha256'].items()),
 'independent_bound_artifacts':all(sha(J/(Path(p).name+'.before-review') if p in amend['before_sha256'] else R/p)==v for p,v in ind['sha256'].items()),
 'one_review_amendment':amend['all_passed'] and all(sha(R/p)==v for p,v in amend['after_sha256'].items()) and all(sha(J/(Path(p).name+'.before-review'))==v for p,v in amend['before_sha256'].items()),
 'user6_unchanged':all(sha(p)==v for p,v in host['user_hashes'].items()),
 'I_closure_preserved':all(prior.values()),
 'src_test_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()==host['master'],
 'fresh_fullgroups_absent':not matches and boot==host['boot_id'],
 'review_accepted':review['accepted'] and not review['unresolved_findings'] and sha(D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP-REVIEW.md')==review['sha256'],
 'G_false_plus_supplement':not read(G/'audit.json')['all_passed'] and read(G/'outcome-supplement.json')['all_passed']}
files=[p for p in J.rglob('*') if p.is_file()]+[D/'STATUS.md',D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP.md',D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-oracle.md']
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':boot,'matches':matches,'I_closure_reconciliation':prior,'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (J/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
