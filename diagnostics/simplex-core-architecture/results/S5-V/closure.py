"""Exclusive S5-V closure after review and preserved continuation update."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';H=Path(__file__).resolve().parent;U=H.parent/'S5-U';M=Path('/home/jspitz/JSimplex.jl')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def bindings(x):return all(sha(k)==v for k,v in x.items())
e=read(H/'evidence.json');a=read(H/'independent.json');review=(H/'review.md').read_text();status=D/'STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';maps={str(status):H/'STATUS.md.before-V',str(road):H/'2026-10-11-simplex-core-architecture.md.before-V'}
c=dict(full166=len(e['sha256'])==166 and bindings(e['sha256']),literal21=len(e['checks'])==21 and e['all_passed'] is True and all(v is True for v in e['checks'].values()),author9=len(a['checks'])==9 and a['all_passed'] is True and all(v is True for v in a['checks'].values()),author7bindings=len(a['sha256'])==7 and bindings(a['sha256']),review_accepted='ACCEPTED' in review and 'Unresolved findings: []' in review,review_copy=sha(H/'review.md')==sha(D/'S5-CRASH-FALLBACK-OWNERSHIP-REVIEW.md'),U123preserved=len(read(U/'closure.json')['sha256'])==123 and all(sha(maps.get(k,k))==v for k,v in read(U/'closure.json')['sha256'].items()),continuation=bindings(read(H/'continuation.json')['sha256']),source_test_env_CI_unchanged=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),master_unchanged=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='2b546e946ddb7fdb6c0092df9cc19f566e301aa2',user6=bindings(read(H/'host.json')['user_hashes']))
groups=set(read(H/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c['full20groups_noJulia']=len(groups)==20 and not matches
files={p for p in H.rglob('*') if p.is_file()}|{status,road,D/'S5-CRASH-FALLBACK-OWNERSHIP.md',D/'S5-CRASH-FALLBACK-OWNERSHIP-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-ownership-contract.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-oracle.md'}
x=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in sorted(files)},groups=sorted(groups),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_ns=time.time_ns())
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));raise SystemExit(0 if x['all_passed'] else 1)
