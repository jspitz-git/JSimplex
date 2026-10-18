"""Bounded independent final review; text/hash checks only, no author code imports."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;checks={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
p=D/'preparation-pins.json';current=rd(p)['sha256'];initial=rd(D/'review-initial.json');oldpins=rd(D/'preparation-pins.json.before-review')['sha256']
check('all1871_current_hashes',len(current)==1871 and all(sha(n)==h for n,h in current.items()))
check('exact_current_membership',set(current)==set(rd(D/'required-paths.json')['paths']))
check('original1865_membership',len(oldpins)==1865 and set(oldpins)==set(rd(D/'required-paths.json.before-review')['paths']))
changed={n for n in oldpins if current[n]!=oldpins[n]}
check('only_expected_input_hash_changes',changed=={str(D/'work-ledger.json'),str(D/'required-paths.json')})
added=set(current)-set(oldpins)
check('six_added_correction_artifacts',added=={str(D/n) for n in ['work-ledger.json.before-review','required-paths.json.before-review','preparation-pins.json.before-review','review-fix.py','review-fix.json','REVIEW-AMENDMENT.md']})
for n,h in initial['sha256'].items():
 q=Path(n)
 if q.name in ('work-ledger.json','required-paths.json','preparation-pins.json') and q.parent==D:q=q.with_name(q.name+'.before-review')
 check('initial_binding_'+n,sha(q)==h)
check('initial_evidence_unchanged',all(sha(n)==h for n,h in initial['evidence_sha256'].items()))
for n,h in rd(D/'source-check.json')['sha256'].items():
 q=Path(n)
 if q==D/'work-ledger.json':q=D/'work-ledger.json.before-review'
 check('source_check_binding_'+n,sha(q)==h)
old=rd(D/'work-ledger.json.before-review');new=rd(D/'work-ledger.json');field=new['new_storage_only_pair_work']['full_partition_token_scans'];old['new_storage_only_pair_work']['full_partition_token_scans']=field
check('only_R1_ledger_field_changed',old==new)
check('R1_corrected','two n-entry Int vector conversions and sorts' in field and 'not asserted linear' in field and 'unmeasured' in field)
check('fix_evidence',rd(D/'review-fix.json')['all_passed'] and all(sha(n)==h for n,h in rd(D/'review-fix.json')['sha256'].items()))
for mode,v in rd(D/'stages.json').items():
 root=Path(v['path']);check('exact_final_stage_'+mode,{str(q.relative_to(root)) for q in root.rglob('*') if q.is_file()}==set(v['sha256']) and not any(q.is_symlink() for q in root.rglob('*')) and all(sha(root/n)==h for n,h in v['sha256'].items()))
check('no_phase_activity',not (D/'runs').exists())
summary=dict(all_passed=all(checks.values()),checks=checks,bindings_verified=len(current),pins_sha256=sha(p),resolved_findings=['R1'],scope='Bounded independent recheck: all current pins, all initial mapped bindings, exact stages and one ledger field; no Julia/author script execution')
save('reviewer-final-check.json',summary)
text='''# Independent split BG driver preparation review — final

Accepted for offline RED/GREEN driver and admission preparation only. Initial minor finding R1 is resolved. Unresolved findings:0. This review grants no numerical allowance, runtime correctness, performance, memory-peak or public-solver acceptance. Cost preparation and each future exact-stage admission remain separate work.

Independent saved reviewer-owned Python text/hash/integer checks verified all1,865initial preparation inputs, all609runtime hashes and resolved paths, and exact75-file RED/81-file GREEN stage membership and source copies. Frozen candidate, oracle, fixture and test files match committed HEAD. Final verification freshly rehashed all1,871current inputs, checked every initial binding against the exact preserved originals, and rechecked stage membership. Only the work-ledger wording and corresponding required/preparation manifests changed; all numeric budgets, candidate/test/driver/control sources are unchanged.

The ten RED symbols are absent from the accepted DIRECT baseline and present in the split candidate. No unmodified-master shortcut is used. GREEN includes25structural and9adapter leaf groups, prospective15,929Test assertions. The inherited structural counts and all11new structural groups were independently expanded from source. The seven inherited adapter counts retain their accepted frozen-body derivation; the two added groups independently expand to284and51. Exact JSON/TOML group order and counts match. These are source predictions, not executed Julia results.

The allocator count independently follows row reserve, seven-array descriptor reserve, three slab buffers, three directories and optional suffix reserve. The inherited calibrations are21,21,14; build90and copy69. An independent integer model of ordered bins, extent capacities and row membership confirms52callbacks for monotone32 and60,0,0for three40fill/delete cycles. Thus706explicit probe operations,419injected failures,10,392callback attempts and9,973completed requests are consistent. The new adapter loops perform129paired scalar edits,3rotations and1row merge without extra solves on substituted matrices. The389factorization count means outer attempted entries only; backend/export/native/normalization/loader work and fixture factories remain additional.

Control source lineage was checked byte-for-byte under its declared transformations. Guard/supervisor/recorder are identical to accepted sources. Top-level includes precede main; raw evidence precedes count aggregation. Loaded paths include Test and require exact membership. Warning/world-age rejection precedes both successful acceptance and pure-timeout return. RED success requires exactly10declared failures; GREEN requires the full tree and accepted reviewed RED. Fresh seal, exact review membership, source/runtime/environment integrity and exclusive reservation precede every launch. Only separately reviewed pure300timeout may permit600; limits remain300/292or600/592. Full PGID AND SID checks, boot/start/command identity, pidfd-owned cleanup, terminal resources and posthost closure are retained. No old or author control code was run by this reviewer.

No unnecessary new production work or retained-memory mechanism was found. Candidate numerical methods and fields are frozen; the driver orchestrates correctness tests only. Full invariants, materializations, bit snapshots, Rational residuals and failure snapshots are intentional bounded test costs. R1 corrected the test-only O(n+C+R+K) traversal statement to separately include two n-entry Int conversions/sorts and invariant allocations, without claiming overall linear or measured cost. The initial ledger, manifests and review are preserved by exact mappings. Header/backing, lower/backend/cache/history, old/new copy/refactor coexistence and high-water fragmented reserve remain additional; no allocation reduction or speedup is inferred.

Fresh read-only host inspection during the initial independent check found no matching historical group/session or visible Julia, with240groups inspected. Inaccessible executable links are explicitly retained as a visibility limit. This does not replace the future fresh host/resource admission. No runs directory exists. No Julia query/parser/import/compile/numerics, seal, launcher, auditor, Git mutation or publication was performed by this review. Actual loading, warning freedom, dispatch, assertion results and runtime memory remain unexecuted.
'''
with (D/'review.md').open('x') as f:f.write(text)
evidence=['review-initial.md','review-initial.json','reviewer-check.py','reviewer-check.json','reviewer-initial-record.py','reviewer-final-check.py','reviewer-final-check.json','review.md']
review=dict(accepted=True,findings=[],scope='split BG driver preparation',pins_sha256=sha(p),sha256=dict(current,**{str(p):sha(p)}),evidence_sha256={str(D/n):sha(D/n) for n in evidence},resolved_findings=['R1'],numerical_allowance=False,runtime_acceptance=False,julia_executed=False)
check('final_review_schema',set(review['sha256'])==set(current)|{str(p)} and review['pins_sha256']==sha(p) and all(sha(n)==h for n,h in review['evidence_sha256'].items()))
save('review.json',review)
print(json.dumps(dict(accepted=True,findings=[],current_inputs=len(current),review_bindings=len(review['sha256']),pins_sha256=review['pins_sha256'],resolved=['R1'],runtime_acceptance=False)))
