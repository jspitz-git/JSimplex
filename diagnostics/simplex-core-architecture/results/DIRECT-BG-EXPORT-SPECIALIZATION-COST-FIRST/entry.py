"""New Task3 first-process preflight; no Julia, seal, outer or numerical reservation."""
from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-COST-FIRST');sys.path.insert(0,str(P));import control as c
expected='e149671cd2c9560ae2a91b80614d36799b845240';checks={}
def ck(n,v):checks[n]=bool(v);c.require(v,n)
h=c.full_host(c.rd(P/'host-closure.json')['groups']);h.update(memory=c.guard.memory(),branch=c.git('branch','--show-current'),status=c.git('status','--porcelain'),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),git_dir=c.git('rev-parse','--absolute-git-dir'),git_common=c.git('rev-parse','--git-common-dir'),superproject=c.git('rev-parse','--show-superproject-working-tree'))
ck('full265groups_ANDsessions_noJulia',c.host_safe(h) and len(h['groups'])==265)
ck('resources',not c.guard.pressure(h['memory']))
ck('exact_refs',h['head']==expected and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture' and expected+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('existing_isolated_checkout',h['git_dir']!=h['git_common'] and h['superproject']=='')
ck('tracked_clean',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('unused_phase',not (P/'runs/cost1-300').exists() and not (P/'outers/cost1-300').exists() and not Q.exists())
c.validate_environment();ck('exact_environment',True);c.validate_sources();ck('source_runtime_stage',True)
files=c.preparation();ck('accepted_preparation',bool(files));extra,groups=c.predecessor('cost1-300');ck('accepted_GREEN_predecessor',bool(extra) and groups==h['groups'])
ck('frozen_publication',c.bindings(c.rd(P/'publication.json')))
Q.mkdir();c.save(Q/'host-entry.json',h)
with (Q/'entry.py').open('xb') as f:f.write(Path(__file__).read_bytes())
with (Q/'request.txt').open('x') as f:f.write('Prosím ověř podmínky spuštění, nech konkrétní první běh nezávisle schválit a proveď krátké srovnávací měření podle Task3 plánu specializace exportu/importu BG s limitem 300 sekund.\n')
c.save(Q/'entry.json',dict(all_passed=True,checks=checks,phase='cost1-300',sha256={str(p):c.sha(p) for p in [Q/'entry.py',Q/'request.txt',Q/'host-entry.json',P/'FINAL.md',P/'review-final.json',P/'preparation-pins-final.json',P/'publication.json']},scope='Fresh preflight only; no launch or numerical reservation'))
print(json.dumps(dict(all_passed=True,checks=len(checks),groups=len(groups),memory=h['memory'],boot_id=h['boot_id'],head=h['head'])))
