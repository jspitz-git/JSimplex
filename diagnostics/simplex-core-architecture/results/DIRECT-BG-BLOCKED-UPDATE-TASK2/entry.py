from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';A=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK1');Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')
sys.path.insert(0,str(P));import control as c
h=c.full_host(c.rd(A/'host-closure.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'))
c.require(c.host_safe(h) and len(h['groups'])==268 and h['head']=='55c5fad5dfa8796b53a38b53c85ff3b024265e2e' and h['master']==c.MASTER,'Host refs')
c.require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'Remote')
c.require(h['branch']=='codex/simplex-core-architecture' and not c.git('diff','HEAD','--name-only'),'Clean branch')
c.require(c.rd(A/'review.json')['accepted'] and c.bindings(c.rd(A/'review.json')),'Task1 review')
c.require(not Q.exists(),'New Task2 path');Q.mkdir();(Q/'entry.py').write_bytes(Path(__file__).read_bytes());c.save(Q/'host-entry.json',h)
files=['AGENTS.md','docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md','docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md']+[str(x.relative_to(R)) for x in (R/'diagnostics/direct-bg-blocked-update/reproduce').iterdir()]+['src/triangular_factorization.jl','src/triangular_spikes.jl','src/triangular_rows.jl','src/bartels_golub_rows.jl','diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl','diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl']
c.save(Q/'entry.json',dict(all_passed=True,sha256={n:c.sha(R/n) for n in files},scope='Fresh offline Task2 entry; no Julia'))
with (R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md').open('a') as f:f.write('\nTask2 started at '+h['head']+'. Offline adapter/tests only, no harness/Julia. Task1 four files frozen. Tests-first with runtime TDD deferred under user request. One independent review after implementation.\n')
print('Task2 entry PASS, no Julia')
