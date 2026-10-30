from pathlib import Path
import hashlib,json,sys
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/green2-1'
sys.path.insert(0,str(P));import common as C
result=C.read('/tmp/devex-green2-numerical-check-result.json');seal=C.read(R/'seal.json');pins=C.read(R/'pins.json')
assert result['accepted'] is True and all(v is True for v in result['checks'].values())
report=Path('/tmp/devex-green2-numerical-admission.md');adpath=Path('/tmp/devex-green2-numerical-admission.json')
bindings=dict(result['bindings'])
for p in (Path(__file__),report,Path('/tmp/devex-green2-numerical-check.py'),Path('/tmp/devex-green2-numerical-check-result.json'),Path('/tmp/devex-green2-numerical-check.log')):bindings[str(p)]=C.sha(p)
assert set(pins['inventory'])<=set(bindings)
assert all(C.sha(p)==h for p,h in bindings.items())
ad=dict(accepted=True,scope='numerical_admission',phase='green2',head=seal['head'],command=seal['command'],seal_sha256=C.sha(R/'seal.json'),pins_sha256=C.sha(R/'pins.json'),review_report=str(report),review_report_sha256=C.sha(report),checks=result['checks'],bindings=bindings,findings=[],maximum_new_attempts=1,remaining_inclusive_seconds=1272.0395071510575,total_shared_seconds=1800,numerical_result_accepted=False,cost_qualified=False,production_admission=False,postexit_independent_review_required=True)
C.fresh(adpath,ad)
C.validate_admission(seal,pins,adpath,seal['head'])
print(json.dumps(dict(accepted=True,scope=ad['scope'],checks=len(ad['checks']),bindings=len(bindings),report_sha256=C.sha(report),admission_sha256=C.sha(adpath),admission=str(adpath))))
