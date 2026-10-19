from pathlib import Path
import sys,json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST'
Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-PLAN')
sys.path.insert(0,str(P));import control as c
old=c.rd(P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-COST-FIRST')/'host-closure.json')
h=c.full_host(old['groups']);h.update(branch=c.git('branch','--show-current'),status=c.git('status','--porcelain'),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),memory=c.guard.memory())
checks={'groups_sessions_noJulia':c.host_safe(h) and len(h['groups'])==268,'refs':h['head']=='a1cc1d768100f199a3e315c89bf39a28651e8970' and h['master']==c.MASTER,'remote':h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'branch':h['branch']=='codex/simplex-core-architecture','tracked_clean':not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'),'new_package':not Q.exists()}
c.require(all(checks.values()),str(checks));Q.mkdir()
(Q/'entry.py').write_bytes(Path(__file__).read_bytes());c.save(Q/'host-entry.json',h)
paths=['AGENTS.md','src/triangular_factorization.jl','src/bartels_golub_rows.jl','src/triangular_indices.jl','src/triangular_rows.jl','src/huangfu_hall_factorization.jl','diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl','diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl','diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST-FIRST/result-review.md','diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST/runs/cost1-300/audit.json']
c.save(Q/'entry.json',dict(all_passed=True,checks=checks,sha256={p:c.sha(R/p) for p in paths},scope='New offline blocked-BG plan; no old checkers or Julia executed'))
(Q/'request.txt').write_text('Prosím připrav plán experimentálního blokového zpracování aktualizací U v BG s povolenou změnou pořadí aritmetiky, zachováním pivotovací politiky a kontrol numerické správnosti a nech ho nezávisle zkontrolovat, zatím bez implementace a Julie.\n')
print(json.dumps({'checks':checks,'head':h['head'],'boot':h['boot_id'],'groups':len(h['groups'])}))
