"""Exclusive closure; preserves explicit historical pin semantics."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;Y=H.parent/'S5-Y';S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
mp={str(S):H/'STATUS.md.before-Z',str(P):H/'2026-10-11-simplex-core-architecture.md.before-Z'}
def binds(d,m={}):return all(sha(m.get(k,k))==v for k,v in d.items())
def good(p,n):
 a=read(p);return a['all_passed'] is True and len(a['checks'])==n and all(v is True for v in a['checks'].values())
rev=(H/'review-final.md').read_text();pins=read(H/'pins-reviewed.json')['sha256'];src=read(H/'source-check.json');ind=read(H/'independent.json')
c=dict(entry24=good(H/'entry.json',24),source19=good(H/'source-check.json',19),reviewed_pins=len(pins)==read(H/'pins-reviewed.json')['count'] and binds(pins,mp),author10=good(H/'independent.json',10),author8bindings=len(ind['sha256'])==8 and binds(ind['sha256'],{str(D/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md'):H/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md.before-review',str(R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-integration.md'):H/'2026-10-13-crash-fallback-observer-test-integration.md.before-review'}),review='Verdict: ACCEPTED' in rev and 'Unresolved findings: []' in rev,reviewcopy=sha(H/'review-final.md')==sha(D/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION-REVIEW.md'),Yclosure51=len(read(Y/'closure.json')['sha256'])==51 and binds(read(Y/'closure.json')['sha256'],mp),continuation=binds(read(H/'continuation.json')['sha256']),candidate=sha(H/'candidate-reviewed.jl')==read(H/'review-fix.json')['candidate_sha256'],review_fix8=good(H/'review-fix.json',8),review_fix_bindings=binds(read(H/'review-fix.json')['sha256']),actualtest=(R/'test/simplex_start_state_tests.jl').read_bytes()==(H/'original-test.jl').read_bytes(),source_test_CI=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),master=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='2b546e946ddb7fdb6c0092df9cc19f566e301aa2',user6=binds(read(Y/'host.json')['user_hashes']))
G=set(read(H/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c['full22groups_noJulia']=len(G)==22 and not matches
files={p for p in H.rglob('*') if p.is_file()}|{S,P,D/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-preparation.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-integration.md'}
with (H/'closure.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in sorted(files)},groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_ns=time.time_ns()),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));assert all(c.values())
