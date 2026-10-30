from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'
R=W/'.superpowers/dual-recovery-devex-task4/cost-1/reference-cost'
sys.path.insert(0,str(D));import common as C
result=C.read('/tmp/devex-reference-cost-numerical-check-result.json')
report=Path('/tmp/devex-reference-cost-numerical-admission.md')
seal=C.read(R/'seal.json');pins=C.read(R/'pins.json')
assert result['accepted'] is True and len(result['checks'])==4657 and all(v is True for v in result['checks'].values())
assert len(result['bindings'])==797 and all(C.sha(p)==h for p,h in result['bindings'].items())
assert sorted(p.name for p in R.iterdir())==['pins.json','seal.json']
bindings=dict(result['bindings'])
for p in [report,Path(__file__),Path('/tmp/devex-reference-cost-numerical-check-result.json'),Path('/tmp/devex-reference-cost-numerical-check.log')]:bindings[str(p)]=C.sha(p)
checks=dict(result['checks'])
checks.update(manual_numerical_work_memory_review=True,manual_canonical_launch_audit_closure_review=True,manual_scope_one_reference_only=True,all_review_evidence_retained=True,no_Julia_or_guard_or_old_main_or_old_tests_executed=True,no_new_production_work_memory_cost_found=True,no_cost_or_candidate_or_production_acceptance=True)
ad=dict(accepted=True,scope='numerical_admission',phase='reference-cost',head=seal['head'],command=seal['command'],seal_sha256=C.sha(R/'seal.json'),pins_sha256=C.sha(R/'pins.json'),review_report=str(report),review_report_sha256=C.sha(report),checks=checks,bindings=bindings)
path=Path('/tmp/devex-reference-cost-numerical-admission.json')
with path.open('x') as f:json.dump(ad,f,indent=2);f.write('\n')
C.validate_admission(seal,pins,str(path),result['host']['refs']['HEAD'],'reference-cost')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),admission=str(path),admission_sha256=C.sha(path),report_sha256=C.sha(report),scope=ad['scope'],phase=ad['phase'])))
