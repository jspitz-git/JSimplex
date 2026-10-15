"""One-shot result continuation and closure AFTER independent RED acceptance."""
from pathlib import Path
import json,hashlib,sys,subprocess
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';R=D.parents[3];RUN=Q/'runs/red'
sys.path.insert(0,str(Q));from control_reviewed import full_host,verify_review
STATUS=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def require(x,m):
 if not x:raise RuntimeError(m)
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def bound(z):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in z['sha256'].items())
a=rd(RUN/'audit.json');require(a['all_passed'] is True and bound(a),'Audit')
verify_review(rd(RUN/'result-review.json'),RUN/'audit.json',list(a['sha256'])+[str(RUN/'audit.json')],'stage result','red')
require(rd(D/'postcheck.json')['all_passed'] is True and bound(rd(D/'postcheck.json')),'Author postcheck')
h=full_host(rd(RUN/'posthost.json')['groups']);save(D/'closure-host.json',h)
require(not h['matches'] and len(h['groups'])==210 and h['head']=='0798705ae92aa2f908b7468439b984deccde4c68' and h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and h['boot_id']==rd(RUN/'sealed.json')['boot_id'],'Fresh host')
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Clean tracked/index')
preserved={str(STATUS):D/'STATUS.md.before-RED',str(ROAD):D/'roadmap.md.before-RED'}
require(all(sha(n)==sha(p) for n,p in preserved.items()),'Continuation preimage')
maps=[]
def walk(rec,obj,loc=()):
 if isinstance(obj,dict):
  for k,v in obj.items():
   full=str(Path(k) if Path(k).is_absolute() else R/k)
   if full in preserved:
    value=v if isinstance(v,str) else v.get('sha256') if isinstance(v,dict) else None
    if value==sha(preserved[full]):maps.append(dict(record=str(rec.relative_to(R)),pointer=list(loc)+( [k] if isinstance(v,str) else [k,'sha256']),key=k,sha256=value,preserved_path=str(preserved[full].relative_to(R))))
   walk(rec,v,loc+(k,))
 elif isinstance(obj,list):
  for i,v in enumerate(obj):walk(rec,v,loc+(i,))
for rec in sorted(list(Q.rglob('*.json'))+list(D.glob('*.json'))):walk(rec,rd(rec))
require(len(maps)>=12,'Missing continuation mappings')
save(D/'continuation-mappings.json',dict(mappings=maps,scope='Only exact current STATUS/roadmap bindings map to preserved before-RED bytes; every older mapping remains'))
text=(D/'continuation-text.md').read_text().strip()+'\n'
s=STATUS.read_text();start=s.index('## Exact next action\n');end=s.index('\n## ',start+1);STATUS.write_text(s[:start]+'## Exact next action\n\n'+text+s[end:])
ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot policy expected RED (2026-10-15)\n\n'+text)
def mapped(rec):
 z=rd(rec)
 for m in [m for m in maps if m['record']==str(rec.relative_to(R))]:
  obj=z
  for key in m['pointer']:obj=obj[key]
  if obj!=m['sha256'] or sha(R/m['preserved_path'])!=obj:return False
 return True
checks=dict(result_review=bound(rd(RUN/'result-review.json')),audit=bound(a),postcheck=bound(rd(D/'postcheck.json')),preparation=bound(rd(Q/'preparation-pins-reviewed.json')),current_maps=all(mapped(R/m['record']) for m in maps),host=not h['matches'],only_red={p.name for p in (Q/'runs').iterdir()}=={'red'},actual_unchanged=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'),old_cost_false=rd(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,index_empty=not git('diff','--cached','--name-only'))
names=rd(D/'publication-names.json')['names'];actual={str(p.relative_to(R)) for base in [D,RUN] for p in base.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [STATUS,ROAD,D/'closure.json',D/'publication.json']}
checks['exact_names']=set(names)==actual and len(names)==len(set(names))
files=[R/n for n in names if n not in [str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))]]
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='Accepted expected RED only; GREEN/cost remain unexecuted'))
require(all(checks.values()),'Closure failed: preserve');print(dict(checks=len(checks),mappings=len(maps),bindings=len(files),all_passed=True))
