"""Exclusive final closure. Read old outputs; never execute old scripts."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;M=Path('/home/jspitz/JSimplex.jl');cache={}
def sh(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 cache[str(p)]=h.hexdigest();return h.hexdigest()
def js(p):return json.loads(Path(p).read_text())
mp={x['original']:x['preserved'] for x in js(H/'before-texts.json')['mappings']}
def verify(d):return all(sh(mp.get(p,p))==v for p,v in d.items())
c={}
for name,num in [('entry.json',23),('reconciliation-2.json',10),('source-contract.json',23),('independent.json',8)]:
 d=js(H/name);c[name]=d['all_passed'] is True and len(d['checks'])==num and verify(d['sha256'])
review=(H/'review.md').read_text();c['independent_review_accepted']=all(t in review for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
c['before_text_identity']=all(sh(x['preserved'])==x['sha256'] for x in js(H/'before-texts.json')['mappings'])
a=js(H.parent/'S5-AA/closure.json');c['AA95bindings_preserved']=len(a['sha256'])==95 and verify(a['sha256'])
c['actual_canonical_tests']=all(sh(r/'test/simplex_start_state_tests.jl')=='ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f' for r in (R,M))
files=subprocess.check_output(['git','ls-files','src','test'],text=True).splitlines();c['source_test511']=len(files)==511 and all(sh(R/f)==sh(M/f) for f in files)
e=js(H/'entry.json');users={p:v for p,v in e['sha256'].items() if p in [str(r/f) for r in (R,M) for f in ['Manifest.toml','LocalPreferences.toml','.vscode/settings.json']]};c['user6']=len(users)==6 and verify(users)
groups=set(e['groups']);live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  text=(p/'stat').read_text();v=text[text.rfind(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().startswith('julia'):live.append(dict(pid=p.name,pgid=v[2],sid=v[3],start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
c['full26groups_sessions_absent']=not live and len(groups)==26
refs={str(r):subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip() for r in (R,M)};c['refs_unchanged']=refs==e['refs']
allowed=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];changed=subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines();c['only_continuation_tracked_edits']=set(changed)==set(allowed)
report=D/'S5-HANDOFF-COVERAGE-RECONCILIATION.md';comp=D/'S5-HANDOFF-COVERAGE-RECONCILIATION-REVIEW.md';plan=R/'docs/superpowers/plans/2026-10-13-cleanup-entry-reuse-design-decision.md'
c['continuation_bound']=all('S5-AC' in (R/p).read_text() and 'S5-AB' in (R/p).read_text() for p in allowed)
bind={str(p):sh(p) for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ['closure.json','publication-check.json','staged-files.json']}
for p in [report,comp,plan,*[R/p for p in allowed]]:bind[str(p)]=sh(p)
with (H/'closure.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=bind,refs=refs,groups=sorted(groups),live=live,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(bind))));assert all(c.values())
