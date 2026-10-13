"""Exclusive final closure; no old executable execution."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;D=H.parent.parent;cache={}
def sh(p):
 p=Path(p)
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def js(p):return json.loads(Path(p).read_text())
records=js(H/'before-texts.json')['mappings']+js(H/'user-reply-before-texts.json')['mappings']
def verify(d):
 return all(sh(p)==v or any(x['original']==p and x['sha256']==v and sh(x['preserved'])==v for x in records) for p,v in d.items())
c={}
for name,n in [('entry.json',15),('provenance.json',17),('independent-supplement.json',4)]:
 d=js(H/name);c[name]=d['all_passed'] is True and len(d['checks'])==n and all(d['checks'].values()) and verify(d['sha256'])
a=js(H/'independent.json');c['initial_false_preserved_and_all_hashes']=a['all_passed'] is False and sum(a['checks'].values())==3 and len(a['checks'])==4 and verify(a['sha256'])
c['review_accepted']=all(t in (H/'finalreview.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
r=js(H/'reviewer-check.json');c['reviewer13_and_hashes']=r['all_passed'] is True and len(r['checks'])==13 and all(r['checks'].values()) and verify(r['sha256'])
u=js(H/'user-linkage.json');c['user_linkage9']=u['all_passed'] is True and len(u['checks'])==9 and all(u['checks'].values()) and verify(u['sha256'])
v=js(H/'reviewer-user-check.json');c['user_review_checks']=v['all_passed'] is True and all(v['checks'].values()) and verify(v['sha256'])
c['before_texts']=all(sh(x['preserved'])==x['sha256'] for x in js(H/'before-texts.json')['mappings'])
c['predecessor_closure33']=len(js(H.parent/'S5-AC/closure.json')['sha256'])==33 and verify(js(H.parent/'S5-AC/closure.json')['sha256'])
e=js(H/'entry.json');groups=set(e['groups']);live=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().startswith('julia'):live.append(dict(pid=p.name,pgid=v[2],sid=v[3],start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
c['all26groups_sessions_absent']=len(groups)==26 and not live
refs={str(r):subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip() for r in (R,M)};c['refs_unchanged']=refs==e['refs']
files=subprocess.check_output(['git','ls-files','src','test'],text=True).splitlines();c['source511']=len(files)==511 and all(sh(R/f)==sh(M/f) for f in files)
c['user6']=len(e['user_hashes'])==6 and verify(e['user_hashes'])
allowed=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];c['only_continuation_tracked']=set(subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines())==set(allowed)
p=R/'docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md';c['nextstep_only_new_evidence']='Continue only when genuinely new' in p.read_text()
base=[p,D/'S6-TEST-MPS-FAILURE-PROVENANCE.md',D/'S6-TEST-MPS-FAILURE-PROVENANCE-REVIEW.md',*[R/x for x in allowed]]
bind={str(p):sh(p) for p in sorted(H.rglob('*')) if p.is_file() and p.name not in ['closure.json','publication-check.json','staged-files.json']}
for p in base:bind[str(p)]=sh(p)
with (H/'closure.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=bind,refs=refs,groups=sorted(groups),live=live,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(bind))));assert all(c.values())
