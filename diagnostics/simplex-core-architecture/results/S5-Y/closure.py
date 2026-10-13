"""Exclusive final closure with explicit historical continuation mapping."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;X=H.parent/'S5-X';S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';B=R/'.superpowers/simplex-core-architecture/S5-Y/qualification-1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def good(p,n):
 x=read(p);return len(x['checks'])==n and x['all_passed'] is True and all(v is True for v in x['checks'].values())
def binds(x):return all(sha(k)==v for k,v in x.items())
mp={str(S):H/'STATUS.md.before-Y',str(P):H/'2026-10-11-simplex-core-architecture.md.before-Y'}
def pins(path,n):
 x=read(path)['inventory'];return len(x)==n and all(sha(mp.get(k,k))==v['sha256'] for k,v in x.items())
a=read(H/'audit.json');post=read(H/'postcheck.json');review=(H/'review.md').read_text();process=read(B/'process.json')
c=dict(entry18=good(H/'entry.json',18),admission1344=pins(H/'admission-pins.json',1344),launch1347=pins(H/'pins.json',1347),audit23=good(H/'audit.json',23),post11=good(H/'postcheck.json',11),post8bindings=len(post['sha256'])==8 and binds(post['sha256']),raw6=len(a['raw_sha256'])==6 and all(sha(B/k)==sha(H/'portable'/k)==v for k,v in a['raw_sha256'].items()),invocation3=len(a['invocation_sha256'])==3 and binds(a['invocation_sha256']),result_review='Verdict: ACCEPTED' in review and 'Unresolved findings: []' in review,review_copy=sha(H/'review.md')==sha(D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION-REVIEW.md'),Xclosure23_preserved=all(sha(mp.get(k,k))==v for k,v in read(X/'closure.json')['sha256'].items()),continuation=binds(read(H/'continuation.json')['sha256']),candidate=sha(X/'candidate.jl')=='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18',source_test_CI=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),master_unchanged=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='2b546e946ddb7fdb6c0092df9cc19f566e301aa2',user6=binds(read(H/'host.json')['user_hashes']))
G=set(post['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c['full22groups_noJulia']=len(G)==22 and not matches
files={p for p in H.rglob('*') if p.is_file()}|{S,P,D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-qualification.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-preparation.md'}
x=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in sorted(files)},groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_ns=time.time_ns())
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));raise SystemExit(0 if x['all_passed'] else 1)
