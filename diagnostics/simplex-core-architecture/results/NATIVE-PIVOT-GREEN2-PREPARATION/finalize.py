"""One-shot OFFLINE GREEN-2 preparation closure AFTER independent review."""
from pathlib import Path
import json,hashlib,sys,subprocess
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';R=D.parents[3];RUN=Q/'runs/green'
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
a=rd(RUN/'audit.json');require(a['all_passed'] is False and bound(a),'Original failed audit')
pins=D/'preparation-pins.json';review=rd(D/'review-final.json')
verify_review(review,pins,list(rd(pins)['sha256'])+[str(pins)],'offline preparation')
require(rd(D/'source-check.json')['all_passed'] is True and bound(rd(D/'source-check.json')),'Source checks')
require(rd(D/'offline-GREEN.json')['all_passed'] is True,'Synthetic checks')
h=full_host(rd(RUN/'posthost.json')['groups']);save(D/'closure-host.json',h)
require(not h['matches'] and len(h['groups'])==212 and h['head']=='30b0b3402ef5d319c8faa0a78aca32ca3c354d22' and h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and h['boot_id']==rd(RUN/'sealed.json')['boot_id'],'Fresh host')
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Clean tracked/index')
preserved={str(STATUS):D/'STATUS.md.before-green2',str(ROAD):D/'roadmap.md.before-green2'}
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
for rec in sorted(list((D.parent/'NATIVE-PIVOT-OBSERVER-FIX').glob('*.json'))+list(D.glob('*.json'))):walk(rec,rd(rec))
require(len(maps)>=4,'Missing continuation mappings')
save(D/'continuation-mappings.json',dict(mappings=maps,scope='Only exact current STATUS/roadmap bindings map to preserved before-fix bytes; every older mapping remains'))
text=(D/'continuation-text.md').read_text().strip()+'\n'
s=STATUS.read_text();start=s.index('## Exact next action\n');end=s.index('\n## ',start+1);STATUS.write_text(s[:start]+'## Exact next action\n\n'+text+s[end:])
ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot GREEN-2 preparation (2026-10-16)\n\n'+text)
def mapped(rec):
 z=rd(rec)
 for m in [m for m in maps if m['record']==str(rec.relative_to(R))]:
  obj=z
  for key in m['pointer']:obj=obj[key]
  if obj!=m['sha256'] or sha(R/m['preserved_path'])!=obj:return False
 return True
checks=dict(new_stage_absent=not (R/'.superpowers/native-pivot-green2/green2').exists() and not (D/'runs').exists(),offline_review=bound(review),audit=bound(a),source_check=bound(rd(D/'source-check.json')),new_pins=bound(rd(pins)),current_maps=all(mapped(R/m['record']) for m in maps),host=not h['matches'],no_cost={p.name for p in (Q/'runs').iterdir()}=={'red','green'},actual_unchanged=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'),old_cost_false=rd(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,index_empty=not git('diff','--cached','--name-only'))
names=rd(D/'publication-names.json')['names'];actual={str(p.relative_to(R)) for base in [D] for p in base.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [STATUS,ROAD,D/'closure.json',D/'publication.json']}
checks['exact_names']=set(names)==actual and len(names)==len(set(names))
files=[R/n for n in names if n not in [str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))]]
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='OFFLINE GREEN-2 preparation only; no Julia, old failed GREEN unchanged, no runtime qualification'))
require(all(checks.values()),'Closure failed: preserve');print(dict(checks=len(checks),mappings=len(maps),bindings=len(files),all_passed=True))
