"""New read-only entry checks. No historical executable is imported or run."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;A=H.parent/'S5-AA';D=H.parent.parent
cache={};maps=[];checks={}
def sha(p):
 p=Path(p)
 if str(p) not in cache:
  z=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):z.update(b)
  cache[str(p)]=z.hexdigest()
 return cache[str(p)]
def js(p):return json.loads(Path(p).read_text())
def bind(d,aa=False):
 bad=[]
 for k,v in d.items():
  p=Path(k)
  if aa and p==D/'STATUS.md':p=A/'STATUS.md.before-AA'
  if aa and p==R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':p=A/'2026-10-11-simplex-core-architecture.md.before-AA'
  if p in [r/'test/simplex_start_state_tests.jl' for r in (R,M)] and v=='47b2cc12ea40055262bc3912beb17cfd00a0ffe3b92e7ca54970dc85eae511ad':p=A/'original-test.jl'
  if str(p)!=k:maps.append(dict(original=k,resolved=str(p),sha256=v))
  if sha(p)!=v:bad.append(k)
 return bad
def gates(p,n):
 d=js(p);return len(d['checks'])==n and d['all_passed'] is True and all(x is True for x in d['checks'].values())
for n,num in [('admission-pins.json',1464),('green/pins.json',1468),('master/pins.json',1493)]:
 d=js(A/n); inv=d['inventory'] if 'inventory' in d else d['sha256']; inv={k:(v['sha256'] if isinstance(v,dict) else v) for k,v in inv.items()}
 bad=bind(inv,True);checks[n]=dict(pass_=len(inv)==num and not bad,count=len(inv),bad=bad)
d=js(A/'required-paths.json')['sha256'];checks['required1463']=dict(pass_=len(d)==1463 and not bind(d,True))
checks['AA_entry2_lineage']=dict(pass_=gates(A/'entry-2.json',38) and not bind(js(A/'entry-2.json')['sha256'],True))
for stage in ['green','master']:
 h=A/stage;a=js(h/'audit.json');p=js(h/'postcheck.json');B=R/'.superpowers/simplex-core-architecture/S5-AA'/f'{stage}-1'
 checks[stage+'_audit33_post10']=dict(pass_=gates(h/'audit.json',33) and gates(h/'postcheck.json',10) and len(p['sha256'])==9 and not bind(p['sha256']))
 checks[stage+'_raw8']=dict(pass_=len(a['raw_sha256'])==8 and all(sha(B/k)==sha(h/'portable'/k)==v for k,v in a['raw_sha256'].items()))
 checks[stage+'_inv3']=dict(pass_=len(a['invocation_sha256'])==3 and not bind(a['invocation_sha256']))
 checks[stage+'_review']=dict(pass_=all(t in (h/'review.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []']))
checks['admission_reviews']=dict(pass_=all('Verdict: ACCEPTED' in p.read_text() for p in [A/'admission-review.md',A/'master/admission-review.md']))
d=js(A/'master/stage-acceptance.json'); print('stage keys',list(d)); b=d['sha256'];checks['master36bindings']=dict(pass_=len(b)==36 and not bind(b),count=len(b))
checks['closure23_95']=dict(pass_=gates(A/'closure.json',23) and len(js(A/'closure.json')['sha256'])==95 and not bind(js(A/'closure.json')['sha256']))
checks['publication6']=dict(pass_=gates(A/'publication-check.json',6))
st=js(A/'staged-files.json')['sha256'];commit='e701e1ecd5536411fa89a41c15b11d603d44dba3';names=set(subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],text=True).splitlines())
checks['committed_exact99']=dict(pass_=len(st)==98 and not bind({str(R/k):v for k,v in st.items()}) and all(hashlib.sha256(subprocess.check_output(['git','show',commit+':'+k])).hexdigest()==v for k,v in st.items()) and names==set(st)|{str((A/'staged-files.json').relative_to(R))})
files=subprocess.check_output(['git','ls-files','src','test'],text=True).splitlines();checks['source_test511']=dict(pass_=len(files)==511 and all(sha(R/f)==sha(M/f) for f in files),count=len(files))
checks['canonical_test']=dict(pass_=all(sha(r/'test/simplex_start_state_tests.jl')=='ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f' for r in (R,M)))
checks['user6']=dict(pass_=not bind(js(A/'host-before.json')['user_hashes']))
groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826,75902,75907,76742,76746,84681,84689,89395,89399,90313,90323};live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
  if int(v[2]) in groups or int(v[3]) in groups or comm.startswith('julia'):live.append(dict(pid=int(p.name),pgid=int(v[2]),sid=int(v[3]),start_ticks=v[19],command=cmd))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
checks['full26groups_sessions_absent']=dict(pass_=not live,live=live)
refs={str(r):subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip() for r in (R,M)}
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True)
checks['refs_remote']=dict(pass_=refs[str(R)]==commit and refs[str(M)]=='d02416c108f06fcd41d58e0a1980b70a51fef9ef' and all(x in remote for x in refs.values()))
result=dict(checks=checks,all_passed=all(v['pass_'] for v in checks.values()),sha256=cache,mappings=maps,refs=refs,remote=remote,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups))
with (H/'entry.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,hashes=len(cache),all_passed=result['all_passed'])));assert result['all_passed']
