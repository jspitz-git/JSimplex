from pathlib import Path
import sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2');H=P.with_name('DIRECT-BG-BLOCKED-UPDATE-HARNESS')
sys.path.insert(0,str(P));import control as c
h=c.full_host(c.rd(Q/'host-closure.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'))
c.require(c.host_safe(h) and len(h['groups'])==268 and h['head']=='1a824ea2d6478ba5ecbd3afc8ffbe83207bf2fd8' and h['master']==c.MASTER,'Host refs')
c.require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'Remote')
c.require(h['branch']=='codex/simplex-core-architecture' and not c.git('diff','HEAD','--name-only'),'Clean branch')
c.require(c.rd(Q/'review.json')['accepted'] and c.bindings(c.rd(Q/'review.json')),'Task2 review')
c.require(not H.exists(),'New harness');H.mkdir();(H/'entry.py').write_bytes(Path(__file__).read_bytes());c.save(H/'host-entry.json',h)
files=[R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md',R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md',Q/'review.json',Q/'closure.json',Q/'publication.json']+list((R/'diagnostics/direct-bg-blocked-update/reproduce').iterdir())
c.save(H/'entry.json',dict(all_passed=True,scope='Offline harness preparation only',sha256={str(p):c.sha(p) for p in files}))
print('Fresh entry PASS; 268 groups AND sessions absent; no Julia; refs remote verified')
