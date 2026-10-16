"""One-shot closure of independently accepted RED; never reruns a numerical audit."""
from pathlib import Path
import sys
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';sys.path.insert(0,str(D))
from control import *
run=D/'runs/red300';HEAD='d7d090d86b1f1ed2d7b68a079437a0136f73a9f6'
def main():
 review=rd(E/'review.json');require(review['accepted'] is True and review['findings']==[] and review['scope']=='dynamic BG RED closure','Closure review')
 paths=sorted([p for p in E.iterdir() if p.is_file() and p.name!='review.json']+[p for p in run.rglob('*') if p.is_file()])
 require(set(review['sha256'])=={str(p) for p in paths} and bindings(review),'Exact closure review files')
 result_review('red300','dynamic BG RED result','result-review.json')
 require(rd(run/'audit.json')['all_passed'] and rd(E/'postcheck.json')['all_passed'] and bindings(rd(E/'postcheck.json')),'Result evidence')
 preparation();validate_environment();validate_sources()
 require(git('rev-parse','HEAD')==HEAD and git('rev-parse','master')==MASTER,'Refs')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');require(HEAD+'\trefs/heads/codex/simplex-core-architecture' in remote and MASTER+'\trefs/heads/master' in remote,'Remote refs')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Early tracked changes')
 h=full_host(rd(run/'posthost.json')['groups']);require(not h['matches'],'Fresh full process closure')
 S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={S:E/'STATUS.md.before-RED',ROAD:E/'roadmap.md.before-RED'}
 require(all(p.read_bytes()==old.read_bytes() for p,old in mapping.items()),'Prior continuation')
 maps=[]
 for record in [D/'closure.json',D/'publication.json']:
  j=rd(record)
  for name,value in j['sha256'].items():
   target=path(name);old=mapping.get(target,target);require(sha(old)==value,'Prior SHA binding')
   if target in mapping:maps.append(dict(record=str(record),field='sha256',key=name,sha256=value,preserved=str(old)))
  for name,value in j.get('git_blobs',{}).items():
   target=path(name);old=mapping.get(target,target);require(git('hash-object','--',str(old))==value,'Prior Git binding')
   if target in mapping:maps.append(dict(record=str(record),field='git_blobs',key=name,git_blob=value,preserved=str(old)))
 require(len(maps)==6,'Continuation mapping count')
 save(E/'closure-host.json',h);save(E/'continuation-map.json',dict(maps=maps,scope='Only current preparation continuation hashes/blobs; all older mappings unchanged'))
 block=(E/'continuation-next.md').read_text();a,b=S.read_text().split('## Exact next action\n\n',1);unused,c=b.split('### Historical prior continuation (superseded)',1)
 S.write_text(a+'## Exact next action\n\n'+block+'\n### Historical prior continuation (superseded)'+c);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## 2026-10-16 dynamic BG Task3 RED result\n\n'+block)
 paths=sorted([p for p in E.iterdir() if p.is_file()]+[p for p in run.rglob('*') if p.is_file()]+[S,ROAD])
 save(E/'closure.json',dict(all_passed=True,checks=dict(exact_result_review=True,exact_closure_review=True,original_audit_pass=True,supplement_pass=True,unchanged_preparation_source_runtime=True,refs_remote_unchanged=True,fresh_groups_sessions=True,prior_continuation_preserved=True,no_green_run=True),sha256={str(p.relative_to(R)):sha(p) for p in paths}))
 print('RED closure9PASS',len(paths),'bindings')
if __name__=='__main__':main()
