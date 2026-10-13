"""Exclusive new predecessor/host verification; no frozen executable is run."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;A=H.parent/'S5-AC';D=H.parent.parent;cache={};maps=[];c={}
def sh(p):
 p=Path(p)
 if str(p) not in cache:
  z=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):z.update(b)
  cache[str(p)]=z.hexdigest()
 return cache[str(p)]
def js(p):sh(p);return json.loads(Path(p).read_text())
mp={x['original']:x['preserved'] for x in js(A/'before-texts.json')['mappings']};old='36e96502096ea0677fa13a4970c217b030375020202226d6b137ca054ac38ef7'
def verify(d,historical=True):
 bad=[]
 for k,v in d.items():
  p=Path(k)
  if historical and k in mp:p=Path(mp[k])
  if p==D/'S5-CLEANUP-ENTRY-REUSE-DECISION.md' and v==old:p=A/'S5-CLEANUP-ENTRY-REUSE-DECISION.md.before-review'
  if str(p)!=k:maps.append(dict(original=k,resolved=str(p),sha256=v))
  if sh(p)!=v:bad.append(k)
 return bad
for name,n in [('entry.json',20),('source-check.json',19),('independent.json',8),('review-fix.json',6),('reviewer-check-20261013.json',14),('reviewer-fix-check-20261013-2.json',12),('closure.json',15),('publication-check.json',6)]:
 d=js(A/name);c[name]=d['all_passed'] is True and len(d['checks'])==n and not verify(d.get('sha256',{}),name not in ['closure.json','publication-check.json'])
c['closure33']=len(js(A/'closure.json')['sha256'])==33
for name in ['review-initial.md','review.md','reviewer-check-failure.md','reviewer-read-failure.md','read-selector-failures.md']:sh(A/name)
c['reviews_preserved']='Verdict: REJECTED' in (A/'review-initial.md').read_text() and all(t in (A/'review.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
commit='393067527dc04eb817c6af75347770b69a1905ee';st=js(A/'staged-files.json')['sha256'];names=set(subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],text=True).splitlines());c['exact36committed']=len(st)==35 and names==set(st)|{str((A/'staged-files.json').relative_to(R))} and all(sh(R/p)==v and hashlib.sha256(subprocess.check_output(['git','show',commit+':'+p])).hexdigest()==v for p,v in st.items())
files=subprocess.check_output(['git','ls-files','src','test'],text=True).splitlines();c['source511']=len(files)==511 and all(sh(R/p)==sh(M/p) for p in files)
e=js(A/'entry.json');users={p:v for p,v in e['sha256'].items() if p in [str(r/f) for r in (R,M) for f in ['Manifest.toml','LocalPreferences.toml','.vscode/settings.json']]};c['user6']=len(users)==6 and not verify(users,False)
groups=set(e['groups']);live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().startswith('julia'):live.append(dict(pid=p.name,pgid=v[2],sid=v[3],start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
c['full26groups_sessions_absent']=len(groups)==26 and not live
refs={str(r):subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip() for r in (R,M)};remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True);c['refs_remote']=refs[str(R)]==commit and refs[str(M)]=='d02416c108f06fcd41d58e0a1980b70a51fef9ef' and all(v in remote for v in refs.values())
sh(__file__)
with (H/'entry.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=cache,mappings=maps,groups=sorted(groups),live=live,refs=refs,remote=remote,user_hashes=users,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,hashes=len(cache))));assert all(c.values())
