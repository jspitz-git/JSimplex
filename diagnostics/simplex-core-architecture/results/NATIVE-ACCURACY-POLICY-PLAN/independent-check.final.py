from pathlib import Path
import hashlib,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
F=R/'diagnostics/simplex-core-architecture/results/NATIVE-ACCURACY-POLICY-PLAN'
S=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers')
E=F.parent/'DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS'
P=R/'docs/superpowers/plans/2026-10-15-native-float64-accuracy-policy.md'
fixed=[F/'source-check.py',F/'common.py',P,S/'umfpack.jl',S/'wrappers.jl',R/'src/factorization.jl',R/'src/triangular_factorization.jl',F.parent/'S4-L/upstream-umfpack-v7.10.1.h',F.parent/'S4-L/upstream-umfpack-v7.10.1.provenance.json',F.parent/'DIRECT-LU-COST-PREPARATION/inputs.json',E/'analysis.json',E/'review.json',E/'closure.json',E/'publication.json',F.parent/'DIRECT-LU-PREPARATION/baseline.json',F/'entry-host.json',F/'STATUS.md.before-policy',F/'roadmap.md.before-policy',R/'AGENTS.md']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,value):
 with p.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
original=read(F/'source-check.json')
initial=read(F/'initial-review.json')
fix=read(F/'review-fix.json')
baseline=read(F.parent/'DIRECT-LU-PREPARATION/baseline.json')
text=P.read_text()
checks=dict(original_19_preserved=all(sha(F/'plan.before-review.md' if p==P else p)==original['sha256'][str(p)] for p in fixed),baseline514=len(baseline['sha256'])==514 and all(sha(R/p)==d for p,d in baseline['sha256'].items()),fix_6_bindings=len(fix['sha256'])==6 and all(sha(Path(p))==d for p,d in fix['sha256'].items()),initial_rejection_preserved=initial['accepted'] is False and len(initial['findings'])==2,current_plan_fixed_hash=sha(P)=='a7a8da142e8e049a723e2287c7e7cd16eacf095bc8a7411ff8dddb0b68baa051',strategy_qualified='ONLY for a captured UNSYMMETRIC' in text and 'STRATEGY_USED and SYM_PIVOT_TOLERANCE for every fixture/arm/window' in text,loader_closed='Import ONLY `SparseArrays`, `LinearAlgebra` and `TOML`' in text and 'no JSimplex import or overlay is permitted' in text,counts_preserved=all(s in text for s in ['141 fresh LU','4245F+2133B =6378','405504 Float64 entries','12 snapshots']),unchanged_accuracy_bound='128*n*2^-52*max(1,||M||inf*||x||inf,||b||inf)' in text,independent_initial_source_pass=read(F/'independent-check.initial.json')['accepted_source_bindings'])
checks['head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='c1901995ac6e7eee26a7c4b9cc6897c3e6b43a12'
checks['master']=subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='6f68e24e8ddac42b948da8fcc2d636c010751194'
# Explicit stable additions only; no mutable STATUS, roadmap, continuation or future publication files.
extras=[F/'source-check.json',F/'plan.before-review.md',F/'independent-check.py',F/'independent-check.initial.json',F/'initial-review.md',F/'initial-review.json',F/'review-fix.py',F/'review-fix.json',R/'diagnostics/simplex-core-architecture/DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS.md',Path(__file__)]
bindings={str(p):sha(p) for p in fixed+extras}
save(F/'independent-check.final.json',dict(all_passed=all(checks.values()),checks=checks,sha256=bindings,scope='Independent final source/design check only; original plan binding maps to plan.before-review.md; no Julia/native execution.'))
assert all(checks.values()),checks
review="""# Independent final source/design review

Accepted for offline Task 1 preparation only. This does not admit a numerical run, qualify a remedy or resume the failed direct-LU benchmark. The two initial Important findings are preserved in initial-review.md/json and resolved in the reviewed amendment. No outstanding findings.

R1 is resolved by describing P as threshold 1.0, recording STRATEGY_USED and SYM_PIVOT_TOLERANCE per window outside timing and in final snapshots, and limiting full partial-pivot interpretation to captured UNSYMMETRIC strategy. AUTO and the symmetric diagonal threshold remain unchanged. R2 is resolved by the exact ordinary project and SparseArrays/LinearAlgebra/TOML-only driver, excluding JSimplex and overlays. Both corrections preserve the arms and operation budget.

The substantive source review checked constructor copying and allocation, workspace sizing and automatic resizing, copy(F) sharing, private lu! mutation before failure, wrapper solve dispatch and Info overwrite semantics, production _copy_backend and fresh _refactorize_backend, and the bound upstream threshold/refinement definitions. Constructor controls and CSC storage are independently owned; copy(F) shares native and CSC state, so it must never become T. An independently constructed T can fail singular refactorization without mutating F/S; discarding T and checking F/S afterward is appropriate. Production whole-F sharing and fresh default-policy reset remain explicit integration exclusions. All 20 control values and constructor caller immutability are required, without mutating timed/shared factor controls.

The independent ledger gives 132 construction windows plus 9 lifecycle constructions, 9 lu! attempts including 3 expected singular failures, 3 shallow copies, 4245 FTRAN and 2133 BTRAN entries (6378 total). It gives 6336 cost output vectors, 405504 Float64 entries (3244032 payload bytes), 1344 lifecycle output elements, and 12 final snapshots. Native correction solves are additional internal work, correctly represented by attempted refinement rather than only accepted steps. Metadata does not establish a full native work trace. The unchanged exact residual bound applies to each actual matrix/RHS pairing; a failing C cell can be a faithful diagnostic result and cannot be promoted to an accuracy remedy. An unexpected exception or integrity failure stops the experiment, while false residuals are retained without selecting a new tolerance.

No production code changes: no unnecessary new production work, allocation or retained memory was found, and there is no affected production hot path to benchmark at this stage. R necessarily adds 4n Float64 scratch elements (32n payload bytes: 1024 at n=32 and 3072 at n=96) per workspace plus bounded residual/correction work per solve. Native fill and factorization costs may also change for P. Both constructor control vectors, native CSC copies and workspaces belong in construction costs. The planned fixed output retention and scalar Info stores are diagnostic overhead, disclosed separately from solver memory. Construction and solve regions, compile contamination, GC, native memory estimates and RSS are separated without claiming native allocation balance or speedup. No precision, coefficient or tolerance change is authorized. Other precisions and real manager lifecycle remain uncovered.

The final independent check verifies 19 original bindings through the preserved original-plan mapping, 514 baseline hashes, current HEAD/master, all 6 amendment bindings and the current plan hash. Its explicit final list binds only stable source/evidence files, excluding mutable continuation and future closure/publication. Read-time source hashes are not launch pins. The original source-check and reviewer checks were not rerun; a new bounded Python source/hash/arithmetic check was used. No Julia, import/compile/native call, driver creation, old auditor replay, test or production change occurred. Future execution still requires concrete preparation and fresh exact admission under the single 45-second attempt and closure gates.
"""
with (F/'review.md').open('x') as stream:stream.write(review)
bindings[str(F/'independent-check.final.json')]=sha(F/'independent-check.final.json')
bindings[str(F/'review.md')]=sha(F/'review.md')
save(F/'review.json',dict(accepted=True,findings=[],resolved_findings=['R1','R2'],sha256=bindings,scope='SOURCE/DESIGN plan only: accepts offline preparation, not execution or policy promotion.',production_cost_conclusion='No production changes or unnecessary new production work/memory. Future R has unavoidable 32n bytes extra workspace payload and refinement work.'))
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),created=['independent-check.final.py','independent-check.final.json','review.md','review.json'])))
