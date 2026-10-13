"""Exclusive S5-T closure, separate execution only after independent acceptance."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;S=H.parent/'S5-S'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
groups=set(read(H/'host-before.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  x=(p/'stat').read_text();v=x[x.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
inv=read(H/'pins.json')['sha256'];e=read(H/'evidence.json');a=read(H/'independent.json');review=(H/'review.md').read_text();prior=read(S/'closure.json')['sha256'];maps={str(D/'STATUS.md'):H/'STATUS.md.before-T',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):H/'2026-10-11-simplex-core-architecture.md.before-T'}
c={'full891':len(inv)==891 and all(sha(k)==v for k,v in inv.items()),'evidence21':len(e['checks'])==21 and e['all_passed'] is True and all(v is True for v in e['checks'].values()),'evidence_bindings6':len(e['sha256'])==6 and all(sha(k)==v for k,v in e['sha256'].items()),'author8':len(a['checks'])==8 and a['all_passed'] is True and all(v is True for v in a['checks'].values()),'author_bindings7':len(a['sha256'])==7 and all(sha(k)==v for k,v in a['sha256'].items()),'review_accepted':'ACCEPTED' in review and 'Unresolved findings: []' in review,'review_copy':sha(H/'review.md')==sha(D/'S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION-REVIEW.md'),'S_closure100_preserved':len(prior)==100 and all(sha(maps.get(k,k))==v for k,v in prior.items()),'continuation_bindings4':len(read(H/'continuation.json')['sha256'])==4 and all(sha(k)==v for k,v in read(H/'continuation.json')['sha256'].items()),'source_test_environment_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='35a6a9f4bb61e204b0c61ec9effe96cd9d2de3ab','user6':len(read(H/'host-before.json')['user_hashes'])==6 and all(sha(k)==v for k,v in read(H/'host-before.json')['user_hashes'].items()),'full16groups_noJulia':len(groups)==16 and not matches,'future_separate_admission':'BEFORE any Julia or actual' in (R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-test-integration.md').read_text()}
files={p for p in H.rglob('*') if p.is_file()}|{D/x for x in ('STATUS.md','S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION.md','S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION-REVIEW.md')}|{R/'docs/superpowers/plans'/x for x in ('2026-10-11-simplex-core-architecture.md','2026-10-13-basis-initialization-stop-test-preparation.md','2026-10-13-basis-initialization-stop-test-integration.md')}
o=dict(checks=c,all_passed=all(c.values()),sha256={str(k):sha(k) for k in sorted(files)},boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,time_ns=time.time_ns())
with (H/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));raise SystemExit(0 if o['all_passed'] else 1)
