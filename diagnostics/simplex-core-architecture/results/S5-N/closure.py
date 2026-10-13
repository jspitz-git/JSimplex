"""One offline N closure after review; no old script or numerical execution."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';H=Path(__file__).resolve().parent;M=H.parent/'S5-M'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def original(p):
 p=Path(p);p=p if p.is_absolute() else R/p
 if p==D/'STATUS.md':return H/'STATUS.md.before-N'
 if p==R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':return H/'2026-10-11-simplex-core-architecture.md.before-N'
 return p
e=json.loads((H/'evidence.json').read_text());i=json.loads((H/'independent.json').read_text());m=json.loads((M/'closure.json').read_text());review=json.loads((H/'review-acceptance.json').read_text());p=json.loads((H/'source-inverse.json').read_text());host=json.loads((H/'host-before.json').read_text());groups=set(host['groups']);matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  s=(q/'stat').read_text();f=s[s.rindex(')')+2:].split()
  if int(f[2]) in groups or (q/'comm').read_text().strip()=='julia':matches.append({'pid':int(q.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
checks={'evidence19_PASS':e['all_passed'] and len(e['checks'])==19 and all(e['checks'].values()),'independent8_PASS':i['all_passed'] and len(i['checks'])==8 and all(i['checks'].values()),'full789_inventory':all(sha(f)==v for f,v in e['sha256'].items()),'independent7_bindings':all(sha(f)==v for f,v in i['sha256'].items()),'candidate_inverse_bound':sha(H/'candidate.jl')==p['candidate_sha256'] and sha(R/p['original_test'])==p['prefix_sha256'],'M_closure_preserved':m['all_passed'] and all(sha(original(f))==v for f,v in m['sha256'].items()),'review_accepted':review['accepted'] is True and review['unresolved_findings']==[] and all(sha(f)==v for f,v in review['sha256'].items()),'user6':all(sha(f)==v for f,v in host['user_hashes'].items()),'source_test_CI_master':not subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='513c05388a82531e4d8fbcfb383e8897fad14ba2','fresh_fullgroups_absent':not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==host['boot_id'],'G_false_and_supplement':not json.loads((H.parent/'S5-G/audit.json').read_text())['all_passed'] and json.loads((H.parent/'S5-G/outcome-supplement.json').read_text())['all_passed']}
files={f for f in H.rglob('*') if f.is_file()}|{D/'STATUS.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-PREPARATION.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-PREPARATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-test-integration.md'}
x={'checks':checks,'all_passed':all(checks.values()),'boot_id':host['boot_id'],'matches':matches,'time_ns':time.time_ns(),'sha256':{str(f.relative_to(R)):sha(f) for f in sorted(files)}}
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
