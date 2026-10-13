"""Exclusive publication closure. Read-only checks plus new closure.json only."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';P=D/'results/S5-P';O=P.parent/'S5-O'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((P/'evidence.json').read_text());i=json.loads((P/'independent.json').read_text());host=json.loads((P/'host-before.json').read_text());review=(P/'review.md').read_text()
status=D/'STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
oldmap={str(status):P/'STATUS.md.before-P',str(roadmap):P/'2026-10-11-simplex-core-architecture.md.before-P'}
old=json.loads((O/'closure.json').read_text());groups=set(host['groups']);hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if int(v[2]) in groups or comm.startswith('julia'):hits.append({'pid':int(p.name),'pgid':int(v[2]),'start_ticks':v[19],'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except (OSError,ValueError,IndexError):pass
checks={
 'evidence22':len(e['checks'])==22 and all(v is True for v in e['checks'].values()),
 'full157':len(e['sha256'])==157 and all(sha(p)==v for p,v in e['sha256'].items()),
 'author9':len(i['checks'])==9 and all(v is True for v in i['checks'].values()),
 'author_bindings7':len(i['sha256'])==7 and all(sha(p)==v for p,v in i['sha256'].items()),
 'review_accepted':'Verdict: ACCEPTED' in review,
 'report_review_identity':(D/'S5-BASIS-INITIALIZATION-CONTRACT-REVIEW.md').read_bytes()==(P/'review.md').read_bytes(),
 'O_closure20_preserved':len(old['checks'])==20 and all(old['checks'].values()) and all(sha(oldmap.get(p,p))==v for p,v in old['sha256'].items()),
 'user6':len(host['user_hashes'])==6 and all(sha(p)==v for p,v in host['user_hashes'].items()),
 'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()==host['refs']['master'],
 'source_test_CI_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'groups_absent':not hits,
 'continuation_source_only':'S5-Q' in status.read_text() and 'S5-Q' in roadmap.read_text() and 'OFFLINE' in (R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-oracle.md').read_text(),
}
paths=[p for p in P.rglob('*') if p.is_file()]+[D/'S5-BASIS-INITIALIZATION-CONTRACT.md',D/'S5-BASIS-INITIALIZATION-CONTRACT-REVIEW.md',status,roadmap,R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-oracle.md']
out=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in sorted(paths)},boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=hits,time_ns=time.time_ns())
with (P/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(checks));assert out['all_passed']
