"""Fresh reviewer read-only verification; never imports author/frozen scripts."""
from pathlib import Path
import hashlib, json, subprocess
R=Path.cwd(); M=Path('/home/jspitz/JSimplex.jl'); H=R/'diagnostics/simplex-core-architecture/results/S5-AC'; B=H.parent/'S5-AB'
seen={}; checks={}; failures=[]
def sha(path):
 p=Path(path)
 if str(p) not in seen:
  d=hashlib.sha256()
  with p.open('rb') as f:
   for block in iter(lambda:f.read(1048576),b''): d.update(block)
  seen[str(p)]=d.hexdigest()
 return seen[str(p)]
def read(path):
 sha(path); return json.loads(Path(path).read_text())
def git(*args,root=R): return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def pins(obj):
 bad=[]
 for p,v in obj.items():
  expected=v['sha256'] if isinstance(v,dict) else v
  try:
   if sha(p)!=expected: bad.append(p)
  except OSError as exc: bad.append(p+': '+str(exc))
 failures.extend(bad); return not bad
for name,n,k in [('entry.json',1910,20),('source-check.json',25,19),('independent.json',6,8)]:
 d=read(H/name); checks[name]=len(d['sha256'])==n and len(d['checks'])==k and d['all_passed'] is True and all(d['checks'].values()) and pins(d['sha256'])
for name,n in [('reviewer-preservation.json',5),('review-fix.json',7),('review-fix-independent.json',5),('closure.json',35)]:
 d=read(B/name); checks['AB_'+name]=len(d['sha256'])==n and pins(d['sha256'])
expected_arch='98b380f86c519fbb1a1bacf92159aabc6c6809fc'; expected_master='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
refs={'architecture':git('rev-parse','HEAD'),'master':git('rev-parse','HEAD',root=M)}
checks['refs']=refs=={'architecture':expected_arch,'master':expected_master} and git('branch','--show-current')=='codex/simplex-core-architecture' and git('branch','--show-current',root=M)=='master'
remote=dict(line.split()[::-1] for line in git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())
checks['remote_refs']=remote=={'refs/heads/master':expected_master,'refs/heads/codex/simplex-core-architecture':expected_arch}
st=read(B/'staged-files.json')['sha256']; names=set(git('diff-tree','--no-commit-id','--name-only','-r',expected_arch).splitlines())
checks['AB_exact38']=len(st)==37 and names==set(st)|{str((B/'staged-files.json').relative_to(R))} and all(hashlib.sha256(subprocess.check_output(['git','-C',str(R),'show',expected_arch+':'+p])).hexdigest()==v and sha(R/p)==v for p,v in st.items())
files=git('ls-files','src','test').splitlines(); other=git('ls-files','src','test',root=M).splitlines()
checks['source_test511']=files==other and len(files)==511 and all(sha(R/p)==sha(M/p) for p in files)
checks['no_tracked_delta']=git('diff','HEAD','--name-only')==''
u=read(H.parent/'S5-AA/host-before.json')['user_hashes']; checks['user6']=len(u)==6 and pins(u)
e=read(H/'entry.json'); groups=set(e['groups']); live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text(); f=s[s.rfind(')')+2:].split(); comm=(p/'comm').read_text().strip()
  if int(f[2]) in groups or int(f[3]) in groups or comm.startswith('julia'): live.append({'pid':p.name,'pgid':f[2],'sid':f[3],'start_ticks':f[19],'comm':comm})
 except (FileNotFoundError,ProcessLookupError,PermissionError): pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
checks['full26_groups_AND_sessions_absent']=len(groups)==26 and not live and boot==e['boot_id']
for path in [R/'diagnostics/simplex-core-architecture/S5-CLEANUP-ENTRY-REUSE-DECISION.md',R/'docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md',Path(__file__)]:sha(path)
result={'checks':checks,'all_passed':all(checks.values()),'failures':failures,'sha256':seen,'refs':refs,'remote':remote,'groups':sorted(groups),'live':live,'boot_id':boot,'scope':'Rehashed all resolved physical entry/source/author pins; independent Git/user/source/process verification. No frozen script or Julia execution. Reviewer source-path read initially attempted nonexistent entry_check.py; retained in transcript, then read actual entry.py.'}
with (H/'reviewer-check-20261013.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':result['all_passed'],'hashes':len(seen),'failures':failures})); assert result['all_passed']
