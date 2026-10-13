"""Exclusive closure after final review. Preserved texts reconcile prior pins."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';H=Path(__file__).resolve().parent;O=R/'.superpowers/simplex-core-architecture/S5-M/qualification-1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
translations={str(D/'STATUS.md'):H/'STATUS.md.before-M',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):H/'2026-10-11-simplex-core-architecture.md.before-M'}
def original(p):
 p=Path(p);p=p if p.is_absolute() else R/p
 return translations.get(str(p),p)
a=json.loads((H/'audit.json').read_text());post=json.loads((H/'postcheck.json').read_text());pins=json.loads((O/'pins.json').read_text());l=json.loads((H.parent/'S5-L/closure.json').read_text());review=json.loads((H/'review-acceptance.json').read_text());p=json.loads((O/'process.json').read_text())
groups={53479,53481,52772,52774,49081,49084,23249,23257,p['runner']['pgid'],p['child']['pgid']};matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  s=(q/'stat').read_text();f=s[s.rindex(')')+2:].split()
  if int(f[2]) in groups or (q/'comm').read_text().strip()=='julia':matches.append({'pid':int(q.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
checks={'audit_accepted':a['all_passed'] and all(a['checks'].values()),'author_postcheck':post['all_passed'] and all(post['checks'].values()),'full_launch_pins_reconciled':all(sha(original(f))==v['sha256'] for f,v in pins['inventory'].items()),'L_closure_preserved':l['all_passed'] and all(sha(original(f))==v for f,v in l['sha256'].items()),'postcheck_artifacts':all(sha(f)==v for f,v in post['sha256'].items()),'review_accepted':review['accepted'] is True and review['unresolved_findings']==[] and all(sha(f)==v for f,v in review['sha256'].items()),'user6':all(sha(f)==v for f,v in json.loads((H/'host-before.json').read_text())['user_hashes'].items()),'source_test_CI_equal_master':subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b'','master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='513c05388a82531e4d8fbcfb383e8897fad14ba2','fresh_fullgroups_absent':not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==p['runner']['boot_id'],'G_false_and_supplement':not json.loads((H.parent/'S5-G/audit.json').read_text())['all_passed'] and json.loads((H.parent/'S5-G/outcome-supplement.json').read_text())['all_passed'],'portable_raw':all(sha(H/'qualification-1'/f)==v for f,v in a['raw_sha256'].items())}
files={f for f in H.rglob('*') if f.is_file()}|{D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-QUALIFICATION.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-QUALIFICATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-test-preparation.md'}
x={'checks':checks,'all_passed':all(checks.values()),'boot_id':p['runner']['boot_id'],'matches':matches,'time_ns':time.time_ns(),'sha256':{str(f.relative_to(R)):sha(f) for f in sorted(files)}}
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed']}));raise SystemExit(0 if x['all_passed'] else 1)
