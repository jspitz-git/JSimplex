"""One bounded offline correction; preserves all original sources and evidence."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def write(p,s):
 with p.open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=(C/'slot-upper.jl').read_text();tests=(C/'slot-upper-tests.jl').read_text();pub=(E/'publication.py').read_text()
red=dict(redundant_prefix_zero='fill!(fresh,zero(T))\n    copyto!' in old,publication_missing_exact_set='set(actual)==expected' not in pub)
need(all(red.values()),'Original finding selectors')
new=old.replace('    fill!(fresh,zero(T))\n    copyto!(fresh,1,old,1,length(old))','    copyto!(fresh,1,old,1,length(old))\n    for i in length(old)+1:C\n        fresh[i]=zero(T)\n    end')
need(new!=old,'Growth fix')
write(C/'slot-upper-reviewed.jl',new)
marker='    for failat in 1:7\n';need(tests.count(marker)==1,'Test insertion anchor')
extra='''    # Success with deliberately dirty fresh buffers: every suffix field must
    # be initialized, independently of memory returned by the allocator.
    U=_bg_slots(_bg_test_matrix(),[3,1,2]); old=_bg_test_buffers(U)
    state=_bg_selected_state(U); C=U.capacity; calls=Ref(0)
    dirtyallocate=function (T,n)
        calls[]+=1
        return fill(T(77),n)
    end
    _bg_reserve_with!(U,C+1,dirtyallocate)
    @test calls[]==7 && U.capacity==32 && _check_bg_slots(U)
    @test all(isequal(a,b[1:C]) for (a,b) in zip(old,_bg_test_buffers(U)))
    @test all(a!==b for (a,b) in zip(old,_bg_test_buffers(U)))
    @test isequal(_bg_selected_state(U),state)
'''
write(C/'slot-upper-tests-reviewed.jl',tests.replace(marker,extra+marker))
prep=(C/'prepare-overlay.py').read_text()
prep=prep.replace('task1-stage','task1-reviewed-stage').replace("C/'slot-upper.jl'","C/'slot-upper-reviewed.jl'").replace("C/'slot-upper-tests.jl'","C/'slot-upper-tests-reviewed.jl'").replace("E/'overlay.json'","E/'overlay-reviewed.json'").replace("E/'preparation-pins.json'","E/'preparation-pins-reviewed.json'")
write(C/'prepare-reviewed.py',prep)
for name in ['publication.py','REPORT.md','progress.md']:
 write(E/(name+'.before-review'),(E/name).read_text())
needle="names=sorted([str(q.relative_to(R)) for q in list(P.rglob('*')) if q.is_file()]+[str(q.relative_to(R)) for q in C.iterdir() if q.is_file()]+extras+[str((P/n).relative_to(R)) for n in ['publication-names.json','publication.json']])"
replacement="actual=[str(q.relative_to(R)) for q in P.rglob('*') if q.is_file()]+[str(q.relative_to(R)) for q in C.iterdir() if q.is_file()]+extras\nexpected=set(c['sha256'])|{str((P/'closure.json').relative_to(R))}\nneed(len(actual)==len(set(actual)) and set(actual)==expected,'Unbound/missing prepublication file')\nnames=sorted(actual+[str((P/n).relative_to(R)) for n in ['publication-names.json','publication.json']])"
need(needle in pub,'Publication selector');pub=pub.replace(needle,replacement);(E/'publication.py').write_text(pub)
checks=(E/'offline-check.py').read_text().replace("C/'slot-upper.jl'","C/'slot-upper-reviewed.jl'").replace("C/'slot-upper-tests.jl'","C/'slot-upper-tests-reviewed.jl'").replace("E/'overlay.json'","E/'overlay-reviewed.json'").replace("E/'offline-check.json'","E/'offline-check-reviewed.json'").replace('18 source-text/ownership/manifest checks','19 source-text/ownership/manifest checks')
write(E/'offline-check-reviewed.py',checks)
report=(E/'REPORT.md').read_text().replace('reproduce/slot-upper.jl','reproduce/slot-upper-reviewed.jl').replace('The new prepare-overlay.py copies','The original prepare-overlay.py and canonical prepare-reviewed.py each copy').replace('It initializes buffers and copies seven old prefixes;','The reviewed version initializes only appended suffixes and copies seven old prefixes;')
report+='''
## Independent review amendments

Initial review I1 found seven redundant prefix fills: 7*C stores or56*C bytes of
avoidable writes per growth on64-bit. The separate reviewed candidate copies the
old prefix and initializes only the appended suffix. The fresh-buffer success
oracle starts every new element at77; all seven OOM tests remain unchanged and
unexecuted. No measured work/time or allocation reduction is inferred.

I2's frozen original offline scope string says18 checks; its mapping has19. The
original record/script remain unchanged. This report and the separate reviewed
checker identify19 textual checks, not Julia assertions. This annotation has no
runtime impact and is explicitly reconciled, not retroactively rewritten.

I3's new publication guard requires actual prepublication paths to equal exactly
all closure-bound paths plus closure.json, rejecting any added unbound file before
staging. A pure Python set-gate test covers extra/missing/duplicate paths below the
real Git boundary; no publication is executed by that synthetic check.

Canonical files are selected in canonical.json. Original candidate/tests, original
77-file overlay and manifests remain SUPERSEDED/UNEXECUTED and frozen. Reviewed
candidate/tests/prepare script and their distinct77-file overlay are authoritative.
Full initial review bindings resolve changed REPORT/progress/publication through
their .before-review copies. No other earlier binding changes.
'''
(E/'REPORT.md').write_text(report)
progress=(E/'progress.md').read_text()+'''\nFinal review correction I1: separate reviewed growth implementation initializes suffix only; new dirty-allocator success oracle UNEXECUTED. Offline text RED→GREEN only, no runtime test claim.\nFinal review annotation I2: preserve original18-label/19-check record and explain the exact19 scope in REPORT; no runtime significance.\nFinal review correction I3: prepublication exact file membership, synthetic added/missing/duplicate cases tested offline before Git stage.\nRuling: Keep superseded candidate/tests/overlay and exclusive scripts frozen; reviewed successors are canonical. No Task2 or Julia despite general continuous-execution skill.\n'''
(E/'progress.md').write_text(progress);(R/'.superpowers/sdd/2026-10-16-direct-bg-dynamic-upper/progress.md').write_text(progress)
green=dict(suffix_only='fill!(fresh,zero(T))' not in new and 'for i in length(old)+1:C' in new,seven_oom_cases='for failat in 1:7' in tests,dirty_allocator_test='return fill(T(77),n)' in (C/'slot-upper-tests-reviewed.jl').read_text(),exact_publication='set(actual)==expected' in pub)
need(all(green.values()),'Correction checks')
# Extract ONLY new pure set expression, not the publication script or Git calls.
expression='len(actual)==len(set(actual)) and set(actual)==expected'
cases=[(['a','b'],{'a','b'},True),(['a','b','new'],{'a','b'},False),(['a'],{'a','b'},False),(['a','a','b'],{'a','b'},False)]
for actual,expected,want in cases:need(eval(expression,{'__builtins__':{},'len':len,'set':set},{'actual':actual,'expected':expected})==want,'Synthetic membership')
paths=[C/n for n in ['slot-upper-reviewed.jl','slot-upper-tests-reviewed.jl','prepare-reviewed.py']]+[E/n for n in ['publication.py','REPORT.md','progress.md','offline-check-reviewed.py','review-fix.py']]
save(E/'review-fix.json',dict(all_passed=True,red=red,green=green,membership_cases=4,scope='Offline source amendment and pure Python membership check; all Julia tests UNEXECUTED',sha256={str(p):sha(p) for p in paths}))
print('Single amendment: RED2/GREEN4 +4 membership cases PASS; no Julia')
