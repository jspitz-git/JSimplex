"""Future explicit external closure, after outer return. Reads saved audit without rerunning it."""
from control import *
def main(phase):
 cfg=config(phase);run=Path(cfg['run']);o=outer_dir(phase);s=rd(run/'sealed.json');outer=verify_outer_invocation(phase,s)
 outcome=rd(o/'outer-outcome.json')
 require(outcome['identity']==outer and outcome['launched'] is True,'Outer outcome')
 groups=s['groups']+[outer['pgid'],outer['sid']]
 for name in ['posthost.json']:
  if (run/name).exists():groups+=rd(run/name)['groups']
 for name in ['current.json','process.json']:
  p=Path(cfg['output'])/name
  if p.exists():
   for role in ['runner','child']:
    if role in rd(p):groups += [rd(p)[role][k] for k in ['pgid','sid']]
 h=full_host(groups);h['memory']=guard.memory();h['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
 require(host_safe(h) and all(h[k]==s[k] for k in ['head','master','boot_id']),'External process/ref closure failed')
 require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and MASTER+'\trefs/heads/master' in h['remote'],'Remote refs changed')
 files=[o/n for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']]+[run/n for n in ['sealed.json','admission.json','posthost.json','audit.json']]
 require(all(p.is_file() for p in files),'Missing closure evidence')
 save(run/'outer-closure.json',dict(all_passed=True,outer_identity=outer,host=h,sha256={str(p):sha(p) for p in files},scope='Outer and all prior/guard/child PGIDs AND SIDs absent; diagnostic closure does not imply qualification acceptance'))
if __name__=='__main__':main(sys.argv[1])
