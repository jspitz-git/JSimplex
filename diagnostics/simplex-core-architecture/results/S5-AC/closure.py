"""Exclusive separate closure; rehash outputs, never run historical executables."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;D=H.parent.parent;cache={}
def sh(p):
 p=Path(p)
 if str(p) not in cache:
  z=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):z.update(b)
  cache[str(p)]=z.hexdigest()
 return cache[str(p)]
def js(p):return json.loads(Path(p).read_text())
mp={x['original']:x['preserved'] for x in js(H/'before-texts.json')['mappings']}
def verify(d,historical=True):return all(sh(mp.get(p,p) if historical else p)==v for p,v in d.items())
c={}
for name,n in [('entry.json',20),('source-check.json',19),('independent.json',8)]:
 d=js(H/name);c[name]=d['all_passed'] is True and len(d['checks'])==n and all(d['checks'].values()) and verify(d['sha256'])
c['accepted_review']=all(t in (H/'review.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
c['preserved_AB35closure']=verify(js(H.parent/'S5-AB/closure.json')['sha256'])
c['continuation_binding']=js(H/'continuation.json')['all_passed'] is True and verify(js(H/'continuation.json')['sha256'],False)
c['before_texts']=all(sh(x['preserved'])==x['sha256'] for x in js(H/'before-texts.json')['mappings'])
e=js(H/'entry.json');groups=set(e['groups']);live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  t=(p/'stat').read_text();v=t[t.rfind(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().startswith('julia'):live.append(dict(pid=p.name,pgid=v[2],sid=v[3],start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
c['full26groups_sessions']=len(groups)==26 and not live
refs={str(r):subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip() for r in (R,M)};c['refs_unchanged']=refs==e['refs']
files=subprocess.check_output(['git','ls-files','src','test'],text=True).splitlines();c['source_test511']=len(files)==511 and all(sh(R/f)==sh(M/f) for f in files)
users={p:v for p,v in e['sha256'].items() if p in [str(r/f) for r in (R,M) for f in ['Manifest.toml','LocalPreferences.toml','.vscode/settings.json']]};c['user6']=len(users)==6 and verify(users)
allowed=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];c['only_continuation_tracked']=set(subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines())==set(allowed)
base=[D/'S5-CLEANUP-ENTRY-REUSE-DECISION.md',D/'S5-CLEANUP-ENTRY-REUSE-DECISION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md',*[R/p for p in allowed]]
c['next_step_source_only']='SOURCE/EVIDENCE ONLY' in base[2].read_text() and 'S6-AP' in base[2].read_text()
bind={str(p):sh(p) for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ['closure.json','publication-check.json','staged-files.json']}
for p in base:bind[str(p)]=sh(p)
with (H/'closure.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=bind,refs=refs,groups=sorted(groups),live=live,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(bind))));assert all(c.values())
