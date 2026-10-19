from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl'); P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK1'); A=P.with_name('DIRECT-BG-BLOCKED-UPDATE-PLAN');C=R/'diagnostics/direct-bg-blocked-update/reproduce'
sys.path.insert(0,str(P));import control as c
h=c.full_host(c.rd(A/'host-closure.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'),gitdir=c.git('rev-parse','--git-dir'),common=c.git('rev-parse','--git-common-dir'))
c.require(c.host_safe(h) and len(h['groups'])==268 and h['head']=='982b56980e38f4438f3c3c6746bd490a60c5eded' and h['master']==c.MASTER,'Host/refs')
c.require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'Remote')
c.require(h['branch']=='codex/simplex-core-architecture' and h['gitdir']!=h['common'] and not c.git('rev-parse','--show-superproject-working-tree') and not c.git('diff','HEAD','--name-only'),'Isolation/clean')
c.require(not Q.exists() and not C.exists(),'New artifact paths')
c.require(c.rd(A/'review.json')['accepted'] and c.bindings(c.rd(A/'review.json')),'Accepted plan')
Q.mkdir();C.mkdir(parents=True)
(Q/'entry.py').write_bytes(Path(__file__).read_bytes());c.save(Q/'host-entry.json',h)
paths=['AGENTS.md','docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md','docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md','src/triangular_factorization.jl','src/triangular_indices.jl','src/bartels_golub_rows.jl','src/triangular_rows.jl',str((A/'review.json').relative_to(R))]
c.save(Q/'entry.json',{'all_passed':True,'sha256':{n:c.sha(R/n) for n in paths},'scope':'Fresh Task1 offline entry, 268 groups AND sessions, no Julia'})
L=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update';L.mkdir(parents=True,exist_ok=True)
with (L/'progress.md').open('a') as f:f.write('# SDD ledger — plan: docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md\nTask1 started at '+h['head']+'.\nRuling: user explicitly authorizes offline candidate/test text, forbids Julia. Tests written first but RED/GREEN execution deferred to Task2 admission; no runtime pass claimed. Existing diagnostic linked worktree reused. No skill setup/install/test commands allowed to override no-Julia scope.\nPreflight: Task1 workspace/decision interface consumed by Task2 adapter; Task1 commit does not append factor history or manage whole-update rollback/busy state. Task2 owns one-rejection latch and original prepare/begin/finish.\n')
print('Task1 entry PASS; isolated worktree; new paths created; no Julia')
