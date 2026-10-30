from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-candidate-cost-run-20261030')
sys.path.insert(0,str(P));import common as C
phase='candidate-cost';r=C.out(phase);seal=C.read(r/'seal.json');pins=C.read(r/'pins.json');path=Path('/tmp/devex-candidate-cost-numerical-admission.json')
ad=C.validate_admission(seal,pins,path,C.git('rev-parse','HEAD'),phase);C.ensure_unused(phase)
for src,name in [(path,'numerical-admission.json'),(Path(ad['review_report']),'ADMISSION-REVIEW.md')]:
 with (r/name).open('xb') as f:f.write(src.read_bytes())
 C.require(C.sha(src)==C.sha(r/name),'admission copy')
h=C.host();C.require(len(h['checked_groups'])==739 and not h['still_active_current_launcher'] and h['refs']['HEAD']==seal['head'],'full prelaunch739/head')
C.fresh(T/'prelaunch-full-host.json',h)
print(json.dumps(dict(accepted=True,review_checks=len(ad['checks']),review_bindings=len(ad['bindings']),pins=len(pins['inventory']),admission_sha256=C.sha(path),boot=h['boot_id'],groups=len(h['checked_groups']),memory=h['memory'])))
