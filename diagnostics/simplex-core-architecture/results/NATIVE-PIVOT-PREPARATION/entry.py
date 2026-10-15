from common import *
h=host();save(Q/'host.json',h);verify_host(h)
require(git('branch','--show-current')=='codex/simplex-core-architecture','Wrong branch')
require(git('rev-parse','--git-dir')!=git('rev-parse','--git-common-dir') and not git('rev-parse','--show-superproject-working-tree'),'Expected isolated worktree')
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes')
for n in ['review-final.json','closure.json','publication.json','continuation.json']:
 z=rd(PREV/n);require(bindings(z),'Prior bindings changed '+n)
for src,name in [(STATUS,'STATUS.md.before-preparation'),(ROAD,'roadmap.md.before-preparation')]:
 with (Q/name).open('xb') as f:f.write(src.read_bytes())
paths=[PREV/n for n in ['review-final.json','closure.json','publication.json','continuation.json']]+[Q/'host.json',Q/'common.py',Path(__file__),Q/'STATUS.md.before-preparation',Q/'roadmap.md.before-preparation']
save(Q/'entry.json',dict(all_passed=True,groups=len(h['groups']),sha256={str(f):sha(f) for f in paths},scope='Fresh host and prior accepted plan binding verification, no Julia'))
print(dict(all_passed=True,groups=len(h['groups']),head=h['head']))
