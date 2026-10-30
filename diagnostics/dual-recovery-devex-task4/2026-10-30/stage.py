from pathlib import Path
import hashlib,json,shutil
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';P=W/'diagnostics';changes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(src.read_bytes())
 changes[str(dst)]=dict(source=str(src),sha256=sha(src))
for mode in ('reference','candidate'):
 root=D/'overlays'/mode
 for src in sorted((W/'src').rglob('*.jl')):copy(src,root/src.relative_to(W))
 for name in ('Project.toml','Manifest.toml','LocalPreferences.toml'):copy(W/name,root/name)
C=P/'dual-recovery-devex-task3/2026-10-30'
for src,dst in [('simplex_numerics.jl','simplex_numerics.jl'),('simplex_recovery-reviewed.jl','simplex_recovery.jl'),('simplex_pivot.jl','simplex_pivot.jl')]:
 target=D/'overlays/candidate/src'/dst;target.write_bytes((C/src).read_bytes());changes[str(target)]=dict(source=str(C/src),sha256=sha(C/src))
T=D/'tests';one=P/'dual-recovery-devex-task1/2026-10-30';two=P/'dual-recovery-devex-task2/2026-10-30'
for src,name in [(one/'refinement_outcome_tests-reviewed.jl','refinement_outcome_tests.jl'),(one/'reference.jl','reference.jl'),(one/'reference_comparison_tests.jl','reference_comparison_tests.jl'),(two/'recovery_weight_tests.jl','recovery_weight_tests.jl'),(two/'legacy_rebuild_reference.jl','legacy_rebuild_reference.jl'),(C/'recovery_devex_fallback_tests-reviewed.jl','recovery_devex_fallback_tests.jl')]:copy(src,T/name)
regressions=['simplex_numerics_tests.jl','basis_recovery_tests.jl','dual_weight_validation_tests.jl','adaptive_pricing_tests.jl','adaptive_pricing_lifecycle_tests.jl','partial_pricing_tests.jl','partial_pricing_edge_tests.jl']
for n in regressions:copy(W/'test'/n,T/n)
copy(W/'test/fixtures/solver/generated/wide-bound129.mps',T/'fixtures/solver/generated/wide-bound129.mps')
G=P/'klu-weight-rejection/2026-10-29/guard'
for n in ('guard_reviewed.py','supervisor_reviewed.py','entry_gate.py'):copy(G/n,D/'guard'/n)
# Bounded test-only fixture extraction: no new production code or method overwrite.
s=(two/'recovery_weight_tests.jl').read_text().split('module RecoveryWeightTests\n',1)[1].split('fields(r)=',1)[0]
s=s.replace('using ..RefinementOutcomeTests\n','').replace('const R=RefinementOutcomeTests\n','')
(D/'weights_fixture.jl').write_text('module Task4WeightFixture\n'+s+'end\n')
(D/'staging.json').write_text(json.dumps(dict(bindings=changes,regressions=regressions,overlays='ordinary full source projects, no nested module clone; candidate changes exactly three files',fixture_extraction_source=sha(two/'recovery_weight_tests.jl')),indent=2)+'\n')
print(json.dumps(dict(copied=len(changes),project_files_per_overlay=74,regression_files=len(regressions))))
