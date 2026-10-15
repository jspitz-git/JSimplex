"""One-time OFFLINE ownership test amendment after rejected initial review."""
from common import *
require(rd(Q/'review.json')['accepted'] is False,'Expected preserved initial rejection')
test=Q/'candidate/test/native_pivot_policy_tests.jl';manifest=Q/'overlay-manifest.json';report=Q/'REPORT.md';ledger=Q/'WORK-AND-TEST-LEDGER.md';cont=Q/'continuation-text.md'
preserved={test:Q/'tests.before-review.jl',manifest:Q/'overlay-manifest.before-review.json',report:Q/'REPORT.before-review.md',ledger:Q/'WORK-AND-TEST-LEDGER.before-review.md',cont:Q/'continuation.before-review.md'}
old=test.read_text();new=old
replacements=[('''        f=J._basis_factorization(B,Val(mode),Val(:native),policy)
        matrix=updated(f);saved=J.copy_basis_factorization(f)
        owner=saved.base.factorization;ctrl=copy(owner.control);hist=history(saved)''','''        f=J._basis_factorization(B,Val(mode),Val(:native),policy)
        J.refactorize!(f,B) # Populate a private spare BEFORE the copy.
        private_spare=f.base.spare
        @test private_spare !== nothing
        matrix=updated(f);saved=J.copy_basis_factorization(f)
        @test f.base.spare === private_spare
        owner=saved.base.factorization;control_owner=owner.control
        ctrl=copy(owner.control);hist=history(saved)'''),('''        @test owner.control == ctrl
        controls(f.base,symbol);controls(saved.base,symbol)''','''        @test owner.control === control_owner && owner.control == ctrl
        controls(f.base,symbol);controls(saved.base,symbol)'''),('''            owner=f.base.factorization;ctrl=copy(owner.control);hist=history(f)
            @test (f.base.spare !== nothing) == with_spare
            singular=copy(B);fill!(singular.nzval,0.0)''','''            owner=f.base.factorization;control_owner=owner.control
            ctrl=copy(owner.control);hist=history(f)
            @test (f.base.spare !== nothing) == with_spare
            saved=J.copy_basis_factorization(f);saved_hist=history(saved)
            @test saved.base !== f.base && saved.base.factorization === owner
            @test saved.base.spare === nothing
            singular=copy(B);fill!(singular.nzval,0.0)'''),('''            @test owner.control == ctrl && history(f)==hist
            @test f.base.spare === nothing
            controls(f.base,symbol);solves(f,matrix)
            J.refactorize!(f,C)
            controls(f.base,symbol);solves(f,C)''','''            @test owner.control === control_owner && owner.control == ctrl && history(f)==hist
            @test f.base.spare === nothing
            @test saved.base.factorization === owner && history(saved)==saved_hist
            controls(f.base,symbol);solves(f,matrix)
            controls(saved.base,symbol);solves(saved,matrix)
            J.refactorize!(f,C)
            controls(f.base,symbol);solves(f,C)
            @test saved.base.factorization === owner && history(saved)==saved_hist
            @test owner.control === control_owner && owner.control == ctrl
            controls(saved.base,symbol);solves(saved,matrix)''')]
for a,b in replacements:
 require(new.count(a)==1,'Unexpected test amendment anchor');new=new.replace(a,b)
for a,b in reversed(replacements):
 require(new.count(b)==1,'Unexpected inverse anchor')
require('private_spare=f.base.spare' not in old and 'saved_hist=history(saved)' not in old,'Initial coverage not RED')
mapping={str(live):dict(sha256=sha(live),preserved=str(before)) for live,before in preserved.items()}
for live,before in preserved.items():
 with before.open('xb') as f:f.write(live.read_bytes())
test.write_text(new)
z=rd(manifest);matched=[e for e in z['candidate'] if e['destination']=='test/native_pivot_policy_tests.jl'];require(len(matched)==1,'Manifest test entry');matched[0]['sha256']=sha(test)
manifest.write_text(json.dumps(z,indent=2)+'\n')
report.write_text(report.read_text().replace('review.md/json','review-final.md/json')+'''\nInitial review rejected the test gap in populated-spare copy isolation and saved\ncopies across failure. The initial test/manifest/report/ledger/continuation are\npreserved. Separate review-fix.json amends only tests and current text/bindings:\na copy starts with a populated private spare, and both failure paths retain a\nsaved history/control owner with solves before and after the later valid refactor.\nAll seven candidate production files and inverse28 remain unchanged. Initial\nauthor/reviewer selector failures remain preserved; no Julia has been executed.\n''')
ledger.write_text(ledger.read_text()+'''\n## Separate ownership-test correction\n\nInitial review found that copying a fresh factor left the spare-isolation check\nvacuous and the two failure branches held no saved copy. Corrected tests first\npopulate a private spare, then copy a nonempty history and require the saved copy\nto have no spare. Both fresh and spare failures now hold a saved copy and check\nits active/control owners, history and valid solves after failure and after the\nlater valid refactor. This adds8refactor entries,16manager copies and64basis-solve\nentries (32F/32B) to the test text, not production; Task2 must include them in the\nfull budget. These are source counts, not observations or native-internal totals.\nOriginal test source and all original pins/reviews remain preserved.\n''')
cont.write_text(cont.read_text().replace('review.md/json','review-final.md/json').replace('four focused test groups','four focused test groups (including populated-spare copy and saved-copy failure isolation)'))
reverse=new
for a,b in reversed(replacements):reverse=reverse.replace(b,a)
oldmanifest=rd(preserved[manifest]);normalized=rd(manifest)
for e in normalized['candidate']:
 if e['destination']=='test/native_pivot_policy_tests.jl':e['sha256']=mapping[str(test)]['sha256']
checks=dict(initial_coverage_gap='private_spare=f.base.spare' not in old and 'saved_hist=history(saved)' not in old,new_spare_copy='private_spare=f.base.spare' in new and '@test f.base.spare === private_spare' in new,new_failure_saved='saved=J.copy_basis_factorization(f);saved_hist=history(saved)' in new,saved_after_failure_and_recovery=new.count('saved.base.factorization === owner && history(saved)==saved_hist')==2,saved_solves=new.count('controls(saved.base,symbol);solves(saved,matrix)')==2,exact_test_inverse=reverse==old,only_manifest_test_hash=normalized==oldmanifest,production_candidates_unchanged=all(sha(n)==h for n,h in rd(Q/'inverse.json')['candidate'].items()),five_before_maps=len(mapping)==5 and all(sha(m['preserved'])==m['sha256'] for m in mapping.values()),final_review_links=all('review-final.md/json' in p.read_text() for p in [report,cont]))
paths=list(preserved)+list(preserved.values())+[Path(__file__),Q/'review.json',Q/'reviewer-check.json',Q/'inverse.json']
save(Q/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,mappings=mapping,sha256={str(p):sha(p) for p in paths},scope='Offline text coverage correction only. RED/ GREEN are literal coverage absence/presence, not Julia results. All numerical work UNEXECUTED.'))
require(all(checks.values()),'Review fix failed; preserve');print(dict(all_passed=True,checks=len(checks),bindings=len(paths)))
