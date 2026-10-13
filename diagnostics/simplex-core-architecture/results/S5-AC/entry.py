"""Exclusive S5-AC read-only host and predecessor binding verification."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;B=H.parent/'S5-AB';A=H.parent/'S5-AA';D=H.parent.parent
cache={};maps=[];c={}
def sh(p):
 p=Path(p)
 if str(p) not in cache:
  z=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):z.update(b)
  cache[str(p)]=z.hexdigest()
 return cache[str(p)]
def js(p):sh(p);return json.loads(Path(p).read_text())
before={x['original']:x['preserved'] for x in js(B/'before-texts.json')['mappings']}
def verify(d,scope='AB'):
 bad=[]
 for k,v in d.items():
  v=v['sha256'] if isinstance(v,dict) else v;p=Path(k)
  if scope=='AB' and k in before:p=Path(before[k])
  if scope=='AB' and p==D/'S5-HANDOFF-COVERAGE-RECONCILIATION.md' and v==sh(B/'S5-HANDOFF-COVERAGE-RECONCILIATION.md.before-review'):p=B/'S5-HANDOFF-COVERAGE-RECONCILIATION.md.before-review'
  if scope=='AA' and p==D/'STATUS.md':p=A/'STATUS.md.before-AA'
  if scope=='AA' and p==R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':p=A/'2026-10-11-simplex-core-architecture.md.before-AA'
  if p in [r/'test/simplex_start_state_tests.jl' for r in (R,M)] and v=='47b2cc12ea40055262bc3912beb17cfd00a0ffe3b92e7ca54970dc85eae511ad':p=A/'original-test.jl'
  if str(p)!=k:maps.append(dict(original=k,resolved=str(p),sha256=v))
  if sh(p)!=v:bad.append(k)
 return bad
for name,n in [('entry.json',23),('reconciliation-2.json',10),('source-contract.json',23),('independent.json',8),('review-fix.json',8),('review-fix-independent.json',5),('closure.json',16),('publication-check.json',6)]:
 d=js(B/name);c[name]=len(d['checks'])==n and d['all_passed'] is True and not verify(d.get('sha256',{}),'CURRENT' if name in ['closure.json','publication-check.json'] else 'AB')
c['AB35closurebindings']=len(js(B/'closure.json')['sha256'])==35
for name in ['review-initial.md','finalreview.md','reviewer-check-failures.md','reviewer-preservation.json']:sh(B/name)
c['rejection_and_final_preserved']='Verdict: REJECTED' in (B/'review-initial.md').read_text() and 'Verdict: ACCEPTED' in (B/'finalreview.md').read_text()
for name,n in [('admission-pins.json',1464),('required-paths.json',1463),('green/pins.json',1468),('master/pins.json',1493)]:
 d=js(A/name);inv=d.get('inventory',d.get('sha256'));c['AA_'+name]=len(inv)==n and not verify(inv,'AA')
c['AA95closurebindings']=len(js(A/'closure.json')['sha256'])==95 and not verify(js(A/'closure.json')['sha256'])
commit='98b380f86c519fbb1a1bacf92159aabc6c6809fc';st=js(B/'staged-files.json')['sha256'];names=set(subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],text=True).splitlines())
c['AB_exact38committed']=len(st)==37 and names==set(st)|{str((B/'staged-files.json').relative_to(R))} and all(hashlib.sha256(subprocess.check_output(['git','show',commit+':'+p])).hexdigest()==v and sh(R/p)==v for p,v in st.items())
files=subprocess.check_output(['git','ls-files','src','test'],text=True).splitlines();c['source_test511']=len(files)==511 and all(sh(R/f)==sh(M/f) for f in files)
c['user6']=not verify(js(A/'host-before.json')['user_hashes'],'CURRENT')
groups=set(js(B/'entry.json')['groups']);live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().startswith('julia'):live.append(dict(pid=p.name,pgid=v[2],sid=v[3],start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
c['full26groups_sessions_absent']=len(groups)==26 and not live
refs={str(r):subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip() for r in (R,M)};remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True)
c['refs_remotes']=refs[str(R)]==commit and refs[str(M)]=='d02416c108f06fcd41d58e0a1980b70a51fef9ef' and all(v in remote for v in refs.values())
sh(__file__)
with (H/'entry.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=cache,mappings=maps,refs=refs,remote=remote,groups=sorted(groups),live=live,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,hashes=len(cache))));assert all(c.values())
