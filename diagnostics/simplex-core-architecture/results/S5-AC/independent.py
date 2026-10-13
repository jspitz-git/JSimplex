"""Exclusive author verification, independently reading saved evidence, not old code."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;B=H.parent/'S5-AB';D=H.parent.parent
cache={}
def sh(p):
 p=Path(p)
 if str(p) not in cache:
  z=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):z.update(b)
  cache[str(p)]=z.hexdigest()
 return cache[str(p)]
def js(p):return json.loads(Path(p).read_text())
e=js(H/'entry.json');s=js(H/'source-check.json');c={}
c['full1910entry_readtimehashes']=len(e['sha256'])==1910 and all(sh(p)==v for p,v in e['sha256'].items())
c['full25sourcehashes']=len(s['sha256'])==25 and all(sh(p)==v for p,v in s['sha256'].items())
c['entry20_source19']=len(e['checks'])==20 and len(s['checks'])==19 and e['all_passed'] is True and s['all_passed'] is True and all(e['checks'].values()) and all(s['checks'].values())
b=js(B/'reviewer-preservation.json');c['AB_reviewer_preservation5']=len(b['sha256'])==5 and all(sh(p)==v for p,v in b['sha256'].items())
for name,n in [('review-fix.json',7),('review-fix-independent.json',5)]:
 b=js(B/name);c['AB_'+name]=len(b['sha256'])==n and all(sh(p)==v for p,v in b['sha256'].items())
c['no_tracked_production_delta']=not subprocess.check_output(['git','diff','HEAD','--','src','test','Project.toml','.github'],text=True)
c['only_new_design_evidence']=not subprocess.check_output(['git','diff','--name-only','HEAD'],text=True)
for p in [H/'entry.json',H/'source-check.json',Path(__file__),B/'reviewer-preservation.json',B/'review-fix.json',B/'review-fix-independent.json']:sh(p)
bind={str(p):sh(p) for p in [H/'entry.json',H/'source-check.json',Path(__file__),B/'reviewer-preservation.json',B/'review-fix.json',B/'review-fix-independent.json']}
with (H/'independent.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),full_rehashed_files=len(cache),sha256=bind),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,full_rehashed_files=len(cache),bindings=len(bind))));assert all(c.values())
