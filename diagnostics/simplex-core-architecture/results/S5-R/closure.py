"""Exclusive S5-R closure; old collectors and auditors are never invoked."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';O=D/'results/S5-R';Q=O.parent/'S5-Q'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((O/'evidence.json').read_text());i=json.loads((O/'independent.json').read_text());h=json.loads((O/'host-before.json').read_text());c=json.loads((Q/'closure.json').read_text());pub=json.loads((Q/'publication-check.json').read_text());fix=json.loads((O/'field-fix.json').read_text())
status=D/'STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={str(status):O/'STATUS.md.before-R',str(road):O/'2026-10-11-simplex-core-architecture.md.before-R'}
groups=set(h['groups']);hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().startswith('julia'):hits.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (OSError,ValueError,IndexError):pass
checks={
 'source19':len(e['checks'])==19 and all(v is True for v in e['checks'].values()),
 'full199':len(e['sha256'])==199 and all(sha(p)==v for p,v in e['sha256'].items()),
 'author8':len(i['checks'])==8 and all(v is True for v in i['checks'].values()),
 'author6bindings':len(i['sha256'])==6 and all(sha(p)==v for p,v in i['sha256'].items()),
 'field_fix4':len(fix['checks'])==4 and all(fix['checks'].values()) and all(sha(p)==v for p,v in fix['sha256'].items()),
 'review_accepted':'Verdict: ACCEPTED' in (O/'review.md').read_text(),
 'review_copy':(O/'review.md').read_bytes()==(D/'S5-BASIS-INITIALIZATION-STOP-PREPARATION-REVIEW.md').read_bytes(),
 'Q_closure14_preserved':len(c['checks'])==14 and all(c['checks'].values()) and all(sha(mapping.get(p,p))==v for p,v in c['sha256'].items()),
 'Q_publication6':len(pub['checks'])==6 and all(pub['checks'].values()),
 'user6':len(h['user_hashes'])==6 and all(sha(p)==v for p,v in h['user_hashes'].items()),
 'refs_unchanged':all(subprocess.check_output(['git','rev-parse',k],text=True).strip()==v for k,v in h['refs'].items()),
 'source_test_CI_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
 'groups_absent':not hits,
 'next_admission':all('S5-S' in p.read_text() for p in [status,road]) and 'BEFORE any Julia' in (R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-qualification.md').read_text(),
}
paths=[p for p in O.rglob('*') if p.is_file()]+[D/'S5-BASIS-INITIALIZATION-STOP-PREPARATION.md',D/'S5-BASIS-INITIALIZATION-STOP-PREPARATION-REVIEW.md',status,road,R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-qualification.md']
out=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in sorted(paths)},boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=hits,time_ns=time.time_ns())
with (O/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(checks));assert out['all_passed']
