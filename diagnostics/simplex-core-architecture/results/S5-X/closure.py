"""Exclusive final S5-X closure after independent review and continuation."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;W=H.parent/'S5-W';S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def good(x,n):return len(x['checks'])==n and x['all_passed'] is True and all(v is True for v in x['checks'].values())
def binds(x):return all(sha(k)==v for k,v in x.items())
e=read(H/'evidence.json');a=read(H/'independent.json');rev=(H/'review.md').read_text();maps={str(S):H/'STATUS.md.before-X',str(P):H/'2026-10-11-simplex-core-architecture.md.before-X'}
c=dict(full213=len(e['sha256'])==213 and binds(e['sha256']),source22=good(e,22),entry17=good(read(H/'entry.json'),17),author9=good(a,9),author10bindings=len(a['sha256'])==10 and binds(a['sha256']),review_accepted='Verdict: ACCEPTED' in rev and 'Unresolved findings: []' in rev,review_copy=sha(H/'review.md')==sha(D/'S5-CRASH-FALLBACK-OBSERVER-PREPARATION-REVIEW.md'),Wclosure21_preserved=all(sha(maps.get(k,k))==v for k,v in read(W/'closure.json')['sha256'].items()),continuation=binds(read(H/'continuation.json')['sha256']),candidate_exact=sha(H/'candidate.jl')=='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18',source_test_env_CI_unchanged=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),master_unchanged=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='2b546e946ddb7fdb6c0092df9cc19f566e301aa2',user6=binds(read(H/'host.json')['user_hashes']))
G=set(read(H/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c['full20groups_noJulia']=len(G)==20 and not matches
files={p for p in H.rglob('*') if p.is_file()}|{S,P,D/'S5-CRASH-FALLBACK-OBSERVER-PREPARATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-PREPARATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-preparation.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-qualification.md'}
x=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in sorted(files)},groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_ns=time.time_ns())
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));raise SystemExit(0 if x['all_passed'] else 1)
