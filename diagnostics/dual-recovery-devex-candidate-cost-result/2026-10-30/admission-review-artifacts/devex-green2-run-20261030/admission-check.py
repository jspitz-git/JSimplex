from pathlib import Path
import sys,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30';T=Path('/tmp/devex-green2-run-20261030')
sys.path.insert(0,str(P));import common as C
R=C.OUT;seal=C.read(R/'seal.json');pins=C.read(R/'pins.json');adpath=Path('/tmp/devex-green2-numerical-admission.json')
ad=C.validate_admission(seal,pins,adpath,C.git('rev-parse','HEAD'))
C.require(not (R/'attempt.json').exists(),'attempt already consumed')
for src,name in [(adpath,'numerical-admission.json'),(Path(ad['review_report']),'ADMISSION-REVIEW.md')]:
 with (R/name).open('xb') as f:f.write(src.read_bytes())
 C.require(C.sha(src)==C.sha(R/name),'admission copy mismatch')
h=C.host();C.require(len(h['checked_groups'])==733 and not h['still_active_current_launcher'] and h['refs']['HEAD']==seal['head'],'full prelaunch groups/head')
C.fresh(T/'prelaunch-full-host.json',h)
print(json.dumps(dict(accepted=True,review_checks=len(ad['checks']),review_bindings=len(ad['bindings']),pins=len(pins['inventory']),admission_sha256=C.sha(adpath),boot=h['boot_id'],full_groups=len(h['checked_groups']),memory=h['memory'])))
