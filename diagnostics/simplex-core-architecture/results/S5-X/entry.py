"""Exclusive S5-X entry validation, saved before execution; no prior script import."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;W=H.parent/'S5-W';V=H.parent/'S5-V';U=H.parent/'S5-U';M=Path('/home/jspitz/JSimplex.jl');cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def read(p):return json.loads(Path(p).read_text())
def bindings(x):return all(sha(k)==v for k,v in x.items())
def good(x,n):return len(x['checks'])==n and x['all_passed'] is True and all(v is True for v in x['checks'].values())
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
e=read(W/'evidence.json');a=read(W/'independent.json');c=read(W/'closure.json');st=read(W/'staged-files.json')['sha256']
checks=dict(W189=len(e['sha256'])==189 and bindings(e['sha256']),W19=good(e,19),Wentry14=good(read(W/'entry.json'),14),Wauthor8=good(a,8) and len(a['sha256'])==8 and bindings(a['sha256']),Wclosure13=good(c,13) and len(c['sha256'])==21 and bindings(c['sha256']),Wpublication7=good(read(W/'publication-check.json'),7),W24=len(st)==23 and bindings({str(R/k):v for k,v in st.items()}) and all(hashlib.sha256(subprocess.check_output(['git','show','9ac5e09:'+k])).hexdigest()==v for k,v in st.items()) and set(subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r','9ac5e09'],text=True).splitlines())==set(st)|{str((W/'staged-files.json').relative_to(R))},Wreview='Verdict: ACCEPTED' in (W/'review.md').read_text() and 'Unresolved findings: []' in (W/'review.md').read_text(),original6=(W/'original-testset.txt').read_text() in (R/'test/simplex_start_state_tests.jl').read_text() and (W/'original-testset.txt').read_text().count('@test ')==6)
vm={str(D/'STATUS.md'):W/'STATUS.md.before-W',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):W/'2026-10-11-simplex-core-architecture.md.before-W'};checks['Vclosure24']=all(sha(vm.get(k,k))==v for k,v in read(V/'closure.json')['sha256'].items())
def old(k,v):
 if k in [str(r/'test/simplex_precision_tests.jl') for r in (R,M)] and v=='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5':return U/'original-test.jl'
 if k==str(D/'STATUS.md'):return U/'STATUS.md.before-U'
 if k==str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):return U/'2026-10-11-simplex-core-architecture.md.before-U'
 return Path(k)
for stage,n in [('master',1512),('green',1489)]:
 inv=read(U/stage/'pins.json')['inventory'];checks[stage+'_pins']=len(inv)==n and all(sha(old(k,v['sha256']))==v['sha256'] for k,v in inv.items())
t=read(H.parent/'S5-T/pins.json')['sha256'];checks['T891']=len(t)==891 and all(sha(old(k,v))==v for k,v in t.items())
users=read(W/'host.json')['user_hashes'];checks['user6']=len(users)==6 and bindings(users)
G=set(read(W/'host.json')['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full20_noJulia']=len(G)==20 and not matches
refs=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines();checks['refs']=refs==['9ac5e0976630fee420cd47c870f2240b9de8176b','2b546e946ddb7fdb6c0092df9cc19f566e301aa2'];checks['source_test_equal']=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml'])
dump(H/'host.json',dict(groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),refs=refs,remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True),user_hashes=users,time_ns=time.time_ns()))
dump(H/'entry.json',dict(checks=checks,all_passed=all(checks.values())));print(json.dumps(checks));assert all(checks.values())
