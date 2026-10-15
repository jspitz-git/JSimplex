from pathlib import Path
import json, hashlib, subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
F=R/'diagnostics/simplex-core-architecture/results/NATIVE-ACCURACY-POLICY-PLAN'
S=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers')
E=F.parent/'DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS'
# Fixed list: excludes mutable continuation and future publication/closure files.
fixed=[F/'source-check.py',F/'common.py',R/'docs/superpowers/plans/2026-10-15-native-float64-accuracy-policy.md',S/'umfpack.jl',S/'wrappers.jl',R/'src/factorization.jl',R/'src/triangular_factorization.jl',F.parent/'S4-L/upstream-umfpack-v7.10.1.h',F.parent/'S4-L/upstream-umfpack-v7.10.1.provenance.json',F.parent/'DIRECT-LU-COST-PREPARATION/inputs.json',E/'analysis.json',E/'review.json',E/'closure.json',E/'publication.json',F.parent/'DIRECT-LU-PREPARATION/baseline.json',F/'entry-host.json',F/'STATUS.md.before-policy',F/'roadmap.md.before-policy',R/'AGENTS.md']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
source=read(F/'source-check.json')
actual={str(p):sha(p) for p in fixed}
checks={str(p):actual[str(p)]==source['sha256'].get(str(p)) for p in fixed}
baseline=read(F.parent/'DIRECT-LU-PREPARATION/baseline.json')
baseline_failures=[name for name,digest in baseline['sha256'].items() if sha(R/name)!=digest]
windows=4*3*(3+8)
lifecycle_f=3*(2+1+1+1+2)
lifecycle_b=lifecycle_f
ledger=dict(windows=windows,fresh_lu=windows+3*3,lu_bang=3*3,copies=3,ftran=windows*16*2+lifecycle_f,btran=windows*16+lifecycle_b,output_vectors=windows*48,output_entries=3*11*48*sum([32,32,96,96]),snapshots=4*3)
ledger['solve_entries']=ledger['ftran']+ledger['btran']
ledger['output_payload_bytes']=8*ledger['output_entries']
ledger['lifecycle_output_entries']=(lifecycle_f+lifecycle_b)*32
ledger['refinement_extra_workspace_bytes']={str(n):4*n*8 for n in [32,96]}
assert ledger['fresh_lu']==141 and ledger['lu_bang']==9 and ledger['solve_entries']==6378
assert ledger['output_vectors']==6336 and ledger['output_entries']==405504
result=dict(accepted_source_bindings=all(checks.values()),checks=checks,binding_count=len(fixed),baseline_count=len(baseline['sha256']),baseline_failures=baseline_failures,ledger=ledger,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),master=subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip(),sha256={**actual,str(F/'source-check.json'):sha(F/'source-check.json'),str(Path(__file__)):sha(Path(__file__))},scope='Independent fixed-list source/design review only; no Julia, imports, solver replay or old auditor execution.')
with (F/'independent-check.initial.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({k:result[k] for k in ['accepted_source_bindings','binding_count','baseline_count','baseline_failures','ledger','head','master']},indent=2))
