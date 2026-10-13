"""Exclusive S5-Y entry; fresh hashes, no prior script import."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;X=H.parent/'S5-X';W=H.parent/'S5-W';U=H.parent/'S5-U';M=Path('/home/jspitz/JSimplex.jl');D=H.parent.parent;cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def read(p):return json.loads(Path(p).read_text())
def binds(x):return all(sha(k)==v for k,v in x.items())
def good(p,n):
 x=read(p);return len(x['checks'])==n and x['all_passed'] is True and all(v is True for v in x['checks'].values())
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
e=read(X/'evidence.json');a=read(X/'independent.json');c=read(X/'closure.json');st=read(X/'staged-files.json')['sha256'];S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
checks=dict(X213=len(e['sha256'])==213 and binds(e['sha256']),X22=good(X/'evidence.json',22),Xentry17=good(X/'entry.json',17),Xauthor9=good(X/'independent.json',9) and len(a['sha256'])==10 and binds(a['sha256']),Xclosure14=good(X/'closure.json',14) and len(c['sha256'])==23 and binds(c['sha256']),Xpublication7=good(X/'publication-check.json',7),X26=len(st)==25 and binds({str(R/k):v for k,v in st.items()}) and all(hashlib.sha256(subprocess.check_output(['git','show','f45899f:'+k])).hexdigest()==v for k,v in st.items()) and set(subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r','f45899f'],text=True).splitlines())==set(st)|{str((X/'staged-files.json').relative_to(R))},Xreview='Verdict: ACCEPTED' in (X/'review.md').read_text() and 'Unresolved findings: []' in (X/'review.md').read_text(),candidate=sha(X/'candidate.jl')=='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18',original6=sha(X/'construction-inverse.txt')==sha(W/'original-testset.txt') and (W/'original-testset.txt').read_text() in (R/'test/simplex_start_state_tests.jl').read_text())
wm={str(S):X/'STATUS.md.before-X',str(P):X/'2026-10-11-simplex-core-architecture.md.before-X'};checks['Wclosure21']=all(sha(wm.get(k,k))==v for k,v in read(W/'closure.json')['sha256'].items())
def old(k,v):
 if k in [str(r/'test/simplex_precision_tests.jl') for r in (R,M)] and v=='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5':return U/'original-test.jl'
 if k==str(S):return U/'STATUS.md.before-U'
 if k==str(P):return U/'2026-10-11-simplex-core-architecture.md.before-U'
 return k
for stage,n in [('master',1512),('green',1489)]:
 inv=read(U/stage/'pins.json')['inventory'];checks[stage+'_pins']=len(inv)==n and all(sha(old(k,v['sha256']))==v['sha256'] for k,v in inv.items())
t=read(H.parent/'S5-T/pins.json')['sha256'];checks['T891']=len(t)==891 and all(sha(old(k,v))==v for k,v in t.items())
users=read(X/'host.json')['user_hashes'];checks['user6']=len(users)==6 and binds(users)
G=set(read(X/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full20_noJulia']=len(G)==20 and not matches
refs=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines();checks['refs']=refs==['f45899f3b06c819943498f9906c8ffefca31c15a','2b546e946ddb7fdb6c0092df9cc19f566e301aa2'];checks['source_test_equal']=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml'])
dump(H/'host.json',dict(groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),refs=refs,remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True),user_hashes=users,time_ns=time.time_ns()))
dump(H/'entry.json',dict(checks=checks,all_passed=all(checks.values())));print(json.dumps(checks));assert all(checks.values())
