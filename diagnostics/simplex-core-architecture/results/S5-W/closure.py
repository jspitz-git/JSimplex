"""Exclusive final S5-W closure. Run once after accepted review/continuation."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;V=H.parent/'S5-V';S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(x):return x['all_passed'] is True and all(v is True for v in x['checks'].values())
def binds(x):return all(sha(k)==v for k,v in x.items())
e=read(H/'evidence.json');a=read(H/'independent.json');review=(H/'review.md').read_text();vm={str(S):H/'STATUS.md.before-W',str(P):H/'2026-10-11-simplex-core-architecture.md.before-W'}
c=dict(full189=len(e['sha256'])==189 and binds(e['sha256']),source19=len(e['checks'])==19 and check(e),entry14=len(read(H/'entry.json')['checks'])==14 and check(read(H/'entry.json')),author8=len(a['checks'])==8 and check(a),author_bindings8=len(a['sha256'])==8 and binds(a['sha256']),review_accepted='Verdict: ACCEPTED' in review and 'Unresolved findings: []' in review,review_copy=sha(H/'review.md')==sha(D/'S5-CRASH-FALLBACK-OBSERVER-ORACLE-REVIEW.md'),Vclosure24_preserved=all(sha(vm.get(k,k))==v for k,v in read(V/'closure.json')['sha256'].items()),continuation=binds(read(H/'continuation.json')['sha256']),source_test_env_CI_unchanged=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),master_unchanged=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='2b546e946ddb7fdb6c0092df9cc19f566e301aa2',user6=binds(read(H/'host.json')['user_hashes']))
G=set(read(H/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c['full20groups_noJulia']=len(G)==20 and not matches
files={p for p in H.rglob('*') if p.is_file()}|{S,P,D/'S5-CRASH-FALLBACK-OBSERVER-ORACLE.md',D/'S5-CRASH-FALLBACK-OBSERVER-ORACLE-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-oracle.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-preparation.md'}
x=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in sorted(files)},groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_ns=time.time_ns())
with (H/'closure.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));raise SystemExit(0 if x['all_passed'] else 1)
