"""One-shot OFFLINE cost preparation closure after independent review."""
from control import *

def main():
 pins=D/'preparation-pins.json';z=rd(pins);review=rd(D/'review-final.json')
 verify_review(review,pins,list(z['sha256'])+[str(pins)],'offline preparation')
 require(bindings(z),'Preparation pins')
 require(rd(D/'source-check.json')['all_passed'] is True and bindings(rd(D/'source-check.json')),'Source checks')
 require(rd(D/'offline-GREEN.json')['all_passed'] is True and rd(D/'offline-RED.json')['all_passed'] is False,'Synthetic RED/GREEN')
 _,groups=predecessor('cost');h=full_host(groups);save(D/'closure-host.json',h);verify_host(h)
 require(len(h['groups'])==214,'Complete process groups')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Clean tracked/index')
 preserved={str(STATUS):D/'STATUS.md.before-cost',str(ROAD):D/'roadmap.md.before-cost'}
 require(all(sha(n)==sha(p) for n,p in preserved.items()),'Continuation preimages')
 maps=[]
 def walk(rec,obj,loc=()):
  if isinstance(obj,dict):
   for k,v in obj.items():
    full=str(path(k))
    if full in preserved:
     value=v if isinstance(v,str) else v.get('sha256') if isinstance(v,dict) else None
     if value==sha(preserved[full]):maps.append(dict(record=str(rec.relative_to(R)),pointer=list(loc)+([k] if isinstance(v,str) else [k,'sha256']),key=k,sha256=value,preserved_path=str(preserved[full].relative_to(R))))
    walk(rec,v,loc+(k,))
  elif isinstance(obj,list):
   for i,v in enumerate(obj):walk(rec,v,loc+(i,))
 for rec in sorted(list(RESULT.glob('*.json'))+list(D.glob('*.json'))):walk(rec,rd(rec))
 require(len(maps)>=4,'Current closure/publication mapping missing')
 save(D/'continuation-mappings.json',dict(mappings=maps,scope='Only current exact GREEN-2 STATUS/roadmap digests map to before-cost copies; all older mappings unchanged'))
 text=(D/'continuation-text.md').read_text().strip()+'\n';s=STATUS.read_text();start=s.index('## Exact next action\n');end=s.index('\n## ',start+1)
 STATUS.write_text(s[:start]+'## Exact next action\n\n'+text+s[end:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot policy component-cost preparation (2026-10-16)\n\n'+text)
 predecessor('cost')
 checks=dict(review=bindings(review),pins=bindings(z),source=bindings(rd(D/'source-check.json')),no_stage=not Path(config('cost')['stage']).exists(),no_run=not (D/'runs').exists(),fresh_host=not h['matches'],preserved_continuation=all(sha(R/m['preserved_path'])==m['sha256'] for m in maps),actual_unchanged=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'),old_cost_absent=not (OLD/'runs/cost').exists(),direct_cost_false=rd(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,index_empty=not git('diff','--cached','--name-only'))
 names=rd(D/'publication-names.json')['names'];actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [STATUS,ROAD,D/'closure.json',D/'publication.json']}
 checks['exact_names']=set(names)==actual and len(names)==len(set(names))
 files=[R/n for n in names if n not in [str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))]]
 save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='Offline cost preparation only; no numerical performance result or launch'))
 require(all(checks.values()),'Closure failed: preserve');print(dict(checks=len(checks),mappings=len(maps),bindings=len(files),all_passed=True))
if __name__=='__main__':main()
