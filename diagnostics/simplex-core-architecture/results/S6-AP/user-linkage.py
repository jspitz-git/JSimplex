"""Exclusive source/evidence update for new human clarification; no script execution."""
from pathlib import Path
import hashlib,json
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
report=D/'S6-TEST-MPS-FAILURE-PROVENANCE.md';plan=R/'docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md';maps=[]
for p in [report,plan,H/'review.md']:
 q=H/(p.name+'.before-user-reply');b=p.read_bytes()
 with q.open('xb') as f:f.write(b)
 maps.append(dict(original=str(p),preserved=str(q),sha256=hashlib.sha256(b).hexdigest()))
with (H/'user-reply-before-texts.json').open('x') as f:json.dump(dict(mappings=maps),f,indent=2);f.write('\n')
old=report.read_text()
notice='''## Subsequent user clarification (authoritative update)

After the initial record and its independent acceptance below, the user supplied
the calling script and confirmed `C:\\tmp\\test.mps`, native reader,
`relax_integrality=true`, HH/native, interval320, dual, legacy, steepest_edge,
iteration_limit1000000 and time_limitInf. This establishes the **user-reported
invocation**, not a captured runtime configuration. The inactive else branch uses
PFI/80 and must not be attributed to the reported solve. Defaults for options not
explicitly supplied still depend on the unknown original source version.

The user does not know the commit, reports approximately 01:00 today (2026-10-13),
and an AMD computer with 8 BLAS threads. These are human provenance statements,
not a runtime thread/version capture. Approximate time cannot select a commit.
Current `/mnt/c/tmp/test.mps` is absent, so no Windows file hash was obtained.
The Linux S0/F11 model hash and dimension match remain supporting evidence only.
No original point/basis/dual witness was supplied. The source interpretation and
unresolved failure are unchanged. Do not repeat the already answered command
question or ask the user to know an unknown commit.

`results/S6-AP/user-clarification.txt` transcribes the reply with normalized
indentation/line endings; it is not an original script-file byte capture. The
initial report, plan and acceptance are preserved as `*.before-user-reply`.
The initial missing-command statements below describe the evidence **before**
this clarification; the invocation gap is now partly filled as stated above.

## Initial record before that clarification

'''
report.write_text(old.replace('# S6-AP: reported test.mps failure provenance\n\n','# S6-AP: reported test.mps failure provenance\n\n'+notice,1))
plan.write_text('''# S6-AQ: conditional original source/witness linkage supplement

S6-AP now includes the user's explicit test.mps native-reader HH/native320 dual
legacy script, Inf/1000000/steepest_edge/relax_integrality settings, approximate
01:00 on 2026-10-13, AMD and user-reported 8 BLAS threads. Do not ask for this script
again or infer a source commit from the approximate time. The user does not know
that commit. Current Windows test_new.jl names runtime.mps and is not the old script.
Current C:\\tmp\\test.mps and the referenced capture-failure.jl are absent here.

Continue only when genuinely new original source/runtime metadata, input hash,
or already stored point/basis/dual certificate input is available. The historical
source/witness linkage gap remains explicit; no equivalent search without new
information. Current Manifest tree and a later installed package cannot silently
become the original source. User-reported settings are not runtime observations.
No proof of the rejecting certificate subpredicate or original arithmetic cause
exists. The historical failure and broader roadmap remain unresolved.

SOURCE/EVIDENCE ONLY: no Julia/query/parser/import/compile/native/numerical call,
model arithmetic, fixture, executable candidate/driver/launcher, benchmark, test,
production/env/cache/CI change, old script/auditor rerun or new numerical allowance.
No HH/DSE/controller/import/isolation or deferred cleanup omission audits.
A new reproduction needs a separately frozen reviewed admission and numerical
allowance; neither this plan nor the supplied old command authorizes one.
Preserve AP's initial and updated records and their exact hash mappings. New claims
require fresh independent gpt-6-astra numerical/work/memory review, separate PASS
closure and exact complete staged names/blobs before failfast publication/push.
Master d02416c, CI-off, HH reuse disabled and all broader gates/rejections persist.
''')
c={'initial_report_preserved':report.read_text().endswith(old.split('\n\n',1)[1]),'initial_review_preserved':(H/'review.md.before-user-reply').read_bytes()==(H/'review.md').read_bytes(),'native_branch_settings_transcribed':all(t in (H/'user-clarification.txt').read_text() for t in ['filename = "test.mps"','reader_native = true','basis_update=:huangfu_hall','basis_refactorization=:native','refactorization_interval=320','algorithm=:dual','simplex_strategy=:legacy','time_limit=Inf','iteration_limit=1_000_000','relax_integrality=true']),'user_report_not_runtime':'user-reported' in report.read_text() and 'not a runtime thread/version capture' in report.read_text(),'unknown_commit_explicit':'user does not know' in report.read_text(),'windows_model_absent':not Path('/mnt/c/tmp/test.mps').exists(),'witness_gap_preserved':'No original point/basis/dual witness was supplied' in report.read_text(),'no_repeat_answered_question':'Do not ask for this script' in plan.read_text(),'no_new_numerical_allowance':'old script/auditor rerun or new numerical allowance.' in plan.read_text()}
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [report,plan,H/'user-clarification.txt',H/'user-reply-before-texts.json',*[Path(x['preserved']) for x in maps],Path(__file__)]}
with (H/'user-linkage.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=pins,windows_model_exists=False),f,indent=2);f.write('\n')
print(c);assert all(c.values())
