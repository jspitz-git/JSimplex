"""One-shot offline closure after independent preparation review; no Julia."""
from control import *
def main():
 preparation();validate_environment();validate_sources();predecessor('cost1-300')
 v=rd(D/'review.json');known=set(v['sha256'])|set(v.get('evidence_sha256',{}))|{str(D/'review.json')}
 require({str(p) for p in D.iterdir() if p.is_file()}=={n for n in known if Path(n).parent==D},'Exact reviewed preparation membership')
 require(not (D/'runs').exists(),'No phase allowed')
 require(git('rev-parse','HEAD')==ENTRY and not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Entry refs/worktree')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');require(ENTRY+'\trefs/heads/codex/simplex-core-architecture' in remote and MASTER+'\trefs/heads/master' in remote,'Remote refs')
 h=full_host(rd(D/'host.json')['groups']);require(not h['matches'],'Fresh groups/sessions')
 S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={S:D/'STATUS.md.before-COST',ROAD:D/'roadmap.md.before-COST'}
 require(all(p.read_bytes()==q.read_bytes() for p,q in mapping.items()),'Prior continuation bytes')
 maps=[];G=D.parent/'DIRECT-BG-DYNAMIC-GREEN'
 for rec in [G/'closure.json',G/'publication.json']:
  j=rd(rec)
  for field in ['sha256','git_blobs']:
   for n,v in j.get(field,{}).items():
    target=path(n);old=mapping.get(target,target);require((sha(old) if field=='sha256' else git('hash-object','--',str(old)))==v,'Prior binding')
    if target in mapping:maps.append(dict(record=str(rec),field=field,key=n,value=v,preserved=str(old)))
 require(len(maps)==6,'Six current GREEN mappings')
 save(D/'closure-host.json',h);save(D/'continuation-map.json',dict(maps=maps,scope='Only current GREEN continuation bindings; all earlier mappings unchanged'))
 block=(D/'continuation-next.md').read_text();a,b=S.read_text().split('## Exact next action\n\n',1);unused,c=b.split('### Historical prior continuation (superseded)',1)
 S.write_text(a+'## Exact next action\n\n'+block+'\n### Historical prior continuation (superseded)'+c);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## 2026-10-16 dynamic BG Task3 cost preparation\n\n'+block)
 files=sorted([p for p in D.iterdir() if p.is_file()]+[S,ROAD]);save(D/'closure.json',dict(all_passed=True,checks=dict(exact_review=True,source_runtime_stage=True,green_lineage=True,refs_remote=True,processes=True,prior_mapping6=True,no_phase=True),sha256={str(p.relative_to(R)):sha(p) for p in files}))
 print('Cost preparation closure7PASS',len(files),'bindings')
if __name__=='__main__':main()
