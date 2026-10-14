from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise SystemExit(msg)
review=json.loads((E/'admission-review-final.json').read_text())
require(review['accepted'] is True and review['findings']==[],'Final review not accepted')
require(review['pins_sha256']==sha(E/'pins-reviewed.json') and all(sha(p)==s for p,s in review['sha256'].items()),'Final review drift')
report=R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-ADMISSION-PREPARATION.md';status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
paths={report:'report.before-completion',status:'STATUS.md.before-completion',road:'roadmap.md.before-completion',E/'ledger.md':'ledger.md.before-completion'}
mapping={}
for p,n in paths.items():
 q=E/n
 with q.open('xb') as f:f.write(p.read_bytes())
 mapping[str(p)]=dict(preserved=str(q),sha256=sha(q))
with (E/'completion-map.json').open('x') as f:json.dump(dict(mapping=mapping,scope='Completion drafts preserved; immutable initial/final review and both manifests unchanged.'),f,indent=2);f.write('\n')
def replace(p,a,b):
 t=p.read_text();require(t.count(a)==1,'Nonunique replacement '+str(p));p.write_text(t.replace(a,b))
replace(report,'Status: preparation completed; independent review pending. No Julia executed.','Status: corrected preparation independently accepted; no unresolved findings. No Julia executed.')
replace(report,'[Concrete admission and work ledger](results/MA-S/admission.md)','[Canonical admission and work ledger](results/MA-S/admission-reviewed.md)')
replace(report,'[Launcher](results/MA-S/launcher.py) and [auditor](results/MA-S/audit.py)','[Canonical launcher](results/MA-S/launcher-reviewed.py) and [auditor](results/MA-S/audit_reviewed.py)')
replace(report,'[New manifest](results/MA-S/pins.json)','[Canonical manifest](results/MA-S/pins-reviewed.json)')
replace(report,'[Offline Python tests](results/MA-S/offline-tests.json)','[Reviewed offline Python tests](results/MA-S/offline-tests-reviewed.json)')
with report.open('a') as f:f.write('''
The initial independent review rejected two P2 raw/stage-schema gaps: Boolean or
float values could pass integer index/exit equality, and invalid memory evidence
could pass one-sided limits. One separate offline correction preserved all original
sources/review/manifests and produced canonical reviewed variants. Seven source
predicate RED counterexamples and65new passing Python checks (including original
coverage and29new checks) bind strict indices, exit/resource/identity/limit schemas.
All original4247pins and16initial-review bindings remain unchanged; final manifest
has4262entries. Fresh final gpt-6-astra review independently accepted the correction
with no unresolved findings and no unnecessary candidate work or retained memory.
See [final review](results/MA-S/admission-review-final.md). This is preparation
acceptance only; the numerical schedule remains unconsumed. No numerical seal or
reservation is created here. Use canonical reviewed files for later admission.
''')
replace(status,'MA-S admission preparation is complete, independent review pending. See','MA-S corrected admission preparation is independently accepted with no unresolved\nfindings. Original two P2 schema findings and rejected review are preserved. See')
replace(status,'4247fresh source/runtime bindings and36passing synthetic Python checks.','Canonical launcher-reviewed.py/audit_reviewed.py/admission-reviewed.md and\npins-reviewed.json have4262fresh source/runtime bindings;65new Python checks pass\n(including original coverage). Original4247pins/36checks/review remain unchanged.')
replace(road,'4247fresh pins and36synthetic Python checks. Independent review pending.','Initial4247pins/36synthetic checks and rejected review preserved. One separate\nS1/S2 schema fix accepted by final independent gpt-6-astra review; canonical\nreviewed variants have4262pins/65Python checks, no unresolved findings and no\nunnecessary candidate work/memory. Numerical schedule remains unconsumed.')
with (E/'ledger.md').open('a') as f:f.write('''
Task2 MA-S admission preparation complete; numerical execution remains pending.
Initial review rejected S1/S2/P2 strict-schema omissions. One separate correction
preserved every original file. RED7source-predicate counterexamples,65new Python
checks and5fix-preservation checks passed. Final independent review accepts the
canonical reviewed files and4262pins without unresolved findings or unnecessary
candidate work/memory. No Julia/parser/import/numerics/guard/launcher ran.
Next: fresh host/ref launch-context and independent numerical-review seal, then
one bounded sequence under standing permission. No new permission request needed.
''')
checks=dict(final_review_accepted=True,final_bindings_unchanged=all(sha(p)==s for p,s in review['sha256'].items()),four_beforecopies=all(sha(v['preserved'])==v['sha256'] for v in mapping.values()))
with (E/'completion-check.json').open('x') as f:json.dump(dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in [*paths,E/'completion-map.json',E/'complete-step.py']}),f,indent=2);f.write('\n')
print(checks)
require(all(checks.values()),'Completion failure')
