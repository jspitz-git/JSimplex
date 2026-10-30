from pathlib import Path
import sys,json
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-production-integration/2026-10-30');T=Path('/tmp/devex-production-integration-20261030');sys.path.insert(0,str(D));import common as C
seal=C.read(C.R/'seal.json');pins=C.read(C.R/'pins.json');path=Path('/tmp/devex-production-master-numerical-admission.json');C.unused();C.verify_pins(pins);ad=C.admit(path,seal,pins);C.require(set(pins['files'])==set(C.paths()),'sealed source membership')
for src,name in ((path,'numerical-admission.json'),(Path(ad['review_report']),'ADMISSION-REVIEW.md')):
 with (C.R/name).open('xb') as f:f.write(src.read_bytes())
 C.require(C.sha(src)==C.sha(C.R/name),'admission copy')
h=C.host();C.require(len(h['checked_groups'])==742 and not h['still_active_current_launcher'],'fresh full742 prelaunch');C.fresh(T/'prelaunch-host.json',h);print(json.dumps(dict(accepted=True,checks=len(ad['checks']),bindings=len(ad['bindings']),pins=len(pins['inventory']),admission_sha256=C.sha(path),memory=h['memory'],refs=h['refs'])))
