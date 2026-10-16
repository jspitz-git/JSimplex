"""Save final independent readiness decision after completed checks; read-only gate verification."""
from pathlib import Path
import json,sys
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control
m=D/'preparation-pins.json';p=control.rd(m);checks=control.rd(D/'review-amendment-checks.json')
control.require(checks['all_passed'] is True and checks['findings']==[] and checks['pins_sha256']==control.sha(m),'Independent checks mismatch')
control.require(control.bindings(p),'Canonical drift')
control.require(set(p['sha256'])==set(control.rd(D/'required-paths.json')['paths']),'Required membership')
live={str(control.R/'diagnostics/simplex-core-architecture/STATUS.md'),str(control.R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
control.require(not any(str(control.path(n)) in live for n in p['sha256']),'Live continuation binding')
evidence=[D/'review-final.md',Path(__file__),D/'review-amendment-check.py',D/'review-amendment-checks.json',D/'review-amendment-host.json']
v=dict(accepted=True,findings=[],scope='production commit readiness',pins_sha256=control.sha(m),production_commit=control.rd(D/'production-commit.json')['commit'],sha256={**p['sha256'],str(m):control.sha(m)},evidence_sha256={str(n):control.sha(n) for n in evidence},limitations=['No actual-master exact-stage admission','No new numerical execution or result','Prior measured policy-dependent fill/work/memory tradeoffs retained'])
control.save(D/'review-final.json',v)
control.verify_review(v,m,list(p['sha256'])+[str(m)],'production commit readiness')
files=control.preparation();control.require(all(Path(n).is_absolute() for n in files),'Absolute runtime paths')
control.save(D/'review-gate-check.json',dict(all_passed=True,scope='Read-only acceptance-consumer check; no launch admission',checks=dict(exact_review_schema=True,exact_canonical_bindings=True,absolute_prepared_runtime_paths=True,no_live_continuation_binding=True,no_run_directory=not (D/'runs').exists()),sha256={str(n):control.sha(n) for n in [D/'review-final.json',m,Path(__file__)]}))
print('Accepted readiness; exact',len(v['sha256']),'review bindings; runtime list',len(files),'absolute paths; no numerical admission')
