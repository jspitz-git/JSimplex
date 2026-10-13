"""Exclusive offline entry verification; never executes historical scripts."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;Y=H.parent/'S5-Y';X=H.parent/'S5-X';W=H.parent/'S5-W';U=H.parent/'S5-U';M=Path('/home/jspitz/JSimplex.jl');S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';cache={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def bind(d,mp={}):return all(sha(mp.get(k,k))==v for k,v in d.items())
def good(p,n):
 a=read(p);return len(a['checks'])==n and a['all_passed'] is True and all(v is True for v in a['checks'].values())
mp={str(S):Y/'STATUS.md.before-Y',str(P):Y/'2026-10-11-simplex-core-architecture.md.before-Y'}
c={}
for name,n in [('pins.json',1347),('admission-pins.json',1344)]:
 a=read(Y/name)['inventory'];c[name]=len(a)==n and bind({k:v['sha256'] for k,v in a.items()},mp) and all(str(Path(k).resolve())==v['resolved'] for k,v in a.items())
for name,n in [('audit.json',23),('postcheck.json',11),('closure.json',17),('publication-check.json',6),('entry.json',18)]:c[name]=good(Y/name,n)
c['closure51']=len(read(Y/'closure.json')['sha256'])==51 and bind(read(Y/'closure.json')['sha256'])
c['post8']=len(read(Y/'postcheck.json')['sha256'])==8 and bind(read(Y/'postcheck.json')['sha256'])
a=read(Y/'audit.json');B=R/'.superpowers/simplex-core-architecture/S5-Y/qualification-1';c['raw6']=len(a['raw_sha256'])==6 and all(sha(B/k)==sha(Y/'portable'/k)==v for k,v in a['raw_sha256'].items());c['invocation3']=len(a['invocation_sha256'])==3 and bind(a['invocation_sha256'])
st=read(Y/'staged-files.json')['sha256'];c['exact53']=len(st)==52 and bind({str(R/k):v for k,v in st.items()}) and all(hashlib.sha256(subprocess.check_output(['git','show','2850c7e:'+k])).hexdigest()==v for k,v in st.items()) and set(subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r','2850c7e'],text=True).splitlines())==set(st)|{str((Y/'staged-files.json').relative_to(R))}
c['reviews']=all('Verdict: ACCEPTED' in (Y/f).read_text() and 'Unresolved findings: []' in (Y/f).read_text() for f in ['admission-review.md','review.md'])
c['X213']=bind(read(X/'evidence.json')['sha256']);c['Xauthor10']=bind(read(X/'independent.json')['sha256']);c['Xclosure23']=bind(read(X/'closure.json')['sha256'],mp)
wm={str(S):X/'STATUS.md.before-X',str(P):X/'2026-10-11-simplex-core-architecture.md.before-X'};c['Wclosure21']=bind(read(W/'closure.json')['sha256'],wm)
def old(k,v):
 if k in [str(r/'test/simplex_precision_tests.jl') for r in (R,M)] and v=='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5':return U/'original-test.jl'
 if k==str(S):return U/'STATUS.md.before-U'
 if k==str(P):return U/'2026-10-11-simplex-core-architecture.md.before-U'
 return k
for stage,n in [('master',1512),('green',1489)]:
 a=read(U/stage/'pins.json')['inventory'];c['U_'+stage]=len(a)==n and all(sha(old(k,v['sha256']))==v['sha256'] for k,v in a.items())
a=read(H.parent/'S5-T/pins.json')['sha256'];c['T891']=len(a)==891 and all(sha(old(k,v))==v for k,v in a.items())
c['candidate']=sha(X/'candidate.jl')=='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18';c['inverse']=sha(X/'construction-inverse.txt')==sha(W/'original-testset.txt') and (W/'original-testset.txt').read_bytes() in (R/'test/simplex_start_state_tests.jl').read_bytes();c['user6']=bind(read(Y/'host.json')['user_hashes']);c['source_test_equal']=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml'])
with (H/'entry.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),fresh_hashes=len(cache)),f,indent=2);f.write('\n')
print(json.dumps(c));assert all(c.values())
