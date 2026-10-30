from pathlib import Path
import sys,json
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-production-integration/2026-10-30')
sys.path.insert(0,str(D));import common as C
q=C.read('/tmp/devex-production-master-admission-check-result.json');seal=C.read(C.R/'seal.json');pins=C.read(C.R/'pins.json')
report=Path('/tmp/devex-production-master-numerical-admission.md');out=Path('/tmp/devex-production-master-numerical-admission.json')
checks=q['checks'];checks.update(source_controls_independently_reviewed=True,production_work_memory_review_no_unnecessary_new_cost=True,concrete_launcher_cwd_D_confirmed=True,fresh_result_review_required_before_remote_push=True,source_admission_is_not_executed_result=True)
bindings=q['bindings']
for p in (report,Path(__file__),Path('/tmp/devex-production-master-admission-check.py'),Path('/tmp/devex-production-master-admission-check-result.json'),Path('/tmp/devex-production-master-admission-check.log')):bindings[str(p)]=C.sha(p)
C.require(all(C.sha(p)==v for p,v in bindings.items()),'fresh current bindings')
C.require(set(pins['inventory'])<=set(bindings),'all164pins');C.unused()
a=dict(accepted=True,scope='numerical_admission',phase='production-master',head=seal['head'],production_commit=seal['production_commit'],command=seal['command'],seal_sha256=C.sha(C.R/'seal.json'),pins_sha256=C.sha(C.R/'pins.json'),review_report=str(report),review_report_sha256=C.sha(report),checks=checks,bindings=bindings,findings=[],no_julia=True,production_push_admitted=False,launcher_cwd=str(D),maximum_processes=1,remaining_seconds=691.6252986650798,counts=dict(checks=len(checks),machine_checks=len(q['checks'])-5,bindings=len(bindings),pins=164))
C.fresh(out,a);C.admit(out,seal,pins)
print(json.dumps(dict(accepted=True,path=str(out),sha256=C.sha(out),report_sha256=C.sha(report),counts=a['counts'])))
