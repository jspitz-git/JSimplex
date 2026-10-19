"""One new offline closure after independent acceptance; no Julia/action entrypoints."""
from pathlib import Path
import hashlib,json,subprocess
import control as c
D=Path(__file__).resolve().parent;R=D.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
review=rd(D/'review.json');pins=rd(D/'preparation-pins.json')
check('independent_preparation_accepted',review['accepted'] is True and review['findings']==[] and review['launch_admitted'] is False)
c.preparation();check('actual_preparation_gate_and_exact_bindings',True)
check('exact_258_inputs_and_259_review_bindings',len(pins['sha256'])==258 and len(review['sha256'])==259)
check('new_synthetic_checks',rd(D/'tests-reviewed.json')['all_passed'] is True and rd(D/'tests-reviewed.json')['count']==894)
check('new_synthetic_bindings',all(sha(D/n)==h for n,h in rd(D/'tests-reviewed.json')['sha256'].items()))
regression=rd(D/'reviewer-regression-results.json')
check('independent_regression_364_pass',regression['all_passed'] is True and regression['count']==364 and all(row['passed'] is True for row in regression['checks']))
fc=rd(D/'review-fix-check.json');mapping=rd(D/'final-mappings.json')['correction_check_maps']
check('fourteen_correction_checks',fc['all_passed'] is True and len(fc['checks'])==14 and all(fc['checks'].values()))
check('correction_check_47_bindings',len(fc['sha256'])==47 and all(sha(mapping.get(n,n))==h for n,h in fc['sha256'].items()))
before=rd(D/'review-fix-provenance.json')['before']
def oldbindings(v):return all(sha(before[n]['preserved_path'] if n in before else n)==h for n,h in v.items())
initial=rd(D/'review.json.before-review')
check('initial_rejection_and_235_bindings_preserved',initial['accepted'] is False and len(initial['findings'])==1 and len(initial['sha256'])==235 and oldbindings(initial['sha256']) and oldbindings(initial['evidence_sha256']))
check('initial_756_of_759_preserved',rd(D/'reviewer-results.json')['passed']==756 and rd(D/'reviewer-results.json')['count']==759 and rd(D/'reviewer-results.json')['all_passed'] is False)
check('initial_source_bindings_preserved',oldbindings(rd(D/'source-check.json')['sha256']))
check('master_unchanged',git('rev-parse','master')==c.MASTER)
check('diagnostic_entry',git('rev-parse','HEAD')==c.ENTRY and git('branch','--show-current')=='codex/simplex-core-architecture')
check('tracked_and_index_unchanged',git('diff','--name-only')=='' and git('diff','--cached','--name-only')=='')
check('no_run_or_admission',all(not (D/n).exists() for n in ['runs','outers','sealed.json','reservation.json','release.json']))
check('exact_source_and_driver_pins',all(sha(n)==h for n,h in rd(D/'preparation-pins.json.before-review')['sha256'].items() if not n.startswith(str(D)+'/')) and sha(D/'driver.jl')==rd(D/'preparation-pins.json.before-review')['sha256'][str(D/'driver.jl')])
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
old=(D/'progress.md.before-p011-harness').read_bytes()
check('continuation_before_preserved',ledger.read_bytes()==old)
append=b'\n\nP011 typed RED/GREEN harness OFFLINE independently accepted after one Important auditor correction; initial rejected review and 756/759 results preserved. New synthetic894/source14 checks PASS; final preparation258 subjects/review259 bindings. Same accepted shared-zero kernel and ordinary master stage both phases: original structural RED expects11759pass/1P011fail, repaired GREEN11768pass/0fail; all four structural groups once, no lifecycle/streams or sixN026 coverage. Separate typed probe requires four strict zero byte/event counters, complete decisions, value/owner preservation; six preparation/cost records plus probe/unit/raw. Exact original P011 expression/location/439-character failure rendering only; warnings checked before stripping. No208-byte oracle. Initial amendment newline-selector refusal preserved before any original edit. New final manifest and explicit before/intermediate mappings, no retroactive acceptance. No Julia/parser/import/compile/IR/numerics/outer/seal/release/reservation or old script rerun. Limit300s supervisor/292s child; fresh exact independent RED admission required next, GREEN only after new accepted RED/external closure/result review. Cold probe/snapshot/serialization overhead charged; tests-cost includes unit serialization, windows overlap, no speedup or production work/memory change. Master26e2291/CI/globalSTATUSroadmap unchanged, broaderplanopen. All new evidence/scripts frozen after publication.\n'
after=old+append
with (D/'progress.md.after-p011-harness').open('xb') as f:f.write(after)
ledger.write_bytes(after)
check('continuation_exact_append',ledger.read_bytes()==after and after.startswith(old))
files=sorted(p for p in D.iterdir() if p.is_file())
with (D/'closure.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope='Offline preparation only; no launch/runtime acceptance',sha256={str(p):sha(p) for p in files}),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(files))))
