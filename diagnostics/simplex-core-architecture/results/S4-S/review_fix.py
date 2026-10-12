from pathlib import Path
import hashlib,json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-S';report=D/'S4-ISOLATED-MODULE-LOADING-CONTRACT.md';plan=R/'docs/superpowers/plans/2026-10-12-hh-isolated-public-lp-work-contract.md';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before={}
for p,n in [(report,'report-before-keyword.md'),(plan,'next-plan-before-keyword.md')]:
 with (E/n).open('xb') as f:f.write(p.read_bytes())
 before[str(p)]=dict(sha256=sha(p),preserved=str(E/n))
t=report.read_text();red='Core.kwcall' in t
anchor='No coincident explicit/generated external signature was identified in this pinned closure.'
addition='''Keyword lowering adds further implicit entries: `Base.sizehint!(::UpperRowIndices,...;
kwargs...)` creates a Core.kwcall method whose positional arguments still contain the
fresh UpperRowIndices type, plus a local keyword body. Other local keyword functions
and @kwdef constructors dispatch through their fresh callable/type identities. These
lowered methods also consume method-table/JIT metadata. The29 explicit plus20 enum
signatures are therefore NOT a complete runtime method count; no keyword-lowering
method table was captured. Fresh owned dispatch prevents the identified keyword routes
from replacing the corresponding production methods under the same preconditions.

'''
assert t.count(anchor)==1;report.write_text(t.replace(anchor,addition+anchor))
t=plan.read_text();anchor='64 files per side, shared external methods/libraries, duplicated metadata/input objects.';assert t.count(anchor)==1;plan.write_text(t.replace(anchor,anchor+'\nInclude implicit keyword-lowering Core.kwcall/local keyword bodies; S explicit/enum\ncounts are not a complete runtime method count.'))
checks=dict(before_missing_keyword=not red,report_keyword_owned_scope='Core.kwcall' in report.read_text() and 'NOT a complete runtime method count' in report.read_text(),next_plan_keyword_accounting='Core.kwcall' in plan.read_text(),preserved_before_hashes=all(sha(x['preserved'])==x['sha256'] for x in before.values()))
obj=dict(finding='Minor: document implicit keyword-lowering methods, no isolation defect',before=before,after={str(p):sha(p) for p in (report,plan)},checks=checks,all_passed=all(checks.values()),scope='One offline textual correction; no manifest/input/source/clone/auditor edits or reruns')
with (E/'review-fix.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(obj));assert obj['all_passed']
