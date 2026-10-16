"""One-shot offline closure after accepted exact preparation review."""
from control import *
def main():
 files=preparation();review=rd(D/'review.json');supp=review.get('evidence_sha256',{})
 require(all(Path(n).parent==D for n in supp),'Review supplements must be local')
 covered=set(files)|set(supp)
 actual={str(p) for p in D.iterdir() if p.is_file()}
 require(actual=={n for n in covered if Path(n).parent==D},'Exact preparation/review file coverage')
 require(not (D/'runs').exists(),'No phase seal/reservation/output')
 require(rd(D/'source-check.json')['all_passed'] and rd(D/'offline-tests.json')['all_passed'],'Source/offline checks')
 validate_environment();validate_sources()
 require(git('rev-parse','HEAD')==ENTRY and git('rev-parse','master')==MASTER,'Exact closure refs')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
 require(ENTRY+'\trefs/heads/codex/simplex-core-architecture' in remote and MASTER+'\trefs/heads/master' in remote,'Remote refs')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'No early tracked change')
 h=full_host();require(not h['matches'] and not guard.pressure(guard.memory()),'Fresh host')
 S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
 require(S.read_bytes()==(D/'STATUS.md.before-Task3').read_bytes() and ROAD.read_bytes()==(D/'roadmap.md.before-Task3').read_bytes(),'Exact previous continuation')
 for m in rd(D/'continuation-map.json')['maps']:
  j=rd(m['record']);v=j[m['field']][m['key']];p=Path(m['preserved'])
  require(v==(sha(p) if m['field']=='sha256' else git('hash-object','--',str(p))),'Prior mapping drift')
 # Fresh host precedes the only continuation mutations.
 save(D/'closure-host.json',h)
 block=(D/'continuation-next.md').read_text();old=S.read_text();a,b=old.split('## Exact next action\n\n',1);unused,c=b.split('### Historical prior continuation (superseded)',1)
 S.write_text(a+'## Exact next action\n\n'+block+'\n### Historical prior continuation (superseded)'+c)
 ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## 2026-10-16 dynamic BG Task3 correctness preparation\n\n'+block)
 paths=sorted([p for p in D.iterdir() if p.is_file()]+[S,ROAD])
 save(D/'closure.json',dict(all_passed=True,checks=dict(exact_independent_review=True,full_preparation_membership=True,author_source_checks=True,pure_offline_checks=True,no_julia_or_phase_outputs=True,actual_source_environment_unchanged=True,refs_remote_unchanged=True,fresh_full_groups_sessions=True,prior_continuation_bindings=True,only_continuation_mutation=True),sha256={str(p.relative_to(R)):sha(p) for p in paths}))
 print('Task3 closure10PASS',len(paths),'bindings')
if __name__=='__main__':main()
