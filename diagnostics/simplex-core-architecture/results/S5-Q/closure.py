"""Exclusive offline closure. Never rerun after closure.json exists."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';Q=D/'results/S5-Q';P=Q.parent/'S5-P'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((Q/'evidence.json').read_text());i=json.loads((Q/'independent.json').read_text());host=json.loads((Q/'host-before.json').read_text());review=(Q/'review.md').read_text()
status=D/'STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
oldmap={str(status):Q/'STATUS.md.before-Q',str(road):Q/'2026-10-11-simplex-core-architecture.md.before-Q'}
pc=json.loads((P/'closure.json').read_text());pp=json.loads((P/'publication-check.json').read_text());pw=json.loads((P/'publication-whitespace.json').read_text());groups=set(host['groups']);hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip().startswith('julia'):hits.append({'pid':int(p.name),'pgid':int(v[2]),'start_ticks':v[19],'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except (OSError,ValueError,IndexError):pass
checks={
 'evidence18':len(e['checks'])==18 and all(v is True for v in e['checks'].values()),
 'full178':len(e['sha256'])==178 and all(sha(p)==v for p,v in e['sha256'].items()),
 'author8':len(i['checks'])==8 and all(v is True for v in i['checks'].values()),
 'author_bindings5':len(i['sha256'])==5 and all(sha(p)==v for p,v in i['sha256'].items()),
 'review_accepted':'Verdict: ACCEPTED' in review,
 'review_copy':(D/'S5-BASIS-INITIALIZATION-STOP-ORACLE-REVIEW.md').read_bytes()==(Q/'review.md').read_bytes(),
 'P_closure12_preserved':len(pc['checks'])==12 and all(pc['checks'].values()) and all(sha(oldmap.get(p,p))==v for p,v in pc['sha256'].items()),
 'P_publication5_whitespace4':len(pp['checks'])==5 and all(pp['checks'].values()) and len(pw['checks'])==4 and all(pw['checks'].values()),
 'user6':len(host['user_hashes'])==6 and all(sha(p)==v for p,v in host['user_hashes'].items()),
 'refs_unchanged':all(subprocess.check_output(['git','rev-parse',k],text=True).strip()==v for k,v in host['refs'].items()),
 'source_test_CI_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'groups_absent':not hits,
 'continuation_offline':all('S5-R' in p.read_text() for p in [status,road]) and 'UNEXECUTED' in (R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-preparation.md').read_text(),
 'no_Q_Julia_candidate':not list(Q.glob('*.jl')) and not list(Q.glob('*launcher*')),
}
paths=[p for p in Q.rglob('*') if p.is_file()]+[D/'S5-BASIS-INITIALIZATION-STOP-ORACLE.md',D/'S5-BASIS-INITIALIZATION-STOP-ORACLE-REVIEW.md',status,road,R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-preparation.md']
out=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in sorted(paths)},boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=hits,time_ns=time.time_ns())
with (Q/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(checks));assert out['all_passed']
